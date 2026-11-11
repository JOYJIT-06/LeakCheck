# Repository Differences & Code Provenance Report

**Date of Audit:** November 8, 2026  
**Auditor:** Google Antigravity Research Engineering & Scientific Software Audit  
**Comparison Scope:** `D:\my lab\LeakCheck` (Historical/Original) vs `D:\my lab\LeakCheck_remote` (Active Git Working Copy)  
**Status:** VERIFIED via SHA-256 Hashes and Unified AST/Source Diffs

---

## 1. Summary of Repository Comparison

| Metric | Count | Details |
|---|---|---|
| **Identical Tracked Files** | 52 | Scripts, core algorithms (`leakcheck.py`, `leakstats.py`, etc.), configs |
| **Modified / Differing Files** | 44 | Includes 3 core source modules, 2 test files, docs, and build bytecode |
| **Files Only in `LeakCheck`** | 16 | Backups (`cache.py.bak`, `run_leakcheck.py.bak`), OpenBMI raw data |
| **Files Only in `LeakCheck_remote`** | 40 | `test_cache.py`, `CLAUDE_HANDOFF_V11.txt`, `V11_current_working.patch`, benchmark results |
| **Test Count (Historical Baseline)** | 87 | 87 passed in 38.72s in `LeakCheck` |
| **Test Count (Remote Working Copy)** | 165 | 165 passed in 34.12s in `LeakCheck_remote` (+78 new tests) |

---

## 2. Detailed Module-by-Module Code Analysis

### 2.1 `src/emi/cache.py`
- **Historical Version (`LeakCheck`):** 287 lines. Simple npz cache saving/loading with basic validation. Schema v1.
- **Remote Version (`LeakCheck_remote`):** 507 lines. Schema v2 implementation.
- **Key Enhancements in Remote:**
  1. **Schema Versioning:** Added `CACHE_SCHEMA_VERSION = 2`.
  2. **Software Provenance:** Added `_software_provenance()` capturing `emi_version`, `python_version`, `numpy_version`, `mne_version` in `provenance_json`.
  3. **Strict Type and Value Validation:**
     - `_numeric_array()`: Rejects booleans and non-numeric types (`kind not in 'iuf'`).
     - `_integer_array()`: Validates integer-valued numeric identifiers, detects NaN/Inf, checks exact floor equivalence (`np.equal(arr, np.floor(arr))`), and guards against 64-bit integer overflow/truncation (`arr < -(2.0**63) | arr >= 2.0**63`).
     - `_validate_labels()`: Enforces binary labels `{0, 1}` before conversion to `int8`.
     - `_validate_eeg()`: Enforces 3D shape `(n_trials, n_channels, n_times)`, checks finiteness, prevents float32 overflow.
     - `_validate_times()`: Validates 1D strictly monotonically increasing finite time vectors.
     - `_validate_sfreq()`: Requires positive finite sampling rate and checks mathematical consistency with time delta `abs(1.0 / sfreq - dt) > 1e-6`.
  4. **Backward Compatibility:** Reads legacy Schema v1 files seamlessly while converting internal representations to strict validated formats.
- **Verdict:** **VERIFIED INTENTIONAL V1.1 IMPROVEMENT**. Retain 100% of the remote implementation.

### 2.2 `src/emi/preprocess.py`
- **Historical Version (`LeakCheck`):** Lines 72–80:
  ```python
  win = window if cfg.reject_window != "full" else (times[0], times[-1] + 1e-9)
  mask = (times >= win[0] - 1e-9) & (times < win[1] - 1e-9)
  if cfg.reject_mode == "fixed":
      bad = ptp_reject_indices(data_v[:, :, mask], cfg.reject_uv)
  ```
- **Remote Version (`LeakCheck_remote`):** Lines 72–78:
  ```python
  if cfg.reject_window == "full":
  # Include every sample in the full epoch.
  mask = np.ones(times.shape, dtype=bool)
  else:
  win = window
  # Preserve the existing analysis-window behaviour.
  mask = (times >= win[0] - 1e-9) & (times < win[1] - 1e-9)
  ```
