# DAY 6 REPORT — STATISTICAL REPORTING, TABLES AND SCIENTIFIC FIGURES

**Sprint**: LeakCheck V1.1 Seven-Day Scientific Repair, Validation & Release Sprint  
**Stage**: Day 6 / Stage 6 Completed  
**Date**: November 18, 2026  
**Lead Author**: Worker Day 6 (Lead Statistical Reporting & Visualization Engineer)  
**Co-Authors & Reviewers**: LEAD (Project Director), AGENT 7 (Evidence & Visualization), AGENT 2 (Biostatistics), AGENT 6 (QA & Regression)  

---

## 1. Executive Summary

Stage 6 (Day 6) has successfully transformed the verified empirical benchmark outputs of the repaired PhysioNet EEGMMIDB dataset ($N = 105$) into a publication-grade scientific reporting and visualization package.

Key achievements on Day 6:
1. **Automated Table Generation Suite (`scripts/generate_tables.py`, T-DAY6-001)**:
   - Generated all 18 scientific summary tables in both machine-readable CSV (`.csv`) and GitHub-flavored Markdown (`.md`) formats under `tables/`.
   - Every single statistic is traceable to genuine benchmark outputs (`inflation_table.csv`, `inflation_by_subject.csv`, `subject_info.csv`, `fold_details.json`, `excluded_or_failed_subjects.csv`, `leakcheck_summary.json`).
   - Zero hardcoding: all statistical metrics, confidence intervals, effect sizes, and counts are calculated dynamically by reproducible scripts.
   - Compiled `evidence/TABLE_INDEX.md` with descriptions and cryptographic SHA-256 hashes for all 18 tables.
2. **Publication-Grade Scientific Visualization Suite (`figures/scripts/generate_figures.py`, T-DAY6-002)**:
   - Generated all 16 figures in high-resolution raster (300 DPI PNG) and scalable vector formats (PDF, SVG) under `figures/`.
   - All figures strictly adhere to publication standards: colorblind-friendly Nature/IEEE palettes, readable typography, explicit sample sizes ($N = 105$), explicit uncertainty intervals (95% BCa CIs), non-truncated axes, and zero fabricated or artificial values.
   - Compiled `evidence/FIGURE_INDEX.md` indexing all 16 figures with detailed scientific interpretations and SHA-256 hashes.
3. **Evidence Package Assembly (`evidence/RESULTS_SUMMARY.md`, T-DAY6-003)**:
   - Produced comprehensive technical synthesis summarizing benchmark performance, cohort screening, line 95 error refutation, run-independent FIR filtering verification ($\Delta = 0.000\,\text{V}$), SVD rank diagnostics (rank 63 post-CAR), and the master table/figure index.
4. **Full Test Suite Verification**:
   - Ran `python -m pytest tests` and verified that all **254 automated tests pass cleanly (100% green)** in 111.83 seconds.
5. **Strict Safety Invariants Preserved**:
   - `benchmark_results/physionet_v1_1_final/` remains 100% READ-ONLY and byte-identical to upstream HEAD.
   - `archive/v2/` remains 100% UNTOUCHED.
   - Single-dataset PhysioNet only; no paper/manuscript prose authored.

---

## 2. Deliverables Inventory

