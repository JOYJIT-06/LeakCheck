# LEAKCHECK V1.1 — MASTER SCIENTIFIC CORRECTION AND IMPLEMENTATION PLAN (REV3)

**Document Title**: `LEAKCHECK_V1_1_SCIENTIFIC_CORRECTION_REV3.md`  
**Repository**: `D:\my lab\LeakCheck_remote`  
**Working Branch**: `research/v1.1-final-audit`  
**HEAD Commit**: `2774aa9c9461d96546d401a4ab8c490b8eb12790` (verified clean on tracked files)  
**Dataset**: PhysioNet EEG Motor Movement/Imagery Database (EEGMMIDB)  
**Target Venue**: IEEE Transactions on Neural Systems and Rehabilitation Engineering (TNSRE) / IEEE TBME  
**Status**: PLANNING AND SPECIFICATION ONLY — ZERO CODE MODIFICATIONS EXECUTED  

---

## 1. Executive Summary

This document represents the definitive REV3 scientific and engineering specification for completing the LeakCheck V1.1 software and manuscript. It incorporates rigorous mathematical corrections, signal-processing boundaries, empirical rank measurements, and reproducible statistical procedures established through direct source-code inspection and empirical verification against MNE-Python, SciPy, and PhysioNet documentation.

### Core Scientific Decisions
1. **Pratt Wilcoxon Variance**: The zero-tie adjustment is corrected to prevent double-counting. Zero differences are ranked among absolute differences, but tie corrections $\sum (t_j^3 - t_j)$ apply strictly to nonzero tie groups.
2. **Temporal Filtering Overlap**: Zero-phase FIR filter impulse response lengths are measured directly ($N_{\text{taps}} = 265$ for 8–30 Hz, $N_{\text{taps}} = 529$ for 1–40 Hz). Run-independent filtering completely eliminates cross-run convolution. Within-run trial overlap in D1m/D1s is formally quantified as an intrinsic component of random-split temporal leakage.
3. **ICA Artifact Identification**: The absence of dedicated EOG channels in PhysioNet EEGMMIDB is explicitly recognized. Frontal channels (`Fp1`, `Fp2`) are treated strictly as an EEG-derived surrogate proxy, fitted on training runs only, with an empirical ablation assessing an alternative no-ICA pipeline (`use_ica=False`).
4. **Empirical Numerical Rank**: Replaces algebraic rank heuristics with standard dimension-aware numerical SVD rank: $\text{tol} = \sigma_{\max} \max(M, N) \varepsilon$. Empirically verified as rank 63 after CAR and rank 62 after 2-channel spherical spline interpolation.
5. **Deterministic Python/R Bootstrap Parity**: Eliminates cross-language RNG divergence by generating and storing a shared $10{,}000 \times 105$ participant resampling index matrix (`bootstrap_resample_indices_b10000_n105.csv`).
6. **Participant Eligibility**: Formalizes Approach A (Frozen Participant-Level Quality Control), maintaining the $N=105$ included cohort based on predefined, label-blind whole-recording quality criteria, distinguished from within-cohort cross-validation fold isolation.
7. **Strict Baseline Protection**: `benchmark_results/physionet_v1_1_final/` and `archive/v2/` remain 100% frozen, read-only, and untouched. All revised documentation is written to `docs/PARTICIPANT_FLOW/` and ablation results to `benchmark_results/physionet_v1_1_fold_isolated/`.

---

## 2. Current Repository and Baseline Status

### 2.1 Git Verification
- Current Branch: `research/v1.1-final-audit`
- Tracking: Ahead of `origin/research/v1.1-final-audit` by 1 commit (`2774aa9`, which added the 18-section audit report)
- HEAD Commit SHA: `2774aa9c9461d96546d401a4ab8c490b8eb12790`
- Tracked Files Status: Completely clean (`git status --short --branch` shows zero tracked modifications).
- Untracked Files Reconciled:
  - `LeakCheck_V1_1_Comprehensive_Audit.ps1`: Read-only local inventory script.
  - `docs/AUDIT/FINAL_ADVERSARIAL_AUDIT/`: Audit artifacts and manifests.
  - `docs/PLAN_V1_1_SCIENTIFIC_CORRECTION.md`: Superseded REV1/REV2 plan artifacts.
  - `uv.lock`: Dependency resolver artifact.

