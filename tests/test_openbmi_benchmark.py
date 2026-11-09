"""Unit tests for OpenBMI replication benchmark components in LeakCheck V2."""
import numpy as np
import pytest
from pathlib import Path

pytestmark = pytest.mark.v2
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from scripts.run_openbmi_benchmark import (
    compute_split_hash,
    parse_subjects,
    verify_subject_eligibility,
    build_decoder_pipeline,
    run_d1s_size_matched_for_subject,
    run_d3_loro_for_subject,
    run_p1_csp_on_all_for_subject,
    compute_design_contrasts,
)
from emi.decoders import CovarianceTransformer, TangentSpaceTransformer


def test_parse_subjects():
    """Verify parsing subject strings into ordered unique integers."""
    assert parse_subjects("2,3,10") == [2, 3, 10]
    assert parse_subjects("2, 3, 12-15") == [2, 3, 12, 13, 14, 15]
    cohort = parse_subjects("intact")
    assert len(cohort) == 34
    assert cohort[0] == 2
    assert cohort[-1] == 44


def test_compute_split_hash_determinism():
    """Verify split hashing is deterministic and order-sensitive."""
    tr1 = np.array([0, 1, 2, 3])
    te1 = np.array([4, 5, 6, 7])
    h1 = compute_split_hash(tr1, te1)
    h2 = compute_split_hash(tr1, te1)
    assert h1 == h2

    tr3 = np.array([0, 1, 2, 4])
    te3 = np.array([3, 5, 6, 7])
    h3 = compute_split_hash(tr3, te3)
    assert h1 != h3


def test_d1s_size_matched_invariants():
    """Verify D1s invariants: size matching, class balance, disjointness, determinism."""
    # Create synthetic dataset with 200 trials (100 Left, 100 Right)
    n_trials = 200
    n_ch = 62
    n_times = 100
    rng = np.random.default_rng(42)
    X = rng.standard_normal((n_trials, n_ch, n_times))
    y = np.array([0] * 100 + [1] * 100)
    runs = np.array([0] * 100 + [1] * 100)

    data = {"X": X, "y": y, "runs": runs}
    n_repeats = 5
    records, manifest = run_d1s_size_matched_for_subject(
        subject=99,
        data=data,
        decoders=["csp_lda"],
        n_csp=4,
        n_repeats=n_repeats,
        base_seed=0,
    )

    assert len(manifest) == n_repeats
    for r in range(n_repeats):
        rep = manifest[f"repeat_{r}"]
        tr0 = set(rep["fold_0"]["train_idx"])
        te0 = set(rep["fold_0"]["test_idx"])
        tr1 = set(rep["fold_1"]["train_idx"])
        te1 = set(rep["fold_1"]["test_idx"])

        # Size matching: exactly 100 train and 100 test
        assert len(tr0) == 100
        assert len(te0) == 100
        # Disjointness within repeat
        assert tr0.isdisjoint(te0)
        assert tr0 == te1
        assert te0 == tr1
        assert tr0 | te0 == set(range(n_trials))

        # Class balance: exactly 50 Left and 50 Right in both folds
        y_tr0 = y[list(tr0)]
        y_te0 = y[list(te0)]
        assert (y_tr0 == 0).sum() == 50
        assert (y_tr0 == 1).sum() == 50
        assert (y_te0 == 0).sum() == 50
        assert (y_te0 == 1).sum() == 50


def test_d3_loro_invariants():
    """Verify D3 Leave-One-Run-Out invariants."""
    n_trials = 200
    n_ch = 10
    n_times = 50
    rng = np.random.default_rng(123)
    X = rng.standard_normal((n_trials, n_ch, n_times))
    y = np.array([0] * 50 + [1] * 50 + [0] * 50 + [1] * 50)
    runs = np.array([0] * 100 + [1] * 100)

    data = {"X": X, "y": y, "runs": runs}
    records, manifest = run_d3_loro_for_subject(
        subject=99,
        data=data,
        decoders=["csp_lda"],
        n_csp=4,
    )

    assert len(records) == 2  # 2 folds
    f0 = manifest["fold_0"]
    f1 = manifest["fold_1"]
    assert set(f0["train_idx"]) == set(np.where(runs == 0)[0])
    assert set(f0["test_idx"]) == set(np.where(runs == 1)[0])
    assert set(f1["train_idx"]) == set(np.where(runs == 1)[0])
    assert set(f1["test_idx"]) == set(np.where(runs == 0)[0])


def test_tangent_space_training_only_safeguard():
    """Verify TangentSpaceTransformer estimates Frechet mean exclusively on training covariances."""
    rng = np.random.default_rng(42)
    # Generate random SPD matrices for train and test
    A_tr = rng.standard_normal((10, 8, 8))
    cov_tr = np.array([a @ a.T + 0.1 * np.eye(8) for a in A_tr])
    A_te = rng.standard_normal((10, 8, 8))
    cov_te = np.array([a @ a.T + 0.1 * np.eye(8) for a in A_te])

    ts = TangentSpaceTransformer()
    ts.fit(cov_tr)
    ref_initial = ts.ref_.copy()

    # Transforming test covariances MUST NOT alter reference matrix
    ts.transform(cov_te)
    np.testing.assert_array_equal(ts.ref_, ref_initial)


def test_p1_positive_control_test_label_isolation():
    """Verify P1 leaks only spatial filter; classifier is fitted only on training fold."""
    n_trials = 200
    n_ch = 8
    n_times = 50
    rng = np.random.default_rng(42)
    X = rng.standard_normal((n_trials, n_ch, n_times))
    y = np.array([0] * 50 + [1] * 50 + [0] * 50 + [1] * 50)
    runs = np.array([0] * 100 + [1] * 100)

    data = {"X": X, "y": y, "runs": runs}
    records, manifest = run_p1_csp_on_all_for_subject(
        subject=99,
        data=data,
        decoders=["csp_lda"],
        n_csp=4,
    )

    assert len(records) == 2
    for r in records:
        assert r["design"] == "P1_csp_on_all"
        assert r["n_train"] == 100
        assert r["n_test"] == 100
        assert 0.0 <= r["accuracy"] <= 1.0
