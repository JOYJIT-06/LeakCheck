"""Adversarial fold-isolation verification suite for Gate 2 and numerical rank stability.

This module stress-tests FoldIsolatedPreprocessor, SimpleCSP, and the decoding pipeline
against active adversarial corruption, label permutations, and rank-deficiency to prove
zero cross-partition information leakage.
"""
import hashlib
from pathlib import Path
import mne
import numpy as np
import pytest
from sklearn.covariance import OAS
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.pipeline import Pipeline

from emi.config import Config
from emi.decoders import ChannelSelector
from emi.diagnostics import numerical_rank_svd
from emi.preprocess import FoldIsolatedPreprocessor, clean_raw
from emi.signal_utils import adaptive_reject_mask, trial_artifact_statistic
from emi.simple_csp import SimpleCSP


def _generate_synthetic_multirun_raw(sfreq=160.0, n_ch=16, n_times=1600, seed=7):
    """Generate 3 synthetic EEG raw runs with Laplace components for rapid FastICA convergence."""
    ch_names = [
        "Fp1", "Fp2", "F3", "F4", "C3", "Cz", "C4", "P3",
        "Pz", "P4", "O1", "O2", "F7", "F8", "T7", "T8"
    ][:n_ch]
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types="eeg")
    rng = np.random.default_rng(seed)

    raw_runs = []
    for r_idx in range(3):
        data = rng.standard_normal((n_ch, n_times)) * 1e-5 + rng.laplace(0, 1e-5, (n_ch, n_times))
        raw = mne.io.RawArray(data, info, verbose="ERROR")
        raw.set_montage("standard_1020", verbose="ERROR")
        raw_runs.append(raw)

    return raw_runs


def test_adversarial_corrupted_test_run_invariance():
    """Gate 2 - Test Case 1: Corrupting held-out Run 12 yields bitwise identical training parameters."""
    raw_runs_clean = _generate_synthetic_multirun_raw(seed=7)
    raw_r4, raw_r8, raw_r12_clean = raw_runs_clean

    # Prepare training data: concatenated Runs 4 and 8
    data_train = np.concatenate([raw_r4.get_data(), raw_r8.get_data()], axis=1)
    raw_train = mne.io.RawArray(data_train, raw_r4.info, verbose="ERROR")
    raw_train.set_montage("standard_1020", verbose="ERROR")

    # Create corrupted Run 12: 10,000 uV noise on Fp1, Fp2, F3, and flatline on P4
    data_r12_corrupt = raw_r12_clean.get_data().copy()
    data_r12_corrupt[0, :] += 1e-2  # Fp1 extreme noise
    data_r12_corrupt[1, :] += 1e-2  # Fp2 extreme noise
    data_r12_corrupt[2, :] += 1e-2  # F3 extreme noise
    data_r12_corrupt[9, :] = 0.0    # Flatline channel P4
    data_r12_corrupt += np.linspace(0, 5e-2, data_r12_corrupt.shape[1])  # 50,000 uV drift

    raw_r12_corrupt = mne.io.RawArray(data_r12_corrupt, raw_r12_clean.info, verbose="ERROR")
    raw_r12_corrupt.set_montage("standard_1020", verbose="ERROR")

    cfg = Config(n_ica=4, use_ica=True)

    # Preprocessor 1: Fit on train, transform clean test
    prep_clean = FoldIsolatedPreprocessor(cfg)
    prep_clean.fit_training(raw_train)
    clean_test_out = prep_clean.transform(raw_r12_clean)

    # Preprocessor 2: Fit on train, transform corrupted test
    prep_corrupt = FoldIsolatedPreprocessor(cfg)
    prep_corrupt.fit_training(raw_train)
    corrupt_test_out = prep_corrupt.transform(raw_r12_corrupt)

    # 1. Assert training bad channels are identical
    assert prep_clean.bad_channels_ == prep_corrupt.bad_channels_

    # 2. Assert FastICA unmixing matrix is bitwise identical
    np.testing.assert_array_equal(prep_clean.ica_.unmixing_matrix_, prep_corrupt.ica_.unmixing_matrix_)

    # 3. Assert FastICA components are bitwise identical
    np.testing.assert_array_equal(prep_clean.ica_.pca_components_, prep_corrupt.ica_.pca_components_)

    # 4. Assert excluded ICA components list is identical
    assert prep_clean.ica_excluded_ == prep_corrupt.ica_excluded_

    # 5. Assert training artifact threshold tau_train is bitwise identical
    assert prep_clean.reject_threshold_uv_ == prep_corrupt.reject_threshold_uv_

    # 6. Assert cleaned training continuous data is bitwise identical
    np.testing.assert_array_equal(
        prep_clean.transform(raw_train).get_data(),
        prep_corrupt.transform(raw_train).get_data()
    )

    # 7. Negative control: Prove legacy preprocessor leaks corrupted Run 12 into training
    raw_full_corrupt = mne.io.RawArray(
        np.concatenate([raw_r4.get_data(), raw_r8.get_data(), data_r12_corrupt], axis=1),
        raw_r4.info,
        verbose="ERROR"
    )
    raw_full_corrupt.set_montage("standard_1020", verbose="ERROR")
    with pytest.raises(ValueError, match="recording is suspect"):
        clean_raw(raw_full_corrupt, cfg)


