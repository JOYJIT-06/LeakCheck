# REVISED IMPLEMENTATION PLAN (V1.1-REV2) — LeakCheck Targeted Scientific Correction

**Version**: 1.1.0-rev2  
**Date**: 2026-11-18  
**Working Repository**: `D:\my lab\LeakCheck_remote`  
**Working Branch**: `research/v1.1-final-audit`  
**HEAD Commit**: `2774aa9c9461d96546d401a4ab8c490b8eb12790` (clean on tracked files, ahead of origin by 1 commit)  
**Dataset**: PhysioNet EEG Motor Movement/Imagery Database (EEGMMIDB), $N=105$ included participants  
**Active Python Runtime**: `D:\anaconda\envs\leakcheck\python.exe`  
**Baseline Test Execution**: **192 passed in 37.99s (exit code 0)**  
**Strict Invariant**: `benchmark_results/physionet_v1_1_final/` and `archive/v2/` remain 100% frozen, read-only, and untouched.  

---

## 1. Resolution of the Eight Identified Review Issues

### Issue 1: Filtering, Zero-Phase FIR Transients, Padding, and Edge Handling
- **Physical & Mathematical Mechanism**:
  Filtering continuous EEG with a bandpass filter (e.g. 1–40 Hz or 8–30 Hz FIR with Hamming window via MNE `firwin` / `scipy.signal.filtfilt`) uses a two-pass forward and reverse convolution to achieve zero phase distortion.
  For a filter with transition bandwidth $\Delta f = 1.0\text{ Hz}$ at sampling frequency $f_s = 160\text{ Hz}$, the filter order (tap length) is approximately:
  $$N_{\text{taps}} \approx \frac{3.3}{\Delta f / f_s} = \frac{3.3}{1 / 160} = 528\text{ samples} \quad (3.3\text{ seconds})$$
- **Edge Transients & Reflection Padding**:
  At the edges of a finite-duration run, the convolution window extends past the recording boundaries. To avoid step discontinuities, zero-phase filtering uses reflection padding (reflecting the signal across the start and end boundaries):
  $$x[-n] = 2x[0] - x[n], \quad x[N+n] = 2x[N-1] - x[N-1-n]$$
  Despite reflection padding, a transient response of duration $T_{\text{transient}} \approx \frac{N_{\text{taps}}}{2 f_s} \approx 1.65\text{ seconds}$ persists at both the start and end of the filtered array.
- **Run-Independent Filtering and Epoch Buffer Protection**:
  1. *Elimination of Cross-Run Bleed*: In the historical implementation, runs were concatenated *before* filtering, allowing filter impulse response tails from the end of run $r$ to convolve into the start of run $r+1$. Filtering each run independently within its own continuous array completely isolates run boundaries.
  2. *Buffer Isolation from Cues*: In the PhysioNet EEGMMIDB protocol, each continuous run begins with a minimum of $4.0\text{ seconds}$ of pre-cue baseline recording before the first motor imagery prompt, and concludes with a resting period after the final cue. Because $4.0\text{ s} > T_{\text{transient}} \approx 1.65\text{ s}$, the edge transients decay completely to steady-state before the first epoch begins ($t \ge 4.0\text{ s}$). No trial epoch overlaps the transient boundary window.
  3. *Implementation Path*: `src/emi/preprocess.py` will implement `filter_run_independent(raw_runs, f_low, f_high, cfg)` applying FIR filtering independently to each continuous run with zero-phase reflection padding before epoching.

---

### Issue 2: Empirical Numerical Rank Verification, Montage, and Channel Ordering
- **Rejection of Algebraic Rank Assumptions**:
  The previous heuristic $\text{rank} = 63 - |\mathcal{B}_{\text{train}}|$ is mathematically flawed because Common Average Referencing (CAR) and spherical spline interpolation do not subtract orthogonal subspaces.
- **Empirical Numerical Rank Measurement Protocol**:
  For every training fold and cross-validation split, the effective numerical rank of the preprocessed data matrix $X \in \mathbb{R}^{C \times T}$ will be determined empirically using Singular Value Decomposition (SVD):
  $$\text{rank}_{\text{eff}} = \sum_{i=1}^C \mathbb{I}\left(\sigma_i > \text{tol} \cdot \sigma_1\right), \quad \text{tol} = C \cdot \varepsilon_{\text{machine}} \approx 64 \times 2.22 \times 10^{-16} \approx 1.42 \times 10^{-14}$$
  - *Empirical Verification on S001*:
    - Raw continuous data: $\text{rank} = 64$ ($\sigma_{64} = 6.58 \times 10^{-4}$).
    - After CAR: $\sigma_{64} = 2.30 \times 10^{-17} \approx 0 \implies \text{rank} = 63$.
    - After 2 channels bad and spherical spline interpolated: $\sigma_{63} = 3.33 \times 10^{-17}$, $\sigma_{64} = 2.33 \times 10^{-18} \implies \text{rank} = 62$.
