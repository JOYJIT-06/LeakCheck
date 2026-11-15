# LeakCheck V1.1 Final Methods Specification

**Document ID**: `manuscript/V1_PhysioNet/FINAL_METHODS_SPECIFICATION.md`  
**Milestone**: M4 (Scientific Manuscript & Evidence Package)  
**Study Scope**: PhysioNet EEGMMIDB Benchmark ($N = 105$)  
**Target Manuscript Section**: Section 4 (Cohort), Section 5 (Preprocessing & Decoder), Section 6 (Statistics)  
**Code Repository**: `D:\my lab\LeakCheck_remote` (`src/emi/`)  
**Date**: November 2026  
**Status**: APPROVED — VERIFIED COMPLETE METHODS SPECIFICATION  

---

## 1. Overview and Engineering Traceability

This specification defines the exact, executable methods implemented in LeakCheck V1.1. It establishes strict 1-to-1 correspondence between the manuscript methods description and the Python/R codebase (`src/emi/`, `scripts/`, `analysis/`).

---

## 2. Dataset and Cohort Selection

### 2.1 Primary Repository and Identifier
- **Repository**: PhysioNet EEG Motor Movement/Imagery Database (EEGMMIDB) \cite{goldberger2000physiobank, schalk2009eegmmidb}.
- **Persistent URL**: `https://physionet.org/content/eegmmidb/1.0.0/`
- **License**: Open Data Commons Attribution License v1.0.
- **Hardware Platform**: BCI2000 64-channel acquisition system \cite{schalk2004bci2000}.
- **Electrode Montage**: International 10–10 system, 64 channels, earlobe reference.
- **Experimental Runs Selected**:
  - Run 04: Motor imagery of opening/closing left fist (T1) vs. right fist (T2).
  - Run 08: Motor imagery of opening/closing left fist (T1) vs. right fist (T2).
  - Run 12: Motor imagery of opening/closing left fist (T1) vs. right fist (T2).
- **Target Motor Tasks**: Two-class motor imagery (Left Fist = Class 0, Right Fist = Class 1).
- **Trial Timing**: Target cue displayed for $4.0\,\text{s}$, separated by resting intervals of varying duration ($3.0$–$4.2\,\text{s}$).

### 2.2 Automated Cohort Screening and Exclusion Rules
All 109 available subject folders (`S001` to `S109`) were ingested through an automated two-stage gate pipeline (`src/emi/pipeline.py`):
1. **Stage 1: Automated Recording Quality Screening**:
   - Defective Channel Criterion: Any subject with $> 15\%$ defective channels ($> 9.6$ of 64 channels) identified via zero variance or high impedance is excluded.
     - *Excluded*: $\text{S044}$ (12/64 bad channels = 18.75%).
     - *Excluded*: $\text{S069}$ (12/64 bad channels = 18.75%).
   - Severe Amplitude Rejection Criterion: Any subject where 100% of motor imagery epochs exceed an extreme peak-to-peak amplitude ceiling ($800\,\mu\text{V}$) is excluded.
     - *Excluded*: $\text{S091}$ (45/45 trials rejected = 100%).
2. **Stage 2: Benchmark Eligibility Threshold**:
   - Minimum Trial Criterion: A minimum of 30 clean post-rejection motor imagery trials across the three runs is required to ensure adequate covariance matrix rank.
     - *Excluded*: $\text{S086}$ (retained only 24 clean trials).
3. **Cohort Summary**:
   - Initial requested: $109$
   - Excluded: $4$ (S044, S069, S086, S091)
   - Evaluated cohort: Exactly $\mathbf{105}$ participants ($96.33\%$ retention).

### 2.3 Dynamic Hardware Sampling Rate Adaptation
- **Standard Cohort**: 102 participants recorded at 160.0 Hz.
- **Non-Standard Cohort**: 3 participants recorded at 128.0 Hz (S088, S092, S100); 1 participant recorded at 160.0 Hz (S104).
- **Implementation**: The pipeline dynamically reads the native sampling frequency $f_s$ from the EDF header and calculates temporal window samples as:
  $$N_{\text{samples}} = \operatorname{int}\left(f_s \cdot (t_{\text{max}} - t_{\text{min}})\right)$$
  For $f_s = 160\,\text{Hz}$, $N = 320$ samples; for $f_s = 128\,\text{Hz}$, $N = 256$ samples. Zero resampling or spline interpolation is performed, preserving raw signal fidelity.

---

## 3. Signal Preprocessing Pipeline

Implemented in `src/emi/preprocess.py`:
1. **Bandpass Filtering**:
   - Filter Type: 5th-order Butterworth digital IIR filter.
   - Passband: $8.0\,\text{Hz}$ to $30.0\,\text{Hz}$ (sensorimotor mu and beta bands).
   - Implementation: Zero-phase forward-backward filtering via second-order sections (`scipy.signal.sosfiltfilt`).
