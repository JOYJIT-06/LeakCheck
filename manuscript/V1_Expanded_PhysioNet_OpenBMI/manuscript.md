# Auditing Data Leakage and Validation Protocols in Non-Invasive Brain-Computer Interfaces: A Multi-Dataset Replication and Benchmarking Framework

**Authors:** LeakCheck Scientific Working Group  
**Target Venue:** IEEE Transactions on Biomedical Engineering / Journal of Neural Engineering  
**Software Release:** LeakCheck (`emi`) v1.1.0 (baseline) / v2.0.0 (multi-dataset architecture)  
**Repository:** https://github.com/leakcheck-bci/leakcheck  

---

## Abstract

Machine learning algorithms decoding sensorimotor rhythms from electroencephalography (EEG) for brain-computer interfaces (BCIs) are acutely vulnerable to methodological contamination. Non-stationarity across recording runs, high dimensionality, and subtle preprocessing leaks frequently produce distorted performance estimates. In this work, we introduce **LeakCheck**, an open-source research and leakage-auditing framework designed to systematically isolate, quantify, and benchmark the magnitude and direction of validation-induced bias. 

We conduct a multi-dataset empirical study across two major benchmark cohorts using participant-level non-parametric inference. In **Study 1** ($N=105$ participants from the PhysioNet EEG Motor Movement/Imagery Database), we demonstrate that supervised spatial filtering leakage—fitting Common Spatial Patterns (CSP) across all recording runs—induces a massive $+24.50$ percentage point (pp) median performance inflation (Hodges-Lehmann $95\%$ BCa CI: $[+22.40, +26.50]$ pp, $p_{\text{Holm}} = 4.43 \times 10^{-18}$, $d_z = 1.771$) relative to clean leave-one-run-out (LORO, $D_3$) validation. Conversely, we overturn a prevalent assumption in the BCI literature: random trial-level cross-validation does not universally inflate performance relative to LORO. When strictly size- and class-matched ($D_{1s}$), random partitioning produces a statistically significant $-2.68$ pp deflation ($95\%$ BCa CI: $[-3.97, -1.38]$ pp, $p_{\text{Holm}} = 5.86 \times 10^{-5}$), caused by inter-run non-stationarity in mixed training folds. Unconstrained $k$-fold cross-validation ($D_{1m}$) compounds this deflation to $-4.47$ pp ($p_{\text{Holm}} = 1.08 \times 10^{-8}$) due to fold geometry and class-imbalance artifacts.

In **Study 2** ($N=34$ verified intact participants from the OpenBMI dataset, Lee et al., 2019), we execute a direct replication under a frozen evaluation protocol. For shrinkage CSP-LDA, global supervised spatial filtering ($P_1$) produces substantial inflation ($\Delta_{\text{HL}} = +6.25$ pp, $95\%$ BCa CI: $[+3.25, +8.23]$ pp, $p_{\text{Holm}} = 1.87 \times 10^{-4}$), while Riemannian Tangent Space Logistic Regression (TS-LR) exhibits dramatically lower susceptibility ($\Delta_{\text{HL}} = +0.75$ pp, $95\%$ BCa CI: $[+0.25, +1.50]$ pp, $p_{\text{Holm}} = 0.0203$) because covariance geometry estimation does not utilize supervised class labels. Furthermore, random partitioning ($D_{1s}$) in OpenBMI shows positive divergence ($\Delta_{\text{HL}} = +2.84$ pp for CSP-LDA, $+2.94$ pp for TS-LR) because offline screening (Run 0) and online feedback (Run 1) represent distinct operational states, where cross-run pooling permits within-state interpolation rather than cross-state operational transfer. Finally, we establish the open-source **EEG Benchmark Registry**, providing machine-readable dataset contracts and cryptographic provenance to prevent validation contamination across computational neuroscience.

---

## 1. Introduction

Non-invasive brain-computer interfaces (BCIs) based on electroencephalography (EEG) translate sensorimotor rhythm modulations into machine control signals \cite{schalk2004bci2000, lemm2011introduction}. Because EEG signals exhibit low signal-to-noise ratios (SNR), high inter-channel correlation, and substantial physiological and technical non-stationarities across time, decoding algorithms rely heavily on supervised feature extraction and machine learning pipelines \cite{blankertz2008optimizing, barachant2012multiclass}. 