### A. Statistical Summary Tables (Tables 1–18)
All generated in `tables/` with dual `.csv` and `.md` formats:
- **Table 1**: Participant Flow, Inclusion/Exclusion Criteria, and Benchmark Demographics ($N = 109$ requested, $N = 105$ evaluated, $N = 4$ excluded).
- **Table 2**: Primary Benchmark Comparison Matrix Across Validation Schemes ($D_3, D_{1m}, D_{1s}, P_1$).
- **Table 3**: Comprehensive Taxonomy of EEG Cross-Validation Leakage Mechanisms (P1–P10).
- **Table 4**: Cohort Sampling Rate Distribution and Covariance Invariance Diagnostics (102 @ 160 Hz, 3 @ 128 Hz).
- **Table 5**: SVD Numerical Rank and Conditioning Across Preprocessing Transformations (pre/post-CAR, interpolation, OAS).
- **Table 6**: Pratt Signed-Rank Test Statistics, Zero-Tie Deductions, and Exact P-Values.
- **Table 7**: BCa Bootstrap Resampling Parameters, Confidence Intervals, and Convergence ($B = 10{,}000$).
- **Table 8**: Parametric and Nonparametric Effect Size Estimates and Location Shifts.
- **Table 9**: Two One-Sided Tests (TOST) Equivalence Bounds and Statistical Decisions ($\pm 2.0\,\text{pp}$).
- **Table 10**: Run-Independent FIR Filter Boundary Isolation and Cross-Run Bleed Verification ($\Delta = 0.000\,\text{V}$).
- **Table 11**: Fold-Isolated Preprocessing Parameter Stability Across Cross-Validation Folds (315 fold fits).
- **Table 12**: Permutation Null Distribution and Signal Noise Burst Robustness.
- **Table 13**: Spatial Covariance Matrix Regularization and Decoder Numerical Conditioning (SCM vs Ledoit-Wolf vs OAS).
- **Table 14**: Participant-Level Decoding Accuracies and Paired Cross-Validation Shifts ($N = 105$).
- **Table 15**: Cross-Design Pearson and Spearman Correlation Matrix of Decoding Accuracies.
- **Table 16**: Comprehensive Technical Screening and Exclusion Accounting for Rejected Participants (S044, S069, S086, S091).
- **Table 17**: Computational Benchmark Performance and Multi-Core Multiprocessing Scaling (1248.24s across 4 workers).
- **Table 18**: Sprint Capacity Ledger, Daily Active Hours, and Cumulative Milestones.

### B. Scientific Figures (Figures 1–16)
All generated under `figures/` as 300 DPI PNG, vector PDF, and vector SVG:
- **Figure 1**: `fig01_workflow_schematic` — LeakCheck Architecture, Preprocessing Pipeline, and Cross-Validation Schemes.
- **Figure 2**: `fig02_participant_flow` — Participant Screening Flowchart and Exclusion Accounting (CONSORT Guideline).
- **Figure 3**: `fig03_paired_accuracy_scatter` — Paired Participant-Level Decoding Accuracies Across Cross-Validation Schemes.
- **Figure 4**: `fig04_inflation_distributions` — Accuracy Distributions and Paired Performance Contrasts.
- **Figure 5**: `fig05_effect_size_forest_plot` — Hodges-Lehmann Effect Size Forest Plot with 95% BCa Confidence Intervals.
- **Figure 6**: `fig06_filter_bleed_comparison` — FIR Filter Boundary Isolation and Cross-Run Bleed Comparison.
- **Figure 7**: `fig07_svd_rank_spectrum` — SVD Numerical Rank Diagnostics, CAR Null Space, and OAS Covariance Conditioning.
- **Figure 8**: `fig08_pratt_wilcoxon_ranking` — Pratt Wilcoxon Ranked Participant Differences for Random Partitioning vs. Positive Leakage.
- **Figure 9**: `fig09_bca_bootstrap_density` — Empirical BCa Bootstrap Distribution Density Curves ($B = 10{,}000$).
- **Figure 10**: `fig10_tost_equivalence_margins` — TOST Equivalence Testing Bounds and 90% Confidence Intervals.
- **Figure 11**: `fig11_cross_validation_fold_stability` — Leave-One-Run-Out Fold Stability and Parameter Invariance.
- **Figure 12**: `fig12_sampling_rate_invariance` — Hardware Sampling Rate Invariance (160 Hz vs 128 Hz).
- **Figure 13**: `fig13_positive_control_dynamics` — Positive Control (P1) Leakage Dynamics and Universal Optimistic Bias.
- **Figure 14**: `fig14_preprocessing_qc_distributions` — Preprocessing Quality-Control and Technical Screening Boundaries.
- **Figure 15**: `fig15_compute_scaling` — Computational Performance Scaling and Multiprocessing Execution Profiles.
- **Figure 16**: `fig16_multimetric_summary_dashboard` — Comprehensive Multi-Metric Scientific Synthesis Dashboard.

---

## 3. Statistical Findings Summary ($N = 105$)

From `benchmark_results/physionet_v1_1_repaired/inflation_table.csv` and Table 2:

1. **Size-Matched Random Partitioning ($D_{1s} - D_3$, Headline)**:
   - Mean Accuracy Shift: $-5.53\,\text{pp}$ (Median: $-6.00\,\text{pp}$).
   - Hodges-Lehmann Location Estimate: **$-5.71\,\text{pp}$** (95% BCa CI: **$[-7.32, -3.94]\,\text{pp}$**).
   - Pratt Wilcoxon Test: $W = 978.0, Z = -5.767, p = 8.07 \times 10^{-9}$ (Holm-adjusted $p = 1.60 \times 10^{-8}$).
   - Effect Sizes: Rank-biserial $r_{rb} = -0.649$, Cohen's $d_z = -0.664$.
   - TOST Equivalence ($\pm 2.0\,\text{pp}$ margin): **REJECTED** ($p = 0.99998$).
2. **$k$-Matched Random Partitioning ($D_{1m} - D_3$)**:
   - Mean Accuracy Shift: $-5.72\,\text{pp}$ (Median: $-6.36\,\text{pp}$).
   - Hodges-Lehmann Location Estimate: **$-5.91\,\text{pp}$** (95% BCa CI: **$[-7.57, -4.09]\,\text{pp}$**).
   - Pratt Wilcoxon Test: $W = 1012.0, Z = -5.654, p = 1.57 \times 10^{-8}$ (Holm-adjusted $p = 1.65 \times 10^{-8}$).
   - Effect Sizes: Rank-biserial $r_{rb} = -0.641$, Cohen's $d_z = -0.644$.
   - TOST Equivalence ($\pm 2.0\,\text{pp}$ margin): **REJECTED** ($p = 0.99998$).
3. **Positive Control Global CSP Leakage ($P_1 - D_3$)**:
   - Mean Accuracy Shift: $+22.31\,\text{pp}$ (Median: $+22.22\,\text{pp}$).
   - Hodges-Lehmann Location Estimate: **$+22.27\,\text{pp}$** (95% BCa CI: **$[+19.24, +25.00]\,\text{pp}$**).
   - Pratt Wilcoxon Test: $W = 41.5, Z = +8.746, p < 1.00 \times 10^{-17}$ (Holm-adjusted $p < 1.00 \times 10^{-17}$).
   - Effect Sizes: Rank-biserial $r_{rb} = +0.989$, Cohen's $d_z = +1.610$.
   - TOST Equivalence ($\pm 2.0\,\text{pp}$ margin): **REJECTED** ($p = 1.00000$).

---

## 4. Team Capacity & Active Hours (Day 6)

| Agent Role | Agent Title | Day 6 Active Hours | Cumulative Hours | Sprint Ceiling | Status |
|:---|:---|:---:|:---:|:---:|:---:|
| **LEAD** | Scientific Project Director & Integrator | 3.5 h | 19.0 h | 60.0 h | ON TRACK |
| **AGENT 1** | Repository, Git & Provenance Auditor | 0.0 h | 5.0 h | 48.0 h | ON TRACK |
| **AGENT 2** | Biostatistics & Numerical Validation | 2.5 h | 12.0 h | 48.0 h | ON TRACK |
| **AGENT 3** | EEG Preprocessing & Leakage Specialist | 0.0 h | 8.5 h | 48.0 h | ON TRACK |
| **AGENT 4** | Rank, CSP, ICA & EDF Specialist | 0.0 h | 11.0 h | 48.0 h | ON TRACK |
| **AGENT 5** | Dataset & Experimental Design Specialist | 0.0 h | 8.5 h | 48.0 h | ON TRACK |
| **AGENT 6** | Software Engineering & QA Specialist | 2.5 h | 14.0 h | 48.0 h | ON TRACK |
| **AGENT 7** | Scientific Evidence & Visualization | 5.0 h | 6.0 h | 48.0 h | ON TRACK |
| **TOTAL** | **Multi-Agent Sprint Team** | **13.5 h** | **84.0 h** | **396.0 h** | **ON TRACK (21.21%)** |

- Total sprint capacity consumed: **84.0 hours / 396.0 hours** ($21.21\%$).
- Remaining sprint capacity: **312.0 hours**.
- Blocked hours: **0.0 hours**.
- Stage 6 status: **COMPLETED & VERIFIED**. Ready to transition to **Stage 7 (Day 7 — QA, Claim-Evidence Matrix, Packaging & Release Readiness)**.