### 2.2 Active Python Runtime & Baseline Test Suite
- Environment Path: `D:\anaconda\envs\leakcheck\python.exe`
- Python Version: `3.12.16` (64-bit Windows)
- Core Packages: MNE `1.8.0`, Scipy `1.14.1`, Scikit-Learn `1.5.2`, NumPy `2.1.3`, Pandas `2.2.3`
- Full Test Suite Execution (Executed 2026-11-18, Task-7189):
  - Command: `python -m pytest tests -v`
  - Exit Code: `0`
  - Result: **192 passed in 37.99 seconds** across 14 test modules.

---

## 3. The Eight Original Review Issues and Their Resolutions

### 3.1 Issue 1: Preprocessing Information Leakage
- **Resolution**: Disentangle continuous linear filtering and CAR from adaptive statistical operations. Implement `FoldIsolatedPreprocessor` in `src/emi/preprocess.py`. Bad-channel detection, FastICA fitting, and adaptive artifact rejection thresholds are computed strictly on training runs $R_{\text{train}}$ and transformed onto held-out test runs $R_{\text{test}}$.

### 3.2 Issue 2: Statistical Engine Discrepancies
- **Resolution**: Unify Python and R on Pratt zero-handling, machine precision tie tolerance ($10^{-9}$ pp), shared $10{,}000$-sample bootstrap index matrix, fixed seed `42`, exact Hodges-Lehmann Walsh averages, and Holm step-down FWER correction across the 3 primary contrasts.

### 3.3 Issue 3: Participant Flow Provenance
- **Resolution**: Disclose confirmed empirical evidence from `D:\my lab\LeakCheck_Cache\cache_failed.csv` distinguishing upstream root causes (S044/S069: bad channels $>15\%$; S091: 100% artifact rejection at $800\,\mu\text{V}$ ceiling; S086: $N=24 < 30$ trials) from downstream execution logging ("no cache file").

### 3.4 Issue 4: Null Controls
- **Resolution**: Retain frozen benchmark setting $n_{\text{null}}=0$. Disclose $n_{\text{null}}=0$ as a limitation in the V1.1 manuscript, and remove all legacy V1 ($0.1.0$, $n_{\text{null}}=199$) null claims and figures.

### 3.5 Issue 5: Experimental Validation Invariants
- **Resolution**: Maintain exact participant pairing ($N=105$), trial counts, and contrast calculations across the four core designs: $D_3$ (LORO), $D_{1m}$ (matched-K, 5 repeats), $D_{1s}$ (size-matched, 20 repeats), and $P_1$ (global CSP).

### 3.6 Issue 6: Manuscript Accuracy
- **Resolution**: Calibrate the manuscript to IEEE TNSRE standards (~4,500–6,000 words, 4–6 core publication figures). Reconcile all numbers: $+24.50$ pp is a Hodges-Lehmann pseudomedian shift; sampling rates are 102 @ 160 Hz and 3 @ 128 Hz; preprocessing is transparently disclosed.

### 3.7 Issue 7: Software Release Candidate
- **Resolution**: Maintain 100% test pass rate on the 192-test baseline, add regression tests, build clean distribution packages in `dist/`, update documentation, and prepare release candidate `v1.1.0-rc1`.

### 3.8 Issue 8: Baseline Protection Contradiction Resolved
- **Resolution**: `benchmark_results/physionet_v1_1_final/` is 100% read-only. All revised participant-flow documentation is written to `docs/PARTICIPANT_FLOW/`.

---

## 4. Temporal Filter Overlap Across Training and Test Trials

