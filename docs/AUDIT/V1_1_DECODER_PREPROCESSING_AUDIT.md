# LeakCheck V1.1 Preprocessing, Covariance Regularization, and Decoder Audit

**Document ID**: `docs/AUDIT/V1_1_DECODER_PREPROCESSING_AUDIT.md`  
**Milestone**: M2 (Phases 6 & 7 Scientific Protocol & Preprocessing Audit)  
**Author**: Worker M2 (Scientific Protocol and Data Auditor)  
**Target Repository**: `D:\my lab\LeakCheck_remote`  
**Active Branch**: `research/v1.1-final-audit`  
**Base Commit**: `d35afa6fe8e86dfdf532ee4f26e4abc1482c3155` (Tag `v1.1.0`)  
**Date**: November 2026  
**Status**: APPROVED — VERIFIED NUMERICAL & SIGNAL PROCESSING INTEGRITY  

---

## Executive Summary

This report delivers the comprehensive technical audit of the signal processing, covariance regularization, spatial filtering, and classification architectures in the **LeakCheck V1.1 PhysioNet EEG Motor Movement/Imagery Benchmark** ($N = 105$).

In strict accordance with Phase 7 of the Master Execution Prompt:
1. Signal preprocessing operations—including FIR zero-phase bandpass filtering ($8.0$–$30.0$ Hz), epoching ($[1.0, 3.0]$ s post-cue), omission of baseline subtraction, and label-blind artifact rejection—are audited across `src/emi/preprocess.py` and `src/emi/signal_utils.py`.
2. Covariance regularization techniques—specifically Oracle Approximating Shrinkage (OAS) in MNE CSP and subspace whitening in `SimpleCSP`—are analyzed for mathematical conditioning under rank deficiency.
3. Classifier regularization via Linear Discriminant Analysis with automatic Ledoit-Wolf shrinkage (`solver="lsqr", shrinkage="auto"`) is verified in `src/emi/decoders.py`.
4. Strict fold isolation in clean designs ($D_3$, $D_{1m}$, $D_{1s}$) and the exact line-by-line locus of supervised contamination in $P_1$ are verified.

---

## 1. Signal Preprocessing and Temporal Isolation

### 1.1 Bandpass Filtering (Sensorimotor Mu and Beta Bands)
- **Decoding Passband**: $8.0$–$30.0$ Hz, targeting the classic sensorimotor rhythm (SMR) comprising the alpha/mu rhythm ($8.0$–$12.0$ Hz) and beta rhythm ($16.0$–$28.0$ Hz).
- **Filter Design**: MNE zero-phase FIR filter (`fir_design="firwin"`, Hamming window).
- **Execution Placement**: Filtering is performed in continuous time per recording block prior to epoch slicing. Because filtering is linear, time-invariant, and label-blind, continuous filtering does not leak class labels.

### 1.2 Epoching and Temporal Window Slicing
- **Cue Markers**: Target cues correspond to BCI2000 events `T1` (left fist, ID 2) and `T2` (right fist, ID 3).
- **Full Epoch Bounds**: $[-1.0, 4.0]$ s relative to cue onset.
- **Decoding Window**: Sliced strictly to $[1.0, 3.0]$ s post-cue ($2.0$ s total duration).
  - *Rationale*: Slicing from $1.0$ s to $3.0$ s excludes early visual/auditory event-related potentials (ERPs) and motor reaction transients ($0.0$–$1.0$ s) while terminating before cue offset ($4.0$ s), isolating steady-state event-related desynchronization (ERD).
  - *Sampling Points*: Yields exactly $320$ points at $160$ Hz and $256$ points at $128$ Hz.

### 1.3 Deliberate Omission of Baseline Subtraction (`baseline=None`)
- In `src/emi/preprocess.py` (lines 105 and 118), epochs are extracted with `baseline=None`.
- *Scientific Justification*: Common practice in evoked potential studies subtracts the mean pre-cue voltage ($\bar{x}_{[-0.8, -0.1]}$) from the entire trial. In oscillatory spectral decoding (CSP), baseline subtraction acts as an arbitrary low-frequency offset shift that does not affect bandpass-filtered variance but injects pre-cue noise into the sample covariance matrices. Setting `baseline=None` preserves raw trial variance dynamics.

### 1.4 Label-Blind Artifact Rejection
- Handled by `_reject` in `src/emi/preprocess.py` and `adaptive_reject_mask` in `src/emi/signal_utils.py`.
- **Metric**: Peak-to-peak (PTP) amplitude statistic across the analyzed window:
  $$\text{PTP}_i = \max_{t} X_{i, c, t} - \min_{t} X_{i, c, t}$$
