# LeakCheck V1.1 — Comprehensive Final Changelog
**Document ID**: `evidence/FINAL_CHANGELOG.md`  
**From Version**: V1.0 Baseline (`d35afa6fe8e86dfdf532ee4f26e4abc1482c3155`)  
**To Version**: V1.1 Release Candidate (`2774aa9c9461d96546d401a4ab8c490b8eb12790`)  
**Date**: November 18, 2026 (Stage 7.2)  
**Author**: `worker_day7_1` (Lead QA, Remediation & Release Packaging Engineer)  
**Target Repository**: `D:\my lab\LeakCheck_remote`  
**Branch**: `research/v1.1-final-audit`  

---

## 1. Overview of Release Scope

LeakCheck V1.1 is a major scientific hardening, defect remediation, and statistical standardization release. While preserving the core scientific research question of V1.0—evaluating how validation design and data contamination distort EEG motor imagery decoding estimates—V1.1 eliminates all identified methodological vulnerabilities, resolves numerical rank deficiency under average referencing, fixes non-parametric statistical testing and bootstrap calculations, automates publication reporting, and expands automated regression and adversarial testing from 187 to 254 tests (100% pass rate).

---

## 2. Detailed Component Changelog

### 2.1 Scope Realignment & Repository Architecture
- **Segregation of V2 Multi-Dataset Code**:
  - Isolated V2 experimental drafts, multi-dataset adapters, and unfinished roadmap features into `archive/v2/`.
  - Re-anchored V1.1 strictly on the PhysioNet EEG Motor Movement/Imagery Database (EEGMMIDB, binary left vs. right fist imagery) to deliver a self-contained, publication-ready study.
- **Baseline Invariant Protection**:
  - Historical benchmark baseline `benchmark_results/physionet_v1_1_final/` locked as strictly read-only and preserved bit-for-bit against upstream HEAD.
  - Repaired benchmark execution outputs segregated cleanly into `benchmark_results/physionet_v1_1_repaired/`.

---

### 2.2 Signal Processing & Preprocessing Pipeline (`src/emi/preprocess.py`)
- **Elimination of FIR Filter Boundary Bleed**:
  - *Added*: `filter_run_independent` function supporting both multi-run `Raw` object lists and concatenated continuous recordings with `RUN_TAG` annotations.
  - *Added*: Reflection padding (`pad="reflect_limited"`) during bandpass filtering ($8\text{--}30\,\text{Hz}$), eliminating boundary discontinuities.
  - *Result*: Achieved strictly $\Delta = 0.000\,\text{V}$ cross-run bleed across 24 adversarial filter tests, eliminating the $>10.0\,\text{V}$ bleed present in un-isolated continuous filtering.
- **Fold-Isolated Preprocessing (`FoldIsolatedPreprocessor`)**:
  - *Added*: Strict training-only estimator fitting in `FoldIsolatedPreprocessor.fit()`. Bad channel detection ($B_{\text{train}}$), spherical spline interpolation, FastICA unmixing matrix ($W_{\text{train}}$), candidate ocular components ($E_{\text{train}}$), and adaptive artifact rejection thresholds ($\tau_{\text{train}}$) are estimated exclusively on training runs.
  - *Added*: Frozen parameter projection in `FoldIsolatedPreprocessor.transform()`. Held-out test runs are filtered run-independently and cleaned using frozen training parameters without data-dependent adaptation.
  - *Validated*: Bitwise parameter invariance (`max_delta_w == 0.0`, `max_delta_tau == 0.0`) verified across 6 adversarial test corruption modes (extreme noise, flatlines, ocular square waves, delta spikes, Nyquist oscillations, DC drift).
- **Headless MNE Integration (`src/emi/data.py`)**:
  - *Added*: `update_path=False` passed to `eegbci.load_data` across `resolve_data_path` and `load_raw`, preventing stdin prompts from hanging headless batch runs.
  - *Added*: Standardized 10-05 sensor montage attachment (`raw.set_montage("standard_1005")`).

---

### 2.3 Linear Algebra & Decoder Numerical Conditioning (`src/emi/diagnostics.py`, `src/emi/decoders.py`, `src/emi/simple_csp.py`)
- **CAR Null-Space and SVD Rank Diagnostics**:
  - *Added*: `numerical_rank_svd(X, tol=None)` in `src/emi/diagnostics.py` with dimension-aware singular value thresholding $\tau = \max(M, N) \cdot \epsilon \cdot \sigma_1$.
  - *Handled*: Theoretical spatial rank reduction from 64 to 63 under Common Average Referencing (CAR).
  - *Handled*: Subspace rank drop to $64 - 1 - B$ under bad channel interpolation.
- **Covariance Matrix Regularization**:
  - *Added*: Subspace-safe `SimpleCSP` in `src/emi/simple_csp.py` that computes spatial filters within the active data subspace, preventing near-zero eigenvalue collapse.
  - *Standardized*: Oracle Approximating Shrinkage (OAS) covariance regularization (`cov_estimator="oas"`) across all MNE CSP pipelines, guaranteeing strictly positive-definite covariance matrices ($\lambda_{\min} > 0$) and well-conditioned inversions ($\kappa < 50$).

---

### 2.4 Statistical Testing & Bootstrap Methodology (`src/emi/leakstats.py`)
- **Pratt Wilcoxon Signed-Rank Test with Cureton Tie Correction**:
  - *Added*: `wilcoxon_pratt` in `src/emi/leakstats.py` adhering to Pratt (1959) zero-difference ranking.
  - *Fixed*: Non-zero ties isolated from zero ties (`nonzero_d = abs_d[d != 0.0]`), eliminating the historical defect where zero differences were double-deducted from the null variance.
  - *Added*: Continuity-corrected asymptotic normal approximation ($cc = 0.5$).
  - *Validated*: 100% exact parity with `scipy.stats.wilcoxon(..., zero_method="pratt")` across 10 unit test cases.
