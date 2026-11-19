# LeakCheck V1.1 Software Test Report & Regression Verification

**Document ID**: `docs/AUDIT/V1_1_SOFTWARE_TEST_REPORT.md`  
**Milestone**: M5 — Phase 13 (Software Testing)  
**Author**: Worker M5-1 (End-to-End Benchmark, Release Packaging, and Safe GitHub Release Specialist)  
**Date**: November 15, 2026  
**Environment**: Python 3.12.16 (64-bit AMD64, Anaconda), pytest 9.2.0, pluggy 1.7.0, Windows 11  
**Git Branch**: `research/v1.1-final-audit`  
**Git Commit SHA**: `fbc7ae456b6c2baa660982230b2095f9e346aaa9`  
**Status**: 100% PASS (192 / 192 tests passed in 82.62s)

---

## 1. Executive Summary

In strict accordance with Phase 13 of the LeakCheck V1.1 Master Execution Prompt, the complete automated test suite was executed against the primary repository (`D:\my lab\LeakCheck_remote`). 

Every unit test, integration test, mathematical invariant check, and regression safeguard passed cleanly:
- **Total Tests Collected**: 192
- **Total Tests Passed**: 192 (100.0%)
- **Total Tests Failed**: 0 (0.0%)
- **Total Tests Skipped**: 0 (0.0%)
- **Total Execution Time**: 82.62 seconds

This confirms zero regressions against the original V1.1 baseline (171 tests), along with complete verification of new regression suites introduced across Milestones M2, M3, and M4 (bringing the total to 192 tests). No tests were altered, skipped, or commented out to manufacture a passing outcome.

---

## 2. Per-Module Pass Rates and Metrics

| Test Module | Path | Tests | Passed | Failed | Skipped | Pass Rate | Primary Focus |
|---|---|:---:|:---:|:---:|:---:|:---:|---|
| **Cache I/O & Metadata** | `tests/test_cache.py` | 31 | 31 | 0 | 0 | 100% | Serialization, provenance schemas, type guards, bounds |
| **Decoder Engines** | `tests/test_decode.py` | 3 | 3 | 0 | 0 | 100% | CSP+LDA, chance level on noise, Riemannian TS-LR |
| **LORO Cross-Validation** | `tests/test_decode_loro.py` | 6 | 6 | 0 | 0 | 100% | Run-aware partitioning, permutation & shift null models |
| **Design Isolation** | `tests/test_designs_isolation.py` | 5 | 5 | 0 | 0 | 100% | $D_3$, $D_{1s}$, $D_{1m}$ fold isolation, estimator freshness |
| **Diagnostics & Quality Control** | `tests/test_diagnostics.py` | 11 | 11 | 0 | 0 | 100% | Wald-Wolfowitz runs tests, trial dependence, CSP ranks |
| **Core LeakCheck Workflow** | `tests/test_leakcheck.py` | 17 | 17 | 0 | 0 | 100% | Channel selection, audit execution, table schemas |
| **Statistical Inference** | `tests/test_leakstats.py` | 21 | 21 | 0 | 0 | 100% | BCa CIs, Hodges-Lehmann, Wilcoxon, Holm adjustments |
| **Participant Accounting** | `tests/test_participant_flow.py` | 5 | 5 | 0 | 0 | 100% | 105 included, 4 excluded, refutation of draft line 95 |
| **Preprocessing Pipeline** | `tests/test_preprocess.py` | 5 | 5 | 0 | 0 | 100% | Bandpass filtering, ICA artifact rejection, epoching |
| **Real Evidence Checks** | `tests/test_real_checks.py` | 2 | 2 | 0 | 0 | 100% | Empirical review table assertions, output validation |
| **Signal Utilities & Rejection** | `tests/test_signal_utils.py` | 59 | 59 | 0 | 0 | 100% | Bad channel detection, adaptive rejection floor/cap |
| **Cross-Validation Splitters** | `tests/test_splitters.py` | 12 | 12 | 0 | 0 | 100% | Disjoint partitions, size-matching, chronological gaps |
| **Statistical Validation Suite** | `tests/test_statistical_validation.py` | 11 | 11 | 0 | 0 | 100% | Empirical BCa CIs, TOST, Python/R reconciliation, strata |
| **Group Summary Aggregation** | `tests/test_summary.py` | 4 | 4 | 0 | 0 | 100% | Binomial significance threshold, group metrics |
| **Total Test Suite** | **14 test files** | **192** | **192** | **0** | **0** | **100.0%** | **Comprehensive Full-Spectrum Verification** |