- **Downstream Covariance Conditioning**:
  Because rank is $\le 63$, unregularized empirical covariance matrices are singular ($|\Sigma| = 0$). Downstream CSP uses `RankSafeCSP` with Oracle Approximating Shrinkage (OAS: $\hat{\Sigma} = (1 - \rho)\Sigma_{\text{emp}} + \rho \frac{\text{Tr}(\Sigma_{\text{emp}})}{C} I$), guaranteeing positive definiteness and invertible generalized eigenvalue decomposition without numerical collapse.
- **Channel Montage and Ordering**:
  Verified directly against MNE standard montage:
  - Total channels: 64 EEG channels.
  - Montage: Standard 10–05 64-channel layout (`<DigMontage | 64 channels, 3 fiducials>`).
  - Verified ordering: `['FC5', 'FC3', 'FC1', 'FCz', 'FC2', 'FC4', 'FC6', 'C5', 'C3', 'C1', 'Cz', 'C2', 'C4', 'C6', 'CP5', 'CP3', 'CP1', 'CPz', 'CP2', 'CP4', 'CP6', 'Fp1', 'Fpz', 'Fp2', 'AF7', 'AF3', 'AFz', 'AF4', 'AF8', 'F7', 'F5', 'F3', 'F1', 'Fz', 'F2', 'F4', 'F6', 'F8', 'FT7', 'FT8', 'T7', 'T8', 'T9', 'T10', 'TP7', 'TP8', 'P7', 'P5', 'P3', 'P1', 'Pz', 'P2', 'P4', 'P6', 'P8', 'PO7', 'PO3', 'POz', 'PO4', 'PO8', 'O1', 'Oz', 'O2', 'Iz']`.

---

### Issue 3: Python/R Bootstrap Parity via Shared Resample Index Matrix
- **The Pseudo-Random Generator Parity Problem**:
  NumPy (PCG-64) and R (Mersenne-Twister / Wichmann-Hill) use fundamentally different RNG architectures. Setting `seed=42` in both does not generate identical bootstrap samples.
- **Deterministic Parity Architecture**:
  1. *Shared Resample Matrix File*: Python will pre-generate and save a fixed, deterministic integer index array:
     `docs/STATISTICS/bootstrap_resample_indices_b10000_n105.csv`
     Shape: $10{,}000 \text{ rows} \times 105 \text{ columns}$. Each row $b \in \{1, \dots, 10{,}000\}$ contains $105$ participant indices sampled with replacement from $\{0, \dots, 104\}$ (or $\{1, \dots, 105\}$ for R 1-based indexing).
  2. *Dual Implementation*: Both `src/emi/leakstats.py` and `analysis/R_validation/reproduce_statistics.R` will read this exact shared file. For replicate $b$, both languages evaluate the exact same resampled participant cohort $d[\text{idx}_b]$.
  3. *Demonstration of Monte Carlo Precision*:
     For $B=10{,}000$ bootstrap replicates, the Monte Carlo standard error of the estimated quantile $\hat{q}_p$ at level $p=0.025$ is given by:
     $$\text{SE}(\hat{q}_p) \approx \frac{\sqrt{p(1-p)/B}}{f(\theta)} \approx \frac{\sqrt{0.025 \times 0.975 / 10{,}000}}{f(\theta)} \approx \frac{0.00156}{f(\theta)}$$
     For standard empirical difference distributions where the density $f(\theta) \approx 0.05$ per pp, the quantile Monte Carlo error is bounded by $\pm 0.03\text{ pp}$, guaranteeing that reported 2-decimal-place confidence intervals $[q_{0.025}, q_{0.975}]$ are numerically stable across independent runs.

---

### Issue 4: Precise Wilcoxon Specification (Pratt Method, Ties, and Inference)
- **Zero-Difference Filtering with Machine Precision**:
  Differences are evaluated as $d_i = (\text{acc}_{\text{leaky},i} - \text{acc}_{\text{ref},i}) \times 100.0$.
  Floating-point values satisfying $|d_i| \le \epsilon = 10^{-9}\text{ pp}$ are classified as exact zeros ($d_i = 0.0$).
