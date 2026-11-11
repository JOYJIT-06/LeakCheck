# LeakCheck V1.1 Benchmark Results: PhysioNet Motor Movement/Imagery

## 1. Overview and Purpose
This benchmark fulfills the primary release requirement for **LeakCheck V1.1**: evaluating the headline **size- and class-matched random split (`D1s_size_matched`)** against clean leave-one-run-out cross-validation (`D3_loro`) across the full $N=105$ participant cohort of the PhysioNet EEG Motor Movement/Imagery dataset.

In the historical V1 run (`091e47dc`), only `D1m_matched_k` (k-fold with $k = \text{number of runs}$) was evaluated, leaving an open scientific question: was the observed $-3.17$ pp deflation caused by fold size and class-balance fluctuations, or does trial mixing across runs inherently lower accuracy?

## 2. Experimental Configuration
- **Dataset**: PhysioNet EEG Motor Movement/Imagery (64 channels, 160 Hz, runs 4, 8, 12).
- **Participants**: 106 subjects evaluated from cache (`D:\LeakCheck_Cache\physionet`).
  - Finished: 105 participants.
  - Technically excluded: Subject 86 (only 24 trials kept, below the 30-trial minimum).
  - Missing from PhysioNet cache: Subjects 44, 69, 91.
- **Decoder**: OAS-regularized Common Spatial Patterns + Linear Discriminant Analysis (`csp_lda`).
- **Designs Evaluated**:
  1. `D3_loro`: Leave-one-run-out cross-validation (clean reference).
  2. `D1m_matched_k`: Stratified random k-fold with $k=3$ (5 repeats).
  3. `D1s_size_matched`: Size- and class-matched random partition (20 repeats).
  4. `P1_csp_on_all`: Global CSP leakage (spatial filters fitted across all runs prior to split).

## 3. Empirical Results Summary ($N = 105$)

| Contrast | Kind | N | Mean Diff (pp) | Median Diff (pp) | Hodges-Lehmann (pp) | 95% BCa CI (pp) | Wilcoxon $p$ (Holm) | Cohen's $d_z$ | TOST Margin | Equivalent? |
|---|---|---|---|---|---|---|---|---|---|---|
| **P1 vs D3** | P1 CSP on all data | 105 | $+24.82$ | $+23.26$ | **$+24.50$** | $[+22.22, +27.78]$ | $4.43 \times 10^{-18}$ | $+1.771$ | $\pm 2.0$ pp | False ($p=1.0$) |
| **D1m vs D3** | k-matched random | 105 | $-4.67$ | $-4.00$ | **$-4.47$** | $[-5.83, -3.14]$ | $1.08 \times 10^{-8}$ | $-0.685$ | $\pm 2.0$ pp | False ($p=0.9999$) |
| **D1s vs D3** | size-matched (headline) | 105 | $-2.77$ | $-2.61$ | **$-2.68$** | $[-3.95, -1.47]$ | $5.86 \times 10^{-5}$ | $-0.449$ | $\pm 2.0$ pp | False ($p=0.898$) |

## 4. Key Scientific Insights
1. **Validation Design Deflation (H1)**: Even when training/test fold sizes and class counts strictly match LORO (`D1s`), random shuffling across runs yields a statistically significant **$-2.68$ pp deflation** relative to LORO ($95\%$ BCa CI: $[-3.95, -1.47]$ pp, $p = 5.86 \times 10^{-5}$). Shuffled validation does not falsely inflate decoding accuracy on this benchmark; rather, non-stationarity across runs and block structure make mixed-run training folds perform worse.
2. **Fold Geometry Impact**: Moving from unconstrained $k$-fold (`D1m`, $-4.47$ pp) to strictly size- and class-matched partitions (`D1s`, $-2.68$ pp) recovers $+1.79$ pp, demonstrating that unconstrained random splitting introduces spurious variance through fold geometry mismatch.
3. **Feature Leakage Dominance (H2)**: Fitting CSP on all data (`P1`) produces an overwhelming **$+24.50$ pp inflation** ($d_z = 1.771$, $p = 1.48 \times 10^{-18}$), proving that preprocessing contamination in spatial filters completely dwarfs temporal validation effects.

## 5. Artifacts and Figures
- `inflation_table.csv`: Complete paired statistical summary table.
- `inflation_by_subject.csv`: Per-subject paired accuracy differences and absolute scores.
- `paired_csp_lda_size_matched.png`: Scatter plot comparing subject-by-subject accuracy of `D1s_size_matched` against `D3_loro`.
- `inflation_csp_lda.png`: Distribution of inflation deltas across participants.
- `leakcheck_summary.json`: Software environment, compute runtime, and configuration metadata.
