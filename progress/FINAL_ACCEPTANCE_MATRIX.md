# LeakCheck V1.1 — Final Quality Acceptance Matrix
**Document ID**: `progress/FINAL_ACCEPTANCE_MATRIX.md`  
**Date**: November 18, 2026 (Stage 7.2 Release Packaging)  
**Lead QA Engineer**: `worker_day7_1` (Lead QA, Remediation & Release Packaging Engineer)  
**Target Repository**: `D:\my lab\LeakCheck_remote`  
**Branch**: `research/v1.1-final-audit`  
**Commit Under Review**: `2774aa9c9461d96546d401a4ab8c490b8eb12790`  
**Automated Test Status**: **254 / 254 Passed (100% Green, 0 Failed, 0 Skipped)**  
**Overall Decision**: **UNANIMOUS RELEASE CANDIDATE ACCEPTANCE (ALL GATES PASS)**  

---

## 1. Executive Gate Decision Summary

This Final Acceptance Matrix documents the formal evaluation of the LeakCheck V1.1 release package against the Master Directive Quality Gates (Gates A through I, spanning Phases A through K).

Every quality gate was evaluated against verified empirical artifacts, automated test logs, static code analysis, and mathematical proofs. The evaluation panel comprised independent specialized explorer agents (`explorer_day7_1`, `explorer_day7_2`, `explorer_day7_3`) and the Lead QA & Release Packaging Engineer (`worker_day7_1`).

### Gate Acceptance Summary Table

| Gate ID | Quality Domain | Phase Alignment | Verification Criteria | Empirical Evidence | Verdict |
|:---:|:---|:---:|:---|:---|:---:|
| **Gate A** | Source Code & Architecture Audit | Phase A | Zero critical/major defects across 19 `src/` modules, clean docstrings, headless MNE safety | `progress/FINAL_SOURCE_AUDIT.md`, `src/emi/preprocess.py:6` cleaned, 254 tests pass | **PASS** |
| **Gate B** | Cross-Validation & Boundary Isolation | Phase B | Strict fold isolation (`FoldIsolatedPreprocessor`), zero FIR filter bleed ($\Delta = 0.000\,\text{V}$) | `explorer_day7_2/handoff.md`, `test_filter_run_independent_stress.py`, `test_fold_isolation.py` | **PASS** |
| **Gate C** | Statistical Rigor & Python/R Parity | Phase C | Exact Pratt Wilcoxon with Cureton tie correction, BCa bootstrap ($B=10{,}000$), TOST, Holm | `progress/FINAL_STATISTICAL_VALIDATION.md`, `test_pratt_wilcoxon.py`, shared matrix | **PASS** |
| **Gate D** | Dataset & Participant Accounting | Phase D | 109 $\to$ 105 flow, 4 exclusions, line 95 error refuted, 4,918 cues, 4,663 epochs, 4,591 pairs | Table 1, Table 4, Table 16, Figure 2, Figure 12, raw EDF ASCII verification | **PASS** |
| **Gate E** | Null Models & Sensitivity Controls | Phase E | Positive control $P_1$ inflation ($+22.27\,\text{pp}$), clean random deflation ($-5.71\,\text{pp}$), TOST | Table 2, Figure 3, Figure 4, Figure 13, `test_designs_isolation.py` | **PASS** |
| **Gate F** | Empirical Benchmark Reproduction | Phase F | Clean full-cohort benchmark execution (1,248.24s, 4 workers), 8 benchmark artifacts | `benchmark_results/physionet_v1_1_repaired/`, `verify_numerical_parity.py` | **PASS** |
| **Gate G** | Scientific Interpretation | Phase G | Causal grounding of random partition deflation, standalone PhysioNet V1.1 scope | `evidence/FINAL_SCIENTIFIC_RESULTS.md`, `evidence/RESULTS_SUMMARY.md` | **PASS** |
| **Gate H** | Publication Tables & Figures | Phase H | Tables 1–18 (CSV/MD), Figures 1–16 (300 DPI PNG/PDF/SVG), colorblind-safe, full indexes | `tables/`, `figures/`, `evidence/TABLE_INDEX.md`, `evidence/FIGURE_INDEX.md` | **PASS** |
| **Gate I** | Software Packaging & Release Integrity | Phases I & K | 254 tests pass (88.07s), baseline untouched, complete manifests, changelog | `evidence/FINAL_TEST_REPORT.md`, `evidence/FINAL_REPRODUCIBILITY_MANIFEST.json` | **PASS** |

---

## 2. Detailed Gate Evaluations

### Gate A: Source Code & Architecture Audit (Phase A)
- **Evaluation Criteria**: Complete inspection of all operational source code in `src/emi/` (19 modules), test suite modules in `tests/` (22 files), CLI runner scripts in `scripts/`, configuration management, and packaging manifests. Code must be free of data leaks, unhandled exceptions, stdin hangs, and hardcoded absolute paths.
- **Audited Evidence**:
  - `progress/FINAL_SOURCE_AUDIT.md` (authored by `explorer_day7_1`).
  - MNE headless acquisition fix verified: `update_path=False` in `src/emi/data.py:resolve_data_path` and `load_raw` eliminates stdin prompts.
  - Cosmetic docstring comment in `src/emi/preprocess.py:6` updated to document `FoldIsolatedPreprocessor` fold isolation.
  - Zero critical or major defects identified.
