"""Leave-one-run-out basic pipeline. Uses the numpy CSP, so it runs without MNE."""
import numpy as np

from emi.config import Config
from emi.decode import evaluate, evaluate_loro
from emi.simple_csp import numpy_csp_factory


def _data(informative=True, seed=0, n_trials=48, n_ch=8, n_times=160):
    rng = np.random.default_rng(seed)
    per = n_trials // 3
    y = np.concatenate([rng.permutation([0, 1] * (per // 2)) for _ in range(3)])   # random label order inside each run
    X = rng.standard_normal((n_trials, n_ch, n_times))
    if informative:
        X[y == 0, 0, :] *= 3.0
        X[y == 1, 1, :] *= 3.0
    return X, y, np.repeat([0, 1, 2], n_trials // 3)


def test_loro_decodes_informative_data_and_reports_its_design():
    X, y, runs = _data(True)
    res = evaluate_loro(X, y, runs, Config(n_perm=19), numpy_csp_factory)
    assert res["mean_acc"] > 0.8 and "leave-one-run-out" in res["validation"]
    assert res["perm_p"] <= 0.1 and res["min_possible_p"] == 1 / 20


def test_loro_is_near_chance_on_noise_with_both_null_types():
    X, y, runs = _data(False, seed=3)
    for nt in ("shift", "perm", "both"):
        res = evaluate_loro(X, y, runs, Config(n_perm=19, null_type=nt), numpy_csp_factory)
        assert 0.25 < res["mean_acc"] < 0.75 and res["perm_p"] > 0.05


def test_both_nulls_are_reported_and_the_larger_p_is_used():
    X, y, runs = _data(True)
    res = evaluate_loro(X, y, runs, Config(n_perm=19, null_type="both"), numpy_csp_factory)
    assert res["perm_p"] == max(res["p_perm"], res["p_shift"])


def test_shift_null_is_degenerate_for_strictly_alternating_labels():
    """Why the audit records label_agreement: with perfectly alternating labels many shifts reproduce the real labels."""
    from emi.nulls import circular_shift_within_runs, label_agreement
    runs = np.repeat([0, 1, 2], 16)
    y = np.tile([0, 1], 24)
    rng = np.random.default_rng(0)
    ag = [label_agreement(y, circular_shift_within_runs(y, runs, rng)) for _ in range(400)]
    assert np.mean(np.array(ag) > 0.99) > 0.05          # a sizeable share of 'null' sets equals the real labels


def test_random_split_result_is_labelled_as_not_run_aware():
    X, y, runs = _data(True)
    res = evaluate(X, y, Config(n_perm=0), numpy_csp_factory)
    assert "not run-aware" in res["validation"] and res["mean_acc"] > 0.8


def test_loro_needs_two_runs():
    X, y, runs = _data(True)
    try:
        evaluate_loro(X, y, np.zeros(len(y), int), Config(n_perm=0), numpy_csp_factory)
    except ValueError:
        return
    raise AssertionError("expected ValueError")