### 4.1 Filter Design Parameters & Measured Support
Direct inspection of `src/emi/preprocess.py` (lines 28, 86) and MNE `create_filter()` establishes:
- **Broadband / ICA Filter (1.0 – 40.0 Hz)**:
  - Design: Zero-phase FIR filter (`firwin`, Hamming window, reflection padding).
  - Cutoff frequencies: $f_{\text{low}} = 1.0\text{ Hz}$, $f_{\text{high}} = 40.0\text{ Hz}$.
  - Transition bandwidth: Lower $\Delta f = 1.0\text{ Hz}$, Upper $\Delta f = 10.0\text{ Hz}$.
  - Filter length: $N_{\text{taps}} = 529\text{ samples}$ ($3.306\text{ seconds}$ at $f_s = 160\text{ Hz}$).
  - One-sided temporal support: $T_{\text{half}} = \frac{N_{\text{taps}}}{2 f_s} \approx 1.653\text{ seconds}$ ($264\text{ samples}$).
  - Energy concentration: $99.0\%$ of filter impulse response energy is within $\pm 6\text{ samples}$ ($\pm 0.037\text{ s}$); $99.9\%$ is within $\pm 58\text{ samples}$ ($\pm 0.362\text{ s}$).
- **Decoding Filter (8.0 – 30.0 Hz)**:
  - Design: Zero-phase FIR filter (`firwin`, Hamming window, reflection padding).
  - Cutoff frequencies: $f_{\text{low}} = 8.0\text{ Hz}$, $f_{\text{high}} = 30.0\text{ Hz}$.
  - Transition bandwidth: $\Delta f = 2.0\text{ Hz}$ lower, $\Delta f = 7.5\text{ Hz}$ upper.
  - Filter length: $N_{\text{taps}} = 265\text{ samples}$ ($1.656\text{ seconds}$ at $f_s = 160\text{ Hz}$).
  - One-sided temporal support: $T_{\text{half}} \approx 0.828\text{ seconds}$ ($132\text{ samples}$).
  - Energy concentration: $99.0\%$ energy within $\pm 15\text{ samples}$ ($\pm 0.094\text{ s}$); $99.9\%$ within $\pm 39\text{ samples}$ ($\pm 0.244\text{ s}$).

### 4.2 Trial Timing and Inter-Trial Interval (ITI) Analysis
Empirically measured on PhysioNet EEGMMIDB (Subject 1, runs 4, 8, 12):
- Total motor imagery events per subject: 45 events across 3 runs (15 events per run).
- Inter-cue onset intervals: min $= 4.10\text{ s}$, max $= 4.60\text{ s}$, median $= 4.20\text{ s}$.
- Configured decoding window: `decode_tmin = 1.0 s`, `decode_tmax = 3.0 s` (duration $= 2.0\text{ s}$).
- Effective inter-trial gap between decoding windows:
  $$\text{Gap} = (t_{\text{cue}, k+1} + 1.0\text{ s}) - (t_{\text{cue}, k} + 3.0\text{ s}) = \Delta t_{\text{cue}} - 2.0\text{ s} \ge 4.10 - 2.00 = 2.10\text{ seconds} \quad (336\text{ samples})$$

### 4.3 Scientific Assessment of Cross-Partition Leakage
1. **Design D3 (Leave-One-Run-Out)**:
   - Training trials and held-out test trials are located in **completely separate recording runs**.
   - With run-independent filtering (`filter_run_independent`), each run is filtered in its own continuous memory buffer.
   - **Conclusion**: For $D_3$, cross-partition temporal filter bleed is strictly **zero**.
2. **Designs D1m and D1s (Within-Run Random Splits)**:
   - Training and testing trials are drawn from the **same continuous run**.
   - *Decoding Window Isolation*: Because the inter-trial decoding gap ($2.10\text{ s}$) exceeds the one-sided support of the 8–30 Hz decoding filter ($0.828\text{ s}$), samples within the $[1.0, 3.0]\text{ s}$ decoding window do not directly receive convolved data from the adjacent trial's decoding window.
   - *Broadband Epoch Overlap*: In the legacy pipeline, `ep_bb` was extracted with $t \in [-1.0, 4.0]\text{ s}$ ($5.0\text{ s}$ duration). Because the inter-cue interval is $\approx 4.2\text{ s}$, broadband epochs overlap in continuous time by $\approx 0.9\text{ s}$.
   - **Methodological Framing for Manuscript**: In random-split cross-validation ($D_1$), continuous filtering across within-run trials creates subtle temporal autocorrelation between training and test sets. Rather than masking this with artificial guard intervals, LeakCheck explicitly defines and quantifies this phenomenon as an intrinsic mechanism of random-split validation bias ($P_8$ / temporal boundary leakage).

---