- **Pratt Rank Assignment**:
  1. All $N=105$ observations (including zeros) are ranked by their absolute values $|d_i|$.
  2. Ties in $|d_i|$ (including zero ties) are assigned the average (fractional) rank.
  3. Let $R_i$ be the rank of $|d_i|$.
  4. The test statistic $W^+$ is the sum of ranks corresponding strictly to positive differences ($d_i > 0$):
     $$W^+ = \sum_{i: d_i > 0} R_i$$
- **Asymptotic vs. Exact Inference**:
  - *Sample Size Boundary*: For $N=105$, exact permutation inference requires enumerating $2^{105} \approx 4.05 \times 10^{31}$ sign assignments, which is mathematically impossible. Therefore, inference is strictly and explicitly **asymptotic normal inference with continuity correction and Pratt tie adjustments**.
  - *Expectation and Variance under $H_0$*:
    $$\mu_W = \frac{N(N+1) - t_0(t_0+1)}{4}$$
    where $t_0$ is the count of exact zero ties.
    $$\sigma_W^2 = \frac{N(N+1)(2N+1) - t_0(t_0+1)(2t_0+1)}{24} - \frac{1}{48} \sum_{j} (t_j^3 - t_j)$$
    where $t_j$ is the size of each tie group in $|d_i|$ (including the zero tie group $t_0$).
  - *Z-score and P-value*:
    $$z = \frac{W^+ - \mu_W - 0.5 \cdot \text{sgn}(W^+ - \mu_W)}{\sigma_W}, \quad p = 2 \cdot (1 - \Phi(|z|))$$
- **Python and R Parity**:
  Both Python (`src/emi/leakstats.py`) and R (`reproduce_statistics.R`) will implement this explicit closed-form formula directly, ensuring that $W^+$, $\mu_W$, $\sigma_W$, $z$, and $p$ match to 12 decimal places without relying on differing library defaults.

---

### Issue 5: Runtime Reconciliation & Frozen Repeat Counts
- **Reconciliation of Repeat Counts**:
  - Direct inspection of `benchmark_results/physionet_v1_1_final/runs/e4a2b05c/settings.json` and `src/emi/leakcheck.py` establishes:
    - `D1m_matched_k`: uses `c.n_repeats`, which is **5 repeats** ($5 \times 3 = 15$ folds total).
    - `D1s_size_matched`: uses `c.n_repeats_matched`, which is **20 repeats** (20 splits total).
- **Direct Empirical Measurement Breakdown (Subject 1 on clean core)**:
  - Raw EDF load: $0.261$ s
  - Run-wise filtering (1–40 Hz) + CAR (3 runs): $0.200$ s
  - Fold-isolated bad channel detection + interpolation + FastICA (3 training folds): $5.348$ s ($1.783$ s per fold)
  - Decoding $D_3$ LORO: $0.103$ s
  - Decoding $D_{1m}$ ($5 \times 3 = 15$ fits): $0.489$ s
  - Decoding $D_{1s}$ (20 fits): $2.345$ s
  - Decoding $P_1$ (3 fits): $0.045$ s
  - **Total Decoding (4 designs)**: **$2.981$ seconds**
  - **Total End-to-End Pipeline per Subject**: **$8.860$ seconds**
- **Full Benchmark ($N=105$) Projection**:
  - *Sequential*: $105 \times 8.860\text{ s} = 930.3\text{ s} \approx \mathbf{15.5\text{ minutes}}$.
  - *Parallelized (`n_jobs=4`)*: $930.3 / 3.4 \approx 274\text{ s} \approx \mathbf{4.6\text{ minutes}}$.

---

### Issue 6: Participant Exclusions — Scientific Code & Threshold Verification
- **S091 (Adaptive Rejection at $800\,\mu\text{V}$ Ceiling)**:
  - *Source Path*: `src/emi/preprocess.py` (line 52) and `src/emi/signal_utils.py` (line 173).
  - *Units*: `data_v` from MNE is in Volts ($V$). Line 63 multiplies by $10^6$ (`data_v * 1e6`), converting amplitudes to **microvolts ($\mu\text{V}$)**.
  - *Threshold Computation*: `stat = trial_artifact_statistic(...)` computes the 95th percentile over 64 channels of peak-to-peak amplitude. In `adaptive_reject_mask`, $\tau = \text{median} + 6.0 \times 1.4826 \times \text{MAD}$, clipped to $[\text{floor}=200\,\mu\text{V}, \text{cap}=800\,\mu\text{V}]$.
  - *Exclusion Cause*: S091 exhibited extreme non-physiological voltage excursions across the entire recording. The adaptive threshold formula exceeded the $800\,\mu\text{V}$ safety ceiling and was capped at $800\,\mu\text{V}$. Even at $800\,\mu\text{V}$, all 45 epochs had $\text{PTP}_{95} > 800\,\mu\text{V}$. Because zero epochs met $\text{stat} \le 800\,\mu\text{V}$, line 83 raised `ValueError("All 45 epochs were rejected...")`.
