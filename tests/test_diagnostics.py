"""v0.3 tests: label-sequence statistics, M2 trial dependence, rank-safe CSP, rejection helper."""
import numpy as np
import pytest

from emi import diagnostics as dg
from emi.signal_utils import ptp_reject_indices
from emi.simple_csp import SimpleCSP
from tests.helpers import make_data


def _perm_runs_p(seq, B=40000, seed=0):
    rng = np.random.default_rng(seed)
    nr = lambda s: 1 + int(np.sum(s[1:] != s[:-1]))
    obs = nr(seq)
    sims = np.array([nr(rng.permutation(seq)) for _ in range(B)])
    # two-sided by probability: runs counts no more likely than the observed one
    vals, counts = np.unique(sims, return_counts=True)
    pm = dict(zip(vals, counts / B))
    return sum(p for p in pm.values() if p <= pm.get(obs, 0) * (1 + 1e-9))


def test_runs_pmf_sums_to_one_and_matches_known_mean():
    pmf = dg._runs_pmf(7, 8)
    assert sum(pmf.values()) == pytest.approx(1.0)
    mean = sum(r * p for r, p in pmf.items())
    assert mean == pytest.approx(1 + 2 * 7 * 8 / 15)


def test_exact_runs_test_matches_permutation():
    rng = np.random.default_rng(1)
    for seq in (np.array([0, 1] * 7 + [0]), np.array([0] * 7 + [1] * 8), rng.permutation(np.r_[np.zeros(7, int), np.ones(8, int)])):
        assert dg.runs_test_p(seq) == pytest.approx(_perm_runs_p(seq), abs=0.02)


def test_runs_test_flags_perfect_alternation_and_blocks():
    assert dg.runs_test_p(np.array([0, 1] * 8)) < 0.001
    assert dg.runs_test_p(np.array([0] * 8 + [1] * 8)) < 0.001
    assert np.isnan(dg.runs_test_p(np.zeros(10, int)))


def test_runs_test_false_positive_rate_not_above_nominal():
    rng = np.random.default_rng(0)
    base = np.r_[np.zeros(8, int), np.ones(7, int)]
    ps = np.array([dg.runs_test_p(rng.permutation(base)) for _ in range(3000)])
    assert (ps < 0.05).mean() <= 0.055                       # exact test is valid (never liberal)


def test_adjusted_min_p_is_not_smaller_than_raw_min_p():
    y = np.array(([0, 1] * 7 + [0]) * 3)
    runs = np.repeat([0, 1, 2], 15)
    s = dg.label_sequence_stats(y, runs)
    assert s["runs_test_p_min_adj"] >= s["runs_test_p_min"]


def _class_effect_only(blocked, seed=0, n_runs=3, n_tr=16, n_ch=8):
    rng = np.random.default_rng(seed)
    X, runs, ys = [], [], []
    for r in range(n_runs):
        y = np.array(([0] * 4 + [1] * 4) * 2) if blocked else rng.permutation(np.repeat([0, 1], n_tr // 2))
        X.append(rng.standard_normal((n_tr, n_ch, 200)) * (1 + y)[:, None, None])
        runs += [r] * n_tr
        ys.append(y)
    return np.concatenate(X), np.array(runs), np.concatenate(ys)


def test_trial_dependence_without_y_is_fooled_by_blocked_labels():
    X, runs, y = _class_effect_only(blocked=True)
    assert dg.trial_dependence(X, runs, max_lag=1)["dep_lag1"] > 0.3          # the v0.2 flaw (documented)


def test_trial_dependence_with_y_removes_the_label_effect():
    vals = []
    for seed in range(10):
        X, runs, y = _class_effect_only(blocked=True, seed=seed)
        vals.append(dg.trial_dependence(X, runs, max_lag=1, y=y)["dep_lag1"])
    assert abs(np.mean(vals)) < 0.1


def test_trial_dependence_with_y_still_sees_real_drift():
    rng = np.random.default_rng(0)
    n_tr, n_ch = 24, 8
    drift = np.cumsum(rng.standard_normal(n_tr) * 0.3)
    y = rng.permutation(np.repeat([0, 1], n_tr // 2))
    X = rng.standard_normal((n_tr, n_ch, 200)) * np.exp(drift)[:, None, None]
    assert dg.trial_dependence(X, np.zeros(n_tr, int), max_lag=1, y=y)["dep_lag1"] > 0.3


def _rank_deficient_data(seed=0):
    """Average-referenced data: every channel minus the mean over channels, so the rank is n_ch - 1."""
    X, y, runs, _ = make_data(seed=seed)
    return X - X.mean(axis=1, keepdims=True), y


def test_simple_csp_ignores_the_empty_direction():
    X, y = _rank_deficient_data()
    csp = SimpleCSP(4).fit(X, y)
    assert csp.rank_ == X.shape[1] - 1
    assert csp.eigenvalues_.min() > 0.01 and csp.eigenvalues_.max() < 0.99     # no eigenvalue at about 0
    F = csp.transform(X)
    assert np.isfinite(F).all() and F.min() > -30                             # no log(1e-30) noise features


def test_simple_csp_still_finds_the_informative_channels():
    X, y = _rank_deficient_data()
    F = SimpleCSP(2).fit(X, y).transform(X)
    assert abs(F[y == 0, 0].mean() - F[y == 1, 0].mean()) > 0.5


def test_ptp_rejection_helper_is_window_blind_to_labels_and_exact():
    rng = np.random.default_rng(0)
    d = rng.standard_normal((5, 3, 100)) * 1e-6
    d[2, 1, 10] = 500e-6                                                       # one big artefact
    assert list(ptp_reject_indices(d, 200.0)) == [2]
    assert len(ptp_reject_indices(d, 600.0)) == 0