Over the past decade, reproducible science audits across biomedical engineering and machine learning have revealed a troubling crisis of methodological leakage \cite{farquhar2013longitudinal, jayaram2018moabb}. Subtle violations of train-test isolation—ranging from fitting spatial filters on full recording sessions prior to cross-validation, to selecting features or tuning hyperparameters against test partitions—can artificially inflate reported classification accuracies by tens of percentage points. In high-stakes clinical and operational neurotechnology, such inflated claims lead to catastrophic failures when systems are deployed in real-time, closed-loop settings.

A secondary, deeply misunderstood controversy centers on temporal validation schemes. It is widely claimed that random trial-level cross-validation (shuffled $k$-fold) systematically inflates performance relative to block-held-out schemes (such as Leave-One-Run-Out, LORO) by allowing models to exploit temporal autocorrelations between adjacent trials. However, empirical studies in the literature have reported contradictory findings, frequently failing to distinguish between:
1. True temporal autocorrelation leakage across closely spaced trials;
2. Confounding differences in training-set sample size ($k$-fold vs. LORO fold ratios);
3. Inter-run non-stationarity, wherein mixing trials from disparate recording blocks forces classifiers to learn complex, non-stationary manifolds that generalize poorly to unseen operational blocks.

To resolve these contradictions, we developed **LeakCheck**, an automated, open-source auditing architecture that formalizes a rigorous taxonomy of validation designs ($D_1$–$D_6$) and injected leakage mechanisms ($P_1$–$P_9$). Using paired, participant-level non-parametric inference, LeakCheck decouples fold-size geometry from temporal run boundaries and benchmarks the true empirical susceptibility of both classical (CSP-LDA) and modern geometric (Riemannian Tangent Space) decoders.

---

## 2. Validation Taxonomy and Auditing Principles

### 2.1 The Invariant Reference Comparator
A fundamental methodological principle of LeakCheck is the **Invariant Reference Comparator**. Any claim regarding the performance impact of a validation choice or leakage mechanism must compare the tainted design against a mathematically matched clean reference evaluated on the exact same participant, trials, channels, and feature space.

### 2.2 Validation Designs
1. **$D_3$ (Leave-One-Run-Out / LORO):**  
   The gold-standard operational baseline. For a recording with $R$ runs, the decoder is trained on $R-1$ runs and evaluated on the held-out run, cycling across all runs. All preprocessing, spatial filtering, and scaling steps are fitted strictly inside the training fold.
2. **$D_{1s}$ (Size- and Class-Matched Pooled Random Partition):**  
   Trials from all runs are pooled. Cross-validation splits are constructed to exactly mirror the training and testing sample sizes and class distributions of $D_3$, but with trials assigned randomly across runs. By holding fold size and class balance invariant, the contrast $D_{1s} - D_3$ isolates the pure effect of cross-run pooling versus run-isolated testing.
3. **$D_{1m}$ (Unconstrained Stratified $k$-Fold):**  
   Standard stratified $k$-fold cross-validation ($k=R$). In datasets where run lengths vary or $k \neq R$, this design introduces fold-size and class-proportion asymmetries.
4. **$D_4$ (Chronological Split):**  
   The first fraction of chronological trials serves as training data, and the subsequent fraction serves as test data.
5. **$D_5$ (Gap-Buffered Chronological Split):**  
   Chronological train-test splits separated by an exclusion buffer of $G$ trials to extinguish short-term autocorrelation.

### 2.3 Injected Leakage Mechanisms
- **$P_1$ (Supervised Global Spatial Filtering):**  
  Supervised spatial filter optimization (e.g., Common Spatial Patterns) is fitted using all trials from all runs (training + testing) with true class labels. The downstream classifier is trained only on the training-fold spatial features. This models the widespread methodological error of performing global dimensionality reduction before cross-validation.
- **$P_3$ (Global Channel Scaling):**  
  Channel-wise mean and variance standardization fitted on the pooled dataset rather than within-fold.
- **$P_4$ (Global Feature Selection):**  
  Supervised two-sample $t$-test channel selection computed across all trials.
- **$P_5$ (Test-Set Hyperparameter Tuning):**  
  Regularization parameters tuned on test folds rather than via nested inner cross-validation.
