import numpy as np

from emi import splitters as sp
from tests.helpers import make_data


def test_loro_has_no_group_overlap_and_covers_all_trials():
    X, y, runs, _ = make_data()
    reps = sp.loro_splits(runs)
    assert sp.validate_splits(reps, y, groups=runs)
    assert len(reps) == 1 and len(reps[0]) == 3
    assert sorted(np.concatenate([te for _, te in reps[0]])) == list(range(len(y)))


def test_kfold_repeats_count_and_no_overlap():
    X, y, runs, _ = make_data()
    reps = sp.kfold_repeats(y, k=5, stratified=True, repeats=4, seed=1)
    assert len(reps) == 4 and all(len(f) == 5 for f in reps)
    assert sp.validate_splits(reps, y)


def test_size_matched_split_has_same_sizes_and_class_counts_as_loro():
    X, y, runs, _ = make_data()
    loro = sp.loro_splits(runs)[0]
    for folds in sp.size_matched_random_repeats(y, runs, repeats=5, seed=0):
        for (tr_l, te_l), (tr_m, te_m) in zip(loro, folds):
            assert len(te_m) == len(te_l) and len(tr_m) == len(tr_l)
            assert y[te_m].sum() == y[te_l].sum()
        sp.validate_splits([folds], y)


def test_size_matched_split_really_mixes_runs():
    X, y, runs, _ = make_data(per_run=20)
    mixed = False
    for folds in sp.size_matched_random_repeats(y, runs, repeats=3, seed=2):
        for tr, te in folds:
            if len(np.unique(runs[te])) > 1:
                mixed = True
    assert mixed


def test_chrono_holdout_respects_time_order_and_gap():
    n = 45
    order = np.arange(n)
    for gap in (0, 2, 4):
        reps = sp.chrono_holdout(n, 1 / 3, gap, order)
        (tr, te), = reps[0]
        assert tr.max() < te.min()
        assert te.min() - tr.max() - 1 == gap
        y = np.tile([0, 1], n)[:n]
        assert sp.validate_splits(reps, y, order=order, min_gap=gap)


def test_chrono_uses_given_order_not_array_position():
    n = 12
    order = np.arange(n)[::-1].copy()          # trial 0 is the LAST in time
    (tr, te), = sp.chrono_holdout(n, 1 / 3, 0, order)[0]
    assert set(te) == set(range(0, 4))         # the latest 4 trials sit at the start of the array


def test_forward_chain_expands_and_never_tests_on_the_past():
    reps = sp.forward_chain(40, n_splits=3, gap=1)
    folds = reps[0]
    assert len(folds) == 3
    sizes = [len(tr) for tr, _ in folds]
    assert sizes == sorted(sizes) and len(set(sizes)) == 3
    for tr, te in folds:
        assert tr.max() < te.min()


def test_validate_rejects_overlap_and_single_class_training():
    y = np.array([0, 1, 0, 1, 0, 1])
    bad = [[(np.array([0, 1, 2]), np.array([2, 3]))]]
    try:
        sp.validate_splits(bad, y)
    except ValueError:
        pass
    else:
        raise AssertionError("overlap not detected")
    one_class = [[(np.array([0, 2, 4]), np.array([1, 3, 5]))]]
    try:
        sp.validate_splits(one_class, y)
    except ValueError:
        return
    raise AssertionError("single-class training fold not detected")


def test_session_split_needs_two_sessions():
    try:
        sp.session_splits(np.zeros(10, int))
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_sklearn_style_wrappers():
    X, y, runs, _ = make_data()
    s = sp.GappedChronologicalSplit(1 / 3, gap=2)
    assert len(list(s.split(X))) == 1
    m = sp.SizeMatchedRandomSplit(n_repeats=2, seed=0)
    assert len(list(m.split(X, y, runs))) == m.get_n_splits(X, y, runs) == 6


# ---- v0.3: D1s is a disjoint partition ---------------------------------------------------------
def test_size_matched_split_is_a_disjoint_partition():
    """Every trial is tested exactly once per repeat (v0.2 reused trials and left others untested)."""
    rng = np.random.default_rng(0)
    runs = np.repeat([0, 1, 2], 15)                          # 15 trials per run: odd, so classes are unbalanced
    y = np.concatenate([rng.permutation(np.r_[np.zeros(7, int), np.ones(8, int)]) for _ in range(3)])
    for folds in sp.size_matched_random_repeats(y, runs, repeats=10, seed=3):
        tests = np.concatenate([te for _, te in folds])
        assert len(tests) == len(y)
        assert len(np.unique(tests)) == len(y)               # no duplicates, nothing missing
        for (tr, te), g in zip(folds, np.unique(runs)):
            assert len(te) == 15 and y[te].sum() == y[runs == g].sum()
            assert len(np.intersect1d(tr, te)) == 0


def test_size_matched_split_differs_between_repeats():
    X, y, runs, _ = make_data(per_run=20)
    reps = sp.size_matched_random_repeats(y, runs, repeats=4, seed=0)
    firsts = [tuple(folds[0][1]) for folds in reps]
    assert len(set(firsts)) > 1