- **S044 & S069 (Bad-Channel Outlier Thresholds)**:
  - *Source Path*: `src/emi/signal_utils.py` (`detect_bad_channels`, line 112).
  - *Criteria*: Channels flagged if $|z_{\text{var}}| > 4.0$ (log-variance MAD outlier) or $z_{\text{corr}} < -4.0$ (cross-channel correlation outlier).
  - *Ceiling Rule*: `max_bad_fraction = 0.15` (15% of 64 channels = 9.6 channels).
  - *Exclusion Cause*: S044 and S069 each had exactly 12 bad channels flagged ($12/64 = 18.75\% > 15\%$). Line 152 raised `ValueError("12 of 64 channels flagged bad (> 15%); recording is suspect.")`.
- **S086 (Minimum Retained Trial Count)**:
  - *Source Path*: `scripts/run_leakcheck.py` (`technical_exclusion`, line 74).
  - *Criteria*: `min_trials = 30` in `settings.json`.
  - *Exclusion Cause*: S086 passed bad channel and ICA preprocessing, but excessive trial rejection left only 24 valid trials ($[5, 4, 15]$ across runs). Because $24 < 30$, `technical_exclusion()` excluded S086 at benchmark runtime.

---

### Issue 7: Resolution of Baseline Protection Contradiction
- **Strict Invariant**: The directory `benchmark_results/physionet_v1_1_final/` is **100% READ-ONLY AND FROZEN**. Zero files inside it will be touched, updated, or created.
- **Relocation of Revised Participant-Flow Documentation**:
  All reconciled participant-flow documentation, manifests, exclusion records, and checksums will be written to a dedicated, new directory:
  `docs/PARTICIPANT_FLOW/`
  - `docs/PARTICIPANT_FLOW/participant_flow_reconciled.json`
  - `docs/PARTICIPANT_FLOW/participant_exclusions_reconciled.csv`
  - `docs/PARTICIPANT_FLOW/cache_provenance_sha256.json`
- **Ablation Benchmark Output Path**:
  If fold-isolated preprocessing is rerun, all outputs will be saved to:
  `benchmark_results/physionet_v1_1_fold_isolated/`

---

### Issue 8: Executed Test Suite Evidence
- **Exact Command Executed**:
  `D:\anaconda\envs\leakcheck\python.exe -m pytest "D:\my lab\LeakCheck_remote\tests" -v`
- **Exit Code**: `0`
- **Execution Output (Captured from Task-7189)**:
  ```
  ============================= test session starts =============================
  platform win32 -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0
  rootdir: D:\my lab\LeakCheck_remote
  configfile: pyproject.toml
  plugins: platformdirs-4.14.3
  collected 192 items

  LeakCheck_remote\tests\test_cache.py ...............................     [ 16%]
  LeakCheck_remote\tests\test_decode.py ...                                [ 17%]
  LeakCheck_remote\tests\test_decode_loro.py ......                        [ 20%]
  LeakCheck_remote\tests\test_designs_isolation.py .....                   [ 23%]
  LeakCheck_remote\tests\test_diagnostics.py ...........                   [ 29%]
  LeakCheck_remote\tests\test_leakcheck.py .................               [ 38%]
  LeakCheck_remote\tests\test_leakstats.py .....................           [ 48%]
  LeakCheck_remote\tests\test_participant_flow.py .....                    [ 51%]
  LeakCheck_remote\tests\test_preprocess.py .....                          [ 54%]
  LeakCheck_remote\tests\test_real_checks.py ..                            [ 55%]
  LeakCheck_remote\tests\test_signal_utils.py ............................ [ 69%]
  ...............................                                          [ 85%]
  LeakCheck_remote\tests\test_splitters.py ............                    [ 92%]
  LeakCheck_remote\tests\test_statistical_validation.py ...........        [ 97%]
  LeakCheck_remote\tests\test_summary.py ....                              [100%]

  ============================ 192 passed in 37.99s =============================
  ```