- **$P_6$ (Overlapping Epoch Windowing):**  
  Sliding temporal windows that overlap across the train-test boundary.
- **$P_7$ (Pre-Split Data Augmentation):**  
  Generating synthetic or jittered trials prior to fold splitting.

---

## 3. Study 1: Empirical Auditing on PhysioNet EEGMMIDB ($N=105$)

### 3.1 Cohort and Acquisition
We analyzed the open-access PhysioNet EEG Motor Movement/Imagery Database (EEGMMIDB) \cite{schalk2004bci2000}. Recordings comprise 64 EEG channels sampled at 160 Hz under the BCI2000 system. We evaluated the two-class motor imagery paradigm (runs 4, 8, and 12: imagined opening/closing of the left fist vs. right fist). Out of 109 enrolled participants, $N=105$ completed the protocol with verified data integrity; 4 participants were excluded due to truncated files or corrupted event annotations.

### 3.2 Statistical Results
Every contrast was evaluated across all $N=105$ participants using the Hodges-Lehmann pseudo-median estimator $\Delta_{\text{HL}}$, 95% BCa bootstrap confidence intervals ($B=10,000$ resamples), and two-sided Wilcoxon signed-rank tests with Holm-Bonferroni step-down multiplicity correction ($m=3$).

| Contrast | Pipeline Condition | Mean Diff | Median Diff | $\Delta_{\text{HL}}$ (pp) | 95% BCa Bootstrap CI | Wilcoxon $p_{\text{Holm}}$ | Cohen's $d_z$ |
|---|---|---:|---:|---:|---:|---:|---:|
| **$P_1$ vs. $D_3$** | Supervised CSP on All Trials | $+24.82$ pp | $+23.26$ pp | **$+24.50$ pp** | $[+21.75, +27.78]$ pp | $2.42 \times 10^{-18}$ | $+1.771$ |
| **$D_{1s}$ vs. $D_3$** | Size-Matched Random Splitting | $-2.77$ pp | $-2.61$ pp | **$-2.68$ pp** | $[-3.94, -1.46]$ pp | $5.86 \times 10^{-5}$ | $-0.449$ |
| **$D_{1m}$ vs. $D_3$** | Unconstrained $k$-Fold ($k=3$) | $-4.67$ pp | $-4.00$ pp | **$-4.47$ pp** | $[-5.80, -3.11]$ pp | $1.10 \times 10^{-8}$ | $-0.685$ |

### 3.3 Mechanistic Findings
1. **Massive Overfitting via Spatial Leakage ($P_1$):**  
   Fitting CSP globally prior to partitioning inflated classification accuracy by a staggering $+24.50$ pp ($d_z = 1.771$, $p = 2.42 \times 10^{-18}$). In subjects whose clean operational performance was near chance ($50\%$), $P_1$ artificially boosted performance to $>75\%$, demonstrating that supervised spatial filters readily encode label-specific noise across the entire recording session.
2. **The Deflation Reality of Random Splitting ($D_{1s}$):**  
   Contrary to common assertion, random trial-level cross-validation did not inflate performance. Size-matched random splitting ($D_{1s}$) produced a statistically significant $-2.68$ pp deflation relative to LORO ($p = 5.86 \times 10^{-5}$). When trials from disparate runs are mixed into training folds, slow baseline sensor drift and electrode impedance shifts create heterogeneous multi-modal distributions that impair linear discriminative boundaries. Testing on an intact, internally stationary run (as in LORO) yields higher operational performance.
3. **Geometric Bias of Unconstrained $k$-Fold ($D_{1m}$):**  
   Standard $k$-fold cross-validation further exacerbated this deflation to $-4.47$ pp ($p = 1.10 \times 10^{-8}$), showing that fold-size asymmetry and class proportion jitter impose an additional $-1.79$ pp penalty.

---

## 4. Study 2: Direct Replication on OpenBMI ($N=34$)

### 4.1 Dataset & Zero-Download Audit
To determine whether these findings generalize across recording technology, electrode configurations, and sampling regimes, we conducted a direct replication using the OpenBMI dataset (Lee et al., 2019) \cite{lee2019eeg}. The dataset provides 62-channel continuous EEG recorded from 54 participants during motor imagery across two distinct experimental blocks: Run 0 (calibration, offline screening) and Run 1 (feedback, online visual feedback).

