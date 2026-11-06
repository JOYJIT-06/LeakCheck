> **Historical review record:** This document records earlier development/review work. It is not a V1 validation certificate. For the empirical V1 scope and limitations, see METHODS.md and REQUIREMENTS_STATUS.md.

# Response to the code review of LeakCheck v0.2 (items 1-37)

Sources: `docs/real_eeg_checks/code_review_leakcheck_v0_2.md` (the review), the reviewer's patch and fix status
(`docs/real_eeg_checks/reviewer_fix_status.md`, tested against real PhysioNet files), and this release (v0.3).
This table says what changed, whether it is tested, and what is still open. "T" = unit-tested here without MNE.
"MNE" = written but not run on the real files by the author of this release; run the check named in the last column first.

I reproduced independently, before changing anything: item 9 (29.3% duplicated test predictions, 13.2 of 45 trials never
tested), item 14 (first CSP component is a null-space direction: filter norm 1e5, constant feature), item 20, item 12.
I also re-derived the review's tables from the supplied CSVs, and checked the exact runs test against the supplied
20,000-permutation p-values (maximum difference 0.004).

| # | Item | Status | What changed | How to check |
|---|---|---|---|---|
| 1 | Rejection threshold too strict | MNE | Default is now an adaptive, label-blind per-subject rule (median + 6 MAD of the per-trial artifact statistic, floor 200, cap 800 uV); `reject_mode="fixed"` restores a fixed threshold | `build_cache.py` prints trials kept per subject. Look at retention only, never at accuracy |
| 2 | Rejection window | T (helper) / MNE | Reviewer's `reject_window="analysis"` kept as default | trials kept |
| 3 | No bad-channel detection | MNE (rule T) | Robust variance and low-correlation outliers are interpolated before re-referencing; subject refused if over 15% of channels flagged; bad channels listed per subject | `bad channels` in the cache log |
| 4 | "Everything nested" claim | FIXED (wording) | Docs and docstrings now say label-blind preprocessing uses all runs and is not nested. P2 (ICA fitted without the held-out run) is still TODO | docs |
| 5 | Blink removal never checked | PARTIAL | Every subject reports bad channels and removed ICA components; `use_ica=False` / `--no-ica` gives a sensitivity run. No component plots yet | compare results with and without ICA |
| 6 | Interactive download prompt | MNE | Reviewer's `resolve_data_path` (no prompt) | first download in Colab |
| 7 | Deprecated montage | FIXED | `mne>=1.7,<1.14` in requirements and pyproject | install |
| 8 | Run ids in `info['description']` | PARTIAL | Run lengths are asserted to add up to the recording length before run ids are used; text field kept | `build_cache.py` stops with a clear error if wrong |
| 9 | D1s overlap | T | Reviewer's disjoint partition, same sizes and class counts as leave-one-run-out | `test_size_matched_split_is_a_disjoint_partition` |
| 10 | Hard-coded window | T | `BASE_WINDOW` comes from `Config.decode_tmin/tmax`; `base_window` is a parameter and a column | `test_audit_records_provenance_columns...` |
| 11 | Silent loss of subjects | T | Warning plus `attrs["dropped_subjects"]`; the script writes `dropped_pairs.csv` | `dropped_pairs.csv` |
| 12 | Different seeds for real and null | T | Same fold seed for real and null label sets (paired) | tests |
| 13 | Binomial threshold assumes independence | FIXED (docs) | Docstring and docs state it is a rough guide; per-subject claims use the label nulls | docs |
| 14 | numpy CSP null-space | T | Reviewer's subspace whitening; `rank_safe` is now the default CSP of the scripts | `test_simple_csp_ignores_the_empty_direction` |
| 15 | MNE CSP with `reg=None` | OPEN | `Config.csp_reg` is passed to MNE's CSP. No default change: no evidence yet that regularisation helps | run `--csp mne` with and without `csp_reg` |
| 16 | Two classifier settings | T | The basic pipeline builds its decoder from `DECODERS["csp_lda"]` (lsqr, shrinkage auto) | `test_decode_loro.py` |
| 17 | Basic pipeline used a leaky design | T (MNE glue untested) | Primary result is leave-one-run-out with a label-null p; random-split accuracy is reported, labelled "not run-aware" | `run_subject.py` output |
| 18 | Decoder coverage | OPEN | `ts_lr` still needs pyriemann and has never run; FBCSP and EEGNet not added | `pip install pyriemann`, run `--decoders ts_lr` |
| 19 | Null table naming | T | Reviewer's `design_type` and `rate_meaning` columns | `null_table.csv` |
| 20 | p-value resolution | T | `min_possible_p`, warnings in the table and the script | log |
| 21 | Few distinct shifts | T | `label_hash` per null set; both nulls are the default; `label_agreement` column; **new finding below** | `subject_empirical_p.csv` |
| 22 | BCa fallback silent | T | `hl_ci_method` column | `inflation_table.csv` |
| 23 | Meta-analysis intervals | T | Hartung-Knapp interval; skipped datasets listed; tau^2 flagged unreliable for k < 5 | `meta_analysis.csv` |
| 24 | Ranking reversal without uncertainty | T | Subject-level bootstrap: P(best decoder changes), tau interval | `ranking_reversal.csv` |
| 25 | Moderator multiplicity | T (end-to-end) | One pre-specified primary moderator (label autocorrelation); Holm inside primary and secondary families | `moderators.csv` |
| 26 | Strata by reference accuracy | T (end-to-end) | Strata now use run-decodability and trial count, not the accuracy being compared | `strata_exploratory.csv` |
| 27 | "Lost significance" | T | Replaced by `paired_delta_vs_null`: the design difference is compared with the same difference under null labels | `paired_delta_vs_null.csv`, `delta_vs_null.csv` |
| 28 | Power from the same data | T (end-to-end) | `--power-from` (pilot folders) and `--exclude-subjects` (keep the pilot out of the confirmatory set); the JSON says where the SD came from | `power_from_pilot.json` |
| 29 | M2 confounded | T | Reviewer's class-mean removal; both `dep_lagK` (removed) and the old behaviour when `y` is None | tests |
| 30 | Runs test | T | Exact two-sided test; Sidak-adjusted minimum over runs; matches the real permutation p-values | `test_exact_runs_test_matches_the_real_permutation_p_values` |
| 31 | M1 chance level | T | Permutation null of the run labels: `run_decode_null_mean`, `run_decode_p` | tests |
| 32 | Broad except | T | Tracebacks logged; `--debug` re-raises | log |
| 33 | Two CSP implementations | T | `csp_impl` column in every audit row and in the basic pipeline result; `--csp rank_safe|mne` | `leakcheck_raw.csv` |
| 34 | No lockfile | OPEN | Not possible to create a true lock without network access here. Do `pip freeze > requirements-lock.txt` in a fresh virtual environment after a successful install and commit it | your environment |
| 35 | MOABB adapter | OPEN | Still untested. The 64-noise-channel dose assumes a 64-channel dataset | run one MOABB subject |
| 36 | One recording day | OPEN | Documented; D6 needs a multi-session dataset | |
| 37 | Missing items | OPEN | D7, P2, dose-response, robustness grid, M3-M7, mixed/Bayesian models, FBCSP, EEGNet, registered plan | `REQUIREMENTS_STATUS.md` |

## New finding from the fixes: the circular-shift null can be nearly degenerate
A unit test with strictly alternating labels failed: a shift by an even number of trials reproduces the real labels, so a share of
the "null" sets equals the true labels and the p-value is too conservative. PhysioNet labels are nearly alternating (the review reports lag-1 label autocorrelation of -0.48 to -0.67 in 5 subjects, and
the 15 real runs contain 9 to 14 runs of identical labels per 15 trials, against 8.5 expected for random order). With 15-trial runs the effect is smaller than for perfectly alternating labels (in a simulation of
nearly alternating labels no null set agreed with the real labels on more than 80% of trials), but it is not absent. Therefore:
the audit records `label_agreement` for every null set; the basic pipeline reports both nulls and uses the larger p-value;
neither null is treated as "the correct one". The review recommended the shift null as more appropriate; this release keeps both.

## Not decided by the code, decided by you
Which rejection rule is final. The adaptive rule is a label-blind default chosen without looking at accuracy and not yet run on the
real files. Look only at trial retention and bad-channel counts, fix the rule, and then run the audit.
