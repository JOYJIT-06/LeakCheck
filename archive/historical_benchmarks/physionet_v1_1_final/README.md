# LeakCheck V1.1 Final Benchmark Results: PhysioNet Motor Movement/Imagery

## 1. Overview and Purpose
This directory contains the finalized, fully reproducible end-to-end benchmark results for **LeakCheck V1.1**, evaluating the headline **size- and class-matched random split (`D1s_size_matched`)** against clean leave-one-run-out cross-validation (`D3_loro`) across the full $N=105$ participant cohort of the PhysioNet EEG Motor Movement/Imagery database.

This run was executed in Phase 14 of the V1.1 release protocol using clean, verified settings on branch `research/v1.1-final-audit`.

## 2. Experimental Configuration
- **Dataset**: PhysioNet EEG Motor Movement/Imagery Database (EEGMMIDB; 64 channels, runs 4, 8, 12).
- **Cohort Size**: 109 requested subjects.
  - Successfully evaluated: 105 participants (S001–S109, excluding S044, S069, S086, S091).
  - Excluded subjects ($n=4$):
    - `S044`: Missing EDF/cache in PhysioNet distribution.
    - `S069`: Missing EDF/cache in PhysioNet distribution.
    - `S086`: Excluded on technical criteria ($24 < 30$ minimum trials).
    - `S091`: Truncated/corrupted EDF in PhysioNet distribution.
- **Decoder**: OAS-regularized Common Spatial Patterns + Linear Discriminant Analysis (`csp_lda`).
- **Designs Evaluated**:
  1. `D3_loro`: Leave-one-run-out cross-validation (clean reference).
  2. `D1m_matched_k`: Stratified random $k$-fold with $k=3$ (5 repeats).
  3. `D1s_size_matched`: Size- and class-matched random partition (20 repeats).
  4. `P1_csp_on_all`: Global CSP leakage (spatial filters fitted across all runs prior to split).
- **Random Seed**: `seed = 0`.
- **Settings Hash**: `e4a2b05c`.

## 3. Empirical Results Summary ($N = 105$)

| Contrast | Kind | N | Mean Diff (pp) | Median Diff (pp) | Hodges-Lehmann (pp) | 95% BCa CI (pp) | Wilcoxon $p$ (Holm) | Cohen's $d_z$ | TOST Margin | Equivalent? |
|---|---|---|---|---|---|---|---|---|---|---|
| **P1 vs D3** | P1 CSP on all data | 105 | $+24.82$ | $+23.26$ | **$+24.50$** | $[+22.22, +27.78]$ | $4.43 \times 10^{-18}$ | $+1.771$ | $\pm 2.0$ pp | False ($p=1.0$) |
| **D1m vs D3** | $k$-matched random | 105 | $-4.67$ | $-4.00$ | **$-4.47$** | $[-5.83, -3.14]$ | $1.08 \times 10^{-8}$ | $-0.685$ | $\pm 2.0$ pp | False ($p=0.9999$) |
| **D1s vs D3** | size-matched (headline) | 105 | $-2.77$ | $-2.61$ | **$-2.68$** | $[-3.95, -1.47]$ | $5.86 \times 10^{-5}$ | $-0.449$ | $\pm 2.0$ pp | False ($p=0.898$) |

## 4. Key Scientific Insights
1. **Validation Design Deflation (H1)**: Even when training/test fold sizes and class counts strictly match LORO (`D1s`), random shuffling across runs yields a statistically significant **$-2.68$ pp deflation** relative to LORO ($95\%$ BCa CI: $[-3.95, -1.47]$ pp, $p = 5.86 \times 10^{-5}$). Shuffled validation does not falsely inflate decoding accuracy on this benchmark; rather, non-stationarity across runs and block structure make mixed-run training folds perform worse.
2. **Fold Geometry Impact**: Moving from unconstrained $k$-fold (`D1m`, $-4.47$ pp) to strictly size- and class-matched partitions (`D1s`, $-2.68$ pp) recovers $+1.79$ pp, demonstrating that unconstrained random splitting introduces spurious variance through fold geometry mismatch.
3. **Feature Leakage Dominance (H2)**: Fitting CSP on all data (`P1`) produces an overwhelming **$+24.50$ pp inflation** ($d_z = 1.771$, $p = 1.48 \times 10^{-18}$), proving that preprocessing contamination in spatial filters completely dwarfs temporal validation effects.

## 5. Artifact Ledger
- `inflation_table.csv`: Complete paired statistical summary table across contrasts.
- `inflation_by_subject.csv`: Per-subject paired accuracy differences and absolute scores.
- `leakcheck_raw.csv`: Raw trial-level and fold-level audit log.
- `subject_info.csv`: Subject-level metadata, sequence runs test statistics, and trial dependence.
- `excluded_or_failed_subjects.csv`: Explicit exclusion ledger documenting technical grounds for S044, S069, S086, S091.
- `participant_flow_manifest.json`: Machine-readable participant flow and historical refutation record.
- `settings.json`: Configuration dictionary and execution flags.
- `leakcheck_summary.json`: Software environment, compute runtime, and configuration metadata.
- `paired_csp_lda_size_matched.png`: Scatter plot comparing subject-by-subject accuracy of `D1s_size_matched` against `D3_loro`.
- `inflation_csp_lda.png`: Distribution of inflation deltas across participants.
- `runs/e4a2b05c/`: Complete outputs preserved under settings hash identifier.
- `per_subject/e4a2b05c/`: Individual CSV and JSON artifacts for each evaluated participant.
