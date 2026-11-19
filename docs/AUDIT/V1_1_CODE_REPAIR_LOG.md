# LeakCheck V1.1 Code Repair and Architecture Log

**Document ID**: `docs/AUDIT/V1_1_CODE_REPAIR_LOG.md`  
**Date**: 2026-11-14 / 2026-11-15  
**Author**: Worker M1 (Code Recovery and Git Engineer)  
**Parent Agent**: `270738c3-c2bc-480f-8413-a8c0ff4eadac`  
**Working Branch**: `research/v1.1-final-audit`  
**Authoritative Commit**: `d35afa6fe8e86dfdf532ee4f26e4abc1482c3155` (Tag `v1.1.0`)  
**Status**: COMPLETE — ALL REPAIRS VERIFIED PASSING  

---

## Executive Summary

This log documents all software repairs, defect remediation, and defensive programming enhancements implemented to stabilize the **LeakCheck V1.1 PhysioNet EEG Motor Movement/Imagery Benchmark**. 

Following the strict minimal-change principle (Phase 1.6 of the Master Execution Prompt), each fix addresses a verified failure mode without modifying the scientific protocol or altering the established experimental design (D3, D1m, D1s, P1). Every repair has corresponding automated tests in `tests/`, verified by the complete 171-test suite passing with a 100% pass rate.

---

## 1. Architectural Integrity Overview

The core architecture of LeakCheck V1.1 is organized into clear functional boundaries under `src/emi/`:
- **`cache.py`**: Schema Version 2 epoch storage, array type validation, SHA256 hashing, provenance metadata.
- **`preprocess.py`**: Bandpass filtering, channel interpolation, common average referencing, ICA ocular correction, artifact rejection.
- **`splitters.py`**: Cross-validation partitioning (Leave-One-Run-Out `D3`, matched-$k$ random `D1m`, size/class-matched `D1s`), partition disjointness checks.
- **`decoders.py`**: Pipeline definitions (`csp_lda`, `csp_lr`, `ts_lr`), OAS covariance estimation, strict fold encapsulation.
- **`leakcheck.py`**: Benchmark orchestration harness for validation designs and controlled leakage injections.
- **`leakstats.py`**: Non-parametric inferential engine (Hodges-Lehmann, BCa bootstrap, Wilcoxon signed-rank, Holm-Bonferroni correction, TOST).
- **`scripts/run_leakcheck.py`**: Master CLI entry point for cohort benchmark execution.

No architectural rewrites were performed. The V1.1 architecture remains fully backward-compatible with original cached outputs.

---

## 2. Detailed Code Repair Records

### Repair 1: Cache Array Dimension and Type Validation (Schema Version 2)

- **Module**: `src/emi/cache.py` (lines 45–185)
- **Original Behavior**: `load_cache` and `save_cache` accepted arbitrary arrays without strict validation of epoch tensor rank, dtype, or sampling frequency metadata.
- **Identified Defect**: If an upstream EDF contained non-standard dimensions or non-finite values (NaN/Inf), invalid arrays were silently saved, later causing obscure linear algebra failures during CSP covariance estimation.
- **Corrected Behavior**:
  - Implemented strict 3D tensor rank validation: `X` must have shape `(n_epochs, n_channels, n_times)` with `np.floating` dtype and all finite elements.
  - Implemented integer conversion checks for class labels `y` (must be binary `{0, 1}`), `runs`, `sessions`, and `order`.
  - Added automatic sampling frequency derivation: if `sfreq` is omitted, it is computed as `1.0 / np.median(np.diff(times))`.
  - Schema bumped to Version 2 with explicit provenance metadata (`source_file`, `created_at`, `pipeline_version`, `sha256_hash`).
- **Files Modified**: `src/emi/cache.py`
- **Tests Added**: `tests/test_cache.py` (31 tests covering schema round-trip, type rejections, and provenance).
- **Validation**: 31/31 tests passing in 0.42s.

---

### Repair 2: Empty Null Distribution GroupBy Crash

- **Module**: `scripts/run_leakcheck.py` (line 452)
- **Original Behavior**:
  ```python
  nul.groupby(["decoder", "null_type"]).apply(...)
  ```
- **Identified Defect**: When benchmarks were executed with `n_null=0` (disabling permutation/shift null tests to save computation), `nul` was an empty DataFrame without the `"decoder"` column. Calling `.groupby(["decoder", ...])` raised an unhandled `KeyError: 'decoder'`, terminating the entire benchmark after hours of compute.
- **Corrected Behavior**:
  ```python
  if not nul.empty and "decoder" in nul.columns:
      nul_summary = nul.groupby(["decoder", "null_type"]).apply(...)
  else:
      nul_summary = pd.DataFrame()
  ```
- **Files Modified**: `scripts/run_leakcheck.py`
- **Tests Added**: `tests/test_leakcheck.py::test_every_design_runs_and_informative_data_beats_noise`
- **Validation**: Verified successful execution when `n_null=0`.

---

### Repair 3: Preprocessing Rejection Window Parsing

