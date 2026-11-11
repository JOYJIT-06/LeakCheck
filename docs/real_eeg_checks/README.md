# Real-data software checks (PhysioNet, supplied with the code review)

These files come from running v0.2 on real PhysioNet recordings. They are SOFTWARE CHECKS, not results of the study:
the subjects were chosen only because they ran, with relaxed trial rejection (600 uV) and unfinished preprocessing.

- `label_runs_test_real.csv`: runs test on the label order of 15 real runs (5 subjects). Used by `tests/test_real_checks.py`
  to check the exact runs test in `emi.diagnostics` against the supplied 20,000-permutation p-values.
- `csp_implementation_loro_accuracy_real.csv`: leave-one-run-out accuracy of 6 subjects with three CSP implementations
  (v0.2 numpy CSP with the null-space defect, the rank-safe numpy CSP, MNE CSP) and the mean accuracy under permuted labels.
- `code_review_leakcheck_v0_2.md`: the review itself.

What they show: labels are far from random order (lag-1 autocorrelation -0.48 to -0.67 as reported in the review; 5 of 15 runs nominally
non-random), the v0.2 numpy CSP differs from the others by up to 30 points for single subjects, and the two correct
implementations agree on the group mean (0.644 vs 0.643) while differing per subject.