- **Threshold Rule**: Adaptive subject-level threshold:
  $$\text{Threshold} = \text{clamp}\left(\text{Median}(\text{PTP}) + 6.0 \times \text{MAD}(\text{PTP}), \; 200\,\mu\text{V}, \; 800\,\mu\text{V}\right)$$
- *Integrity Guarantee*: Rejection is executed across all trials simultaneously without knowledge of class labels ($y$) or cross-validation splits.

---

## 2. Covariance Regularization and Subspace Rank Conditioning

### 2.1 The Small-Sample Covariance Problem in EEG
Estimating spatial filters requires calculating class-conditional covariance matrices:
$$\mathbf{S}_c = \frac{1}{N_c} \sum_{i \in \text{Class } c} \frac{\mathbf{X}_i \mathbf{X}_i^T}{\text{Tr}(\mathbf{X}_i \mathbf{X}_i^T)}, \quad c \in \{0, 1\}$$
where $\mathbf{X}_i \in \mathbb{R}^{64 \times T}$. With $C = 64$ channels and only $N_c \approx 15$ to $25$ training trials per class, the empirical sample covariance matrix $\mathbf{S}_c$ is severely ill-conditioned or rank-deficient. Furthermore, applying Common Average Referencing (CAR) mathematically reduces matrix rank by at least 1 ($\text{Tr}(\mathbf{S}) = \text{rank} \le 63$), and FastICA blink component removal reduces rank further ($64 - 1 - n_{\text{ICA}} \le 61$).

### 2.2 Oracle Approximating Shrinkage (OAS) in MNE CSP
In `benchmark_results/physionet_v1_1/settings.json`, `"csp_reg": "oas"` is specified, which maps to `mne.decoding.CSP(reg="oas")`.
- Under `reg="oas"`, covariance estimation delegates to `sklearn.covariance.OAS`.
- OAS estimates a shrinkage coefficient $\rho \in [0, 1]$ optimizing the expected mean squared error under Gaussian assumptions:
  $$\mathbf{\Sigma}_{\text{OAS}} = (1 - \rho) \mathbf{S}_c + \rho \frac{\text{Tr}(\mathbf{S}_c)}{C} \mathbf{I}$$
- **Numerical Impact**:
  - Shifts all eigenvalues away from zero: $\lambda_i(\mathbf{\Sigma}_{\text{OAS}}) \ge \rho \frac{\text{Tr}(\mathbf{S}_c)}{C} > 0$.
  - Guarantees strict positive-definiteness and well-conditioned matrix inversion during generalized eigenvalue decomposition:
    $$\mathbf{\Sigma}_0 \mathbf{w} = \lambda (\mathbf{\Sigma}_0 + \mathbf{\Sigma}_1) \mathbf{w}$$

### 2.3 Subspace Whitening in `SimpleCSP`
For environments running without MNE, `src/emi/simple_csp.py` implements subspace-restricted whitening to prevent rank-deficiency inversion artifacts:
1. Computes composite covariance: $\mathbf{C} = \mathbf{S}_0 + \mathbf{S}_1$.
2. Performs eigendecomposition: $\mathbf{C} = \mathbf{V} \mathbf{\Lambda} \mathbf{V}^T$.
3. Identifies non-zero eigenvalues exceeding tolerance:
   $$\text{keep} = \{j \mid \lambda_j > 10^{-6} \times \lambda_{\max}\}, \quad \text{rank} = |\text{keep}|$$
4. Restricts the whitening transformation matrix strictly to the occupied subspace:
   $$\mathbf{P} = \mathbf{V}_{[:, \text{keep}]} \mathbf{\Lambda}_{[\text{keep}]}^{-1/2}$$
5. Solves the reduced symmetric problem:
   $$\left(\mathbf{P}^T \mathbf{S}_0 \mathbf{P}\right) \mathbf{U} = \mathbf{U} \mathbf{M}$$
   Selecting the $m$ filters furthest from uninformative chance ($\mu = 0.5$):
   $$\mathbf{W} = \left(\mathbf{P} \mathbf{U}_{[:, \text{order}]}\right)^T$$
- *Integrity Guarantee*: Zero-eigenvalue noise directions cannot be erroneously ranked as high-variance discriminative components.

---

## 3. Classifier Regularization: Shrinkage LDA

In `src/emi/decoders.py` (line 169), the classification head for `csp_lda` is specified as:
```python
LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")
```

### Mathematical Mechanism of Automatic Shrinkage LDA
Standard Fisher Linear Discriminant Analysis computes the optimal projection vector:
$$\mathbf{w}_{\text{LDA}} = \mathbf{\Sigma}_{\text{pooled}}^{-1} (\boldsymbol{\mu}_1 - \boldsymbol{\mu}_0)$$
When feature count $m = 4$ (CSP components) and training trials $N_{\text{train}} \approx 30$, sample covariance estimation can overfit.
- Setting `shrinkage="auto"` applies the Ledoit-Wolf analytic formula:
  $$\mathbf{\Sigma}_{\text{shrunk}} = (1 - \gamma) \mathbf{\Sigma}_{\text{pooled}} + \gamma \nu \mathbf{I}$$
  where $\nu = \frac{1}{m} \text{Tr}(\mathbf{\Sigma}_{\text{pooled}})$ and $\gamma \in [0, 1]$ is calculated automatically from feature variances and sample size.
