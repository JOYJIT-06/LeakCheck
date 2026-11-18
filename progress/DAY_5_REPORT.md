# DAY 5 REPORT — BENCHMARK EXECUTION & REPRODUCIBILITY MANIFEST

**Sprint**: LeakCheck V1.1 Seven-Day Scientific Repair, Validation & Release Sprint  
**Stage**: Day 5 / Stage 5 Completed  
**Date**: November 18, 2026  
**Lead Author**: Worker Day 5 (Lead Benchmark Execution Engineer)  
**Co-Authors & Reviewers**: LEAD, AGENT 1 (Provenance & Manifest), AGENT 5 (Dataset & Screening), AGENT 6 (QA & Regression)  

---

## 1. Executive Summary

Stage 5 (Day 5) completed the implementation and execution of the LeakCheck V1.1 Repaired Benchmark across the PhysioNet Motor Movement/Imagery dataset, establishing the empirical foundation of the repaired scientific pipeline.

Key achievements on Day 5:
1. **Automated Headless Loading Fix**: Fixed MNE's interactive stdin prompt in `src/emi/data.py` by adding `update_path=False` to `eegbci.load_data`, ensuring fully headless and non-blocking benchmark runs across all environments.
2. **Benchmark Runner Architecture (`scripts/run_benchmark.py`)**: Implemented the standardized benchmark runner incorporating whole-recording technical screening, fold-isolated preprocessing, run-independent FIR filtering, and four experimental designs ($D_3$, $D_{1m}$, $D_{1s}$, $P_1$).
3. **Gate 3 Pilot Cohort Execution (T-DAY5-001)**: Successfully executed the Gate 3 pilot across 7 representative test subjects (`S001`, `S002`, `S088`, `S044`, `S069`, `S086`, `S091`). Validated that healthy participants (`S001`, `S002`, `S088`) completed cleanly while all 4 pathological subjects were rejected with structured error categorizations in `excluded_or_failed_subjects.csv`.
4. **Full Repaired Benchmark Execution ($N=105$, T-DAY5-002)**: Executed all 109 subjects with 4-way parallel multiprocessing (`joblib.Parallel(n_jobs=4)`). Evaluated 105 eligible participants and deterministically rejected exactly 4 subjects across 1248.24 seconds of compute time with zero crashes and zero NaNs.
5. **Empirical Findings Summary**:
   - **$D_{1m}$ vs. $D_3$ (k-matched random split)**: Mean accuracy difference = $-5.72\,\text{pp}$ (Hodges-Lehmann median difference = $-5.91\,\text{pp}$, 95% BCa CI: $[-7.57, -4.09]\,\text{pp}$, Pratt Wilcoxon $p = 1.57 \times 10^{-8}$, rank-biserial $r = -0.641$).
   - **$D_{1s}$ vs. $D_3$ (size-matched random split headline)**: Mean accuracy difference = $-5.53\,\text{pp}$ (Hodges-Lehmann median difference = $-5.71\,\text{pp}$, 95% BCa CI: $[-7.32, -3.94]\,\text{pp}$, Pratt Wilcoxon $p = 8.07 \times 10^{-9}$, rank-biserial $r = -0.649$).
   - **$P_1$ vs. $D_3$ (positive control global CSP leakage)**: Mean accuracy difference = $+22.31\,\text{pp}$ (Hodges-Lehmann median difference = $+22.27\,\text{pp}$, 95% BCa CI: $[+19.24, +25.00]\,\text{pp}$, Pratt Wilcoxon $p = 0.00$, rank-biserial $r = +0.989$).
   - **Historical Draft Line 95 Refutation**: Proved that the true evaluable cohort comprises exactly $N=105$ subjects (not 104 as drafted), and subjects `S088`, `S092`, `S100` have native 128 Hz hardware sampling rates without invalidating $64 \times 64$ spatial covariance rank.
6. **Reproducibility Manifest (`evidence/REPRODUCIBILITY_MANIFEST.json`, T-DAY5-003)**: Generated complete cryptographic manifest recording SHA-256 hashes of all 327 raw input EDF files, intermediate features, the deterministic bootstrap index matrix, and all 8 primary benchmark output artifacts.
7. **Safety Invariants**: Verified that `benchmark_results/physionet_v1_1_final/` and `archive/v2/` remain 100% untouched and byte-identical to upstream HEAD.