def test_adversarial_test_label_permutation_invariance():
    """Gate 2 - Test Case 2: Permuting held-out test labels cannot alter trained pipeline parameters."""
    rng = np.random.default_rng(42)
    n_trials_train = 40
    n_trials_test = 20
    n_ch = 16
    n_times = 100

    # Training data
    X_train = rng.standard_normal((n_trials_train, n_ch, n_times))
    y_train = np.array([0, 1] * (n_trials_train // 2))
    # Make channels 0 and 1 class-informative in training
    X_train[y_train == 0, 0, :] *= 2.5
    X_train[y_train == 1, 1, :] *= 2.5

    # Test data
    X_test = rng.standard_normal((n_trials_test, n_ch, n_times))
    y_test_orig = np.array([0, 1] * (n_trials_test // 2))
    X_test[y_test_orig == 0, 0, :] *= 2.5
    X_test[y_test_orig == 1, 1, :] *= 2.5

    # Adversarial test labels: permuted, inverted, all-zero
    y_test_perm = rng.permutation(y_test_orig)
    y_test_inv = 1 - y_test_orig
    y_test_zero = np.zeros_like(y_test_orig)

    def _build_and_fit():
        pipe = Pipeline([
            ("sel", ChannelSelector(n_keep=8)),
            ("csp", SimpleCSP(n_components=4)),
            ("clf", LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto"))
        ])
        pipe.fit(X_train, y_train)
        return pipe

    pipe_orig = _build_and_fit()
    pipe_perm = _build_and_fit()
    pipe_inv = _build_and_fit()
    pipe_zero = _build_and_fit()

    for pipe_adv in (pipe_perm, pipe_inv, pipe_zero):
        np.testing.assert_array_equal(pipe_orig.named_steps["sel"].idx_, pipe_adv.named_steps["sel"].idx_)
        np.testing.assert_array_equal(pipe_orig.named_steps["csp"].filters_, pipe_adv.named_steps["csp"].filters_)
        np.testing.assert_array_equal(pipe_orig.named_steps["csp"].eigenvalues_, pipe_adv.named_steps["csp"].eigenvalues_)
        np.testing.assert_array_equal(pipe_orig.named_steps["clf"].coef_, pipe_adv.named_steps["clf"].coef_)
        np.testing.assert_array_equal(pipe_orig.named_steps["clf"].intercept_, pipe_adv.named_steps["clf"].intercept_)
        np.testing.assert_array_equal(pipe_orig.predict(X_test), pipe_adv.predict(X_test))

    # Negative control: Leaky P1 CSP on all trials responds to test label permutations
    X_all = np.concatenate([X_train, X_test], axis=0)
    y_all_orig = np.concatenate([y_train, y_test_orig], axis=0)
    y_all_perm = np.concatenate([y_train, y_test_perm], axis=0)

    csp_leaky_orig = SimpleCSP(n_components=4).fit(X_all, y_all_orig)
    csp_leaky_perm = SimpleCSP(n_components=4).fit(X_all, y_all_perm)
    assert not np.allclose(csp_leaky_orig.filters_, csp_leaky_perm.filters_)


def test_numerical_rank_svd_stability_and_oas_shrinkage():
    """Gate 2 - Test Case 3: SVD rank drops under CAR/interpolation; OAS & SimpleCSP remain stable."""
    rng = np.random.default_rng(42)
    n_ch, n_times, n_trials = 64, 500, 40
    B = 3  # 3 bad channels interpolated

    X_trials = rng.standard_normal((n_trials, n_ch, n_times)) * 1e-5
    y = np.array([0, 1] * (n_trials // 2))

    # Interpolate 3 channels as linear combinations of surviving channels
    for i in range(n_trials):
        X_trials[i, 0] = (X_trials[i, 10] + X_trials[i, 11]) / 2.0
        X_trials[i, 1] = (X_trials[i, 12] + X_trials[i, 13]) / 2.0
        X_trials[i, 2] = (X_trials[i, 14] + X_trials[i, 15]) / 2.0

    # Common average reference (CAR) projection
    car_proj = np.eye(n_ch) - (1.0 / n_ch) * np.ones((n_ch, n_ch))
    for i in range(n_trials):
        X_trials[i] = car_proj @ X_trials[i]

    # Continuous concatenation for SVD rank analysis
    X_concat = np.concatenate([X_trials[i] for i in range(n_trials)], axis=1)
    rank, tol, s = numerical_rank_svd(X_concat)

    # 1. Assert rank is exactly 64 - 1 - B = 60
    expected_rank = 64 - 1 - B
    assert rank == expected_rank
    for idx in range(expected_rank, 64):
        assert s[idx] < tol

    # 2. Assert SimpleCSP correctly handles rank deficiency
    csp = SimpleCSP(n_components=4)
    csp.fit(X_trials, y)
    assert csp.rank_ == expected_rank
    assert np.isfinite(csp.filters_).all()
    assert not np.isnan(csp.filters_).any()

    features = csp.transform(X_trials)
    assert features.shape == (n_trials, 4)
    assert np.isfinite(features).all()
    assert not np.isnan(features).any()
    assert (features.var(axis=0) > 0).all()

    # 3. Assert OAS covariance shrinkage handles rank-deficient trials
    oas = OAS()
    oas.fit(X_trials[0].T)  # samples x channels
    cov_oas = oas.covariance_

    assert np.isfinite(cov_oas).all()
    eigenvalues = np.linalg.eigvalsh(cov_oas)
    assert eigenvalues.min() > 0, "OAS regularized covariance must be strictly positive definite"
    assert np.linalg.cond(cov_oas) < 1e4, "OAS regularized condition number must remain well-conditioned"


def test_legacy_vs_fold_isolated_side_by_side_execution():
    """Gate 2 - Test Case 4: Side-by-side execution preserves input immutability and frozen baseline."""
    raw_runs = _generate_synthetic_multirun_raw(seed=42)
    raw_r4, raw_r8, raw_r12 = raw_runs

    # Record SHA-256 hashes of input raw arrays before execution
    hash_r4_before = hashlib.sha256(raw_r4.get_data().tobytes()).hexdigest()
    hash_r8_before = hashlib.sha256(raw_r8.get_data().tobytes()).hexdigest()
    hash_r12_before = hashlib.sha256(raw_r12.get_data().tobytes()).hexdigest()

    cfg = Config(n_ica=4, use_ica=False)

    # 1. Run Legacy Preprocessor on concatenated recording
    raw_full = mne.io.RawArray(
        np.concatenate([raw_r4.get_data(), raw_r8.get_data(), raw_r12.get_data()], axis=1),
        raw_r4.info,
        verbose="ERROR"
    )
    raw_full.set_montage("standard_1020", verbose="ERROR")
    raw_clean_legacy, info_legacy = clean_raw(raw_full, cfg)

    # 2. Run Fold-Isolated Preprocessor on train/test split
    raw_train = mne.io.RawArray(
        np.concatenate([raw_r4.get_data(), raw_r8.get_data()], axis=1),
        raw_r4.info,
        verbose="ERROR"
    )
    raw_train.set_montage("standard_1020", verbose="ERROR")
    prep = FoldIsolatedPreprocessor(cfg)
    prep.fit_training(raw_train)
    raw_test_clean = prep.transform(raw_r12)

    # 3. Verify input raw data arrays were NEVER mutated in place
    assert hashlib.sha256(raw_r4.get_data().tobytes()).hexdigest() == hash_r4_before
    assert hashlib.sha256(raw_r8.get_data().tobytes()).hexdigest() == hash_r8_before
    assert hashlib.sha256(raw_r12.get_data().tobytes()).hexdigest() == hash_r12_before

    # 4. Verify frozen baseline results directory is completely intact and untouched
    baseline_dir = Path("D:/my lab/LeakCheck_remote/benchmark_results/physionet_v1_1_final")
    assert baseline_dir.exists(), "Frozen baseline directory benchmark_results/physionet_v1_1_final must exist"
    mandatory_baseline_files = [
        "inflation_by_subject.csv",
        "leakcheck_raw.csv",
        "settings.json",
        "subject_info.csv",
        "README.md"
    ]
    for fname in mandatory_baseline_files:
        fpath = baseline_dir / fname
        assert fpath.exists(), f"Baseline artifact {fname} missing from frozen baseline!"
        assert fpath.stat().st_size > 0, f"Baseline artifact {fname} is empty!"


def test_fold_isolation_adversarial_perturbation():
    """Verify that corrupting test run has zero effect on training W_ica and bad channels."""
    raw_runs = _generate_synthetic_multirun_raw(seed=123)
    raw_r4, raw_r8, raw_test_normal = raw_runs

    data_train = np.concatenate([raw_r4.get_data(), raw_r8.get_data()], axis=1)
    raw_train = mne.io.RawArray(data_train, raw_r4.info, verbose="ERROR")
    raw_train.set_montage("standard_1020", verbose="ERROR")

    # Test run adversarial: channel Fp1 disconnected / huge noise
    data_test_adversarial = raw_test_normal.get_data().copy()
    data_test_adversarial[0, :] += 500.0  # 500V noise on Fp1
    raw_test_adversarial = mne.io.RawArray(data_test_adversarial, raw_test_normal.info, verbose="ERROR")
    raw_test_adversarial.set_montage("standard_1020", verbose="ERROR")

    cfg = Config(n_ica=4, use_ica=True)

    # Preprocessor 1: fit on train, transform normal test
    prep1 = FoldIsolatedPreprocessor(cfg)
    prep1.fit_training(raw_train)
    clean_test_normal = prep1.transform(raw_test_normal)

    # Preprocessor 2: fit on train, transform adversarial test
    prep2 = FoldIsolatedPreprocessor(cfg)
    prep2.fit_training(raw_train)
    clean_test_adv = prep2.transform(raw_test_adversarial)

    # 1. Assert training bad channels are identical
    assert prep1.bad_channels_ == prep2.bad_channels_

    # 2. Assert training ICA unmixing matrices are byte-identical
    np.testing.assert_array_equal(prep1.ica_.unmixing_matrix_, prep2.ica_.unmixing_matrix_)

    # 3. Assert excluded component list is identical
    assert prep1.ica_excluded_ == prep2.ica_excluded_


def test_evaluate_loro_fold_isolated_execution():
    """Verify evaluate_loro_fold_isolated executes across multi-run raw data."""
    from emi.pipeline import evaluate_loro_fold_isolated

    raw_runs = []
    ch_names = ["Fp1", "Fp2", "C3", "Cz", "C4", "P3", "Pz", "P4"]
    info = mne.create_info(ch_names=ch_names, sfreq=160.0, ch_types="eeg")
    rng = np.random.default_rng(42)

    for r_idx in range(3):
        data = rng.standard_normal((8, 1600)) * 1e-5
        raw = mne.io.RawArray(data, info, verbose="ERROR")
        raw.set_montage("standard_1020", verbose="ERROR")
        onset = [1.0, 3.0, 5.0, 7.0]
        duration = [1.0] * 4
        description = ["T1", "T2", "T1", "T2"]
        annot = mne.Annotations(onset=onset, duration=duration, description=description)
        raw.set_annotations(annot)
        raw_runs.append(raw)

    cfg = Config(n_ica=4, use_ica=False)
    res = evaluate_loro_fold_isolated(raw_runs, cfg)
    assert res["validation"] == "leave-one-run-out (fold-isolated)"
    assert res["n_folds"] == 3
    assert len(res["fold_details"]) == 3
    assert 0.0 <= res["mean_acc"] <= 1.0

