# LeakCheck V2 — Preprint Evidence Audit (11 November 2026)

## Verdict
**Preprint drafting: GO. Submission and V2 release/merge: HOLD pending CI and data relabeling.** The two-dataset empirical evidence is usable if claims are narrowed to the evaluated datasets, decoders and protocols. The current manuscript overstates taxonomy completeness and mislabels one OpenBMI control.

## GitHub state
- `v2-dev` head reviewed: `d5891dbffb3e6cedd1ce843666553ef9e0eacc1b`.
- PR #5 to main remains open and unmerged.
- Latest Actions run #15 failed in all six OS/Python jobs. Ubuntu/Python 3.12: 438 passed, 2 skipped, 1 failed.
- Failure: `test_contrasts_small_cohort_n_less_than_3`; N=2 incorrectly returned HL=20 pp. The patch now restricts HL, BCa CI, Wilcoxon and effect sizes to N>=3.
- The push trigger omitted v2-dev; current workflow includes it.

## PhysioNet V1.1 results
Source: `benchmark_results/physionet_v1_1/inflation_table.csv`.
105 completed from 109 requested. Exclusions per `excluded_or_failed_subjects.csv`: 44,69,91 missing cache files; 86 had 24 trials (<30). OAS CSP-LDA; 64 channels; 160 Hz; runs 4,8,12. `n_null=0`.

| Contrast | N | Mean pp | Median pp | HL pp | BCa 95% CI pp | Raw p | Holm p | dz |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| P1 global CSP − D3 |105|+24.815|+23.256|+24.503|[22.222,27.778]|1.477e-18|4.431e-18|1.771|
| D1s − D3 |105|−2.771|−2.614|−2.677|[−3.946,−1.471]|5.859e-5|5.859e-5|−0.449|
| D1m − D3 |105|−4.666|−4.000|−4.470|[−5.835,−3.136]|5.413e-9|1.083e-8|−0.685|

## OpenBMI Session 1 results
Source: `benchmark_results/openbmi_v2/design_comparisons.csv` and manifest. 34 intact participants; 62 channels; 200 trials/participant; 1000→250 Hz; epoch [−0.5,4.0) s; 8–30 Hz run-isolated FIR; baseline [−0.5,0) s; 150 μV non-destructive artifact flag; 2,992 fold rows and 204 participant rows.

| Contrast | N | Mean pp | Median pp | HL pp | BCa 95% CI pp | Raw p | Holm p | dz |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| CSP-LDA P1 global CSP − D3 |34|+5.603|+7.000|+6.250|[3.250,8.229]|1.466e-4|1.872e-4|0.745|
| CSP-LDA D1s − D3 |34|+3.372|+1.850|+2.837|[1.463,4.975]|9.359e-5|1.872e-4|0.751|
| TS-LR D1s − D3 |34|+3.110|+2.488|+2.938|[1.663,4.513]|9.722e-5|1.944e-4|0.771|
| TS-LR global reference+scaling − D3 |34|+0.853|+0.500|+0.750|[0.250,1.500]|0.02029|0.02029|0.417|

**Critical correction:** OpenBMI's TS-LR code fitted a global tangent-space reference and global StandardScaler without labels. Only CSP-LDA used supervised global CSP. The historical TS-LR output row was incorrectly named P1. It is now a distinct T1 reference/scaling control in the runner; the historical CSVs and inflation figure must be relabeled/regenerated before citation.

## P1–P9 status
- P1: real-EEG evidence for CSP-LDA only, PhysioNet N=105 and OpenBMI N=34.
- P2: continuous raw-data ICA pipeline not integrated; epoch-level ICA helper is not equivalent.
- P3–P7: synthetic probes only; P4/P8 terminology and P5/P7 aliases need canonical cleanup.
- P8: no distinct global contaminated comparator found.
- P9: no distinct temporal/run-boundary injection found. D1s-vs-D3 is a design contrast, not P9.
- PhysioNet V1.1 ran with n_null=0. No null-based result is claimed.

## Manuscript/figure issues
- Existing dual-cohort manuscript's PhysioNet confidence intervals and p-values conflict with the authoritative CSV.
- TS-LR +0.75 pp is mislabeled as P1 in the historical OpenBMI output and inflation figure.
- Explanations involving electrode drift or operational state are hypotheses; those variables were not directly measured.
- Existing completion dashboard overstates V2 completion.
- Figures exist for both datasets, but OpenBMI inflation figure needs regeneration after relabeling.
- The existing manuscript is not submission-ready. A corrected working draft is added under `preprint/`.

## Remaining gates
1. Run full local pytest and GitHub CI after patch.
2. Relabel TS-LR rows in OpenBMI fold/participant CSVs, recalculate contrasts, update manifest hashes, regenerate PNG/PDF.
3. Independently recompute statistics from participant rows.
4. Resolve P-series aliases and implement/validate P2/P8/P9 or remove unsupported completeness claims.
5. Rerun selected real-data benchmarks under exact V2 commit if claiming V2-generated results.
6. Convert manuscript to LaTeX, verify citations, affiliations, disclosures and figures.
