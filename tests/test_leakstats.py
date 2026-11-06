import numpy as np

from emi import leakstats as ls
from emi import nulls as nl
from emi import diagnostics as dg
from tests.helpers import make_data


def test_hodges_lehmann_matches_median_for_symmetric_data():
    assert abs(ls.hodges_lehmann([1, 2, 3, 4, 5]) - 3) < 1e-9


def test_bca_ci_contains_estimate():
    rng = np.random.default_rng(0)
    d = rng.normal(2.0, 3.0, 40)
    lo, hi = ls.bca_ci(d, n_resamples=500)
    assert lo < ls.hodges_lehmann(d) < hi


def test_rank_biserial_extremes():
    assert ls.rank_biserial([1, 2, 3, 4]) == 1.0
    assert ls.rank_biserial([-1, -2, -3]) == -1.0
    assert ls.rank_biserial([0, 0]) == 0.0


def test_holm_matches_hand_calculation():
    adj = ls.holm([0.01, 0.04, 0.03])
    assert np.allclose(adj, [0.03, 0.06, 0.06])


def test_tost_declares_equivalence_for_tiny_differences_and_not_for_big_ones():
    rng = np.random.default_rng(1)
    small = rng.normal(0.0, 0.5, 60)
    big = rng.normal(5.0, 1.0, 60)
    assert ls.tost_paired(small, margin=2.0)["equivalent"] is True
    assert ls.tost_paired(big, margin=2.0)["equivalent"] is False


def test_paired_summary_detects_a_real_shift():
    rng = np.random.default_rng(2)
    ref = rng.uniform(0.5, 0.8, 40)
    leaky = ref + 0.05 + rng.normal(0, 0.01, 40)
    s = ls.paired_summary(leaky, ref, n_test=45, n_boot=300)
    assert 4.0 < s["hl_pp"] < 6.0
    assert s["wilcoxon_p"] < 1e-4 and s["t_logit_p"] < 1e-4
    assert s["rank_biserial"] > 0.9 and s["equivalent"] is False


def test_meta_analysis_identical_studies_has_no_heterogeneity():
    r = ls.random_effects_meta([3.0, 3.0, 3.0], [1.0, 1.0, 1.0])
    assert abs(r["pooled"] - 3.0) < 1e-9 and r["tau2"] == 0.0 and r["I2"] == 0.0


def test_meta_analysis_heterogeneous_studies():
    r = ls.random_effects_meta([0.0, 10.0, 20.0], [0.5, 0.5, 0.5])
    assert r["tau2"] > 10 and r["I2"] > 0.9 and r["pred_low"] < r["ci_low"]


def test_required_subjects_is_larger_for_smaller_effects():
    n_big = ls.required_subjects(sd=3.0, effect=3.0)
    n_small = ls.required_subjects(sd=3.0, effect=1.0)
    assert n_small > n_big >= 3


def test_ranking_reversal():
    r = ls.ranking_reversal({"a": 0.9, "b": 0.8, "c": 0.7}, {"a": 0.6, "b": 0.7, "c": 0.65})
    assert r["n_pairs_reversed"] == 2 and r["best_changed"] is True
    same = ls.ranking_reversal({"a": 0.9, "b": 0.8}, {"a": 0.7, "b": 0.6})
    assert same["kendall_tau"] == 1.0 and same["n_pairs_reversed"] == 0


def test_permutation_keeps_class_counts_per_run():
    X, y, runs, _ = make_data()
    yp = nl.permute_within_runs(y, runs, np.random.default_rng(0))
    for r in np.unique(runs):
        assert y[runs == r].sum() == yp[runs == r].sum()
    assert not np.array_equal(y, yp)


def test_circular_shift_preserves_sequence_structure():
    runs = np.zeros(20, int)
    y = np.array([0] * 10 + [1] * 10)             # fully blocked labels
    ys = nl.circular_shift_within_runs(y, runs, np.random.default_rng(3))
    changes = lambda v: int((v[1:] != v[:-1]).sum())
    assert changes(ys) <= 2 and not np.array_equal(ys, y)       # still two blocks, just rotated
    # a plain permutation destroys the blocks
    yp = nl.permute_within_runs(y, runs, np.random.default_rng(3))
    assert changes(yp) > 2


def test_empirical_p_formula():
    assert nl.empirical_p(0.9, [0.5] * 99) == 1 / 100
    assert nl.empirical_p(0.4, [0.5] * 9) == 1.0


