# Consolidated code review of eeg-motor-imagery-mne v0.2 (all parts)

Supersedes `code_review_leakcheck_v0.2.md` (it keeps those items and adds the files skipped before).
**37 items.** Evidence labels: **REPRODUCED** = I ran it. **READ** = seen in the code, not run. **HYPOTHESIS** = plausible, untested.
Items marked "simulation" first used simulated data; the ones that could be checked on real EEG were then re-checked (section 4).

Coverage: every module in `src/emi` and every script was read. `plotting.py` and `tfr.py` were read in the parts that draw ERD curves and slope plots, and I found no defect there
(ERD inherits the trial loss from item 1 because it uses the rejected epochs). Tests: 50 passed.

**Checked and dropped:** I suspected that `run_leakcheck.py` reuses old per-subject files after the settings change. That is wrong: results are stored in a folder named after a hash of the settings. Re-running with other designs and another decoder recomputed everything.

## Real-data observations used above
- Subject 1 keeps 10 of 45 trials at 200 uV; subjects 2-7 keep 39, 1, 0, 7, 20, 27 (from my first real-data run).
- Subject 2 with relaxed rejection (600 uV, a software check only, no accuracy examined): 45 trials, no blink component found, near-singular channel covariance (smallest/largest singular value 4e-9; effective rank 61 of 64 at a 1e-6 tolerance).

### Preprocessing and data

| # | Part | Flaw | Evidence | Fix |
|---|---|---|---|---|
| 1 | Rejection threshold | `reject_uv = 200` on the worst of 64 channels over a 5 s epoch keeps only 0-39 of 45 trials per subject (subjects 1-7). Subject 1 keeps 10 trials; subjects 3 and 4 fall far below any usable count. | REPRODUCED | Label-blind rule fixed in advance (bad-channel interpolation, adaptive per-subject threshold). Report exclusions per subject. Never choose it by accuracy. |
| 2 | Rejection window | Rejection uses the -1 to 4 s epoch, but the cache and decoding use 0-4 s. Artefacts in the pre-cue baseline remove trials that the decoder never sees. | READ | Reject on the analysed window only (keep the baseline check for the ERD figure only). |
| 3 | Bad channels | No bad-channel detection before average reference and ICA. Peripheral channels (O2, F8, F7, Iz) caused most rejections for subject 1. | Channel counts REPRODUCED; the causal link to the average reference is a HYPOTHESIS | Detect (robust variance or correlation), interpolate, then re-reference. |
| 4 | 'Everything nested' claim | ICA, filtering and rejection use all runs, including the held-out run. They don't use labels, so label leakage is unlikely, but the statement 'fitted inside training folds' would be false for the reference design. | READ (status file lists P2 as TODO) | Add P2 and a preprocessing-order audit, or limit the claim to label-dependent steps. |
| 5 | Blink removal | Automatic detection from Fp1/Fp2 only, at most 2 components, never checked. Outcomes differ: one component found for subject 1, none for subject 2. | REPRODUCED (counts); effect on accuracy unknown | Inspect components for a sample of subjects; report the number removed per subject; add a no-ICA sensitivity run. |
| 6 | Interactive download prompt | First PhysioNet download opens a config-path prompt that hangs non-interactive jobs. | REPRODUCED | Set `MNE_DATA` or `data_path`; document in the README. |
| 7 | Deprecated montage | `standard_1005` is removed in MNE 1.14 but `requirements.txt` allows `mne>=1.7,<2`. | REPRODUCED (FutureWarning) | Use the new name or pin `mne<1.14`. |
| 8 | Run ids stored in `info['description']` | A text field carries data used for run assignment. | READ (worked in my run) | Store run onsets in an explicit array and assert total length. |

### Validation designs and leaks

| # | Part | Flaw | Evidence | Fix |
|---|---|---|---|---|
| 9 | D1s (labelled headline comparator) | Test sets are drawn independently per fold and overlap. In a 45-trial, 3-run example, 30% of pooled test predictions were duplicates and 13.4 trials were never tested. | REPRODUCED | Disjoint size- and class-matched partition (tested code in section 3). |
| 10 | Hard-coded window | `BASE_WINDOW = (1.0, 3.0)` in `leakcheck.py` duplicates `decode_tmin/tmax` in `config.py`. | READ | One source of truth, or read the window from the cache. |
| 11 | Silent loss of subjects | A design that raises `ValueError` becomes a NaN row; `inflation_by_subject` then drops that subject from the comparison without a warning. | READ | Report counts and reasons for every dropped subject-design pair; fail loudly in the final run. |
| 12 | Different seeds for real and null labels | `seed + k` gives different random folds to real and null label sets. | READ (minor) | Use the same fold seeds so the null is paired. |
| 13 | Chance threshold | The binomial threshold is exact (29/45 for n = 45) but assumes independent trials, which trials within a run are not. | REPRODUCED (matches exact binomial) | Use permutation p-values for single-subject claims; state the assumption. |

