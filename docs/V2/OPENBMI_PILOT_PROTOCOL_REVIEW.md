# Scientific Protocol Specification & Review: OpenBMI Replication Benchmark (Revised)

**Document Identifier**: `docs/V2/OPENBMI_PILOT_PROTOCOL_REVIEW.md`  
**Dataset Target**: OpenBMI (Lee et al. 2019) Session 1 Intact Cohort ($N=34$)  
**Target Runner**: `scripts/run_openbmi_benchmark.py`  
**Date**: November 2026 (Revised Post-Consolidated Review)  
**Status**: APPROVED REVISED SPECIFICATION — IMPLEMENTATION READY PENDING GATE 3A

---

## 1. Scientific Objective & Formal Interpretive Boundary

The primary scientific objective of the OpenBMI Replication Benchmark is to evaluate whether the empirical validation phenomena discovered in PhysioNet EEGMMIDB ($N=105$):
1. **Validation Design Divergence**: Differences between random trial-level validation ($D_{1s}$) and operational out-of-block evaluation ($D_3$ Leave-One-Run-Out); and
2. **Supervised Spatial Contamination**: Performance inflation from transductive spatial filtering ($P_1$ Common Spatial Patterns fitted on all trials);
generalize to an independent, high-density (62-channel BrainAmp), internationally collected motor imagery cohort ($N=34$) under zero network download conditions.

### Inviolable Scientific Interpretation (Consolidated Review Consensus)
> **Defensible Scientific Wording**:
> $D_{1s}$ evaluates random trial-level generalization across a pooled two-run dataset, while $D_3$ evaluates transfer to a held-out operational run. Their matched training and test sizes and class distributions reduce sample-size and class-balance confounding. Differences between them reflect the combined consequences of run-wise distribution shift and the dependence structure preserved or disrupted by the respective partitioning strategies.
>
> The $D_{1s} - D_3$ contrast **does not isolate a single causal effect called "run boundaries."** In OpenBMI Session 1, Run 0 is offline calibration and Run 1 is online feedback; differences between them reflect operational transfer between these distinct behavioural and recording blocks. Furthermore, Session 1 operational transfer does not establish cross-day or cross-session generalization (which requires Session 2 and a $D_6$ Leave-One-Session-Out design).

---

## 2. Experimental Design: Primary Triad (Option B Adopted)

To eliminate algorithmic redundancy between $D_{1m}$ and $D_{1s}$ (identified in Section 2 of the Consolidated Review), the OpenBMI benchmark adopts **Option B (Simplified Primary Triad)**:

```
+---------------------------------------------------------------------------------------------------------+
|                                    OPENBMI REPLICATION PROTOCOL MATRIX                                  |
+-------------+---------------------+----------+--------------+-------------+-----------------------------+
| Design ID   | Scientific Role     | Folds(k) | N_train / N_te| Class Ratio | Partitioning Mechanism      |
+-------------+---------------------+----------+--------------+-------------+-----------------------------+
| **D3**      | Primary Operational | 2        | 100 / 100    | 50L / 50R   | Leave-One-Run-Out (Run0/Run1|
| **D1s**     | Primary Randomized  | 2 (x20)  | 100 / 100    | 50L / 50R   | Pooled Random Partition     |
| **P1**      | Positive Control    | 2        | 100 / 100    | 50L / 50R   | Global CSP Leaked into D3   |
| *D1m*       | Secondary Sensitiv. | 2 (x5)   | 100 / 100    | 50L / 50R   | Standard StratifiedKFold    |
+-------------+---------------------+----------+--------------+-------------+-----------------------------+
```

### 2.1 Protocol 1: Operational Reference ($D_3$ Leave-One-Run-Out)
- Evaluates operational transfer across the two recording blocks:
  - Fold 1: Train Run 0 (Offline Calibration, 100 trials: 50L, 50R) $\rightarrow$ Test Run 1 (Online Feedback, 100 trials: 50L, 50R).
  - Fold 2: Train Run 1 (Online Feedback, 100 trials: 50L, 50R) $\rightarrow$ Test Run 0 (Offline Calibration, 100 trials: 50L, 50R).