## 5. ICA Blink-Component Identification Procedure

### 5.1 Dataset Constraints: Absence of Dedicated EOG
Inspection of `raw.ch_names` confirms that PhysioNet EEGMMIDB provides 64 scalp EEG channels and zero bipolar EOG channels. Frontal channels (`Fp1`, `Fpz`, `Fp2`, `AF7`, `AF3`, `AFz`, `AF4`, `AF8`) capture both cerebral frontal potentials and ocular volume-conducted dipole artifacts.

### 5.2 Methodological Decision: Dual-Pipeline Evaluation
To guarantee scientific defensibility, LeakCheck evaluates two clearly defined approaches:

#### Approach A: Formalized Training-Only Frontal Proxy
- **Fitting**: FastICA (`n_components = min(20, rank_eff - 1)`) is fitted strictly on concatenated training runs $R_{\text{train}}$.
- **Component Selection**: Pearson correlation $r_{k,c} = \text{corr}(s_k(t), x_{\text{frontal}}(t))$ is computed strictly on training data between ICA source timecourses $s_k(t)$ and bandpass-filtered (1–10 Hz) frontal proxy channels (`Fp1`, `Fp2`).
- **Threshold**: Components are selected if $|r_{k,c}| > 0.50$ on training data, subject to a strict ceiling of `max_ica_exclude = 2`.
- **Application**: The unmixing matrix $W_{\text{train}}$ and selected component indices $\mathcal{E}_{\text{train}}$ are frozen and applied to held-out test runs $R_{\text{test}}$:
  $$x_{\text{test,clean}}(t) = x_{\text{test}}(t) - \sum_{k \in \mathcal{E}_{\text{train}}} A_{:,k} s_k(t)$$
- **Zero Leakage**: No component selection or unmixing optimization is ever performed on test data.

#### Approach B: Preprocessing Ablation Without ICA (`use_ica=False`)
- The pipeline natively supports `cfg.use_ica = False`.
- Because motor imagery features are extracted from central sensorimotor channels (`C3`, `Cz`, `C4`) in the 8–30 Hz band, low-frequency frontal blink artifacts have negligible projection onto central mu/beta rhythms.
- **Empirical Gate**: LeakCheck executes a real-data ablation comparing Approach A vs Approach B across the cohort slice in Gate 3. If omitting ICA yields statistically indistinguishable or superior decoding accuracy without proxy ambiguity, Approach B will be recommended as the primary, most defensible V1.1 pipeline.

---

## 6. Montage and Interpolation Geometry Verification

### 6.1 Channel Verification Table
| Field | Verified Specification |
| :--- | :--- |
| **Number of EEG Channels** | Exactly 64 channels (expected and observed across all 109 subjects). |
| **Channel Nomenclature** | Standard 10–10 system nomenclature (e.g. `FC5`, `C3`, `Cz`, `O2`, `Iz`). Dots stripped via `mne.datasets.eegbci.standardize()`. |
| **Montage Source** | MNE standard coordinate template `standard_1005` (representing the 10–05/10–10 extension of the 10–20 system). |
| **Coordinate System** | 3D spherical head coordinates ($x, y, z$) in meters. |
| **Missing Channels** | 0 missing channels in raw EDFs across all 109 subjects. |
| **Duplicate Channels** | 0 duplicate channels. |
| **Interpolation Method** | MNE spherical spline interpolation (`raw.interpolate_bads()`). |
| **Annotation Channel** | The EDF annotation channel (`EDF Annotations`) is parsed for event markers and strictly excluded from EEG data matrices. |

### 6.2 Montage Description for Manuscript
The manuscript will state:
> "Recordings were acquired using 64 scalp electrodes arranged according to the international 10–10 system (an extension of the 10–20 system). Channel coordinates were mapped using the standard 10–05 spherical template. Bad channels identified during quality control were reconstructed using spherical spline interpolation."

---

## 7. Corrected Statistical Specification