### Decoders

| # | Part | Flaw | Evidence | Fix |
|---|---|---|---|---|
| 14 | `SimpleCSP` (used by `--csp numpy`) picks a null-space direction | Average-referenced real EEG is rank-deficient. On real subject 2 (relaxed rejection), the generalised eigenproblem has eigenvalues of about 0 that rank as the most extreme, so a noise direction becomes a CSP component (feature range -36 to -16 vs -21 to -16 after the fix). Unit tests pass because simulated data are full rank. | REPRODUCED (one real subject). On real data the three CSP versions disagree strongly, see section 4 | Whiten inside the data subspace first (tested `RankSafeCSP` in section 3), or never use `--csp numpy` for real data and say so in the README. |
| 15 | MNE CSP with `reg=None` | With 64 channels and 15-30 training trials per fold, unregularised covariances are unstable. The MNE fit did run on subject 2, so this is a risk, not a failure I saw. | HYPOTHESIS, now with indirect support: MNE reports full rank 64 and does not project, and on real subject 2 its leave-one-run-out accuracy (0.622) differs from the rank-safe version (0.911). This does not show which is right | Test shrinkage or `rank=` options; compare stability across folds. |
| 16 | Inconsistent classifier settings | `decode.py` uses plain LDA; the audit uses `lsqr` with automatic shrinkage. | READ | Use one decoder specification for both. |
| 17 | Basic pipeline uses the design the audit calls leaky | `decode.evaluate`, `run_subject` and `run_group` report accuracy from shuffled stratified 5-fold CV plus a label permutation p-value from that same CV. The group summary's Wilcoxon test and 'fraction significant' are built on it. | READ | Default to leave-one-run-out, or print a warning and label the numbers 'random-split accuracy'. |
| 18 | Decoder coverage | Only CSP+LDA and CSP+LR are tested; tangent space (needs pyriemann) was never run; FBCSP and EEGNet are missing. | READ | Run `ts_lr`, add FBCSP, add EEGNet only for datasets with enough trials. |

### Null models

| # | Part | Flaw | Evidence | Fix |
|---|---|---|---|---|
| 19 | Null table naming | The 'false_positive_rate' column reads 1.0 for leaky designs such as P1. That is a detection rate for the injected leak. | REPRODUCED (synthetic run) | Separate clean designs (should be about 5%) from leaky designs (detection). |
| 20 | Empirical p-value resolution | The smallest possible p is 1/(n_null + 1). With the README's `--n-null 3` or `5` no subject can reach p < 0.05, so `lost_significance` counts zero. | READ (arithmetic) | Use n_null of at least 20 for any subject-level significance statement; warn when it is lower. |
| 21 | Circular-shift null | With about 15 trials per run only about 14 distinct non-zero shifts exist per run. | READ (minor) | Report the number of distinct nulls; combine with the permutation null. |

### Statistics (`leakstats.py`, `analyze_leakcheck.py`)

| # | Part | Flaw | Evidence | Fix |
|---|---|---|---|---|
| 22 | BCa interval fallback | If BCa fails, the code silently switches to a percentile interval with at most 2000 resamples. | READ | Record which method produced each interval. |
| 23 | Random-effects meta-analysis | Normal-based 95% CI with DerSimonian-Laird tau^2. With 2-4 datasets this is too narrow, and tau^2 is poorly estimated for k = 2. `meta()` also skips datasets with fewer than 3 subjects or zero variance without saying so. | READ | Use Hartung-Knapp adjustment or report the prediction interval only; list skipped datasets. |
| 24 | Ranking reversal | Kendall tau on group-mean accuracies, with no uncertainty; with 2 decoders tau can only be +1 or -1. | READ | Bootstrap subjects and report the probability that the best decoder changes. |
| 25 | Moderator regressions | Four moderators x decoders x designs are tested with raw p-values. | READ | Pre-specify one primary moderator (label autocorrelation) and correct the rest. |
| 26 | Strata by reference accuracy (M8) | Inflation is leaky minus reference, and subjects are grouped by the reference accuracy. This mechanically produces regression to the mean. It is labelled exploratory. | READ | Stratify on something independent of the contrast, such as an independent split or a signal-quality measure. |
| 27 | `lost_significance` | Counts subjects significant under the leaky design but not under the reference. A difference between 'significant' and 'not significant' is not itself significant. | READ | Report the paired accuracy difference with CI per subject, or a test of the paired difference. |
| 28 | Power from the pilot | The SD comes from the data passed in. Reusing the pilot subjects in the final analysis would be circular. | READ (README says to freeze the plan) | Keep pilot subjects out of the confirmatory set. |

