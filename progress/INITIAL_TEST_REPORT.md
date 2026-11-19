# INITIAL AUTOMATED TEST SUITE REPORT

**Repository**: `D:\my lab\LeakCheck_remote`  
**Date**: November 18, 2026 (Stage 1 / Day 1)  
**Auditor**: AGENT 6 (Software Engineering & QA) & AGENT 2 (Biostatistician)  
**Command**: `D:\anaconda\envs\leakcheck\python.exe -m pytest tests/ -v`  
**Execution Time**: 83.18 seconds  
**Exit Code**: `0`  
**Result**: **192 PASSED, 0 FAILED, 0 SKIPPED (100% PASS RATE)**  

---

## 1. Test Suite Coverage Breakdown

The 192 tests are distributed across 13 test modules:

| Test Module | Test Count | Status | Key Coverage |
| :--- | :---: | :---: | :--- |
| `tests/test_cache.py` | 31 | PASS | Cache fingerprinting, `.npz` serialization, metadata validation |
| `tests/test_decode.py` | 3 | PASS | Core decoder fitting, CSP feature transformation |
| `tests/test_decode_loro.py` | 6 | PASS | Leave-one-run-out decoder workflow |
| `tests/test_designs_isolation.py` | 5 | PASS | $D_3, D_{1m}, D_{1s}, P_1$ configuration isolation |
| `tests/test_diagnostics.py` | 11 | PASS | Bad-channel variance outliers, rank diagnostics |
| `tests/test_leakcheck.py` | 17 | PASS | End-to-end benchmark pipeline checks |
| `tests/test_leakstats.py` | 21 | PASS | Statistical functions, BCa resampling, Wilcoxon |
| `tests/test_participant_flow.py` | 5 | PASS | Exclusion rule assertions, cohort size ($N=105$) |
| `tests/test_preprocess.py` | 5 | PASS | Filtering, CAR referencing, epoching |
| `tests/test_real_checks.py` | 2 | PASS | Real data loading and format checks |
| `tests/test_signal_utils.py` | 59 | PASS | Signal math, covariance, OAS shrinkage, whitening |
| `tests/test_splitters.py` | 12 | PASS | LORO, matched-K, and size-matched split generators |
| `tests/test_statistical_validation.py` | 11 | PASS | P-value bounds, Holm step-down, TOST equivalence |
| `tests/test_summary.py` | 4 | PASS | Summary statistics and output formatting |
| **TOTAL** | **192** | **ALL PASS** | **100% Baseline Preserved** |

---

## 2. Invariant Verification

1. All 192 baseline tests pass without errors or warnings.
2. Zero test skips or expected failures.
3. Strict baseline stability confirmed prior to Day 2/Day 3 modifications.