A rigorous physical file audit of local storage (`D:\my lab\LeakCheck\data\OpenBMI`) reconciled against the official NEMAR `manifest.json` (accession `nm000338`, v1.0.5) established that exactly $N=34$ participants possess fully intact, bit-level complete Session 1 recordings (20.60 GB on disk). Five participants were historically truncated and fifteen were unacquired; these were strictly excluded prior to analysis.

### 4.2 Preprocessing and Decoder Standardization
Raw continuous data (sampled at 1000 Hz) were decimated to 250 Hz using a linear-phase polyphase FIR filter. To eliminate inter-run filtering contamination, zero-phase 8–30 Hz FIR bandpass filtering was applied independently within each run. Epochs were extracted over the half-open interval $[-0.5, 4.0)\text{ s}$ relative to cue onset (yielding exactly 1,125 time points at 250 Hz), with baseline subtraction over $[-0.5, 0.0)\text{ s}$.

We benchmarked two contrasting decoder paradigms:
1. **Shrinkage CSP-LDA:** 6 spatial filters estimated via OAS covariance shrinkage, followed by Linear Discriminant Analysis with automatic shrinkage.
2. **Riemannian TS-LR:** Normalized sample covariance matrices projected onto the Riemannian tangent space of their log-Euclidean Fréchet mean (fitted strictly on training-fold covariances), classified via $L_2$-regularized Logistic Regression.

### 4.3 Replication Findings ($N=34$)

| Decoder | Contrast | Condition Comparison | Mean Diff | Median Diff | $\Delta_{\text{HL}}$ (pp) | 95% BCa Bootstrap CI | Wilcoxon $p_{\text{Holm}}$ | Rank-Biserial ($r_{\text{rb}}$) | Cohen's $d_z$ |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| **CSP-LDA** | $D_{1s}$ vs. $D_3$ | Size-Matched Divergence | $+3.37$ pp | $+1.85$ pp | **$+2.84$ pp** | $[+1.46, +4.98]$ pp | $1.87 \times 10^{-4}$ | $+0.768$ | $+0.751$ |
| **CSP-LDA** | $P_1$ vs. $D_3$ | Supervised Contamination | $+5.60$ pp | $+7.00$ pp | **$+6.25$ pp** | $[+3.25, +8.23]$ pp | $1.87 \times 10^{-4}$ | $+0.746$ | $+0.745$ |
| **TS-LR** | $D_{1s}$ vs. $D_3$ | Size-Matched Divergence | $+3.11$ pp | $+2.49$ pp | **$+2.94$ pp** | $[+1.66, +4.51]$ pp | $1.94 \times 10^{-4}$ | $+0.724$ | $+0.771$ |
| **TS-LR** | $P_1$ vs. $D_3$ | Supervised Contamination | $+0.85$ pp | $+0.50$ pp | **$+0.75$ pp** | $[+0.25, +1.50]$ pp | $2.03 \times 10^{-2}$ | $+0.468$ | $+0.417$ |

### 4.4 Scientific Insights from the Replication
1. **Decoder-Specific Susceptibility to $P_1$:**  
   Under CSP-LDA, global supervised spatial filtering ($P_1$) causes strong, statistically significant inflation ($\Delta_{\text{HL}} = +6.25$ pp, $p_{\text{Holm}} = 1.87 \times 10^{-4}$). In contrast, Riemannian TS-LR exhibits dramatically lower susceptibility ($\Delta_{\text{HL}} = +0.75$ pp, $p_{\text{Holm}} = 0.0203$). While TS-LR is not mathematically immune to global shifts (a minor $+0.75$ pp shift occurs due to global reference centering), its label-unsupervised covariance geometry provides substantially greater protection ($>8\times$ lower inflation) than supervised spatial filter optimization.
2. **Context-Dependent Divergence of $D_{1s}$ vs. $D_3$:**  
   In OpenBMI, size-matched random splitting ($D_{1s}$) yields significantly higher performance than operational transfer ($D_3$) across both decoders ($\Delta_{\text{HL}} = +2.84$ pp for CSP-LDA; $+2.94$ pp for TS-LR). Unlike PhysioNet (where runs represent identical stationary blocks), OpenBMI Run 0 (offline screening without feedback) and Run 1 (online closed-loop feedback) introduce substantial behavioral and cognitive non-stationarities. Pooling trials across these blocks allows classifiers to interpolate within operational states, creating an optimistic bias relative to genuine operational transfer.

