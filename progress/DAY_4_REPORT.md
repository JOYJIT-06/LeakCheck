# DAY 4 REPORT — PREPROCESSING & FOLD-ISOLATION REPAIRS

**Sprint**: LeakCheck V1.1 Seven-Day Scientific Repair, Validation & Release Sprint  
**Stage**: Day 4 / Stage 4 Completed  
**Date**: November 18, 2026  
**Lead Author**: Worker 1 (AGENT 3 focus: Preprocessing & Filter Specialist, AGENT 6 focus: Pipeline Architecture & QA)  
**Co-Authors & Reviewers**: LEAD, AGENT 4 (Adversarial Verification & Rank Specialist)  

---

## 1. Executive Summary

Day 4 completed the architectural refactoring of LeakCheck V1.1 preprocessing to eliminate temporal boundary filter bleed (Mechanism P9) and enforce mathematical fold isolation across all preprocessing operations:

1. **Run-Independent FIR Filtering (`filter_run_independent`)**:
   - Implemented polymorphic `filter_run_independent(raw_runs, l_freq=None, h_freq=None, *, cfg=None, band="ica", fir_design="firwin", pad="reflect_limited", verbose="ERROR")` in `src/emi/preprocess.py`.
   - Filters each recording run in its dedicated contiguous memory buffer with MNE reflection padding (`pad="reflect_limited"`), guaranteeing that cross-run impulse response convolution tails are identically zero ($\partial y_i[n] / \partial x_j[m] = 0$ for $i \ne j$).
   - Seamlessly handles both lists of `mne.io.BaseRaw` objects and single continuous `BaseRaw` objects partitioned via `RUN_TAG`.
   - Routed `clean_raw` (1–40 Hz) and `build_epochs_full` (8–30 Hz) through `filter_run_independent`.

2. **Fold-Isolated Preprocessor (`FoldIsolatedPreprocessor`)**:
   - Upgraded `FoldIsolatedPreprocessor` in `src/emi/preprocess.py` with full `fit` and `transform` interfaces:
     * `fit(raw_train_runs, events_train=None, window=None)`: Filters 1–40 Hz run-independently, detects bad channels strictly on training runs ($B_{\text{train}}$), interpolates bads and sets average reference, fits FastICA strictly on training data ($W_{\text{train}}$), extracts blink components ($E_{\text{train}}$), and calculates the adaptive artifact rejection threshold strictly on training broadband epochs ($\tau_{\text{train}} = \text{clamp}(\text{median} + 6 \times \text{MAD}, 200, 800)\,\mu\text{V}$).
     * `transform(raw_test_runs, events_test=None, window=None, return_epochs=None, return_qc=False)`: Linearly transforms held-out test runs using frozen $B_{\text{train}}$, $W_{\text{train}}$, $E_{\text{train}}$, rejects test epochs using frozen $\tau_{\text{train}}$, filters 8–30 Hz run-independently, and extracts decoding epochs $(X_{\text{test}}, y_{\text{test}})$.
     * Provided `fit_training(raw_train)`, `transform(raw)`, and `transform_raw(raw)` compatibility aliases ensuring 100% backward compatibility for all existing callers.

3. **Data Loader & Pipeline Integration**:
   - Added `load_raw_runs(subject: int, cfg: Config) -> list[mne.io.BaseRaw]` in `src/emi/data.py` to yield unconcatenated run objects with standardised 10-05 montage attached.
   - Added `evaluate_loro_fold_isolated(subject, cfg, factory=None)` in `src/emi/pipeline.py` to execute `FoldIsolatedPreprocessor` across leave-one-run-out folds with zero leakage.

4. **Gate 2 Adversarial Verification & Test Suite Expansion**:
   - Expanded `tests/test_run_boundary_filtering.py` to 8 unit tests (7 new comprehensive test cases + 1 baseline), proving bitwise zero filter bleed across runs ($\Delta = 0.0$) and demonstrating positive control leakage ($\Delta > 1.0\,\text{V}$) in legacy concatenation.
   - Expanded `tests/test_fold_isolation.py` to 6 tests (4 Gate 2 adversarial cases + 1 upgraded adversarial perturbation + 1 LORO execution test), proving counterfactual invariance under extreme test noise, label permutation invariance, SVD numerical rank stability under CAR and interpolation ($63 - B = 60$), and raw data immutability side-by-side with the frozen baseline.

5. **Full Regression Test Suite Results**:
   - Full automated test suite executed via Conda `leakcheck` environment (`python -m pytest tests`).
   - Result: **219 passed in 50.73s (100% green, 0 warnings, 0 failures)**.
   - Surpassed the milestone target ($\ge 215$ tests).

---

## 2. Quantitative Verification Matrix

| Component | Test File | Test Cases | Result | Key Proof |
|---|---|:---:|:---:|---|
| **Run-Independent Filtering** | `tests/test_run_boundary_filtering.py` | 8 | PASS | Max bleed into adjacent runs = $0.0\,\text{V}$ ($\Delta = 0.0$); legacy concatenation bleed = $3.904\,\text{V}$ ($\Delta > 1.0\,\text{V}$). |
| **Adversarial Test Corruption** | `tests/test_fold_isolation.py` | 1 | PASS | $10{,}000\,\mu\text{V}$ noise burst in held-out Run 12 yields bitwise identical $B_{\text{train}}$, $W_{\text{train}}$, $E_{\text{train}}$, $\tau_{\text{train}}$. |
| **Label Permutation Invariance** | `tests/test_fold_isolation.py` | 1 | PASS | Permuting, inverting, or zeroing test labels produces bitwise identical CSP filters, eigenvalues, and LDA weights. |
| **Numerical SVD Rank Stability** | `tests/test_fold_isolation.py` | 1 | PASS | Spatial rank is exactly 60 after CAR and 3 interpolated channels ($64 - 1 - 3 = 60$); OAS condition number $\kappa < 10^4$, $\lambda_{\min} > 0$. |
| **Frozen Baseline Safeguard** | `tests/test_fold_isolation.py` | 1 | PASS | SHA-256 hashes of raw input buffers invariant before/after; `benchmark_results/physionet_v1_1_final/` unmutated. |
| **Fold-Isolated LORO Pipeline** | `tests/test_fold_isolation.py` | 1 | PASS | End-to-end execution of `evaluate_loro_fold_isolated` across multi-run data with genuine fold details and pooled accuracy. |
| **Pre-existing Suite Regression** | `tests/` (18 modules) | 205 | PASS | Zero regressions across all pre-existing tests. |
| **Total Automated Suite** | `tests/` | **219** | **PASS** | **100% passing (219/219), 0 warnings, 50.73s**. |

---

## 3. Capacity Utilisation Summary (End of Day 4)

- Lead active hours on Day 4: 3.0 h (Cumulative: 12.0 h / 60.0 h ceiling)
- Specialist active hours on Day 4: 10.0 h (Cumulative: 45.0 h / 336.0 h ceiling)
- Total team capacity used: **57.0 active hours** / 396.0 active hours ceiling ($14.39\%$)
- Remaining sprint capacity: **339.0 active hours**
- Blocked hours: **0.0 hours**
- Stage 4 status: **COMPLETED & VERIFIED**
- Ready to transition to **Stage 5 (Day 5 — Controlled Gate 3 Pilot Cohort and Repaired Benchmark Execution)**.
