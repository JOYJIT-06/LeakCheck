"""Validation tests for experimental design isolation, fold disjointness, and leakage behavior."""
import numpy as np
import pytest
from sklearn.base import clone
from sklearn.exceptions import NotFittedError

from emi import splitters as sp
from emi.decoders import DECODERS, get_csp_factory
from emi.leakcheck import Ctx, d1m_matched_k, d1s_size_matched, d3_loro, p1_csp_on_all
from emi.metrics import evaluate_repeats


def test_d3_loro_strict_run_isolation():
    """Verify that Leave-One-Run-Out (D3) strictly isolates acquisition runs."""
    groups = np.array([0] * 15 + [1] * 15 + [2] * 15)
    y = np.array([0, 1] * 22 + [0])
    repeats = sp.loro_splits(groups)

    assert len(repeats) == 1, "D3 must have exactly 1 repeat"
    folds = repeats[0]
    assert len(folds) == 3, "D3 must have 3 folds for 3 runs"

    tested_indices = []
    for k, (tr, te) in enumerate(folds):
        tr_set, te_set = set(tr), set(te)
        # 1. Fold indices are disjoint
        assert tr_set.isdisjoint(te_set), f"Fold {k} train and test indices overlap!"

        # 2. Group labels are disjoint
        tr_runs = set(groups[tr])
        te_runs = set(groups[te])
        assert tr_runs.isdisjoint(te_runs), f"Fold {k} train and test runs overlap!"
        assert len(te_runs) == 1, f"Fold {k} test set must come from exactly one run"

        tested_indices.extend(te)

    # 3. Every trial tested exactly once
    assert sorted(tested_indices) == list(range(len(groups))), "Every trial must be tested once"


def test_d1s_size_matched_disjoint_and_class_preserving():
    """Verify that D1s produces disjoint test partitions with exact size and class preservation."""
    groups = np.array([0] * 16 + [1] * 14 + [2] * 15)
    y = np.array([0] * 8 + [1] * 8 + [0] * 7 + [1] * 7 + [0] * 7 + [1] * 8)
    repeats = sp.size_matched_random_repeats(y, groups, repeats=5, seed=42)

    assert len(repeats) == 5, "D1s must produce the requested repeat count"

    for r_idx, folds in enumerate(repeats):
        assert len(folds) == 3, f"Repeat {r_idx} must have 3 folds"
        repeat_tested = []
        for k, (tr, te) in enumerate(folds):
            tr_set, te_set = set(tr), set(te)
            # Disjoint train and test
            assert tr_set.isdisjoint(te_set), f"Repeat {r_idx} fold {k} train and test overlap"
            assert len(tr) + len(te) == len(y), f"Repeat {r_idx} fold {k} partition incomplete"

            # Test size matches corresponding run size exactly
            assert len(te) == np.sum(groups == k), f"Repeat {r_idx} fold {k} size mismatch"

            # Test class counts match corresponding run class counts exactly
            for c in (0, 1):
                expected_count = int(np.sum((groups == k) & (y == c)))
                actual_count = int(np.sum(y[te] == c))
                assert actual_count == expected_count, (
                    f"Repeat {r_idx} fold {k} class {c} count mismatch: "
                    f"expected {expected_count}, got {actual_count}"
                )

            repeat_tested.extend(te)

        # Union of test sets covers all trials with zero overlap
        assert sorted(repeat_tested) == list(range(len(y))), (
            f"Repeat {r_idx} test sets do not form a complete disjoint partition"
        )


def test_d1m_matched_k_stratification():
    """Verify that D1m creates k folds with balanced class proportions."""
    y = np.array([0] * 20 + [1] * 25)
    k = 3
    repeats = sp.kfold_repeats(y, k=k, stratified=True, repeats=3, seed=0)

    for r_idx, folds in enumerate(repeats):
        assert len(folds) == k
        all_tested = []
        for fold_idx, (tr, te) in enumerate(folds):
            assert set(tr).isdisjoint(set(te))
            all_tested.extend(te)
            # Check non-empty classes in both train and test
            assert len(np.unique(y[tr])) == 2
            assert len(np.unique(y[te])) == 2
        assert sorted(all_tested) == list(range(len(y)))


def test_pipeline_estimator_freshness_between_folds():
    """Verify that evaluate_repeats instantiates fresh, independent model instances per fold."""
    spec = DECODERS["csp_lda"]
    csp_factory = get_csp_factory("rank_safe")

    pipe1 = spec.build(csp_factory)
    pipe2 = spec.build(csp_factory)

    assert pipe1 is not pipe2, "Pipelines must be distinct objects"
    assert pipe1.named_steps["csp"] is not pipe2.named_steps["csp"], "CSP objects must be distinct"
    assert pipe1.named_steps["clf"] is not pipe2.named_steps["clf"], "Classifier objects must be distinct"

    # Fit pipe1 on dummy data
    X_dummy = np.random.randn(10, 8, 50)
    y_dummy = np.array([0, 1] * 5)
    pipe1.fit(X_dummy, y_dummy)

    # pipe2 must remain completely unfitted
    assert not hasattr(pipe2.named_steps["clf"], "classes_")
    assert not hasattr(pipe2.named_steps["csp"], "filters_")


def test_p1_supervised_leakage_on_null_noise():
    """Verify that P1 (global CSP) induces artificial optimistic inflation on pure noise data.

    On random Gaussian noise where no genuine class-discriminative signal exists:
    - Clean LORO (D3) must yield chance-level decoding accuracy (~50%).
    - Leaky P1 (global CSP on all trials) must yield inflated accuracy (>60-70%).
    """
    rng = np.random.default_rng(42)
    n_trials = 45
    n_channels = 16
    n_times = 100

    # Pure Gaussian noise data
    X = rng.standard_normal((n_trials, n_channels, n_times))
    y = np.array([0, 1] * 22 + [0])
    runs = np.array([0] * 15 + [1] * 15 + [2] * 15)
    times = np.linspace(0.0, 4.0, n_times)
    order = np.arange(n_trials)
    sessions = np.zeros(n_trials, dtype=int)

    spec = DECODERS["csp_lda"]
    csp_factory = get_csp_factory("rank_safe")

    ctx = Ctx(
        X=X, y=y, runs=runs, sessions=sessions, order=order, times=times,
        spec=spec, csp_factory=csp_factory, seed=0,
        n_repeats=1, n_repeats_matched=1, base_window=(0.5, 3.5)
    )

    # Clean D3 evaluation
    res_d3 = d3_loro(ctx, dose=None)
    acc_d3 = res_d3["acc_pooled"]

    # Leaky P1 evaluation
    res_p1 = p1_csp_on_all(ctx, dose=None)
    acc_p1 = res_p1["acc_pooled"]

    # D3 should be near chance on pure noise
    assert abs(acc_d3 - 0.50) < 0.20, f"Clean D3 accuracy {acc_d3:.3f} should be near chance"

    # P1 must show significant optimistic inflation over D3
    assert acc_p1 > acc_d3, f"P1 accuracy ({acc_p1:.3f}) must exceed D3 accuracy ({acc_d3:.3f}) on noise"
    assert acc_p1 >= 0.70, f"P1 accuracy ({acc_p1:.3f}) on noise should be heavily inflated (>= 0.70)"