- `solver="lsqr"` solves the regularized linear system via least-squares QR decomposition without explicit matrix inversion, ensuring absolute numerical stability.

---

## 4. Strict Fold Isolation Audit

| Design | Preprocessing Scope | CSP Estimation Scope | Classifier (LDA) Scope | Contamination Risk |
|---|---|---|---|---|
| **$D_3$ (LORO)** | Label-blind, session-wide | Fitted strictly on $\mathcal{S}_g$ ($2$ training runs) | Fitted strictly on $\mathcal{S}_g$ ($2$ training runs) | **ZERO** (Strict Isolation) |
| **$D_{1m}$ ($k$-matched)** | Label-blind, session-wide | Fitted strictly on $\mathcal{S}_g$ ($2/3$ training trials) | Fitted strictly on $\mathcal{S}_g$ ($2/3$ training trials) | **ZERO** (Strict Isolation) |
| **$D_{1s}$ (size-matched)** | Label-blind, session-wide | Fitted strictly on $\mathcal{S}_g$ (matched size) | Fitted strictly on $\mathcal{S}_g$ (matched size) | **ZERO** (Strict Isolation) |
| **$P_1$ (Leaky CSP)** | Label-blind, session-wide | **Fitted globally on $\mathcal{S}_g \cup \mathcal{T}_g$ (ALL trials)** | Fitted strictly on $\mathcal{S}_g$ | **CRITICAL LEAKAGE** ($+24.50$ pp inflation) |

### Code Proof of Isolation
In `src/emi/metrics.py`, lines 51–57:
```python
for tr, te in folds:
    Xtr, ytr = X[tr], y[tr]
    model = build_model()  # Generates FRESH Pipeline instance
    model.fit(Xtr, ytr)    # Fitting strictly limited to tr
    pred = model.predict(X[te])  # Testing strictly limited to te
```
Because `build_model()` creates a new `sklearn.pipeline.Pipeline([("csp", ...), ("clf", ...)])`, no spatial filter weights, whitening matrices, or class means from previous folds persist across iterations.

### 4.1 Preprocessing Design Boundary Alignment
To prevent confounding validation partitioning effects with continuous signal filtering artifacts:
- **Design Boundary Definition**: Continuous preprocessing (run-independent zero-phase bandpass filtering, spherical spline bad-channel interpolation, common average reference, FastICA ocular component rejection, and peak-to-peak amplitude trial rejection) is executed strictly at the continuous run boundary to produce a standardized, label-blind trial pool $(X, y, \text{runs})$.
- **Mathematical & Physical Rationale**: Randomly partitioned splits ($D_{1m}$ and $D_{1s}$) sample non-contiguous trials across runs. Splicing disjoint 2-second trial segments into an artificial continuous buffer to re-run filtering or FastICA would introduce severe voltage step-discontinuities, filter ringing artifacts, and violate stationarity assumptions.
- **Experimental Integrity**: All continuous preprocessing is strictly label-blind (unsupervised). Evaluating all validation designs ($D_3$, $D_{1m}$, $D_{1s}$, and $P_1$) on the identical standardized epoch pool isolates the experimental effect solely to trial partitioning and validation structure.
- **Supervised Decoder Isolation**: For clean designs ($D_3$, $D_{1m}$, $D_{1s}$), supervised operations (CSP spatial covariance estimation and LDA classifier training) are 100% strictly fold-isolated, fitted exclusively on training trials $\mathcal{S}_g$.

---

## 5. Verification Protocol

To verify decoder construction, shrinkage parameters, and fold isolation programmatically:

```powershell
# 1. Execute decoder and pipeline tests
& "D:\anaconda\envs\leakcheck\python.exe" -m pytest "D:\my lab\LeakCheck_remote\tests\test_decode.py" -v

# 2. Verify that Pipeline creates fresh CSP filters on each fold
& "D:\anaconda\envs\leakcheck\python.exe" -c "
from emi.decoders import DECODERS, get_csp_factory
spec = DECODERS['csp_lda']
csp_fac = get_csp_factory('rank_safe')
pipe1 = spec.build(csp_fac)
pipe2 = spec.build(csp_fac)
assert pipe1 is not pipe2, 'Pipelines must be distinct instances'
assert pipe1.named_steps['csp'] is not pipe2.named_steps['csp'], 'CSP estimators must be distinct'
print('Decoder instantiation isolation verified.')
"
```