- Preprocessing and decoders are fitted strictly on the training run. Zero information crosses the run boundary.

### 2.2 Protocol 2: Size- and Class-Matched Pooled Random Partition ($D_{1s}$)
- Pools the 100 Left Hand and 100 Right Hand trials across both runs (200 trials total).
- For each repeat $r \in \{0, \dots, 19\}$ (`seed = 0 + r`):
  1. Shuffles Left Hand trials without replacement into two disjoint sets of 50.
  2. Shuffles Right Hand trials without replacement into two disjoint sets of 50.
  3. Fold 1: $\text{Test}_1$ = 50 Left + 50 Right (100 trials); $\text{Train}_1$ = remaining 50 Left + 50 Right (100 trials).
  4. Fold 2: $\text{Test}_2 = \text{Train}_1$; $\text{Train}_2 = \text{Test}_1$.
- **Implementation Invariants**:
  - Exactly 2 folds per repeat.
  - Exactly 100 training trials and 100 test trials per fold.
  - Exactly 50 Left and 50 Right trials in every training and testing fold.
  - Every trial is evaluated exactly once per repeat ($\text{Test}_1 \cap \text{Test}_2 = \emptyset$, $\text{Test}_1 \cup \text{Test}_2 = \text{All Trials}$).
  - Exact fold indices, random seed (`seed=0`), and split SHA-256 hash are recorded to disk.

### 2.3 Protocol 3: Supervised Spatial Contamination ($P_1$ Positive Control)
- Fits Common Spatial Patterns ($\mathbf{W}_{\text{global}}$) on all 200 trials and labels simultaneously.
- Projects all trials into log-variance features $\mathbf{Z}_{\text{all}}$.
- **Crucial Safeguard**: Evaluates using the $D_3$ fold partition where the **classifier is fitted strictly on the training fold features** ($\mathbf{Z}_{\text{train}}$) and tested on $\mathbf{Z}_{\text{test}}$. The classifier never receives held-out test labels; only the spatial filter is transductively contaminated.

---

## 3. Frozen Preprocessing Configuration

To eliminate ambiguity, preprocessing is **strictly frozen** prior to execution:

```
+---------------------------------------------------------------------------------------------------------+
|                                    FROZEN PREPROCESSING SPECIFICATION                                   |
+--------------------------+------------------------------------------------------------------------------+
| Parameter                | Frozen Specification                                                         |
+--------------------------+------------------------------------------------------------------------------+
| **Sampling Frequency**   | **250.0 Hz** (Exact integer factor-of-4 decimation from native 1,000 Hz)     |
| **Resampling Method**    | Polyphase anti-aliasing FIR filter (`scipy.signal.resample_poly`)            |
| **Run-Isolated Filtering**| Bandpass **8.0–30.0 Hz** zero-phase FIR; applied independently per run        |
|                          | (Filter state never crosses between Run 0 and Run 1)                         |
| **Epoch Time Window**    | **[-0.5, 4.0] s** relative to visual cue (t=0.0 s); 1,125 samples at 250 Hz   |
| **Baseline Treatment**   | **[-0.5, 0.0] s** pre-cue interval mean subtraction                          |
| **Channel Layout**       | 62 EEG scalp electrodes (standard 10-20 international montage)               |
| **Rejection Rule**       | Peak-to-peak amplitude > 150 µV flagged non-destructively                    |
+--------------------------+------------------------------------------------------------------------------+
```

---

## 4. Decoder Specifications & Transductive Safeguards

Decoders are evaluated and reported **strictly separately** (never averaged together):

### 4.1 Primary Decoder: Shrinkage CSP-LDA
- **Spatial Filtering**: 6 CSP components ($m=3$ pairs for binary classification).
- **Covariance Regularization**: Oracle Approximating Shrinkage (OAS).
- **Normalization**: Trace-normalized sample covariance matrices.
- **Features**: Log-variance of spatially filtered components: $f_j = \log(\text{var}(\mathbf{w}_j^T \mathbf{X}))$.
- **Classifier**: Linear Discriminant Analysis with automatic Ledoit-Wolf shrinkage (`solver='lsqr'`, `shrinkage='auto'`).

