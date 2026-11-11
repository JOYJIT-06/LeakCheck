"""Label-sequence statistics and mechanism diagnostics (numpy, scipy, scikit-learn only).

Implemented: label autocorrelation and runs test, class balance per run (section 1/H2),
M1 run-decodability, M2 trial-to-trial dependence of band power.
Not implemented: M3 (covariance shift), M4 (spatial plausibility), M5, M6, M7. See docs/REQUIREMENTS_STATUS.md.
"""
import numpy as np
from scipy import stats
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import StratifiedKFold, cross_val_score


def lag1_label_autocorr(y, runs):
    """Lag-1 autocorrelation of the label sequence, using only consecutive trials inside the same run."""
    y, runs = np.asarray(y, float), np.asarray(runs)
    a, b = [], []
    for r in np.unique(runs):
        seq = y[runs == r]
        a.extend(seq[:-1])
        b.extend(seq[1:])
    a, b = np.array(a), np.array(b)
    if a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def _runs_pmf(n1, n0):
    """Exact distribution of the number of runs in a random arrangement of n1 ones and n0 zeros."""
    from math import comb
    total = comb(n1 + n0, n1)
    pmf = {}
    for r in range(2, n1 + n0 + 1):
        k = r // 2
        if r % 2 == 0:
            ways = 2 * comb(n1 - 1, k - 1) * comb(n0 - 1, k - 1)
        else:
            ways = comb(n1 - 1, k) * comb(n0 - 1, k - 1) + comb(n1 - 1, k - 1) * comb(n0 - 1, k)
        if ways:
            pmf[r] = ways / total
    return pmf


def runs_test_p(y):
    """Wald-Wolfowitz runs test for randomness of a binary sequence: EXACT two-sided p-value.

    Sum of the probabilities of all run counts that are no more likely than the observed one.
    (v0.2 used a normal approximation, which is unreliable for the 15-trial runs used here.)
    """
    y = np.asarray(y).astype(int)
    n1, n0 = int(y.sum()), int((1 - y).sum())
    if n1 == 0 or n0 == 0:
        return float("nan")
    n_runs = 1 + int(np.sum(y[1:] != y[:-1]))
    pmf = _runs_pmf(n1, n0)
    p_obs = pmf[n_runs]
    return float(min(1.0, sum(p for p in pmf.values() if p <= p_obs * (1 + 1e-9))))


def label_sequence_stats(y, runs):
    y, runs = np.asarray(y), np.asarray(runs)
    runs_p = [runs_test_p(y[runs == r]) for r in np.unique(runs)]
    n_ok = int(np.sum(~np.isnan(runs_p)))
    p_min = float(np.nanmin(runs_p)) if n_ok else float("nan")
    return {
        "label_lag1_autocorr": lag1_label_autocorr(y, runs),
        "runs_test_p_min": p_min,
        "runs_test_p_min_adj": float(min(1.0, 1 - (1 - p_min) ** n_ok)) if n_ok else float("nan"),  # Sidak, over runs
        "class_balance_per_run": [float(y[runs == r].mean()) for r in np.unique(runs)],
        "trials_per_run": [int((runs == r).sum()) for r in np.unique(runs)],
    }


def _logvar(X):
    return np.log(X.var(axis=2) + 1e-30)


def run_decodability(X, y, runs, n_splits=5, n_perm=50, seed=0):
    """M1: can the RUN a trial came from be predicted from its EEG, within each class?

    Uses random trial-level folds on purpose, because the question is whether run identity is encoded in the
    signal at all. The comparison level is NOT 1/n_runs (runs differ in size, and with unequal runs the majority
    run alone beats 1/n_runs): run labels are permuted within class `n_perm` times, giving a null mean and a
    permutation p-value. `run_decode_chance` (1/n_runs) is kept only for backward compatibility.
    """
    X, y, runs = np.asarray(X), np.asarray(y), np.asarray(runs)
    F = _logvar(X)
    rng = np.random.default_rng(seed)

    def score(r_lab):
        accs = []
        for c in np.unique(y):
            idx = y == c
            r = r_lab[idx]
            k = int(min(n_splits, np.bincount(np.unique(r, return_inverse=True)[1]).min()))
            if k < 2:
                continue
            cv = StratifiedKFold(k, shuffle=True, random_state=seed)
            clf = LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")
            accs.append(cross_val_score(clf, F[idx], r, cv=cv).mean())
        return float(np.mean(accs)) if accs else float("nan")

    obs = score(runs)
    null = []
    for _ in range(n_perm):
        rp = runs.copy()
        for c in np.unique(y):
            idx = np.where(y == c)[0]
            rp[idx] = rng.permutation(runs[idx])
        null.append(score(rp))
    null = np.array([v for v in null if not np.isnan(v)])
    return {"run_decode_acc": obs, "run_decode_chance": 1.0 / len(np.unique(runs)),
            "run_decode_null_mean": float(null.mean()) if len(null) else float("nan"),
            "run_decode_p": float((1 + np.sum(null >= obs)) / (1 + len(null))) if len(null) and not np.isnan(obs) else float("nan")}


def trial_dependence(X, runs, max_lag=5, y=None):
    """M2: lag-1..lag-max autocorrelation of log band power across consecutive trials in a run.

    If `y` is given, the class mean (within each run) is removed first. Without it, a class effect
    on band power combined with a non-random label order shows up as "trial dependence"
    (v0.2 behaviour, still the default when `y` is None). Pass `y` for the M2 diagnostic.

    Averaged over channels and runs. Values above zero mean neighbouring trials resemble each
    other, which is the dependence that trial-level random splits ignore. (The cache holds one
    8-30 Hz band, so mu and beta are not separated here.)
    """
    F = _logvar(np.asarray(X))
    runs = np.asarray(runs)
    y = None if y is None else np.asarray(y)
    out = {}
    for lag in range(1, max_lag + 1):
        vals = []
        for r in np.unique(runs):
            seg = F[runs == r].copy()
            if y is not None:
                yr = y[runs == r]
                for c in np.unique(yr):
                    seg[yr == c] -= seg[yr == c].mean(axis=0)
            if len(seg) <= lag + 2:
                continue
            a, b = seg[:-lag], seg[lag:]
            ok = (a.std(axis=0) > 0) & (b.std(axis=0) > 0)
            if ok.any():
                vals.append(np.mean([np.corrcoef(a[:, i], b[:, i])[0, 1] for i in np.where(ok)[0]]))
        out[f"dep_lag{lag}"] = float(np.mean(vals)) if vals else float("nan")
    return out
