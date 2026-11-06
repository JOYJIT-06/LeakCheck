## 1.0.0

### V1 release

- Published the LeakCheck EEG validation and data-leakage benchmark package.
- Added the PhysioNet EEGMMIDB V1 benchmark outputs and documented
  methods, settings, exclusions, and limitations.
- V1 empirical evaluation covers 105 completed participants, CSP + LDA,
  D3 leave-one-run-out, D1m k-matched stratified folds, and P1 global-CSP
  positive control.
- Added permutation and circular-shift null results.
- Clarified that D1s, OpenBMI, multi-dataset validation, multi-site
  validation, and fully fold-nested preprocessing are not V1 claims.
- The benchmark run recorded package version 0.1.0; this release is 1.0.0.

# Changelog

## 0.3.0 (code-review fixes; reviewer patch plus the items it left open)
- D1s (size-matched random k-fold) is now a disjoint partition: every trial is tested once per repeat. v0.2 test sets overlapped and left trials untested.
- `SimpleCSP` (`--csp numpy`) works inside the data's own subspace; null-space directions from the average reference can no longer become CSP components.
- Diagnostics: exact runs test (was a normal approximation) and a Sidak-adjusted minimum p over runs; `trial_dependence(..., y=...)` removes class means within each run (the script now passes `y`).
- Tables: dropped subjects are logged and kept in `attrs["dropped_subjects"]`; `null_table` has `design_type` and `rate_meaning`; `subject_empirical_p` has `min_possible_p` and warns when n_null is too small for p < 0.05; the audit script warns for `--n-null` below 20 and logs tracebacks.
- Statistics: `bca_ci(..., return_method=True)` and `hl_ci_method` column; Hartung-Knapp interval option in `random_effects_meta` (used by `analyze_leakcheck.py`); Holm-adjusted moderator p-values.
- Preprocessing: `Config.reject_window="analysis"` (default) rejects on the analysed window only; `"full"` restores v0.2. Clear error when every epoch is rejected.
- Data: `resolve_data_path` avoids the interactive MNE download prompt. `mne` pinned `<1.14` (requirements.txt and pyproject.toml).
- Basic pipeline results carry `validation` (it is the shuffled k-fold design, audit design D2).
- Merged on top of the reviewer's patch (all of the above kept as is):
  - Preprocessing order is now band-pass, bad-channel detection and interpolation, average reference, ICA. Trial rejection defaults to an adaptive, label-blind per-subject rule (`reject_mode="fixed"` restores a fixed threshold). Every subject reports bad channels, removed ICA components and trial loss. Run lengths are asserted to add up. **Not yet run on real files.**
  - Basic pipeline: leave-one-run-out is the primary result; random-split accuracy is reported but labelled. One decoder specification for the pipeline and the audit. `--csp rank_safe|mne`, `csp_impl` in every output, `--no-ica`.
  - Nulls: both the permutation and the circular-shift null are reported (the larger p is used); `label_agreement` and `label_hash` per null set; new finding that the shift null can be near-degenerate for alternating labels.
  - Audit: real and null labels share fold seeds; base window comes from the config; provenance columns (`csp_impl`, `n_channels`, `base_window`); `paired_delta_vs_null` replaces "lost significance".
  - Statistics and diagnostics: bootstrap ranking reversal, M1 permutation null, independent strata, primary-moderator Holm, pilot handling (`--power-from`, `--exclude-subjects`).
  - Real-data evidence and checks in `docs/real_eeg_checks`; item-by-item answer in `docs/REVIEW_RESPONSE.md`.
- Results from v0.2 are not comparable for D1s, numpy-CSP runs and the diagnostics columns; re-run them.

## 0.2.0
- LeakCheck audit: validation designs D1, D2, D1m, D1s (size-matched), D3, D4, D4b, D5, D6 and injected leaks P1, P3, P4, P5, P6, P7.
- Null labels: within-run permutation and circular shift. Empirical p-values.
- Decoders: CSP+LDA, CSP+logistic regression, tangent space + logistic regression (optional pyriemann).
- Statistics: Hodges-Lehmann with BCa interval, Wilcoxon, rank-biserial, Holm, TOST, random-effects meta-analysis, power from a pilot.
- Diagnostics: label autocorrelation, runs test, run-decodability (M1), trial dependence (M2).
- Cache format with run, session and trial order. MOABB adapter (untested). Synthetic data generator.
- Fix: the earlier 5-fold comparison mixed leakage with training-set size; the size-matched design D1s now removes that confound.

## 0.1.0
- Basic pipeline: PhysioNet motor imagery, ICA, ERD, CSP + LDA, permutation test.
