# EEG Data Leakage Mechanisms: Taxonomy and Controls

This document details the nine primary data leakage pathways identified in the literature, their mathematical mechanisms, their evidence tiers in LeakCheck, and the strict prevention controls enforced by the framework.

---

## 1. Leakage Taxonomy (P1–P9)

| Key | Mechanism Name | Nature | Evidence Tier | Impact on Accuracy |
|---|---|---|---|---|
| **P1** | **Supervised Spatial Filter Leakage** | Supervised | **Tier 1 (Empirically Proven)** | Severe Artificial Inflation ($+24.50$ pp on PhysioNet, $+6.25$ pp on OpenBMI) |
| **P2** | **Unsupervised Spatial Filter Leakage (ICA)** | Unsupervised | **Tier 2 (Architecturally Designed)** | Moderate Shift (contaminates artifact rejection subspaces) |
| **P3** | **Temporal Filter / Boundary Leakage** | Unsupervised | **Tier 3 (Registry Protocol)** | Subtle Inflation / Edge Discontinuities |
| **P4** | **Temporal Window Peeking** | Supervised | **Tier 3 (Registry Protocol)** | Optimistic Bias (tuning post-cue window to test metrics) |
| **P5** | **Global Feature Normalization** | Unsupervised | **Tier 2 (Prototype Implemented)** | Mild to Moderate Distortion |
| **P6** | **Cross-Validation Hyperparameter Snooping** | Supervised | **Tier 2 (Prototype Implemented)** | Overfitting to Validation Fold |
| **P7** | **Global Feature Selection** | Supervised | **Tier 3 (Registry Protocol)** | Extreme Inflation (analogous to P1) |
| **P8** | **Sliding Window / Segment Overlap Leakage** | Structural | **Tier 3 (Registry Protocol)** | Massive Pseudo-Replication Inflation |
| **P9** | **Subject Identity Confounding** | Structural | **Tier 3 (Registry Protocol)** | Complete Invalidation of Cross-Subject Generalization |

---

## 2. In-Depth Analysis of Key Mechanisms

### 2.1 Mechanism P1: Supervised Spatial Filtering on Pooled Data
**The Flaw**: Common Spatial Pattern (CSP) spatial filters are fitted on the entire dataset $\mathcal{D} = \mathcal{D}_{\text{train}} \cup \mathcal{D}_{\text{test}}$ prior to partitioning into cross-validation folds.

**Mathematical Pathway**:
The CSP algorithm finds spatial projection vectors $\mathbf{w}$ that maximize variance for class 1 while minimizing variance for class 2 by solving the generalized eigenvalue problem:
$$\mathbf{\Sigma}_1 \mathbf{w} = \lambda \mathbf{\Sigma}_2 \mathbf{w}$$
where $\mathbf{\Sigma}_c$ is the average spatial covariance matrix for class $c$:
$$\mathbf{\Sigma}_c = \frac{1}{|\mathcal{I}_c|} \sum_{i \in \mathcal{I}_c} \frac{\mathbf{x}_i \mathbf{x}_i^\top}{\operatorname{tr}(\mathbf{x}_i \mathbf{x}_i^\top)}$$

When $\mathcal{I}_c$ includes test-set indices, $\mathbf{\Sigma}_c$ directly encodes the spatial covariance structure of the unseen test trials. As a consequence:
1. The projection filters $\mathbf{w}$ are explicitly aligned to project the test trials into well-separated clusters.
2. Even if the raw EEG data consists of **pure white noise**, fitting CSP on the entire dataset produces artificial accuracies exceeding $80\%\text{--}90\%$.
3. On real datasets, this injects **$+24.50$ pp** of artificial accuracy on PhysioNet and **$+6.25$ pp** on OpenBMI.

### 2.2 Mechanism P2: Unsupervised Spatial Filtering (ICA on Concatenated Runs)
**The Flaw**: Independent Component Analysis (ICA) is computed across concatenated recording blocks containing both train and test trials to remove ocular or cardiac artifacts.

**Mathematical Pathway**:
While ICA is unsupervised (class labels are not used), fitting the unmixing matrix $\mathbf{W}_{\text{ICA}}$ on continuous data spanning all runs allows statistical dependencies, slow baseline drifts, and subject state changes from the test runs to influence the spatial decomposition applied to training trials.

### 2.3 Mechanism P5: Global Feature Normalization
**The Flaw**: Feature matrices $\mathbf{F} \in \mathbb{R}^{N \times d}$ are z-score standardized using the global mean and standard deviation:
$$\mu = \frac{1}{N} \sum_{i=1}^N \mathbf{f}_i, \quad \sigma = \sqrt{\frac{1}{N} \sum_{i=1}^N (\mathbf{f}_i - \mu)^2}$$
$$\hat{\mathbf{f}}_i = \frac{\mathbf{f}_i - \mu}{\sigma}$$

**Mathematical Pathway**:
Test features directly contribute to $\mu$ and $\sigma$, centering and scaling training vectors relative to the test distribution. In stationary conditions, the bias is modest, but under distribution shifts (e.g., sensor drying or impedance increases), global normalization leaks the distribution shift into the training pipeline.

### 2.4 Mechanism P8: Sliding Window Overlap Leakage
**The Flaw**: Slicing continuous EEG into overlapping windows (e.g. 2-second windows with 75% overlap) and then performing random train/test splits.

**Mathematical Pathway**:
Two successive overlapping windows share 75% of their raw temporal samples. When one window is placed in the training set and its neighbor is placed in the test set, the classifier is effectively tested on data it has already seen during training, producing near-perfect, completely ungeneralizable classification scores.

---

## 3. Decoder Resilience: CSP vs. Riemannian Geometry

A critical finding from LeakCheck V2 is the comparative susceptibility of spatial filtering vs. Riemannian geometry decoders to spatial leakage:

| Decoder | Spatial Projection | Vulnerability to P1 | Explanation |
|---|---|---|---|
| **Shrinkage CSP-LDA** | Supervised generalized eigenvectors | **Extremely Vulnerable** ($+6.25$ to $+24.50$ pp) | Uses test class labels directly to optimize spatial variance filters. |
| **Riemannian TS-LR** | Unsupervised Fréchet covariance mean | **Resilient but not immune** ($+0.75$ pp on OpenBMI, $p = 0.0203$) | Covariance matrices and Fréchet reference points are computed without class labels; test set inclusion causes only a minor reference shift. |

---

## 4. Prevention and Defensive Auditing Rules

To guarantee zero leakage, scientific EEG pipelines must enforce the following invariants:

1. **Strict Scikit-Learn Pipeline Encapsulation**: All transformations that depend on training data (CSP, PCA, Scaler, Imputer) must reside inside an `sklearn.pipeline.Pipeline` or equivalent container and be called strictly via `.fit(X_train, y_train)` and `.transform(X_test)`.
2. **Block-Level Group Splitting**: When cross-validating multi-run recordings, use `GroupKFold` or `LeaveOneGroupOut` with recording run IDs as groups.
3. **No Epoch Slicing Prior to Splitting**: Slicing overlapping sub-windows must happen strictly *after* cross-validation partitioning, or within-run fold grouping must be preserved.
4. **Pre-Registration of Evaluation Scripts**: Validation scripts should produce cryptographic manifests (as done by `scripts/run_openbmi_benchmark.py`) locking data hashes and split indices before reporting benchmark metrics.