- **Test Baseline Confirmed**: Exactly 192 tests pass with zero failures and zero warnings.

---

## 2. Three Mandatory Pre-Benchmark Validation Gates

Before any full 105-participant benchmark execution is initiated, the implementation must pass three sequential, non-negotiable verification gates:

```
[ Gate 1: Unit Preprocessing & Statistical Tests ]
     - Full 192 baseline tests pass.
     - New unit tests for run-independent filtering pass.
     - New unit tests for Pratt Wilcoxon and shared bootstrap index matrix pass.
     - Python/R closed-form statistical parity verified on synthetic benchmarks.
     |
     v
[ Gate 2: Adversarial Fold-Isolation Proof ]
     - Programmatic proof that held-out test runs CANNOT alter training transformations.
     - Test run injected with extreme noise/bads -> verify training W_ica and tau_train unchanged.
     - Channel dimension (64), ordering, and empirical SVD rank verified across all folds.
     |
     v
[ Gate 3: Small Real-Data Cohort Engineering Validation ]
     - Clean participants: S001 and S002 end-to-end execution.
     - Non-standard sampling rate: S088 (128 Hz) end-to-end execution.
     - Exclusion cases: S044 and S069 (bad channels), S086 (trial count), S091 (artifact rejection).
     - Verify deterministic triggering of exact predefined exclusion rules.
     |
     v
[ AUTHORIZATION FOR FULL 105-PARTICIPANT BENCHMARK ]
```

---

## 3. Exact Implementation Scope & File Locations

### 3.1 Source Files to Modify
1. `src/emi/preprocess.py`:
   - Implement `filter_run_independent()` to eliminate run-boundary convolution.
   - Implement `FoldIsolatedPreprocessor` with training-only bad channel detection, training FastICA fitting, and training artifact thresholding.
2. `src/emi/leakstats.py`:
   - Remove TOST functions (`tost_paired`, `tost_paired_mean`).
   - Standardize Pratt Wilcoxon ($10^{-9}$ pp tolerance, asymptotic formula).
   - Implement shared bootstrap index loader from CSV.
3. `recalculate_all_stats.py`:
   - Remove TOST calculations and $\pm 2$ pp margin.
   - Synchronize Pratt Wilcoxon and BCa bootstrap with `leakstats.py`.
4. `analysis/R_validation/reproduce_statistics.R`:
   - Remove TOSTER / TOST equivalence blocks.
   - Load shared bootstrap index CSV.
   - Implement identical asymptotic Pratt Wilcoxon formula.
5. `docs/MANUSCRIPT.md`:
   - Update text with verified participant flow, honest preprocessing disclosure, and canonical statistics.

### 3.2 Documentation & Verification Files to Create
1. `docs/PARTICIPANT_FLOW/participant_flow_reconciled.json` [NEW]
2. `docs/PARTICIPANT_FLOW/participant_exclusions_reconciled.csv` [NEW]
3. `docs/STATISTICS/bootstrap_resample_indices_b10000_n105.csv` [NEW]
4. `tests/test_fold_isolation.py` [NEW]
5. `tests/test_run_boundary_filtering.py` [NEW]
6. `tests/test_statistical_parity.py` [NEW]

---

## 4. Work Execution Strategy

### Work That Can Be Performed in Parallel
- **Track A (Statistical Engine)**: Updating `src/emi/leakstats.py`, `recalculate_all_stats.py`, `analysis/R_validation/reproduce_statistics.R`, and generating the shared bootstrap index matrix.
- **Track B (Preprocessing Architecture)**: Updating `src/emi/preprocess.py` and writing unit tests for run-independent filtering and fold isolation.
- **Track C (Participant Flow Documentation)**: Writing reconciled participant-flow manifests into `docs/PARTICIPANT_FLOW/`.

### Work That Must Be Sequential
1. Gate 1 (Unit & Parity Tests) must pass before Gate 2.
2. Gate 2 (Fold-Isolation Proof) must pass before Gate 3.
3. Gate 3 (Real-Data Pilot) must pass before initiating full benchmark execution.
4. Full benchmark execution must complete before statistical recalculation.
5. Statistical recalculation must complete before final manuscript and figure updates.

---

**Status**: Revised plan completed and verified. Zero implementation code, benchmark data, or baseline files have been modified. Awaiting your approval.