---

## 2. Experimental Design and Benchmark Protocol

The benchmark evaluated each participant across four experimental designs using identical OAS-regularized Common Spatial Patterns (4 components) and Linear Discriminant Analysis with automatic Ledoit-Wolf shrinkage (`lsqr` solver):

| Design ID | Design Name | Partition Scheme | Preprocessing Protocol | Role in Benchmark |
|:---|:---|:---|:---|:---|
| **$D_3$** | Leave-One-Run-Out (LORO) | 3 folds (held-out runs R04, R08, R12) | `FoldIsolatedPreprocessor` + `filter_run_independent` | Leak-Free Reference Standard |
| **$D_{1m}$** | Matched-$k$ Random Split | 5 repeats of 3-fold StratifiedKFold (15 evals) | `FoldIsolatedPreprocessor` | Random Partitioning Comparison |
| **$D_{1s}$** | Size-Matched Random Split | 20 repeats matching $D_3$ fold class counts (60 evals) | `FoldIsolatedPreprocessor` | Headline Random Partitioning Comparison |
| **$P_1$** | Global Supervised CSP Leakage | 3 folds LORO LDA | Global CSP fit on all trials before fold split | Positive Control Leakage Mechanism |

---

## 3. Cohort Participant Flow & Technical Screening

Every subject underwent whole-recording participant screening prior to cross-validation evaluation:
- Total subjects requested: 109 (`S001` through `S109`).
- Total subjects evaluated: 105.
- Total subjects excluded: 4.
- Overall retention rate: $96.33\%$.

### Detailed Breakdown of Excluded Subjects

| Subject | Reason Category | Specific Exclusion Rationale | Sampling Rate |
|:---|:---|:---|:---:|
| **S044** | `AUTOMATED_PREPROCESSING_QC` | Quality-control channel rejection >15% bad channels (12 of 64 channels flagged bad) | 160.0 Hz |
| **S069** | `AUTOMATED_PREPROCESSING_QC` | Quality-control channel rejection >15% bad channels (12 of 64 channels flagged bad) | 160.0 Hz |
| **S086** | `MINIMUM_TRIAL_THRESHOLD_VIOLATION` | Sample size threshold violation: 24 trials < minimum 30 threshold (min_trials=30) | 160.0 Hz |
| **S091** | `AUTOMATED_PREPROCESSING_QC` | 100% trials rejected by adaptive peak-to-peak thresholding (all 45 epochs dropped) | 160.0 Hz |

All 4 exclusions were logged in `benchmark_results/physionet_v1_1_repaired/excluded_or_failed_subjects.csv` and documented in `participant_flow_manifest.json`.

---

## 4. Benchmark Statistical Results ($N=105$)

From `benchmark_results/physionet_v1_1_repaired/inflation_table.csv`:

| Contrast | Comparison Kind | $N$ | Mean $\Delta$ (pp) | Median $\Delta$ (pp) | Hodges-Lehmann (pp) | 95% BCa CI (pp) | Pratt Wilcoxon $p$ | Rank-Biserial $r$ | Cohen's $d_z$ | TOST Equivalence ($[-2, +2]$\,pp) |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **$D_{1m} - D_3$** | $k$-matched | 105 | $-5.72$ | $-6.36$ | $-5.91$ | $[-7.57, -4.09]$ | $1.57 \times 10^{-8}$ | $-0.641$ | $-0.644$ | REJECTED ($p = 0.99998$) |
| **$D_{1s} - D_3$** | Size-matched (headline) | 105 | $-5.53$ | $-6.00$ | $-5.71$ | $[-7.32, -3.94]$ | $8.07 \times 10^{-9}$ | $-0.649$ | $-0.664$ | REJECTED ($p = 0.99998$) |
| **$P_1 - D_3$** | Global CSP leakage | 105 | $+22.31$ | $+22.22$ | $+22.27$ | $[+19.24, +25.00]$ | $0.00$ | $+0.989$ | $+1.610$ | REJECTED ($p = 1.00000$) |