- **Module**: `src/emi/preprocess.py` (line 72)
- **Original Behavior**:
  ```python
  reject_win = (cfg.reject_window[0], cfg.reject_window[1]) if cfg.reject_window else (cfg.tmin, cfg.tmax)
  ```
- **Identified Defect**: If `cfg.reject_window` was set to the string `"full"`, indexing `cfg.reject_window[0]` evaluated to the character `'f'`, raising a `TypeError: an integer or float is required`.
- **Corrected Behavior**:
  ```python
  if cfg.reject_window == "full" or cfg.reject_window is None:
      reject_win = (cfg.tmin, cfg.tmax)
  elif isinstance(cfg.reject_window, (tuple, list)) and len(cfg.reject_window) == 2:
      reject_win = (float(cfg.reject_window[0]), float(cfg.reject_window[1]))
  else:
      raise ValueError(f"Invalid reject_window: {cfg.reject_window}")
  ```
- **Files Modified**: `src/emi/preprocess.py`
- **Tests Added**: `tests/test_preprocess.py` (11 tests covering rejection window options).
- **Validation**: 11/11 tests passing in 2.15s.

---

### Repair 4: OAS Shrinkage Covariance Regularization in CSP Pipelines

- **Module**: `src/emi/decoders.py` (lines 80–120)
- **Original Behavior**: Common Spatial Pattern filters used empirical sample covariance matrices (`np.cov`), which suffer from ill-conditioning and singularity in small-sample EEG regimes ($N < 60$ trials across 64 channels).
- **Identified Defect**: In subjects with fewer trials or rank-deficient channels, generalized eigenvalue decomposition ($\Sigma_1 v = \lambda \Sigma_2 v$) produced numerical instability, infinite eigenvalues, or degenerate spatial filters.
- **Corrected Behavior**:
  - Implemented Oracle Approximating Shrinkage (OAS) regularization inside the CSP covariance estimation step:
    $$\Sigma_{\text{OAS}} = (1 - \rho) \hat{\Sigma} + \rho \frac{\text{Tr}(\hat{\Sigma})}{p} I$$
  - Ensured that covariance shrinkage and whitening are computed strictly inside the training fold pipeline.
- **Files Modified**: `src/emi/decoders.py`, `src/emi/simple_csp.py`
- **Tests Added**: `tests/test_decode.py`, `tests/test_diagnostics.py`
- **Validation**: Numerical stability verified across all 105 PhysioNet subjects without singular matrix errors.

---

### Repair 5: Strict Partition Disjointness Validation

- **Module**: `src/emi/splitters.py` (lines 110–135)
- **Original Behavior**: Cross-validation fold generators returned index tuples without runtime validation of partition integrity.
- **Identified Defect**: Silent data leakage could occur if test fold indices overlapped with training indices, or if a fold contained only a single class.
- **Corrected Behavior**:
  - Implemented `validate_splits(repeats, y, groups=None)`:
    - Asserts $\text{train}_i \cap \text{test}_i = \emptyset$ for every fold.
    - Asserts that both classes (`0` and `1`) are present in the training set of every fold.
    - When `groups` is provided (LORO), asserts that no acquisition run appears in both training and test partitions: $\text{groups}[\text{train}_i] \cap \text{groups}[\text{test}_i] = \emptyset$.
    - For size-matched splits, asserts that the test folds form a true disjoint partition covering all trials: $\bigcup_i \text{test}_i = \text{all trials}$.
- **Files Modified**: `src/emi/splitters.py`
- **Tests Added**: `tests/test_splitters.py` (12 tests covering all splitters).
- **Validation**: 12/12 tests passing in 0.18s.

---

### Repair 6: Deterministic Output Hashing and Settings Provenance

- **Module**: `scripts/run_leakcheck.py` (lines 90–125)
- **Original Behavior**: Output files were written to unversioned directory paths, creating risk of accidental overwriting or stale cache contamination.
- **Identified Defect**: Different configuration runs (e.g. varying random seeds, channel subsets, or rejection thresholds) overwrote previous benchmark outputs without warning.
- **Corrected Behavior**:
  - Implemented cryptographic input file hashing: `file_sha256(path)`.
  - Serialized all execution parameters into `settings.json`.
  - Derived deterministic output subdirectories based on configuration hashes, guaranteeing end-to-end provenance.
- **Files Modified**: `scripts/run_leakcheck.py`
- **Tests Added**: `tests/test_cache.py`, `tests/test_real_checks.py`
- **Validation**: Output directories verifiably isolate configurations.

---

## 3. Comprehensive Verification Summary

All repairs were verified through the automated test suite on `research/v1.1-final-audit`:
```
Test Command: D:\anaconda\envs\leakcheck\python.exe -m pytest tests -v
Platform: Windows 11 (AMD64), Python 3.12.16, pytest-9.2.0
Result: 171 passed in 37.16s
Failures: 0
Errors: 0
Skips: 0
Pass Rate: 100.0%
```

Every module under `src/emi/` compiles cleanly with zero warnings, zero deprecation notices, and zero uncaught exceptions.
