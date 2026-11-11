# LeakCheck Existing Capabilities & Implementation Audit

**Date of Audit:** November 8, 2026  
**Auditor:** Google Antigravity Research Engineering & Scientific Software Audit  
**Status:** VERIFIED against `src/emi/` source code and test suite

---

## 1. Implemented Validation Designs

| Design ID | Scientific Definition | Implementation Status | Code Location | Test Verification |
|---|---|---|---|---|
| **D1** | Random trial split (unstratified shuffled k-fold) | **VERIFIED** | `src/emi/leakcheck.py::d1_shuffled_kfold` | `tests/test_leakcheck.py` |
| **D2** | Stratified random trial split (class-balanced k-fold) | **VERIFIED** | `src/emi/leakcheck.py::d2_stratified_kfold` | `tests/test_leakcheck.py` |
| **D1m** | Matched random split (fold count matches LORO run count) | **VERIFIED** | `src/emi/leakcheck.py::d1m_matched_k` | `tests/test_leakcheck.py` |
| **D1s** | Size- and class-matched random split (exact trial counts and class balance match LORO folds) | **VERIFIED (Code)** / **MISSING (Benchmark)** | `src/emi/splitters.py::SizeMatchedRandomSplit`, `src/emi/leakcheck.py::d1s_size_matched` | `tests/test_splitters.py::test_size_matched_split_*` |
| **D3** | Leave-one-run-out (LORO; genuine held-out acquisition block) | **VERIFIED** | `src/emi/leakcheck.py::d3_loro`, `src/emi/decode.py::evaluate_loro` | `tests/test_decode_loro.py`, `tests/test_leakcheck.py` |
| **D4** | Chronological holdout (train on early runs, test on late runs) | **VERIFIED** | `src/emi/splitters.py::chrono_holdout`, `src/emi/leakcheck.py::d4_chrono_holdout` | `tests/test_splitters.py::test_chrono_holdout` |
| **D4b** | Forward-chaining validation (expanding window across runs) | **VERIFIED** | `src/emi/splitters.py::forward_chain`, `src/emi/leakcheck.py::d4b_forward_chain` | `tests/test_splitters.py::test_forward_chain` |
| **D5** | Gapped chronological validation (temporal buffer between train and test) | **VERIFIED** | `src/emi/splitters.py::GappedChronologicalSplit`, `src/emi/leakcheck.py::d5_gapped_chrono` | `tests/test_splitters.py` |
| **D6** | Leave-one-session-out (held-out longitudinal session) | **VERIFIED** | `src/emi/splitters.py::session_splits`, `src/emi/leakcheck.py::d6_loso` | `tests/test_leakcheck.py::test_session_design_is_skipped` |
| **D7** | Leave-one-subject-out (cross-subject generalisation) | **PROPOSED** | Not yet implemented in `src/emi/` | Planned for V2 |

---

## 2. Implemented Leakage Mechanisms

| Mechanism ID | Contamination Pathway | Implementation Status | Clean Reference | Contaminated Implementation | Test Verification |
|---|---|---|---|---|---|
| **P1** | Global Common Spatial Pattern (CSP) | **VERIFIED** | Fold-nested CSP in `d3_loro` | CSP fitted on all trials and labels before CV in `leakcheck.py::p1_csp_on_all` | `tests/test_leakcheck.py::test_p1_*` |
| **P2** | Global ICA contamination | **PARTIALLY VERIFIED** | Stubbed in `leakcheck.py::p2_ica_on_all` | Simulates global component rejection | Requires full MNE ICA pipeline |
| **P3** | Global scaling / normalization | **VERIFIED** | Fold-nested scaler | Mean/std fitted across all trials in `leakcheck.py::p3_scale_on_all` | `tests/test_leakcheck.py` |
| **P4** | Global feature/channel selection | **VERIFIED** | Fold-nested channel selection | Selected best channels across all trials using labels in `p4_channel_select_on_all` | `tests/test_leakcheck.py::test_channel_selector_*` |
| **P5** | Test-set hyperparameter tuning | **VERIFIED** | Fold-nested evaluation | Regularisation parameter chosen on test fold in `p5_tune_on_test` | `tests/test_leakcheck.py` |
| **P6** | Overlapping-window contamination | **VERIFIED** | Clean window slicing | Synthetic overlapping epoch injection in `p6_overlap_windows` | `tests/test_leakcheck.py` |
| **P7** | Augmentation contamination | **VERIFIED** | Training-only augmentation | Augmented trials from test fold leaked into training in `p7_augment_leak` | `tests/test_leakcheck.py` |
| **P8** | Channel-selection contamination | **PARTIALLY VERIFIED** | Conflated with P4 ChannelSelector | Dedicated physiological selection needed | Planned for V1.1/V2 formal separation |
| **P9** | Temporal / run-boundary contamination | **VERIFIED** | Gapped boundary holdout | Cross-boundary filtering simulation in `p9_boundary_filter` | `tests/test_leakcheck.py` |