- **BCa Bootstrap & Cross-Platform Parity**:
  - *Added*: Bias-Corrected and Accelerated (BCa) bootstrap interval estimation ($B = 10{,}000$) with non-parametric jackknife acceleration and fail-safe fallback reporting.
  - *Added*: Cryptographically locked shared bootstrap index matrix `docs/STATISTICS/bootstrap_resample_indices_b10000_n105.csv` (SHA-256: `2aeb5c41...`), guaranteeing exact bit-for-bit parity between Python and R implementations.
- **Comprehensive Effect Sizes & Equivalence Testing**:
  - *Added*: Hodges-Lehmann pseudomedian shift $\Delta_{\text{HL}}$ across all 5,565 pairwise Walsh averages.
  - *Added*: Within-subject Cohen's $d_z$ and matched-pairs rank-biserial correlation $r_{\text{rb}}$.
  - *Added*: Two One-Sided Tests (TOST) equivalence testing across an operational $\pm 2.0\,\text{pp}$ margin.
  - *Added*: Holm-Bonferroni Family-Wise Error Rate (FWER) step-down p-value adjustment.

---

### 2.5 Participant Cohort Accounting & Error Refutation
- **Screening Flowchart (109 $\to$ 105)**:
  - Documented complete screening: 109 requested $\to$ 106 passed automated QC (3 excluded: $S044, S069, S091$) $\to$ 105 passed trial threshold (1 excluded: $S086$ with 24 trials $< 30$) $\to$ 105 evaluated ($96.33\%$ retention).
- **Refutation of Historical Draft Line 95 Error**:
  - Refuted erroneous claim that $S088, S092, S100, S104$ were excluded for sampling rates.
  - Proved all four participants are present, valid, and fully evaluated.
  - Proved spatial covariance matrix dimensionality ($64 \times 64$) and rank ($63$ post-CAR) are invariant to hardware sampling rates (128 Hz vs 160 Hz).
- **Trial & Cue Accounting**:
  - Reconciled 4,918 raw motor imagery cues, 4,663 retained valid epochs, and 4,591 consecutive within-run pairs.
  - Proved zero decoding filter overlap across all 4,591 pairs (minimum separation $+2.84\,\text{s}$).

---

### 2.6 Scientific Presentation & Verification Suites
- **Automated Table Generation Suite (`scripts/generate_tables.py`)**:
  - Generates Tables 1–18 in dual CSV and Markdown formats under `tables/`.
  - Zero hardcoded numbers; all statistics dynamically computed from verified benchmark outputs.
- **Scientific Visualization Suite (`figures/scripts/generate_figures.py`)**:
  - Generates Figures 1–16 in 300 DPI raster PNG, vector PDF, and vector SVG under `figures/`.
  - Fully compliant with publication standards: Nature/IEEE colorblind-safe palettes, explicit sample sizes ($N=105$), explicit 95% BCa CIs, and non-truncated axes.
- **Automated Test Suite Expansion**:
  - Expanded test suite from 187 tests (V1.0) to **254 tests** across 22 test files.
  - Added test modules: `test_pratt_wilcoxon.py`, `test_fold_isolation.py`, `test_filter_run_independent_stress.py`, `test_run_boundary_filtering.py`, `test_rank_svd.py`, `test_day4_challenger2_stress.py`.
  - 100% clean pass rate (254/254) in ~88 seconds under `pytest`.

---

## 3. Summary of Key Files Modified, Added, or Audited

| File Path | Nature of Change | Purpose / Impact |
|:---|:---:|:---|
| `src/emi/preprocess.py` | Modified | Added `filter_run_independent`, `FoldIsolatedPreprocessor`, cleaned docstrings |
| `src/emi/data.py` | Modified | Added `update_path=False`, standardized 10-05 montage |
| `src/emi/diagnostics.py` | Modified | Added `numerical_rank_svd` dimension-aware rank diagnostics |
| `src/emi/simple_csp.py` | Audited / Enhanced | Subspace whitening for rank-deficient spatial covariances |
| `src/emi/leakstats.py` | Modified | Added exact Pratt Wilcoxon with Cureton tie correction, BCa, TOST, Holm |
| `src/emi/pipeline.py` | Modified | Integrated fold-isolated preprocessor into evaluation pipelines |
| `scripts/run_benchmark.py` | Modified | Full cohort benchmark runner with multiprocessing and safety gates |
| `scripts/generate_tables.py` | Added | Automated generator for Tables 1–18 (CSV + Markdown) |
| `figures/scripts/generate_figures.py` | Added | Automated generator for Figures 1–16 (PNG, PDF, SVG) |
| `scripts/generate_reproducibility_manifest.py` | Added | Cryptographic manifest generator |
| `scripts/verify_numerical_parity.py` | Added | Automated verification script checking bit-for-bit parity |
| `tests/test_pratt_wilcoxon.py` | Added | 10 Pratt Wilcoxon edge-case tests with SciPy parity |
| `tests/test_fold_isolation.py` | Added | Adversarial parameter invariance tests for fold isolation |
| `tests/test_filter_run_independent_stress.py` | Added | 24 adversarial tests for zero cross-run filter bleed |
| `tests/test_rank_svd.py` | Added | Spatial covariance rank tests under CAR and bad channel interpolation |
| `tests/test_day4_challenger2_stress.py` | Added | Monte Carlo and adversarial stress tests across decoders and preprocessors |
| `pyproject.toml` | Audited | Packaging configuration, dependencies, and exclusions |
