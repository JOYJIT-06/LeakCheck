"""Unit and integration tests for expanded decoders, canonical leakage mechanisms,
and generalized multi-run benchmark protocols in LeakCheck V2.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import stats
from sklearn.pipeline import Pipeline

from emi.decoders import (
    DECODERS,
    DEFAULT_FILTER_BANKS,
    ChannelScaler,
    ChannelSelector,
    CovarianceTransformer,
    FBCSP,
    FilterBankCSP,
    TangentSpaceTransformer,
    build_decoder_pipeline,
    get_csp_factory,
)
from emi.leakcheck import (
    Ctx,
    DESIGN_FUNCS,
    PRESETS,
    REFERENCE,
    audit_subject,
    p1_csp_on_all,
    p2_ica_inside,
    p2_ica_on_all,
    p5_scale_inside,
    p5_scale_on_all,
    p7_select_inside,
    p7_select_on_all,
)
from emi.splitters import (
    kfold_repeats,
    loro_splits,
    size_matched_random_repeats,
    validate_splits,
)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------
@pytest.fixture
def synthetic_epochs():
    """Create reproducible synthetic 2-class EEG epochs."""
    rng = np.random.default_rng(42)
    n_trials = 60
    n_channels = 16
    n_times = 250
    sfreq = 250.0

    y = np.array([0] * (n_trials // 2) + [1] * (n_trials // 2))
    # 3 distinct runs of 20 trials each
    runs = np.array([0] * 20 + [1] * 20 + [2] * 20)
    rng.shuffle(y)

    X = rng.standard_normal((n_trials, n_channels, n_times)) * 15.0
    for i in range(n_trials):
        if y[i] == 1:
            X[i, 0, :] += np.sin(np.linspace(0, 4 * np.pi, n_times)) * 8.0
        else:
            X[i, 1, :] += np.sin(np.linspace(0, 4 * np.pi, n_times)) * 8.0

    times = np.linspace(0, n_times / sfreq, n_times)
    return {"X": X, "y": y, "runs": runs, "times": times, "sfreq": sfreq}


# -----------------------------------------------------------------------------
# Decoder Unit Tests
# -----------------------------------------------------------------------------
def test_all_five_decoders_registered():
    """Verify that all 5 canonical decoders are registered in DECODERS."""
    expected = {"csp_lda", "csp_svm", "csp_lr", "ts_lr", "fbcsp"}
    assert expected.issubset(set(DECODERS.keys()))


@pytest.mark.parametrize("dec_name", ["csp_lda", "csp_svm", "csp_lr", "ts_lr", "fbcsp"])
def test_decoder_pipeline_fit_predict_score(dec_name, synthetic_epochs):
    """Verify build_decoder_pipeline produces valid Pipelines with fit, predict, and score."""
    X, y = synthetic_epochs["X"], synthetic_epochs["y"]
    pipe = build_decoder_pipeline(dec_name, n_csp=4, sfreq=synthetic_epochs["sfreq"])
    assert isinstance(pipe, Pipeline)

    pipe.fit(X, y)
    y_pred = pipe.predict(X)
    assert y_pred.shape == y.shape
    assert set(np.unique(y_pred)).issubset({0, 1})

    acc = pipe.score(X, y)
    assert 0.0 <= acc <= 1.0

    # Decision scores check
    if hasattr(pipe, "predict_proba"):
        proba = pipe.predict_proba(X)
        assert proba.shape == (len(y), 2)
        assert np.allclose(proba.sum(axis=1), 1.0)
    if hasattr(pipe, "decision_function"):
        df = pipe.decision_function(X)
        assert df.shape == (len(y),) or df.shape == (len(y), 1)


def test_fbcsp_estimator_interface(synthetic_epochs):
    """Verify FBCSP standalone estimator implements full scikit-learn interface."""
    X, y = synthetic_epochs["X"], synthetic_epochs["y"]
    model = FBCSP(sfreq=synthetic_epochs["sfreq"], n_components=4, k_features=6)

    model.fit(X, y)
    y_pred = model.predict(X)
    assert y_pred.shape == y.shape

    feats = model.transform(X)
    assert feats.shape == (len(y), 6)

    acc = model.score(X, y)
    assert 0.0 <= acc <= 1.0

    df = model.decision_function(X)
    assert df.shape == (len(y),)


def test_fbcsp_nyquist_pruning():
    """Verify FilterBankCSP prunes filter bands exceeding Nyquist frequency gracefully."""
    rng = np.random.default_rng(123)
    # Low sampling rate: sfreq = 32 Hz -> Nyquist = 16 Hz
    X = rng.standard_normal((10, 8, 128))
    y = np.array([0] * 5 + [1] * 5)

    # 9 default bands (up to 40 Hz) should be pruned to those <= 16 Hz
    fb = FilterBankCSP(sfreq=32.0, n_components=2)
    fb.fit(X, y)
    assert len(fb.active_bands_) > 0
    for low, high in fb.active_bands_:
        assert high <= 16.0

    feats = fb.transform(X)
    assert feats.shape[0] == 10
    assert feats.shape[1] == len(fb.active_bands_) * 2


def test_covariance_transformer_shrinkage():
    """Verify CovarianceTransformer with OAS and Ledoit-Wolf handles CAR rank-deficient data."""
    rng = np.random.default_rng(42)
    n_trials, n_channels, n_times = 15, 32, 500
    X = rng.standard_normal((n_trials, n_channels, n_times))
    # Apply Common Average Reference (CAR), reducing rank by 1
    X_car = X - X.mean(axis=1, keepdims=True)

    for est in ["oas", "ledoit_wolf", "empirical"]:
        cov_trans = CovarianceTransformer(estimator=est)
        covs = cov_trans.transform(X_car)
        assert covs.shape == (n_trials, n_channels, n_channels)
        # Every covariance matrix must be strictly positive definite
        for c in covs:
            min_eig = np.min(np.linalg.eigvalsh(c))
            assert min_eig > 0.0, f"Covariance matrix is singular or negative definite under {est}"

        # Feed to TangentSpaceTransformer
        ts = TangentSpaceTransformer().fit_transform(covs)
        assert ts.shape[0] == n_trials
        assert not np.isnan(ts).any(), f"Tangent space projection produced NaNs under {est}"


# -----------------------------------------------------------------------------
# Multi-Run Splitter Protocol Tests (Arbitrary K >= 2)
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("k_runs", [2, 3, 4, 6])
def test_multi_run_loro_splits_no_dropped_runs(k_runs):
    """Verify LORO splits partition arbitrary K runs without dropping any trials or runs."""
    trials_per_run = 20
    runs = np.repeat(np.arange(k_runs), trials_per_run)
    y = np.tile([0, 1], len(runs) // 2)

    repeats = loro_splits(runs)
    assert len(repeats) == 1
    folds = repeats[0]
    assert len(folds) == k_runs, f"Expected {k_runs} folds, got {len(folds)}"

    tested_indices = []
    for tr, te in folds:
        assert len(np.intersect1d(tr, te)) == 0, "Train and test overlap"
        assert len(te) == trials_per_run
        assert len(tr) == len(runs) - trials_per_run
        # The held-out run must not appear in train
        held_out = np.unique(runs[te])
        assert len(held_out) == 1
        assert held_out[0] not in np.unique(runs[tr])
        tested_indices.extend(te)

    # Every trial must be tested exactly once across the folds
    assert sorted(tested_indices) == list(range(len(runs)))
    assert validate_splits(repeats, y, groups=runs)


@pytest.mark.parametrize("k_runs", [2, 3, 4, 6])
def test_multi_run_size_matched_random_repeats(k_runs):
    """Verify size_matched_random_repeats matches LORO fold sizes and disjoint partitions for K runs."""
    trials_per_run = 30
    runs = np.repeat(np.arange(k_runs), trials_per_run)
    y = np.tile([0, 1, 0], len(runs) // 3)

    n_repeats = 3
    repeats = size_matched_random_repeats(y, runs, repeats=n_repeats, seed=42)
    assert len(repeats) == n_repeats

    for rep_idx, folds in enumerate(repeats):
        assert len(folds) == k_runs
        all_test_in_rep = []
        for fold_idx, (tr, te) in enumerate(folds):
            assert len(np.intersect1d(tr, te)) == 0
            assert len(te) == trials_per_run
            assert len(tr) == len(runs) - trials_per_run
            all_test_in_rep.extend(te)
        # In each repeat, test sets must form a complete disjoint partition
        assert sorted(all_test_in_rep) == list(range(len(runs)))


# -----------------------------------------------------------------------------
# Canonical Leakage Injection Tests
# -----------------------------------------------------------------------------
def test_canonical_leakage_mechanisms_in_leakcheck(synthetic_epochs):
    """Verify P1, P2, P5, and P7 execute and produce valid metrics in leakcheck.py."""
    X, y, runs, times = (
        synthetic_epochs["X"],
        synthetic_epochs["y"],
        synthetic_epochs["runs"],
        synthetic_epochs["times"],
    )

    spec = DECODERS["csp_lda"]
    factory = get_csp_factory("rank_safe")
    ctx = Ctx(
        X, y, runs, np.zeros_like(y), np.arange(len(y)), times, spec, factory,
        seed=42, n_repeats=2, n_repeats_matched=2, base_window=(0.0, 1.0)
    )

    # 1. P1: CSP on all
    m_p1 = p1_csp_on_all(ctx, "")
    assert np.isfinite(m_p1["acc_pooled"])
    assert 0.0 <= m_p1["acc_pooled"] <= 1.0

    # 2. P2: ICA on all vs ICA inside
    m_p2_leaky = p2_ica_on_all(ctx, "8")
    m_p2_clean = p2_ica_inside(ctx, "8")
    assert np.isfinite(m_p2_leaky["acc_pooled"])
    assert np.isfinite(m_p2_clean["acc_pooled"])

    # 3. P5: Scale on all vs Scale inside
    m_p5_leaky = p5_scale_on_all(ctx, "")
    m_p5_clean = p5_scale_inside(ctx, "")
    assert np.isfinite(m_p5_leaky["acc_pooled"])
    assert np.isfinite(m_p5_clean["acc_pooled"])

    # 4. P7: Select on all vs Select inside
    m_p7_leaky = p7_select_on_all(ctx, "16")
    m_p7_clean = p7_select_inside(ctx, "16")
    assert np.isfinite(m_p7_leaky["acc_pooled"])
    assert np.isfinite(m_p7_clean["acc_pooled"])


def test_leakcheck_audit_subject_with_all_decoders(synthetic_epochs):
    """Verify audit_subject runs with expanded decoders and canonical presets."""
    X, y, runs, times = (
        synthetic_epochs["X"],
        synthetic_epochs["y"],
        synthetic_epochs["runs"],
        synthetic_epochs["times"],
    )

    df = audit_subject(
        X, y, runs, times, subject=1,
        decoders=("csp_lda", "csp_svm", "csp_lr", "fbcsp"),
        designs="quick",
        n_null=0,
        n_repeats=1,
        n_repeats_matched=1,
        csp_factory=get_csp_factory("rank_safe"),
        base_window=(0.0, 1.0),
    )
    assert not df.empty
    assert set(df["decoder"].unique()) == {"csp_lda", "csp_svm", "csp_lr", "fbcsp"}
    assert set(df["design"].unique()) == {"D3_loro", "D1m_matched_k", "P1_csp_on_all"}


# -----------------------------------------------------------------------------
# End-to-End Unified Benchmark CLI Smoke Test
# -----------------------------------------------------------------------------
def test_unified_benchmark_cli_all_decoders_and_designs(tmp_path):
    """Verify scripts/run_unified_benchmark.py end-to-end with all 5 decoders and 7 designs."""
    repo_root = Path(__file__).resolve().parent.parent
    script_path = repo_root / "scripts" / "run_unified_benchmark.py"
    out_dir = tmp_path / "unified_smoke_out"

    cmd = [
        sys.executable,
        str(script_path),
        "--dataset", "bnci2014_001",
        "--subjects", "1",
        "--decoders", "csp_lda,csp_svm,csp_lr,ts_lr,fbcsp",
        "--designs", "D3,D1s,D1m,P1,P2,P5,P7",
        "--synthetic",
        "--smoke",
        "--outdir", str(out_dir),
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Unified benchmark CLI failed: {res.stderr}\n{res.stdout}"

    # 1. Level 1 Fold Metrics
    fold_file = out_dir / "fold_metrics.csv"
    assert fold_file.is_file()
    fold_df = pd.read_csv(fold_file)
    req_fold_cols = [
        "dataset", "subject_id", "design", "fold_id", "split_hash",
        "accuracy", "balanced_accuracy", "auroc", "f1",
        "n_train", "n_test", "train_time_s", "test_time_s"
    ]
    for col in req_fold_cols:
        assert col in fold_df.columns, f"Missing required Level 1 column: {col}"

    assert set(fold_df["decoder"].unique()) == {"csp_lda", "csp_svm", "csp_lr", "ts_lr", "fbcsp"}
    assert "P1_csp_on_all" in set(fold_df["design"].unique())
    assert "P1_ts_on_all" in set(fold_df["design"].unique())

    # 2. Level 2 Participant Metrics
    part_file = out_dir / "participant_metrics.csv"
    assert part_file.is_file()
    part_df = pd.read_csv(part_file)
    assert "dataset" in part_df.columns
    assert "mean_accuracy" in part_df.columns
    assert "sem_accuracy" in part_df.columns

    # 3. Level 3 Design Comparisons
    comp_file = out_dir / "design_comparisons.csv"
    assert comp_file.is_file()
    comp_df = pd.read_csv(comp_file)
    req_comp_cols = [
        "dataset", "contrast", "estimator", "hodges_lehmann_delta",
        "bca_ci_lower", "bca_ci_upper", "wilcoxon_w", "raw_p_value",
        "holm_p_value", "cohens_dz", "rank_biserial"
    ]
    for col in req_comp_cols:
        assert col in comp_df.columns, f"Missing required Level 3 column: {col}"

    # 4. Manifest
    manifest_file = out_dir / "benchmark_manifest.json"
    assert manifest_file.is_file()
    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert "sha256_metrics" in manifest
    assert "fold_metrics" in manifest["sha256_metrics"]