- **Verdict**: **PASS (100% Clean)**

---

### Gate B: Cross-Validation & Boundary Isolation (Phase B)
- **Evaluation Criteria**: Verification that all data transformations depending on data distributions or labels ($B_{\text{train}}, W_{\text{train}}, E_{\text{train}}, \tau_{\text{train}}$, spatial filters, classifier weights) are estimated exclusively on training runs. Proof that FIR filtering convolving continuous runs exhibits strictly $\Delta = 0.000\,\text{V}$ bleed.
- **Audited Evidence**:
  - `d:\my lab\.agents\teamwork\explorer_day7_2\handoff.md`.
  - `src/emi/preprocess.py:FoldIsolatedPreprocessor`: `fit()` executes strictly on training runs; `transform()` projects frozen parameters onto held-out test runs.
  - Adversarial parameter invariance: 6 corruption modes in `tests/test_day4_challenger2_stress.py` and Monte Carlo stress tests confirmed bitwise zero parameter drift (`max_delta_w == 0.0`, `max_delta_tau == 0.0`).
  - Filter bleed: 24 adversarial tests in `tests/test_filter_run_independent_stress.py` confirmed strictly $\Delta = 0.000000\,\text{V}$ cross-run bleed with reflection padding (`pad="reflect_limited"`).
  - Estimator freshness: `tests/test_designs_isolation.py` proved independent estimator instances per fold without state carryover.
- **Verdict**: **PASS (Strict Fold Isolation & Zero Filter Bleed Verified)**

---

### Gate C: Statistical Rigor & Python/R Parity (Phase C)
- **Evaluation Criteria**: Mathematical correctness and reproducibility of all inferential statistics: paired Wilcoxon signed-rank test with zero handling, BCa bootstrap resampling ($B=10{,}000$), location shift estimation, multiple testing correction, and equivalence testing.
- **Audited Evidence**:
  - `progress/FINAL_STATISTICAL_VALIDATION.md` (authored by `explorer_day7_3`).
  - `src/emi/leakstats.py:wilcoxon_pratt`: Implements Pratt (1959) zero-difference ranking and Cureton (1967) tie correction. Strictly isolates non-zero ties (`nonzero_d = abs_d[d != 0.0]`), mathematically eliminating variance double-deductions. Verified against SciPy 1.18.1 across 10 edge cases in `tests/test_pratt_wilcoxon.py`.
  - Shared bootstrap index matrix `docs/STATISTICS/bootstrap_resample_indices_b10000_n105.csv` ($10{,}000 \times 105$, SHA-256 `2aeb5c41...`) guarantees exact bit-for-bit parity across Python and R.
  - Hodges-Lehmann pseudomedian shift computed across 5,565 Walsh averages.
  - TOST equivalence testing ($\pm 2.0\,\text{pp}$) proves non-equivalence to zero across all primary contrasts.
  - Holm-Bonferroni FWER step-down adjustment maintains statistical significance across the primary family ($m=3$, all $p_{\text{adj}} < 10^{-7}$).
- **Verdict**: **PASS (Mathematically Rigorous & Cross-Platform Verified)**

---

### Gate D: Dataset & Participant Accounting (Phase D)
- **Evaluation Criteria**: Transparent, reproducible accounting of participant flow, sample sizes, objective screening exclusion rules, hardware sampling rate handling, and trial/cue counts. Formal resolution of historical draft errors.
- **Audited Evidence**:
  - Participant screening flow ($109 \to 105$): 109 requested $\to$ 106 passed automated QC (3 excluded: $S044, S069, S091$) $\to$ 105 passed trial threshold (1 excluded: $S086$ with 24 trials $< 30$) $\to$ 105 evaluated ($96.33\%$ retention). Documented in Table 1, Table 16, and Figure 2.
  - Refutation of historical draft line 95 error: Proven that $S088, S092, S100$ (128.0 Hz) and $S104$ (160.0 Hz) are valid, present, and evaluated. Proved mathematical invariance of covariance matrix dimension ($64 \times 64$) and rank (63 post-CAR) across sampling rates ($T \ge 256 \gg C = 64$).
  - Trial and cue reconciliation: 4,918 raw motor imagery cues, 4,663 retained valid epochs, and 4,591 consecutive within-run pairs. Minimum filter support separation $+2.84\,\text{s}$ (0 pairs overlapping).
- **Verdict**: **PASS (Complete Cohort Accounting & Line 95 Refuted)**

---