### 4.2 Secondary Decoder: Riemannian Tangent Space Logistic Regression (`ts_lr`)
- **Covariance Estimation**: OAS-regularized covariance matrices per trial.
- **Strict In-Sample Reference Safeguard**:
  - The Riemannian Fréchet geometric mean reference matrix $\mathbf{C}_{\text{ref}}$ is estimated **exclusively from training-fold covariance matrices**:
    $$\mathbf{C}_{\text{ref}} = \arg\min_{\mathbf{C}} \sum_{i \in \text{train}} \delta_R^2(\mathbf{C}, \mathbf{C}_i)$$
  - Test covariance matrices are projected onto the tangent space at $\mathbf{C}_{\text{ref}}$ using the matrix logarithm $\mathbf{S}_i = \log(\mathbf{C}_{\text{ref}}^{-1/2} \mathbf{C}_i \mathbf{C}_{\text{ref}}^{-1/2})$ **without allowing test matrices to update $\mathbf{C}_{\text{ref}}$**.
- **Vectorization**: Upper triangular elements scaled by $\sqrt{2}$ for off-diagonal terms to preserve the Riemannian metric.
- **Feature Scaling**: Standard scaling fitted strictly on training tangent vectors.
- **Classifier**: $L_2$-regularized Logistic Regression ($C=1.0$, `solver='lbfgs'`).

---

## 5. Statistical Inference & Multiplicity Plan

### 5.1 Participant-Level Aggregation
For each participant $i \in \{1, \dots, 34\}$:
- $\text{Acc}_i(D_3) = \frac{1}{2}(\text{Acc}_{i,\text{Fold1}} + \text{Acc}_{i,\text{Fold2}})$.
- $\text{Acc}_i(D_{1s}) = \frac{1}{20} \sum_{r=0}^{19} \frac{1}{2}(\text{Acc}_{i,r,\text{Fold1}} + \text{Acc}_{i,r,\text{Fold2}})$.
- $\text{Acc}_i(P_1) = \frac{1}{2}(\text{Acc}_{i,\text{Fold1}}^{\text{leaked}} + \text{Acc}_{i,\text{Fold2}}^{\text{leaked}})$.

### 5.2 Prespecified Multiplicity Families
- **Primary Confirmatory Family** (Shrinkage CSP-LDA, $m=2$ contrasts):
  1. Contrast 1: $\Delta_{\text{size-matched}, i} = \text{Acc}_i(D_{1s}) - \text{Acc}_i(D_3)$
  2. Contrast 2: $\Delta_{\text{inflation}, i} = \text{Acc}_i(P_1) - \text{Acc}_i(D_3)$
  - Multiplicity control: Two-sided Holm-Bonferroni step-down adjustment ($m=2$).
- **Secondary Family** (Riemannian `ts_lr`, $m=2$ contrasts):
  - Evaluated independently; reported as secondary cross-decoder validation.
- **Secondary Sensitivity Contrast**:
  - $\Delta_{\text{matched-k}, i} = \text{Acc}_i(D_{1m}) - \text{Acc}_i(D_3)$ ($m=1$).

### 5.3 Non-Parametric Inference
- **Hypothesis Tests**: Two-sided Wilcoxon signed-rank test with Pratt correction for zero differences.
- **Effect Size**: Hodges-Lehmann pseudo-median estimator (median of pairwise Walsh averages).
- **Confidence Intervals**: 95% BCa (Bias-Corrected and Accelerated) non-parametric bootstrap resampling **participants** (2,000 resamples), never resampling trials or folds.

---

## 6. Participant Eligibility & Automated Validation Pass

Every participant must satisfy the following automated validation criteria before inclusion in the benchmark:
1. File matches authoritative NEMAR manifest size to the byte.
2. Contains exactly 200 trials across Run 0 (100) and Run 1 (100).
3. Class balance is exactly 50 Left Hand and 50 Right Hand trials in both runs.
4. Channel count is exactly 62, matching the standard 10-20 reference order.
5. Sampling frequency is verified at 1,000 Hz, decimating cleanly to 250 Hz.
6. Zero NaN and zero Inf values across all channels and time samples.
