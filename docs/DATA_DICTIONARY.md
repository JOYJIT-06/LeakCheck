# Data dictionary

## leakcheck_raw.csv (one row per dataset x subject x decoder x design x label set)
| Column | Meaning |
|---|---|
| dataset, subject, decoder | what was analysed |
| design | design id; a suffix after @ is the dose (noise channels for P4, window step in seconds for P6, copies for P7) |
| label_type | real, perm (within-run permutation) or shift (circular shift) |
| perm | 0 for real labels; 1..n for null label sets |
| n_trials | trials of the subject (or windows/augmented samples are NOT counted here) |
| acc_pooled | accuracy over all test trials of a repeat, averaged over repeats. PRIMARY |
| acc_fold_mean | mean of per-fold accuracies |
| bal_acc, auc, kappa, recall_left, recall_right | secondary metrics (NaN when not defined, for example AUC in P5) |
| n_folds, n_test_mean | folds per repeat and mean test size per fold |
| seconds | compute time of this design |
| error | reason a design returned NaN (for example a training fold with one class) |

## inflation_by_subject.csv
`delta_pp` = 100 x (acc_leaky - acc_ref) for the same subject, decoder and dataset. `kind` names the contrast.

## inflation_table.csv
`hl_pp` Hodges-Lehmann estimate and `hl_ci_*` BCa interval over subjects; `wilcoxon_p`, `wilcoxon_p_holm` (Holm within
dataset x decoder), `t_logit_p`, `rank_biserial`, `cohens_dz`, `tost_p`/`equivalent` (equivalence within +-`tost_margin_pp`).

## null_table.csv
`null_mean_acc`, `optimism_pp` (null mean minus 50%), `false_positive_rate` (share of null datasets reaching the binomial threshold).
Null accuracy can sit BELOW 50% for random splits when the data have structure; see docs/LEAKCHECK.md.

## subject_empirical_p.csv
Per subject and design: observed accuracy, mean and 95th percentile of its own null distribution, and
`empirical_p = (1 + number of null values >= observed) / (1 + number of nulls)`.

## subject_info.csv
Trial counts, label autocorrelation (`label_lag1_autocorr`), runs-test p, class balance per run, run-decodability
(`run_decode_acc` vs `run_decode_chance`) and trial dependence (`dep_lag1` ... `dep_lag5`).