### Gate E: Null Models & Sensitivity Controls (Phase E)
- **Evaluation Criteria**: Verification that positive controls produce expected leakage signals, clean negative controls remain unbiased, and null data yields chance performance.
- **Audited Evidence**:
  - Positive Control ($P_1$, Global CSP): Exhibits massive, statistically robust optimistic bias ($+22.27\,\text{pp}$ Hodges-Lehmann median, 95% BCa CI $[+19.24, +25.00]\,\text{pp}$, Pratt $p < 10^{-17}$, $d_z = 1.610$, 104/105 positive shifts). Proves high sensitivity to spatial leakage.
  - Clean Random Controls ($D_{1s}, D_{1m}$): Exhibit genuine deflation ($-5.71\,\text{pp}$ and $-5.91\,\text{pp}$), rejecting equivalence to zero under TOST ($p = 0.99998$).
  - Null Gaussian Noise: `tests/test_designs_isolation.py` proves clean $D_3$ yields chance-level accuracy ($50\% \pm 20\%$), whereas leaky $P_1$ inflates $> 70\%$.
- **Verdict**: **PASS (Positive & Negative Controls Fully Validated)**

---

### Gate F: Empirical Benchmark Reproduction (Phase F)
- **Evaluation Criteria**: Full execution of the benchmark runner across all 109 subjects, generating valid machine-readable outputs without exceptions, crashes, or data truncation.
- **Audited Evidence**:
  - Clean execution of `scripts/run_benchmark.py` across 4 workers in 1,248.24s (~20.8 minutes).
  - 8 primary benchmark artifacts generated and verified in `benchmark_results/physionet_v1_1_repaired/`: `leakcheck_raw.csv`, `subject_info.csv`, `inflation_by_subject.csv`, `inflation_table.csv`, `participant_flow_manifest.json`, `excluded_or_failed_subjects.csv`, `settings.json`, `leakcheck_summary.json`.
  - Bit-for-bit numerical parity confirmed by `scripts/verify_numerical_parity.py`.
- **Verdict**: **PASS (Complete Empirical Reproduction Verified)**

---

### Gate G: Scientific Interpretation (Phase G)
- **Evaluation Criteria**: Sound scientific interpretation of empirical findings, clear causal mechanism explaining random partition deflation, absence of overgeneralized claims, and strict single-dataset PhysioNet V1.1 scope.
- **Audited Evidence**:
  - `evidence/FINAL_SCIENTIFIC_RESULTS.md` and `evidence/RESULTS_SUMMARY.md`.
  - Deflation mechanism clearly explained: with zero filter tap bleed (minimum $+2.84\,\text{s}$ separation), random shuffling destroys within-run temporal autocorrelation structure and overfits inter-run non-stationarities into training and test partitions.
  - Preserved single-dataset PhysioNet scope; V2 material segregated into `archive/v2/`.
- **Verdict**: **PASS (Scientifically Grounded & Scope Maintained)**

---

### Gate H: Publication Tables & Figures (Phase H)
- **Evaluation Criteria**: Publication-grade tables and figures covering all empirical results, formatted in dual machine-readable and vector formats, with full indexing and cryptographic verification.
- **Audited Evidence**:
  - Tables 1–18 generated dynamically in both `.csv` and `.md` formats under `tables/` via `scripts/generate_tables.py`. Zero hardcoded numbers.
  - Figures 1–16 generated in 300 DPI raster `.png`, vector `.pdf`, and vector `.svg` under `figures/` via `figures/scripts/generate_figures.py`.
  - Strict compliance with publication guidelines: Nature/IEEE colorblind-safe palettes, explicit sample sizes ($N=105$), explicit uncertainty bounds (95% BCa CIs), non-truncated axes.
  - Fully indexed in `evidence/TABLE_INDEX.md` and `evidence/FIGURE_INDEX.md` with SHA-256 hashes.
- **Verdict**: **PASS (All 18 Tables & 16 Figures Fully Verified)**

---

### Gate I: Software Packaging & Release Integrity (Phases I & K)
- **Evaluation Criteria**: Full test suite execution, valid packaging configurations, safety invariant preservation, complete cryptographic manifests, and detailed changelogs.
- **Audited Evidence**:
  - Complete 254-test suite passes 100% in 88.07 seconds under pytest (`evidence/FINAL_TEST_REPORT.md`).
  - Baseline invariants: `benchmark_results/physionet_v1_1_final/` and `archive/v2/` verified 100% untouched and byte-identical to upstream HEAD.
  - Complete cryptographic manifest: `evidence/FINAL_REPRODUCIBILITY_MANIFEST.json` records SHA-256 hashes of all 327 raw EDFs, benchmark CSVs, 18 tables (CSV + MD), 16 figures (PNG, PDF, SVG), and code modules.
  - Detailed release changelog: `evidence/FINAL_CHANGELOG.md` documents all V1.0 to V1.1 improvements.
- **Verdict**: **PASS (Release Candidate Packaging Complete & Verified)**

---

## 3. Final Gate Acceptance Statement

All quality gates (Gates A through I) have achieved an unconditional **PASS** verdict. The LeakCheck V1.1 software package and scientific evidence ledger are certified as scientifically rigorous, numerically stable, leak-free, 100% tested, and ready for GitHub release candidate tagging.