### Diagnostics (`diagnostics.py`)

| # | Part | Flaw | Evidence | Fix |
|---|---|---|---|---|
| 29 | M2 `trial_dependence` is confounded by class and label order | On SIMULATED data with a class effect and no drift at all, lag-1 'dependence' was -0.074 with random label order and +0.594 with blocked labels. The metric therefore partly measures the label sequence. | REPRODUCED in simulation, and CHECKED on real EEG: the repo value was reproduced exactly, and removing class means changed it by +0.00 to +0.11 per subject (section 4). The confound exists but is modest on these data | Remove class means within each run before computing autocorrelation. |
| 30 | Runs test on short sequences | Normal approximation with 8 and 7 trials. On SIMULATED random sequences the per-run rate of p < 0.05 was 0.024 (conservative), and the minimum p over 3 runs was 0.078 (nominal 0.05). `runs_test_p_min` is therefore anti-conservative. | REPRODUCED in simulation. On 15 real runs the normal approximation and a 20,000-permutation p-value agreed closely (5 of 15 runs below 0.05 with both); the approximation was slightly liberal near 0.05 (0.057 vs 0.068). The min-p-over-runs issue remains | Use an exact or permutation runs test and correct for the number of runs. |
| 31 | M1 `run_decodability` chance level | Chance is taken as 1/n_runs, ignoring unequal run sizes (for example [1, 5, 4]), and there is no permutation null. | READ | Compare with a null where run labels are permuted within class. |

### Scripts and software

| # | Part | Flaw | Evidence | Fix |
|---|---|---|---|---|
| 32 | Broad `except Exception` in `run_one` | Any bug becomes the string 'FAILED: <message>' with no traceback, and the run ends with 'No subject finished'. | READ | Log the traceback; re-raise in debug mode. |
| 33 | Two CSP implementations | `--csp numpy` and MNE give different numbers (the file says so). | READ | Label every output with the CSP implementation used. |
| 34 | No lockfile | Installing MNE upgraded numpy and broke the system scikit-learn in my first attempt. | REPRODUCED (environment) | Lockfile; record versions in every output. |

### Data coverage and unfinished work

| # | Part | Flaw | Evidence | Fix |
|---|---|---|---|---|
| 35 | MOABB adapter | Untested; dataset names unverified; MOABB's own preprocessing differs from the PhysioNet path (average reference, ICA, rejection); channel counts differ, so the 64-noise-channel dose in P4 means different things. | READ | Run one MOABB subject; document each dataset's preprocessing; check dose sensitivity. |
| 36 | PhysioNet design | One recording day, three runs of about 15 trials; leave-one-run-out is not a session test. | READ (README says so) | Add multi-session datasets and make D6 a main design for them. |
| 37 | Missing items (your status file) | D7 leave-one-subject-out, P2, dose-response, robustness grid, mechanism diagnostics M3-M7, mixed-effects and Bayesian models, FBCSP, EEGNet, pre-registered plan, and no empirical result yet. | READ | See order of fixes. |

## 4. Real-EEG re-check of the simulated findings (PhysioNet, subjects 1-7)
**Setup (software check, not a result):** one relaxed rejection threshold of 600 uV, fixed in advance, label-blind and not tuned on accuracy; it keeps 45, 45, 36, 22, 45, 45, 45 trials for subjects 1-7. Subject 4 (22 trials, runs [4, 6, 12]) fails the repo's own 30-trial rule and is left out of the accuracy table. Subject 3 has 36 trials and runs [12, 15, 9]. Tables: [m2_trial_dependence_real.csv](real_eeg_checks/m2_trial_dependence_real.csv), [label_runs_test_real.csv](real_eeg_checks/label_runs_test_real.csv), [csp_implementation_loro_accuracy_real.csv](real_eeg_checks/csp_implementation_loro_accuracy_real.csv).

**M2 trial dependence (item 29).** The repo's `dep_lag1` matches my re-implementation exactly. Removing class means within each run changed it as follows (repo, then class-residualised): subject 1, 0.058 to 0.129; 2, 0.062 to 0.101; 3, -0.043 to -0.060; 4, -0.017 to -0.017; 5, 0.131 to 0.135; 6, 0.357 to 0.367; 7, 0.082 to 0.188. Subject 6 stays high either way, which points to slow drift and not to the label sequence. The shift is upward for most subjects, as expected when labels alternate (next point).