def test_label_autocorr_detects_blocked_labels():
    runs = np.zeros(40, int)
    blocked = np.array([0] * 20 + [1] * 20)
    rng = np.random.default_rng(0)
    shuffled = rng.permutation(blocked)
    assert dg.lag1_label_autocorr(blocked, runs) > 0.8
    assert abs(dg.lag1_label_autocorr(shuffled, runs)) < 0.4
    assert dg.runs_test_p(blocked) < 0.001
    assert dg.runs_test_p(shuffled) > 0.01


def test_run_decodability_detects_run_specific_signal():
    X, y, runs, _ = make_data(informative=False, per_run=24, seed=5)
    for r in np.unique(runs):
        X[runs == r, 3, :] *= (1 + 2 * r)            # run-specific amplitude in channel 3
    out = dg.run_decodability(X, y, runs)
    assert out["run_decode_acc"] > out["run_decode_chance"] + 0.3
    X0, y0, runs0, _ = make_data(informative=False, per_run=24, seed=6)
    assert dg.run_decodability(X0, y0, runs0)["run_decode_acc"] < 0.55


def test_trial_dependence_detects_drift():
    X, y, runs, _ = make_data(informative=False, per_run=30, seed=7)
    drift = np.linspace(1, 3, 30)
    for r in np.unique(runs):
        X[runs == r] *= drift[:, None, None]            # slow amplitude drift on every channel
    assert dg.trial_dependence(X, runs)["dep_lag1"] > 0.5
    X0, _, runs0, _ = make_data(informative=False, per_run=30, seed=8)
    assert abs(dg.trial_dependence(X0, runs0)["dep_lag1"]) < 0.15


# ---- v0.3 ---------------------------------------------------------------------------------------
def test_bca_ci_reports_its_method():
    from emi.leakstats import bca_ci
    d = np.array([1.0, 2.0, 0.5, 3.0, 1.5, 2.5, 0.0, 1.0])
    lo, hi, method = bca_ci(d, n_resamples=500, return_method=True)
    assert method in ("BCa", "percentile") and lo < hi
    assert bca_ci(np.ones(5), return_method=True)[2] == "degenerate"
    assert bca_ci(np.ones(2), return_method=True)[2] == "too_few"
    assert len(bca_ci(d, n_resamples=200)) == 2                      # default API unchanged


def test_hksj_interval_is_never_narrower_than_dl_with_few_datasets():
    from emi.leakstats import random_effects_meta
    r = random_effects_meta([4.0, 6.5, 5.0], [0.5, 0.6, 0.4], hksj=True)
    assert r["ci_high_hksj"] - r["ci_low_hksj"] >= r["ci_high"] - r["ci_low"]
    assert "ci_low_hksj" not in random_effects_meta([4.0, 6.5, 5.0], [0.5, 0.6, 0.4])


# ---- v0.3 additions ----
def test_ranking_reversal_bootstrap_is_stable_when_one_decoder_clearly_wins():
    rng = np.random.default_rng(0)
    a = {"x": 0.70 + rng.normal(0, 0.03, 30), "y": 0.60 + rng.normal(0, 0.03, 30)}
    r = ls.ranking_reversal_bootstrap(a, a)
    assert r["p_best_decoder_changes"] == 0.0 and r["best_leaky"] == r["best_clean"] == "x"


def test_ranking_reversal_bootstrap_detects_a_swap():
    rng = np.random.default_rng(1)
    leaky = {"x": 0.80 + rng.normal(0, 0.02, 40), "y": 0.65 + rng.normal(0, 0.02, 40)}
    clean = {"x": 0.55 + rng.normal(0, 0.02, 40), "y": 0.65 + rng.normal(0, 0.02, 40)}
    r = ls.ranking_reversal_bootstrap(leaky, clean)
    assert r["p_best_decoder_changes"] > 0.95 and r["best_leaky"] == "x" and r["best_clean"] == "y"


def test_run_decodability_has_a_permutation_null_that_sits_below_the_signal():
    from emi import diagnostics as dg
    from tests.helpers import make_data
    X, y, runs, _ = make_data(informative=False, per_run=24, seed=5)
    for r in np.unique(runs):
        X[runs == r, 3, :] *= (1 + 2 * r)
    out = dg.run_decodability(X, y, runs, n_perm=20)
    assert out["run_decode_p"] <= 0.1 and out["run_decode_acc"] > out["run_decode_null_mean"] + 0.2
    X0, y0, runs0, _ = make_data(informative=False, per_run=24, seed=6)
    out0 = dg.run_decodability(X0, y0, runs0, n_perm=20)
    assert out0["run_decode_p"] > 0.05