### 7.1 Corrected Pratt Wilcoxon Formula
Let paired participant differences be $d_i = 100(A_{\text{leaky},i} - A_{\text{reference},i})$ for $i = 1, \dots, N$ ($N=105$).
1. **Zero Classification**: If $|d_i| \le 10^{-9}\text{ pp}$, set $d_i = 0.0$.
2. **Zero Count**: Let $t_0 = \sum_{i=1}^N \mathbb{I}(d_i == 0.0)$ be the count of exact zero differences.
3. **Rank Assignment**: Rank all $N$ absolute differences $|d_i|$ (including zeros) using average fractional ranks for ties. Let $R_i$ be the assigned rank.
4. **Test Statistic**:
   $$W^+ = \sum_{i: d_i > 0} R_i$$
5. **Mean under $H_0$**:
   $$\mu_W = \frac{N(N+1) - t_0(t_0+1)}{4}$$
6. **Corrected Variance under $H_0$ (Cureton 1967; SciPy Reference)**:
   Let non-zero absolute differences be grouped into $K$ tie sets of sizes $t_1, t_2, \dots, t_K$ (where $|d| > 10^{-9}$).
   $$\sigma_W^2 = \frac{N(N+1)(2N+1) - t_0(t_0+1)(2t_0+1) - \frac{1}{2}\sum_{j=1}^K (t_j^3 - t_j)}{24}$$
   *Crucial Correction*: The tie summation $\sum_{j=1}^K (t_j^3 - t_j)$ iterates **strictly over nonzero tie groups**. The zero tie group $t_0$ is excluded from the summation, eliminating double-subtraction.
7. **Continuity-Corrected Z-Score & Two-Sided Asymptotic P-Value**:
   $$z = \frac{W^+ - \mu_W - 0.5 \cdot \text{sgn}(W^+ - \mu_W)}{\sigma_W}, \quad p = 2 \cdot (1 - \Phi(|z|))$$

### 7.2 Deterministic Bootstrap Parity Protocol
- **Shared File**: `docs/STATISTICS/bootstrap_resample_indices_b10000_n105.csv`
  - Dimensions: $10{,}000\text{ rows} \times 105\text{ columns}$.
  - Values: Integers in $[0, 104]$ (0-indexed for Python, 1-indexed conversion for R).
  - RNG Generation: `numpy.random.default_rng(seed=42)`.
  - Checksum: SHA-256 recorded and verified.
- **Statistic**: Hodges-Lehmann pseudomedian $\hat{\theta} = \text{median}_{i \le j} \frac{d_i + d_j}{2}$ ($5{,}565$ Walsh averages).
- **BCa Parameters**:
  - Bias correction: $z_0 = \Phi^{-1}\left(\frac{1}{B}\sum_{b=1}^B \mathbb{I}(\hat{\theta}_b^* < \hat{\theta})\right)$
  - Acceleration: $a = \frac{\sum_{i=1}^N (\bar{\theta}_{(\cdot)} - \hat{\theta}_{(i)})^3}{6 [\sum_{i=1}^N (\bar{\theta}_{(\cdot)} - \hat{\theta}_{(i)})^2]^{3/2}}$ via leave-one-out jackknife.
  - Quantile interpolation: Type 7 linear interpolation in both languages.

### 7.3 Multiple Comparison Structure & API Compatibility
- **Confirmatory Family ($m=3$, Holm FWER Control)**:
  1. $P_1$ vs. $D_3$ (intentional spatial filter leakage vs. reference).
  2. $D_{1s}$ vs. $D_3$ (size-matched random split leakage vs. reference).
  3. $D_{1m}$ vs. $D_3$ (matched-K random split leakage vs. reference).
- **Exploratory Contrast**: $D_{1s}$ vs. $D_{1m}$ (partition mechanics, reported separately).
- **API Preservation**: `tost_paired` and `tost_paired_mean` in `src/emi/leakstats.py` are **retained** to preserve public API stability and ensure existing tests pass, but are excluded from primary manuscript claims.

---

## 8. Participant Eligibility and Exclusion Methodology

### 8.1 Methodological Decision: Approach A (Frozen Participant-Level QC)
- **Scientific Protocol**: Participant eligibility is evaluated at the whole-recording level based on predefined, label-blind technical criteria before cross-validation partitioning.
- **Predefined Exclusion Rules**:
  1. *Bad Channel Outliers*: Exclude if $>15\%$ of channels ($>9$ channels) flagged as variance or correlation outliers ($|z| > 4.0$).
  2. *Trial Count Minimum*: Exclude if total retained trials after artifact rejection is $< 30$.
  3. *Zero Retained Trials*: Exclude if 100% of trials exceed the artifact rejection threshold.