- **Finding:** A critical **IndentationError (SyntaxError)** exists in `LeakCheck_remote`. Lines 73–78 were left unindented during an incomplete edit. Because existing unit tests run on synthetic or cached npz arrays without calling raw preprocessing, this bug was hidden during automated pytest runs.
- **Verdict:** **CRITICAL RELEASE BLOCKER**. Must be corrected immediately in V1.1 by applying the proper 4-space indentation and adding explicit test coverage for `preprocess.py`.

### 2.3 `src/emi/signal_utils.py`
- **Historical Version (`LeakCheck`):** 102 lines. Minimal signal math functions without defensive input checking.
- **Remote Version (`LeakCheck_remote`):** 315 lines. Comprehensive mathematical and boundary validation added to every public function.
- **Key Enhancements in Remote:**
  1. `_as_finite_real_array()`: Enforces float64 conversion, rejects booleans, complex numbers, and non-finite values.
  2. `_finite_number()`: Strict scalar validation with optional inclusive bounds.
  3. `_integer_array()`: Strict bounds-checking for integer arrays.
  4. `_validated_range()`: Verifies that interval ranges `[t_min, t_max]` satisfy `t_min <= t_max`.
  5. `_epoch_array()`: Validates 3D epoch dimensions `(trials, channels, time)`.
  6. Mathematical safety guards in `percent_change()`, `band_timecourse()`, `ptp_reject_indices()`, `adaptive_reject_mask()`.
- **Verdict:** **VERIFIED INTENTIONAL V1.1 IMPROVEMENT**. Retain the remote implementation.

### 2.4 `src/emi/__init__.py`
- **Historical Version:** `__version__ = "0.1.0"`
- **Remote Version:** `__version__ = "1.0.0"`
- **Verdict:** **VERIFIED**. Remote reflects the release milestone version. For the upcoming V1.1 stabilization release, this will be incremented to `"1.1.0"`.

### 2.5 `tests/test_cache.py`
- **Status in Historical (`LeakCheck`):** Missing.
- **Status in Remote (`LeakCheck_remote`):** Present (375 lines, 31 test cases).
- **Coverage:** Comprehensive validation of Schema v2, Schema v1 backward compatibility, non-binary label rejection, non-finite EEG rejection, integer overflow guarding, large run/session IDs, and corrupted metadata handling.
- **Verdict:** **VERIFIED INTENTIONAL V1.1 IMPROVEMENT**.

### 2.6 `tests/test_signal_utils.py`
- **Historical Version:** 106 lines, 12 tests.
- **Remote Version:** 381 lines, 59 tests (+47 new tests).
- **Coverage:** Rigorous edge-case testing for negative baselines, NaN/Inf handling, non-numeric inputs, and boundary violations.
- **Verdict:** **VERIFIED INTENTIONAL V1.1 IMPROVEMENT**.

---

## 3. Backups and Patch Files

The repository contains several historical patch and backup files:
1. `CLAUDE_HANDOFF_V11.txt`: Document detailing the state of `fix/v1.1-stabilization` when work was paused, recording working tree diffs, commit hashes, and file lists.
2. `V11_current_working.patch`: Clean unified diff of the unstaged changes in `LeakCheck_remote` (`cache.py`, `signal_utils.py`, `test_signal_utils.py`).
3. `scripts/run_leakcheck.py.bak` & `run_leakcheck.py.pre_csp_backup`: Pre-CSP refactor snapshots of the benchmark orchestrator.
4. `src/emi/cache.py.bak` & `cache.py.validation_backup`: Intermediate revisions before Schema v2 finalization.
5. `LICENSE.pre_release_backup`: Historical MIT license file prior to copyright line formatting.

**Action:** All historical backups will be preserved in their existing locations and excluded from the release distribution packages.