---

## 3. Implemented Decoders & Extensibility

1. **CSP + LDA Baseline (`csp_lda`):**
   - Implemented via MNE-Python `mne.decoding.CSP` and Scikit-Learn `LinearDiscriminantAnalysis(solver='lsqr', shrinkage='auto')`.
   - Standalone fallback implemented in `simple_csp.py::SimpleCSP` for lightweight NumPy/SciPy execution without MNE dependencies.
2. **Modular Decoder Abstraction (`src/emi/decoders.py`):**
   - `DecoderSpec`: Encapsulates pre-feature scaling (`ChannelScaler`), channel selection (`ChannelSelector`), spatial filtering factory, and scikit-learn classifier.
   - Clean extensibility hooks ready for CSP-SVM, CSP-LogisticRegression, and Riemannian classifiers in V2.

---

## 4. Implemented Statistical Inference Engine (`src/emi/leakstats.py`)

- **Participant as Unit of Analysis:** Every statistical test operates on paired participant-level distributions ($N=105$), never on pooled trials.
- **Hodges-Lehmann Estimator (`hodges_lehmann`):** Robust, non-parametric point estimate of the median paired difference.
- **BCa Bootstrap Confidence Intervals (`bca_ci`):** Bias-corrected and accelerated bootstrap confidence intervals resampling participants.
- **Rank-Biserial Correlation (`rank_biserial`):** Non-parametric effect size matching Wilcoxon signed-rank test.
- **Cohen's $d_z$ (`cohens_dz`):** Standardized paired effect size.
- **TOST Equivalence Testing (`tost_paired`):** Two One-Sided Tests for statistically establishing equivalence within equivalence margins $[-\Delta, +\Delta]$.
- **Multiple Comparison Correction (`holm`):** Step-down Holm-Bonferroni Family-Wise Error Rate (FWER) control.
- **Meta-Analytic Heterogeneity (`meta_analysis`):** Derives DerSimonian-Laird random effects, Cochran's $Q$, and $I^2$ inconsistency metrics across participants or datasets.

---

## 5. Negative Controls & Null Models (`src/emi/nulls.py`)

1. **Within-Run Permutation Null (`permute_within_runs`):**
   - Permutes trial labels strictly within each recording run, preserving exact per-run class ratios while destroying the EEG-label relationship.
2. **Within-Run Circular Shift Null (`circular_shift_within_runs`):**
   - Applies a circular shift to labels within each run, preserving the first-order label autocorrelation while breaking the alignment with neural responses.
3. **Empirical P-Value Calculation (`empirical_p`):**
   - Exact Monte Carlo formula: $p = \frac{1 + \sum [acc_{null} \ge acc_{real}]}{1 + N_{null}}$.

---

## 6. Caching and Provenance Engine (`src/emi/cache.py`)

- **Schema Version 2:**
  - Full software provenance recorded in JSON metadata (`emi`, `python`, `numpy`, `mne` versions).
  - Strict type checking (rejecting booleans, complex numbers, non-finite arrays, invalid label sets).
  - Monotonic finite time array validation and sampling-rate mathematical consistency checks.
  - Backward compatibility: reads all 106 existing historical PhysioNet cache files in `LeakCheck_Cache`.