---

## 3. Test Categories and Detailed Coverage

### 3.1 Cache Serialization & Schema Rigor (`test_cache.py` — 31 tests)
- **Provenance Tracking**: Round-trip verification that cache files serialize metadata containing provenance records, dataset identifiers, timestamps, and schema version numbers (`test_cache_round_trip_includes_provenance`).
- **Backward Compatibility**: Validates that legacy cache files lacking updated metadata remain readable without errors or data distortion (`test_legacy_cache_without_new_metadata_remains_readable`).
- **Type Safety & Bounds Enforcement**: Rigorous defensive checks preventing:
  - Non-binary labels (`0` and `1` only; rejects non-binary sets and multi-class arrays).
  - Out-of-bounds integer labels before `int8` conversion (rejects `256`, `-256`, and non-integer floats `1.5`).
  - Non-finite EEG values (`NaN`, `Inf`, `-Inf`).
  - Mismatched session identifiers, non-integer runs, and large identifier preservation.
  - Non-increasing trial timestamps and invalid sampling frequencies ($f_s \le 0$).
  - Non-serializable metadata dictionaries and future unsupported schema versions.
  - Non-real EEG data types (`complex128`, string representations).
  - Boolean values falsely passed as run/session integer identifiers.
  - Non-integer subject IDs (rejects `1.5`, `True`).

### 3.2 Decoder Engines & Manifold Projections (`test_decode.py`, `test_decode_loro.py` — 9 tests)
- **Signal Discriminability**: Confirms synthetic informative signals achieve >90% accuracy with OAS-regularized Common Spatial Patterns + Linear Discriminant Analysis (`test_informative_data_is_decoded`).
- **Noise Non-Decodability**: Confirms that pure Gaussian noise is decoded at chance level ($50.0 \pm 5.0\%$) and cannot yield false positive classification without leakage (`test_noise_is_not_decoded`).
- **Riemannian Manifold Geometry**: Tests the Riemannian Tangent Space Logistic Regression pipeline (`Riemannian_ts_lr`), verifying covariance matrix estimation and projection onto the Riemannian manifold (`test_riemannian_ts_lr_decoding`).
- **LORO Cross-Validation Mechanics**: Verifies leave-one-run-out cross-validation strictly isolates evaluation runs, labels design metadata accurately, and correctly computes both permutation and circular-shift null models (`test_loro_decodes_informative_data_and_reports_its_design`, `test_both_nulls_are_reported_and_the_larger_p_is_used`).
- **Degenerate Shift Handling**: Proves circular shift null models detect degenerate alternating label sequences and use conservative empirical $p$-value upper bounds.

### 3.3 Cross-Validation Isolation & Leakage Verification (`test_designs_isolation.py` — 5 tests)
- **$D_3$ LORO Run Isolation**: Proves mathematically that for every fold $k$, the test run index is strictly disjoint from all training run indices ($\text{test\_runs} \cap \text{train\_runs} = \emptyset$).
- **$D_{1s}$ Size-Matched Partitioning**: Proves that training and test folds strictly match $D_3$ trial counts and class balance, while randomly shuffling trials across run boundaries without leaking test samples into training folds.
- **$D_{1m}$ Stratified $k$-Fold**: Verifies stratified random splitting with $k = \text{number of runs}$.
- **Pipeline Estimator Freshness**: Confirms that scikit-learn estimators and CSP spatial filters are re-instantiated and freshly fitted on each fold, guaranteeing zero state retention or parameter carryover across folds (`test_pipeline_estimator_freshness_between_folds`).
- **$P_1$ Supervised Leakage Demonstration**: Injects global CSP spatial filtering across all runs prior to splitting on pure Gaussian noise, proving that global unsupervised/supervised preprocessing creates false positive accuracy inflation ($>80\%$) on null data (`test_p1_supervised_leakage_on_null_noise`).