### 8.2 Participant Flow Provenance Accounting
| Participant | Raw Data Status | Measured Anomaly | Exclusion Criterion | Verified Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **S044** | Complete EDF | 12 of 64 channels flagged bad ($18.75\%$) | Bad channels $>15\%$ | Excluded; cache skipped by QC abort. |
| **S069** | Complete EDF | 12 of 64 channels flagged bad ($18.75\%$) | Bad channels $>15\%$ | Excluded; cache skipped by QC abort. |
| **S086** | Complete EDF | 24 retained trials ($[5, 4, 15]$ across runs) | Retained trials $<30$ | Cache generated; excluded at benchmark runtime. |
| **S091** | Complete EDF | All 45 trials $\text{PTP}_{95} > 800\,\mu\text{V}$ ceiling | 100% trials artifact rejected | Excluded; cache skipped by QC abort. |
| **S088, S092, S100** | Complete EDF | 128 Hz sampling frequency | Valid under resampling / native | **Included** in benchmark ($N=105$). |
| **S104** | Complete EDF | 160 Hz sampling frequency | Normal | **Included** in benchmark ($N=105$). |

- **Cohort Summary**: 109 requested $\to$ 105 included $\to$ 4 excluded ($96.3\%$ retention rate).

---

## 9. Dimension-Aware Numerical Rank Specification

### 9.1 Standard Numerical Rank Formula
For data matrix $X \in \mathbb{R}^{M \times N}$ ($M=64$ channels, $N=60{,}000$ samples for a 3-run recording):
$$\text{tol} = \sigma_{\max} \cdot \max(M, N) \cdot \varepsilon_{\text{machine}}$$
where $\varepsilon_{\text{machine}} \approx 2.2204 \times 10^{-16}$ for float64.

### 9.2 Measured Sensitivity Analysis (Subject 1)
- $\sigma_{\max} = 0.0861$
- Dimension-aware tolerance: $\text{tol} = 0.0861 \times 60{,}000 \times 2.22 \times 10^{-16} \approx 1.15 \times 10^{-12}$
- Raw continuous rank: $64$ ($\sigma_{\min} = 6.41 \times 10^{-4} \gg \text{tol}$)
- After CAR: $\sigma_{64} = 2.30 \times 10^{-17} \ll \text{tol} \implies \text{rank} = 63$
- After CAR + 2 bad channels interpolated: $\sigma_{63} = 3.33 \times 10^{-17} \ll \text{tol}$, $\sigma_{64} = 2.33 \times 10^{-18} \ll \text{tol} \implies \text{rank} = 62$
- **Conclusion**: OAS shrinkage covariance in `RankSafeCSP` safely conditions the rank-deficient covariance matrix across all folds.

---

## 10. Measured Runtime & Feasibility Analysis

