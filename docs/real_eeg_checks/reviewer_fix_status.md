# emi v0.3 fix status

Patch: [emi_v0.3_fixes.patch](emi_v0.3_fixes.patch) (against v0.2; `pyproject.toml` has the same `mne<1.14` pin and is not in the patch). **68 tests pass** (50 before, 18 new).
Numbers in "item" refer to [code_review_leakcheck_v0.2_consolidated.md](code_review_leakcheck_v0.2_consolidated.md).

## Fixed, with a test
| Item | Fix | Test |
|---|---|---|
| 9 D1s overlap | Disjoint partition, same sizes and class counts as leave-one-run-out | `test_size_matched_split_is_a_disjoint_partition` (15-trial runs, unbalanced classes) |
| 14 numpy CSP | Whitening inside the data subspace | `test_simple_csp_ignores_the_empty_direction`, `..._still_finds_the_informative_channels` |
| 29 M2 confound | `trial_dependence(..., y=)` removes class means per run; script passes `y` | blocked-label simulation (no drift): about 0 with `y`, above 0.3 without; real drift still detected |
| 30 runs test | Exact p-value; Sidak-adjusted min p (`runs_test_p_min_adj`) | matches a 40,000-permutation p; false-positive rate at most 0.055 |
| 11 silent drops | Warning plus `attrs["dropped_subjects"]` | `test_inflation_by_subject_reports_dropped_subjects` |
| 19 null table | `design_type`, `rate_meaning` columns | `test_null_table_says_what_the_rate_means` |
| 20 n_null | `min_possible_p`, warnings in the table and the script | `test_empirical_p_warns_when_too_few_nulls_for_p05` |
| 22 BCa fallback | `return_method`, `hl_ci_method` column | `test_bca_ci_reports_its_method` |
| 23 few datasets | HKSJ interval option, used by `analyze_leakcheck.py` | never narrower than the DL interval |
| 25 moderators | Holm-adjusted `p_holm` | covered by the end-to-end run (not a unit test) |
| 2 rejection window | `reject_window="analysis"` default, `"full"` = v0.2 | `ptp_reject_indices` unit test; real-data counts below |
| 6, 7 | Data path without a prompt; `mne<1.14` | not unit-tested (needs a download / install) |
| 32 | Tracebacks logged; clear error when all epochs are rejected | seen in the real-data run |
| 17 (label only) | `validation` key on basic-pipeline results | not unit-tested |

## Checked on real EEG (PhysioNet, software check)
- Rejection at 200 uV, kept trials with the old rule vs the analysed-window rule: subject 1, 10 vs 12; 2, 39 vs 39; 3, 0 vs 4; 4, 0 vs 0; 5, 7 vs 9; 6, 20 vs 20; 7, 27 vs 29. The change is small; it does not solve the over-rejection (items 1 and 3).
- The patched audit script ran end to end on 6 real subjects (relaxed 600 uV caches, numpy CSP, 20 nulls, quick designs). The new columns were present. These numbers are a smoke test, not results.
- The warning "Only one sample available" comes from subject 3 (runs of 12, 15 and 9 trials) and is the same with the v0.2 code.

## Not fixed (needs a decision from you, or more work)
- **Item 1/3 rejection rule and bad channels.** Which label-blind rule to adopt (interpolation, adaptive threshold) is a design choice.
- 4 (P2 and the "nested" wording), 5 (ICA review), 8, 10, 12, 13, 15, 16, 18, 21, 24, 26, 27, 28, 31, 33, 34 (lockfile), 35-37.
- Item 17: only labelled. The basic pipeline still reports shuffled k-fold accuracy by default.
- I did not run the full audit on the 109-subject dataset.