### Interpretation
- **Deflation under Random Splitting**: Rather than inflating accuracy, random trial partitioning ($D_{1m}$ and $D_{1s}$) in the absence of leakage deflates test performance by $\approx 5.5$ to $5.7$ percentage points relative to LORO. This reflects the breaking of within-run temporal autocorrelation structure.
- **Massive Positive Control Inflation**: When supervised CSP is improperly fit across all trials ($P_1$), performance inflates by $+22.31\,\text{pp}$ ($p = 0.00$, $d_z = 1.61$), proving the high sensitivity of the benchmark to genuine methodological leakage.

---

## 5. Artifacts and Cryptographic Checksums

All benchmark deliverables have been generated in `benchmark_results/physionet_v1_1_repaired/`:
- `leakcheck_raw.csv` (SHA-256: `f24e3a938162a1415c7840d8b5f2d0fad3f729e44bde2e371d276687b3f88b68`) — 420 fold evaluation rows across 105 subjects.
- `inflation_by_subject.csv` (SHA-256: `63b8e2576efd008e6047d91ae43afde188a996e00f0eb5da0da050a409c3cc96`) — 315 subject contrast rows across 105 subjects.
- `inflation_table.csv` (SHA-256: `d6f7be5a380dca4732e611dbef212e5e48ff6225cd8000bc8c31414cecfd2c7f`) — Summary statistics and confidence intervals.
- `subject_info.csv` (SHA-256: `58c6071b2004b9716a55c7b8a48a729c483c09ba9d948fa047a68d2ec51cf1cb`) — Subject-level recording metadata and autocorrelation.
- `excluded_or_failed_subjects.csv` (SHA-256: `0b24647957f50138a9e205c7e38163304f60cffac8ff18f02488a2da4e603778`) — Rejection register for S044, S069, S086, S091.
- `participant_flow_manifest.json` (SHA-256: `f60f2723006430b59f8b5cd4a1eb5a696f1c53c4c2654eddf99067a643df9b27`) — Complete participant accounting.
- `settings.json` (SHA-256: `197ab5f6b43e57d393a50fc5b4c3e7c95d3b75e51a99e457d664587876940cab`) — Complete runtime configuration.
- `leakcheck_summary.json` (SHA-256: `f63ea13a2cc4271d100c5598f93d7f175d61b9e866a4451506a0c7b9e46845a6`) — Compute duration and environment specs.
- `evidence/REPRODUCIBILITY_MANIFEST.json` — Comprehensive provenance manifest.
- `data/manifests/raw_edf_sha256.json` — Cryptographic inventory of all 327 PhysioNet EDF files.

---

## 6. Team Capacity & Active Hours (Day 5)

| Agent Role | Agent Title | Day 5 Active Hours | Cumulative Hours | Sprint Ceiling | Status |
|:---|:---|:---:|:---:|:---:|:---:|
| **LEAD** | Scientific Project Director & Integrator | 3.5 h | 15.5 h | 60.0 h | ON TRACK |
| **AGENT 1** | Repository, Git & Provenance Auditor | 3.0 h | 5.0 h | 48.0 h | ON TRACK |
| **AGENT 2** | Biostatistics & Numerical Validation | 0.0 h | 9.5 h | 48.0 h | ON TRACK |
| **AGENT 3** | EEG Preprocessing & Leakage Specialist | 0.0 h | 8.5 h | 48.0 h | ON TRACK |
| **AGENT 4** | Rank, CSP, ICA & EDF Specialist | 0.0 h | 11.0 h | 48.0 h | ON TRACK |
| **AGENT 5** | Dataset & Experimental Design Specialist | 3.5 h | 8.5 h | 48.0 h | ON TRACK |
| **AGENT 6** | Software Engineering & QA Specialist | 3.5 h | 11.5 h | 48.0 h | ON TRACK |
| **AGENT 7** | Scientific Evidence & Visualization | 0.0 h | 1.0 h | 48.0 h | ON TRACK |
| **TOTAL** | **Multi-Agent Sprint Team** | **13.5 h** | **70.5 h** | **396.0 h** | **ON TRACK (17.80%)** |

- Total sprint capacity consumed: **70.5 hours / 396.0 hours** ($17.80\%$).
- Remaining sprint capacity: **325.5 hours**.
- Blocked hours: **0.0 hours**.
- Stage 5 status: **COMPLETED & VERIFIED**. Ready to transition to **Stage 6 (Day 6 — Statistical Summary Tables & Publication-Grade Figure Generation)**.