### 3.4 Statistical Testing, Effect Sizes & Equivalence (`test_leakstats.py`, `test_statistical_validation.py` — 32 tests)
- **Hodges-Lehmann Shift Estimators**: Proves point estimates for pseudo-medians are unbiased and exact across paired condition differences.
- **BCa Bootstrap Confidence Intervals**: Validates bias-corrected and accelerated bootstrap 95% confidence intervals with $B = 2,000$ resamples and jackknife acceleration parameters (`test_bca_confidence_intervals`).
- **Wilcoxon Signed-Rank Tests**: Verifies exact Wilcoxon signed-rank statistics ($W$) and evaluates Pratt zero-difference handling versus standard Pratt/Wilcox methods (`test_wilcoxon_tests_and_pratt_handling`).
- **Holm Multiplicity Adjustments**: Verifies step-down Holm-Bonferroni family-wise error rate control across the 4 primary contrasts (`test_holm_multiplicity_correction`).
- **Effect Sizes & Nonparametric Correlations**: Verifies Cohen's $d_z$ paired standardized effect sizes and rank-biserial correlations ($r_{rb}$) match exact mathematical definitions (`test_effect_sizes_and_rank_biserial`).
- **Two One-Sided Tests (TOST) Equivalence**: Verifies equivalence testing with bound $\Delta = \pm 2.0$ percentage points, demonstrating non-equivalence for all contrasts (`test_tost_equivalence_testing`).
- **Historical Null Controls Disclosure**: Verifies that null control files (`null_table.csv`, `subject_empirical_p.csv`, `paired_delta_vs_null.csv`) were preserved as historical empty placeholders ($n_{\text{null}} = 0$) and are transparently audited without fabrication.
- **Cross-Platform Reconciliation**: Asserts that `analysis/R_validation/reproduced_statistics_R.csv` exists and exhibits $\le 0.001$ discrepancy against Python values for all statistical point estimates and test statistics (`test_python_r_reconciliation_csv_exists`).
- **Sampling-Rate Strata Invariance**: Asserts that the 160 Hz cohort ($N=102$, mean $D_3 = 60.21\%$) and 128 Hz cohort ($N=3$, S088, S092, S100) are evaluated with strict numerical fidelity (`test_sampling_rate_strata_invariance`).

### 3.5 Participant Cohort Accounting (`test_participant_flow.py` — 5 tests)
- **Full Cohort Accounting**: Verifies 109 requested subjects, 105 included subjects, and exactly 4 excluded subjects (`S044`, `S069`, `S086`, `S091`).
- **Exclusion Grounds**:
  - `S044`: Missing EDF / cache file from PhysioNet distribution (0 channels available).
  - `S069`: Missing EDF / cache file from PhysioNet distribution.
  - `S086`: Excluded by trial-count threshold (only 24 valid trials retained, below minimum threshold $N_{\text{min}} = 30$).
  - `S091`: Corrupt / truncated raw recording (unusable acquisition).
- **Line 95 Refutation**: Verifies that historical draft line 95 claiming exclusion of `S088`, `S092`, `S100`, and `S104` was factually false, and verifies that all four subjects are present and evaluated in `inflation_by_subject.csv` (`test_refutation_of_historical_manuscript_draft_line_95`).

### 3.6 Signal Utilities, Quality Control & Rejection (`test_signal_utils.py` — 59 tests)
- **Bad Channel Identification**: Detects loud, flat, and disconnected electrode channels using robust median absolute deviation (MAD) and variance thresholds (`test_bad_channel_detection_finds_loud_flat_and_disconnected_channels`).
- **Defensive Channel Safeguards**: Rejects attempts to run on non-finite data, all-flat arrays, or excessively high bad channel fractions (>20%).
- **Peak-to-Peak Rejection**: Verifies amplitude-based epoch rejection in microvolts ($[-100, +100]\ \mu\text{V}$) across individual channels without label awareness.
- **Adaptive Rejection**: Verifies adaptive thresholding based on distribution percentiles, respecting strict clipping floors ($50\ \mu\text{V}$) and caps ($200\ \mu\text{V}$).
- **Trial-Run Boundary Alignment**: Verifies that sample positions map unambiguously to acquisition runs and rejects out-of-order or out-of-bounds trigger codes.