2. **Epoch Extraction**:
   - Extraction Interval: $[-0.5, +4.0]\,\text{s}$ relative to cue onset.
   - Baseline Correction: Mean signal in the pre-stimulus baseline interval $[-0.5, 0.0]\,\text{s}$ subtracted per channel.
3. **Active Decoding Slice**:
   - Analysis Interval: $[+1.0, +3.0]\,\text{s}$ post-cue ($2.0\,\text{s}$ duration).
   - Rationale: Discards early visual evoked potentials ($0$–$1.0\,\text{s}$) and avoids movement offset artifacts ($> 3.0\,\text{s}$).
4. **Trial-Level Artifact Screening**:
   - Threshold: Trials exhibiting peak-to-peak amplitude exceeding $150.0\,\mu\text{V}$ across any channel during the active decoding slice are flagged and discarded.

---

## 4. Cross-Validation Designs and Partitioning Architecture

Implemented in `src/emi/splitters.py`:

### 4.1 Design $D_3$: Leave-One-Run-Out (LORO, Operational Reference)
- **Folds ($K = 3$)**:
  - Fold 1: Train on Runs 8 & 12; Test on Run 4.
  - Fold 2: Train on Runs 4 & 12; Test on Run 8.
  - Fold 3: Train on Runs 4 & 8; Test on Run 12.
- **Nesting Invariant**: OAS covariance shrinkage, CSP spatial filter decomposition, and LDA classifier training are executed strictly inside `fit()` on the training runs. The test run is evaluated strictly via `transform()` and `predict()`.

### 4.2 Design $D_{1s}$: Size- and Class-Matched Random Partition
- **Folds ($K = 3$)**:
  - For each fold $k \in \{1, 2, 3\}$ and class $c \in \{0, 1\}$, exact trial cardinalities are determined from $D_3$:
    $$N_{k, c} = \sum_{i=1}^M \mathbb{I}(r_i = k \land y_i = c)$$
  - Test fold $\mathcal{S}_{\text{test}}^{(k)}$ is constructed by drawing $N_{k, 0}$ class 0 trials and $N_{k, 1}$ class 1 trials uniformly at random without replacement from the pooled aggregate dataset.
  - Training fold $\mathcal{S}_{\text{train}}^{(k)} = \mathcal{D} \setminus \mathcal{S}_{\text{test}}^{(k)}$.
- **Properties**: Ensures identical training sample size and class balance as $D_3$ per fold, isolating inter-run non-stationarity from sample-efficiency artifacts.
- **Repetitions**: 20 independent random partition repeats (`n_repeats_matched = 20`, base random seed $= 0$ via `numpy.random.default_rng(0)`). For each participant, decoding accuracy is evaluated per repeat and averaged across all 20 repeats (each with $K = 3$ size-matched folds) to minimize stochastic partition variance without inflating degrees of freedom.

### 4.3 Design $D_{1m}$: $k$-Matched Stratified Random Partition
- **Folds ($K = 3$) and Repetitions**: Standard stratified $K$-fold cross-validation with $K = 3$ folds (matching the number of physical runs in $D_3$) repeated across 5 independent iterations (`n_repeats = 5`, base random seed $= 0$). Repetition $r \in \{0, 1, 2, 3, 4\}$ initializes `sklearn.model_selection.StratifiedKFold(n_splits=3, shuffle=True, random_state=seed + r)`. Decoding accuracy is averaged across the 5 repeats for each participant.
- **Properties**: Equal split of available trials across folds, allowing fold trial counts to fluctuate relative to physical run counts.

### 4.4 Mechanism $P_1$: Supervised Spatial Filter Contamination (Positive Control)
- **Contamination Procedure**: Common Spatial Patterns filter decomposition is fitted globally across all available trials in the aggregate dataset $\mathcal{D} = \mathcal{D}_{\text{train}} \cup \mathcal{D}_{\text{test}}$ prior to fold partitioning.
- **Evaluation**: The extracted global spatial filters are held fixed. Fold partitioning follows $D_3$ (Leave-One-Run-Out), but features are extracted using the globally contaminated projection matrix.

---

## 5. Decoder Implementation and Spatial Filtering

Implemented in `src/emi/decoders.py`:

### 5.1 Covariance Regularization
- **Estimator**: Oracle Approximating Shrinkage (`sklearn.covariance.OAS`).
- **Mathematical Formulation**:
  $$\hat{\mathbf{\Sigma}}_{\text{OAS}} = (1 - \hat{\rho}) \hat{\mathbf{\Sigma}} + \hat{\rho} \left(\frac{\operatorname{tr}(\hat{\mathbf{\Sigma}})}{C}\right) \mathbf{I}_C$$
  where $\hat{\mathbf{\Sigma}} = \frac{1}{N} \sum_{i=1}^N \mathbf{X}_i \mathbf{X}_i^\top$ is the sample covariance matrix, $C = 64$ is the channel dimension, and $\hat{\rho}$ is the optimal analytical shrinkage coefficient.

### 5.2 Common Spatial Patterns (CSP)
- **Eigenvalue Problem**: Generalized eigenvalue decomposition of average class covariance matrices:
  $$\hat{\mathbf{\Sigma}}_1 \mathbf{w} = \lambda \hat{\mathbf{\Sigma}}_2 \mathbf{w}$$
- **Components Extracted**: 6 spatial filters (3 corresponding to maximum eigenvalues for Class 1; 3 corresponding to maximum eigenvalues for Class 2).
- **Feature Extraction**: Normalized log-variance of spatially filtered signals:
  $$f_j = \log \left( \frac{\operatorname{var}(\mathbf{w}_j^\top \mathbf{X})}{\sum_{k=1}^6 \operatorname{var}(\mathbf{w}_k^\top \mathbf{X})} \right), \quad j = 1, \dots, 6$$

### 5.3 Classifier
- **Model**: Linear Discriminant Analysis (`sklearn.discriminant_analysis.LinearDiscriminantAnalysis`).
- **Solver**: Least-squares with Ledoit-Wolf automatic shrinkage covariance estimation (`solver='lsqr', shrinkage='auto'`).

---

## 6. Inferential Statistical Procedures

Implemented in `src/emi/leakstats.py` and `recalculate_all_stats.py`:

### 6.1 Participant-Level Pooling (Pseudoreplication Prevention)
- For each subject $i$ and design, all fold predictions are pooled into a single confusion matrix:
  $$A_i = \frac{\sum_{k=1}^K N_{\text{correct}}^{(k)}}{\sum_{k=1}^K N_{\text{total}}^{(k)}}$$
- Paired difference: $D_i = A_{i, \text{contrast}} - A_{i, D_3}$ (in percentage points, pp).

### 6.2 Non-Parametric Point & Interval Estimation
- **Hodges-Lehmann Estimator ($\Delta_{\text{HL}}$)**: Pseudo-median of all pairwise Walsh averages:
  $$\Delta_{\text{HL}} = \operatorname{median}_{1 \le i \le j \le N} \left( \frac{D_i + D_j}{2} \right)$$
- **95% BCa Bootstrap Confidence Intervals**:
  - Bootstrap replicates: $B = 10{,}000$.
  - PRNG Seed: `0` (via `np.random.RandomState(seed)`).
  - Acceleration parameter $a$ computed via jackknife influence values:
    $$a = \frac{\sum_{i=1}^N (\bar{U} - U_{(i)})^3}{6 \left[ \sum_{i=1}^N (\bar{U} - U_{(i)})^2 \right]^{3/2}}$$

### 6.3 Hypothesis Testing & Equivalence
- **Wilcoxon Signed-Rank Tests**: Two-sided non-parametric tests evaluated under both standard zero-handling (`zero_method='wilcox'`) and Pratt zero-handling (`zero_method='pratt'`).
- **Holm-Bonferroni Correction**: FWER control across the primary contrast family ($m = 3$: $P_1$ vs $D_3$, $D_{1s}$ vs $D_3$, $D_{1m}$ vs $D_3$) and the extended family ($m = 4$, adding $D_{1s}$ vs $D_{1m}$).
- **Two One-Sided Tests (TOST)**: Evaluated at $\pm 2.0$ pp bounds ($[-0.02, +0.02]$).
- **Effect Sizes**: Within-subject Cohen's $d_z = \frac{\bar{D}}{s_D}$; rank-biserial correlation $r_{\text{rb}} = \frac{W_+ - W_-}{W_+ + W_-}$.

---

## 7. Software Dependencies and Environment Manifest

All scripts were executed and validated in the locked Conda environment:
- **Operating System**: Microsoft Windows 11 Pro (x86_64)
- **Python**: 3.12.16 (Anaconda, `D:\anaconda\envs\leakcheck\python.exe`)
- **NumPy**: 2.5.4
- **SciPy**: 1.18.1
- **Pandas**: 3.1.0
- **Scikit-Learn**: 1.6.1
- **MNE-Python**: 1.9.0
- **Matplotlib**: 3.10.1
- **Pytest**: 8.3.4 (190 passing unit tests)
- **R Environment**: R 4.4.2 (for independent cross-platform replication)