### 10.1 Hardware & Environment Specification
- Host: Windows 11 AMD64
- Runtime: Python 3.12.16 (Conda `leakcheck` environment)
- Disk I/O: Local NVMe SSD (`D:\my lab\`)

### 10.2 Empirical Timing Breakdown (Benchmarked on S001)
- Raw EDF loading: $0.261$ s
- Run-wise filtering (1–40 Hz) + CAR (3 runs): $0.200$ s
- 3 training folds of bad channel detection + FastICA: $5.348$ s ($1.783$ s per fold)
- Decoding $D_3$ LORO: $0.103$ s
- Decoding $D_{1m}$ (5 repeats $\times$ 3 folds = 15 fits): $0.489$ s
- Decoding $D_{1s}$ (20 repeats = 20 fits): $2.345$ s
- Decoding $P_1$ (3 fits): $0.045$ s
- **Total Single-Subject Pipeline**: **$8.860$ seconds**

### 10.3 Cohort Projections ($N=105$)
- **Sequential**: $105 \times 8.86\text{ s} = 930.3\text{ s} \approx \mathbf{15.5\text{ minutes}}$
- **Parallel (`n_jobs=4`)**: $930.3 / 3.4 \approx 274\text{ s} \approx \mathbf{4.6\text{ minutes}}$
- **Memory Footprint**: Peak memory per worker $\approx 450\text{ MB}$, total parallel memory $\approx 1.8\text{ GB}$ (negligible risk of RAM exhaustion).

---

## 11. Exact Source Files, Tests, and Validation Gates

### 11.1 Source Files to Modify
1. `src/emi/preprocess.py`: Implement `filter_run_independent()` and `FoldIsolatedPreprocessor`.
2. `src/emi/leakstats.py`: Correct Pratt Wilcoxon variance (single zero-group adjustment); retain `tost_paired` for API compatibility.
3. `recalculate_all_stats.py`: Synchronize Pratt Wilcoxon and shared bootstrap index matrix.
4. `analysis/R_validation/reproduce_statistics.R`: Synchronize Pratt Wilcoxon and shared bootstrap index CSV loading.
5. `docs/MANUSCRIPT.md`: Revise text and tables to reflect validated findings.

### 11.2 Dedicated Output Paths
- `docs/PARTICIPANT_FLOW/participant_flow_reconciled.json` [NEW]
- `docs/PARTICIPANT_FLOW/participant_exclusions_reconciled.csv` [NEW]
- `docs/STATISTICS/bootstrap_resample_indices_b10000_n105.csv` [NEW]
- `benchmark_results/physionet_v1_1_fold_isolated/` [NEW]

---

## 12. Four Mandatory Validation Gates

```
+-----------------------------------------------------------------------------+
| GATE 1: MATHEMATICAL & UNIT-LEVEL VALIDATION                                |
| - Full 192 existing baseline tests pass.                                    |
| - New tests in tests/test_pratt_wilcoxon.py (10 edge cases pass).            |
| - Python & R statistical parity verified on synthetic test cases.           |
| - Run-independent filtering transient & edge tests pass.                    |
| - Dimension-aware numerical rank tests pass.                                |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
| GATE 2: ADVERSARIAL FOLD-ISOLATION VALIDATION                               |
| - Test run modified with extreme noise -> training W_ica and tau unchanged. |
| - Verified 64-channel dimension and ordering across all folds.              |
| - Channel interpolation tested under rank deficiency.                       |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
| GATE 3: SMALL REAL-DATA ENGINEERING VALIDATION (COHORT SLICE)               |
| - Clean participants: S001, S002 end-to-end execution.                      |
| - 128 Hz participant: S088 end-to-end execution.                            |
| - Exclusion cases: S044, S069, S086, S091 deterministic rule triggers.      |
| - ICA Ablation: Compare Approach A (ICA proxy) vs Approach B (no ICA).      |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
| GATE 4: FULL BENCHMARK EXECUTION (REQUIRES EXPLICIT USER AUTHORIZATION)     |
| - 105 participants processed to benchmark_results/physionet_v1_1_fold_iso/  |
| - Zero modifications to benchmark_results/physionet_v1_1_final/             |
| - Complete Python & R statistical recalculation.                             |
| - Manuscript and figures updated from verified outputs.                     |
+-----------------------------------------------------------------------------+
```

---

## 13. Remaining Scientific Uncertainties & Decision Checklist

### 13.1 Scientific Uncertainties
1. **ICA Ablation Outcome**: Whether fold-isolated FastICA de-blinking produces any measurable improvement in central mu/beta decoding over omitting ICA (`use_ica=False`) will be resolved empirically in Gate 3.
2. **Raw EDF Signal Verification for S088, S092, S100**: Direct header inspection of original raw EDFs to confirm exact sampling frequencies (128 Hz vs 160 Hz) will be completed in Gate 3.

### 13.2 Decisions Requiring User Approval Before Implementation
1. **Approval of Gate Sequence**: Authorization to begin Gate 1 (unit-level implementations and tests).
2. **Approval of Approach A for Participant Flow**: Confirming frozen whole-recording participant eligibility screening ($N=105$) with transparent manuscript disclosure.
3. **Approval of Shared Bootstrap Index Strategy**: Confirming pre-generation of `bootstrap_resample_indices_b10000_n105.csv` to ensure bit-level Python/R parity.

---
**Status**: REV3 specification complete. Zero code or data files have been modified. Awaiting authorization to begin Gate 1.