**Label sequences (new finding, 5 subjects with full runs).** Lag-1 label autocorrelation is strongly negative (-0.48, -0.67, -0.48, -0.52, -0.48 for subjects 1, 2, 5, 6, 7): labels alternate more than a random order would. Runs counts reach 14 of 15 trials, against about 8.5 expected. 5 of 15 runs have p < 0.05 by both the normal approximation and permutation; the minimum p per subject is below 0.05 for subjects 2, 5 and 6. No label sequence is shared between subjects. This is evidence about these 5 subjects only. It matters for the audit: label order is not i.i.d., so the circular-shift null is the more appropriate null than the permutation null here.

**CSP implementation vs accuracy (items 14, 15; leave-one-run-out, 1-3 s window, CSP+LDA; mean of 15 within-run permuted-label nulls in brackets).**

| Subject | numpy SimpleCSP | rank-safe CSP | MNE CSP |
|---|---|---|---|
| 1 | 0.622 (0.539) | 0.489 (0.474) | 0.667 (0.484) |
| 2 | 0.622 (0.495) | 0.911 (0.496) | 0.622 (0.486) |
| 3 | 0.472 (0.487) | 0.444 (0.548) | 0.500 (0.533) |
| 5 | 0.511 (0.499) | 0.578 (0.523) | 0.511 (0.527) |
| 6 | 0.533 (0.513) | 0.444 (0.498) | 0.578 (0.511) |
| 7 | 0.933 (0.498) | 1.000 (0.496) | 0.978 (0.474) |
| Mean | 0.615 (0.505) | 0.644 (0.506) | 0.643 (0.503) |

What this does and does not show:
- All three clean pipelines sit at chance under permuted labels (group means 0.503-0.506), so none of them leaks in the clean design.
- Per-subject accuracy depends strongly on the CSP implementation: the spread across implementations is up to 29 percentage points (subject 2) with about 45 trials, and the best implementation changes between subjects. The group means of the rank-safe and MNE versions are almost the same (0.644 vs 0.643).
- The accuracy table does **not** show that the rank-safe CSP is better. The fix is justified by removing a numerically empty direction, not by accuracy. With 36-45 trials per subject and 3 test folds, single-subject accuracies are noisy.
- Consequence for the audit: report which CSP implementation produced every number, and consider an implementation-sensitivity row in the paper.

## Order of fixes
1. Items 1-3 (label-blind rejection and bad channels), then 9 (D1s), then 14 (CSP null space).
2. Items 6, 7, 34 (data path, MNE pin, lockfile) and 11, 19, 20 (silent drops, null naming, n_null).
3. Item 17 (make the basic pipeline use leave-one-run-out or label it) and 16 (one decoder specification).
4. Statistics items 22-28, diagnostics 29-31.
5. Item 4 (P2 and the 'nested' wording), then decoders and datasets (items 18, 35, 36).

## 3. Tested code
D1s partition (item 9) is in `code_review_leakcheck_v0.2.md`. Rank-safe CSP (item 14), tested on real subject 2: the old version produced a feature range of -36.0 to -16.3, the new one -21.4 to -16.3 with 61 of 64 dimensions kept.
Not tested: whether the new CSP changes decoding accuracy. I did not look at accuracy.
```python
import warnings; warnings.filterwarnings("ignore")
import numpy as np, scipy.linalg
from sklearn.base import BaseEstimator, TransformerMixin
from emi.cache import load_cache, cache_path
from emi.simple_csp import SimpleCSP

class RankSafeCSP(BaseEstimator, TransformerMixin):
    """Two-class CSP that first whitens in the data's own subspace, so null-space directions
    (from average reference or removed ICA components) can never be picked as 'discriminative'."""
    def __init__(self, n_components=4, rank_tol=1e-6):
        self.n_components, self.rank_tol = n_components, rank_tol
    def fit(self, X, y):
        y = np.asarray(y)
        covs = [np.mean([x @ x.T / np.trace(x @ x.T) for x in X[y == c]], axis=0) for c in (0, 1)]
        w, V = np.linalg.eigh(covs[0] + covs[1])
        keep = w > self.rank_tol * w.max()
        self.rank_ = int(keep.sum())
        P = V[:, keep] / np.sqrt(w[keep])                      # whitening restricted to the data subspace
        ev, U = np.linalg.eigh(P.T @ covs[0] @ P)
        order = np.argsort(np.abs(ev - 0.5))[::-1][: self.n_components]
        self.filters_ = (P @ U[:, order]).T
        self.eigenvalues_ = ev
        return self
    def transform(self, X):
        Z = np.einsum("kc,ncs->nks", self.filters_, X)
        return np.log((Z ** 2).mean(axis=2) + 1e-30)

```