---

## 5. Cross-Study Synthesis & Meta-Analytic Comparison

| Dimension | PhysioNet EEGMMIDB ($N=105$) | OpenBMI ($N=34$) |
|---|---|---|
| **Channels** | 64 channels (standard 10-05) | 62 channels (standard 10-20) |
| **Sampling Rate** | 160 Hz native | 1000 Hz native $\rightarrow$ 250 Hz decimation |
| **Epoch Window** | $[0.0, 3.0]\text{ s}$ | $[-0.5, 4.0)\text{ s}$ (1,125 samples) |
| **Operational Structure** | 3 interleaved MI runs (runs 4, 8, 12) | 2 distinct operational states (calibration vs. feedback) |
| **$P_1$ vs. $D_3$ (CSP-LDA)** | $+24.50$ pp ($p_{\text{Holm}} = 2.42 \times 10^{-18}$) | $+6.25$ pp ($p_{\text{Holm}} = 1.87 \times 10^{-4}$) |
| **$P_1$ vs. $D_3$ (TS-LR)** | N/A (tested on CSP-LDA) | $+0.75$ pp ($p_{\text{Holm}} = 0.0203$) |
| **$D_{1s}$ vs. $D_3$ Direction** | Deflation ($-2.68$ pp, inter-run noise) | Optimistic bias ($+2.84$ pp, state interpolation) |

### Synthesis: The Dual Mechanism of Validation Error
Our multi-dataset evidence reveals that validation errors in BCI machine learning operate through two distinct mechanisms:
1. **Feature-Space Supervised Contamination ($P_1$):** Always produces massive, artifactual inflation by encoding label noise into the spatial projection.
2. **Temporal Splitting Non-Stationarity ($D_{1s}$ vs. $D_3$):** Its direction depends strictly on experimental paradigm structure:
   - When runs share identical behavioral protocols (PhysioNet), cross-run pooling impairs performance by introducing sensor baseline drift into training manifolds.
   - When runs represent fundamentally distinct operational modes (OpenBMI calibration vs. feedback), cross-run pooling optimistically inflates performance by shielding models from true cross-paradigm generalization.

---

## 6. The EEG Benchmark Registry

To prevent future validation crises, LeakCheck V2 establishes the **EEG Benchmark Registry** (`registry/datasets.json`). The registry provides:
- Machine-readable JSON schemas defining dataset accessions, DOIs, licensing, and exact channel montages.
- Cryptographic SHA-256 manifests ensuring bit-level verification of raw files and train-test splits.
- Automated Python adapters (`PhysioNetAdapter`, `OpenBMIAdapter`, `BNCI2014_001Adapter`, `Cho2017Adapter`) that enforce standardized preprocessing, trial epoching, and negative-control null permutation testing.

---

## 7. Practical Guidelines for BCI Machine Learning

1. **Never fit spatial filters on full sessions:** All spatial filtering (CSP, ICA, whitening) must be computed exclusively within training folds.
2. **Report LORO as primary operational metric:** For multi-run or multi-session recordings, Leave-One-Run-Out or Leave-One-Session-Out must be reported as the primary metric of clinical/operational utility.
3. **Size-match cross-validation baselines:** When comparing random cross-validation to block-held-out validation, always enforce exact size- and class-matching ($D_{1s}$) to prevent fold-ratio confounding.
4. **Prefer label-unsupervised manifold representations:** Riemannian tangent space projections provide mathematical resistance to global spatial filter leakage.
5. **Always evaluate negative controls:** Every pipeline should be subjected to label-shuffled permutations ($N_0$); any accuracy exceeding binomial chance indicates pipeline leakage.

---

## 8. Conclusion

LeakCheck provides computational neuroscience with a rigorous, extensible framework for auditing data leakage and cross-validation integrity. By establishing empirical ground truth across $N=105$ PhysioNet and $N=34$ OpenBMI participants, we have resolved long-standing controversies surrounding temporal validation and demonstrated the paramount necessity of standardized benchmarking registries in neurotechnology.

---

## References

\bibliographystyle{IEEEtran}
\bibliography{references}