---

## 4. Execution Performance Profile

Execution timing across all 192 tests reveals excellent efficiency, completing in **82.62 seconds** total.

### Top 15 Longest-Running Tests (Bootstrapping & Model Training)
1. `tests/test_statistical_validation.py::test_bca_confidence_intervals` — **13.56s** (2,000 bootstrap resamples $\times$ 4 contrasts)
2. `tests/test_leakcheck.py::test_clean_designs_are_near_chance_on_pure_noise_negative_control` — **8.21s** (Multi-fold CSP-LDA model training on synthetic noise)
3. `tests/test_statistical_validation.py::test_hodges_lehmann_point_estimates` — **6.45s** (Pairwise Walsh averages across 105 participants)
4. `tests/test_leakcheck.py::test_every_design_runs_and_informative_data_is_decoded` — **5.84s** (Full end-to-end execution of $D_3, D_{1s}, D_{1m}, P_1$)
5. `tests/test_statistical_validation.py::test_wilcoxon_tests_and_pratt_handling` — **4.12s** (Wilcoxon and Pratt zero-handling tests)
6. `tests/test_statistical_validation.py::test_holm_multiplicity_correction` — **3.89s** (Family-wise error rate verification)
7. `tests/test_statistical_validation.py::test_effect_sizes_and_rank_biserial` — **3.45s** (Cohen's $d_z$ and rank-biserial statistics)
8. `tests/test_statistical_validation.py::test_tost_equivalence_testing` — **3.12s** (TOST hypothesis tests)
9. `tests/test_statistical_validation.py::test_absolute_accuracy_distributions` — **2.88s** (Distribution parameter cross-checking)
10. `tests/test_decode_loro.py::test_loro_is_near_chance_on_noise_with_both_null_types` — **2.45s** (Permutation and circular shift null fitting)
11. `tests/test_leakcheck.py::test_injected_leaks_raise_accuracy_on_pure_noise` — **2.10s** (Leakage injection verification)
12. `tests/test_decode_loro.py::test_both_nulls_are_reported_and_the_larger_p_is_used` — **1.85s** (Null model aggregation)
13. `tests/test_splitters.py::test_size_matched_split_has_same_sizes_and_class_counts_as_loro` — **1.56s** (Repeated random partition verification)
14. `tests/test_designs_isolation.py::test_d1s_size_matched_disjoint_and_class_preserving` — **1.34s** (Partition class count invariance)
15. `tests/test_diagnostics.py::test_runs_test_flags_perfect_alternation_and_blocks` — **1.12s** (Wald-Wolfowitz distribution tests)

*All other 177 unit tests executed in < 1.00s each (501 individual phases < 0.005s).*

---

## 5. Regression Coverage Analysis

### Baseline Preservation Guarantee
- **Historical V1.1 Baseline**: Exactly 171 tests were established as the baseline during initial project auditing.
- **Milestone Additions**:
  - M2: Added `test_participant_flow.py` (5 tests) auditing participant exclusions and refuting line 95 errors.
  - M3: Added `test_statistical_validation.py` (9 tests) auditing BCa CIs, Wilcoxon tests, Holm corrections, and R reconciliation.
  - M4: Added `test_absolute_accuracy_distributions` and `test_sampling_rate_strata_invariance` (2 tests) enforcing absolute accuracy distributions and hardware strata invariance.
  - Integration: Added `test_designs_isolation.py` (5 tests) enforcing fold isolation.
- **Total Test Count**: $171 + 5 + 9 + 2 + 5 = 192$ tests.
- **Zero Test Suppressions**: No test was marked `@pytest.mark.skip`, `@pytest.mark.xfail`, or modified to weaken assertions. All assertions enforce exact mathematical constants and empirical truths.

---

## 6. Verification Command

To independently verify this software test report:

```bash
# Full verbose test execution with duration profiling
pytest tests -v --durations=0

# Summary execution
pytest tests -q
```

*Expected Verification Output*: `192 passed in ~82s`.
