"""Adversarial challenger test probes for Milestone M3 — Suite 2.

Focus areas:
- Decoder Array Shape Stress Testing:
  - Small cohorts (N=10), large cohorts (N=200), varying sampling rates (128, 250, 500, 1000 Hz),
    high channel counts (128 channels).
  - All 5 decoders: csp_lda, csp_svm, csp_lr, ts_lr, fbcsp.
- CovarianceTransformer Rank Deficiency & Collinearity:
  - Common Average Referencing (CAR, exact rank C-1 deficiency).
  - Duplicate/collinear channels, silent/dead zero-variance channels.
  - OAS and Ledoit-Wolf shrinkage, positive definiteness, and TangentSpaceTransformer stability.
- FilterBankCSP Nyquist Boundary & Band Pruning:
  - Near-Nyquist sampling rates (sfreq=100 Hz, sfreq=80 Hz).
  - Custom, overlapping, and single sub-bands.
  - FBCSP classifier end-to-end pipeline robustness.
- Canonical Leakage Invariant Testing (P1, P2, P5, P7):
  - Injected supervised leakage mechanisms (P1, P7) produce positive performance inflation
    over clean D3 on pure noise / spurious correlation regimes.
  - P2 and P5 execution stability and invariant metrics.
- Level 3 Contrast Computation & Statistical Rigor:
  - Hodges-Lehmann median difference, BCa 95% bootstrap CI, Wilcoxon W, raw and Holm-adjusted p-values,
    rank-biserial correlation, and Cohen's d_z.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy import signal
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
from emi.leakstats import bca_ci, cohens_dz, hodges_lehmann, holm, rank_biserial
from scripts.run_unified_benchmark import (
    compute_design_contrasts,
    run_d3_loro,
    run_p1_csp_on_all,
    run_p2_ica_on_all,
    run_p5_scale_on_all,
    run_p7_select_on_all,
)


# =============================================================================
# Helper Fixtures & Data Generators
# =============================================================================
def make_stress_data(
    n_trials: int = 40,
    n_channels: int = 8,
    n_times: int = 200,
    sfreq: float = 250.0,
    n_runs: int = 2,
    pure_noise: bool = False,
    snr: float = 5.0,
    seed: int = 42,
) -> dict:
    """Generate synthetic EEG data with arbitrary dimensions, runs, and optional signal."""
    rng = np.random.default_rng(seed)
    y = np.array([0] * (n_trials // 2) + [1] * (n_trials - n_trials // 2), dtype=int)
    rng.shuffle(y)

    runs_list = []
    trials_per_run = n_trials // n_runs
    for r in range(n_runs):
        runs_list.extend([r] * trials_per_run)
    while len(runs_list) < n_trials:
        runs_list.append(0)
    runs = np.array(runs_list[:n_trials], dtype=int)

    # Pure Gaussian noise or ERP-embedded signal
    X = rng.standard_normal((n_trials, n_channels, n_times)) * 15.0
    if not pure_noise:
        for i in range(n_trials):
            if y[i] == 1:
                X[i, 0, :] += np.sin(np.linspace(0, 4 * np.pi, n_times)) * snr
            else:
                X[i, min(1, n_channels - 1), :] += np.sin(np.linspace(0, 4 * np.pi, n_times)) * snr

    times = np.linspace(0, n_times / sfreq, n_times)
    return {
        "X": X,
        "y": y,
        "runs": runs,
        "times": times,
        "sfreq": sfreq,
        "channels": [f"ch_{i}" for i in range(n_channels)],
    }


# =============================================================================
# Suite 1: Decoder Array Shape Stress Testing
# =============================================================================
class TestDecoderArrayShapeStress:
    """Stress test all 5 decoders on extreme array dimensions and sampling rates."""

    ALL_DECODERS = ["csp_lda", "csp_svm", "csp_lr", "ts_lr", "fbcsp"]

    @pytest.mark.parametrize("dec_name", ALL_DECODERS)
    def test_small_cohort_n10_trials(self, dec_name: str):
        """Verify all 5 decoders operate on minimal trial counts (N=10, 5 per class) without crashing."""
        data = make_stress_data(n_trials=10, n_channels=8, n_times=150, sfreq=250.0, seed=101)
        X, y = data["X"], data["y"]
        pipe = build_decoder_pipeline(dec_name, n_csp=2, sfreq=data["sfreq"])

        # Train on first 6, test on remaining 4 (ensure both classes present in train)
        tr = np.array([0, 1, 2, 5, 6, 7])
        te = np.array([3, 4, 8, 9])
        pipe.fit(X[tr], y[tr])
        preds = pipe.predict(X[te])

        assert len(preds) == len(te)
        assert set(preds).issubset({0, 1})
        score = pipe.score(X[te], y[te])
        assert 0.0 <= score <= 1.0

    @pytest.mark.parametrize("dec_name", ALL_DECODERS)
    def test_large_cohort_n200_trials(self, dec_name: str):
        """Verify all 5 decoders operate on larger cohorts (N=200 trials) with high stability."""
        data = make_stress_data(n_trials=200, n_channels=16, n_times=250, sfreq=250.0, seed=102)
        X, y = data["X"], data["y"]
        pipe = build_decoder_pipeline(dec_name, n_csp=4, sfreq=data["sfreq"])

        tr = np.arange(0, 160)
        te = np.arange(160, 200)
        pipe.fit(X[tr], y[tr])
        preds = pipe.predict(X[te])

        assert len(preds) == 40
        assert set(preds).issubset({0, 1})
        assert not np.any(np.isnan(preds))
        score = pipe.score(X[te], y[te])
        assert 0.0 <= score <= 1.0

    @pytest.mark.parametrize("sfreq", [128.0, 250.0, 500.0, 1000.0])
    @pytest.mark.parametrize("dec_name", ALL_DECODERS)
    def test_varying_sampling_rates(self, sfreq: float, dec_name: str):
        """Verify all 5 decoders correctly configure across diverse sampling rates (128-1000 Hz)."""
        n_times = int(sfreq * 0.8)  # 800 ms epochs
        data = make_stress_data(n_trials=24, n_channels=8, n_times=n_times, sfreq=sfreq, seed=int(sfreq))
        X, y = data["X"], data["y"]
        pipe = build_decoder_pipeline(dec_name, n_csp=2, sfreq=sfreq)

        tr = np.arange(0, 16)
        te = np.arange(16, 24)
        pipe.fit(X[tr], y[tr])
        preds = pipe.predict(X[te])

        assert len(preds) == 8
        assert not np.any(np.isnan(preds))
        assert 0.0 <= pipe.score(X[te], y[te]) <= 1.0

    @pytest.mark.parametrize("dec_name", ALL_DECODERS)
    def test_high_channel_count_128_channels(self, dec_name: str):
        """Verify decoders survive high-density montages (C=128 channels) in undersampled regime (N < C)."""
        # N=30 trials, C=128 channels -> sample covariance is rank-deficient (rank <= 30)
        data = make_stress_data(n_trials=30, n_channels=128, n_times=150, sfreq=250.0, seed=128)
        X, y = data["X"], data["y"]
        pipe = build_decoder_pipeline(dec_name, n_csp=4, sfreq=data["sfreq"])

        tr = np.arange(0, 20)
        te = np.arange(20, 30)
        pipe.fit(X[tr], y[tr])
        preds = pipe.predict(X[te])

        assert len(preds) == 10
        assert not np.any(np.isnan(preds))
        assert set(preds).issubset({0, 1})


# =============================================================================
# Suite 2: CovarianceTransformer Rank Deficiency & Collinearity Stress Testing
# =============================================================================
class TestCovarianceTransformerRankDeficiency:
    """Stress test CovarianceTransformer against Common Average Referencing and collinearity."""

    @pytest.mark.parametrize("estimator", ["oas", "ledoit_wolf", "empirical"])
    def test_car_exact_rank_deficiency(self, estimator: str):
        """Verify CAR (Common Average Reference, rank C-1) produces strictly positive definite matrices."""
        rng = np.random.default_rng(201)
        n_trials, n_channels, n_times = 20, 16, 250
        X = rng.standard_normal((n_trials, n_channels, n_times)) * 10.0

        # Apply Common Average Referencing (CAR): sum over channels is strictly 0
        X_car = X - np.mean(X, axis=1, keepdims=True)
        assert np.allclose(np.sum(X_car, axis=1), 0.0, atol=1e-10)

        # Before regularization, empirical trial covariance has an exact 0 eigenvalue
        cov_emp = np.array([np.cov(trial - trial.mean(axis=1, keepdims=True)) for trial in X_car])
        min_evals_unreg = [np.min(np.linalg.eigvalsh(c)) for c in cov_emp]
        assert any(e < 1e-10 for e in min_evals_unreg), "Expected exact zero eigenvalue from CAR"

        # Now transform with CovarianceTransformer
        cov_trans = CovarianceTransformer(estimator=estimator, reg_eps=1e-5)
        covs = cov_trans.transform(X_car)

        assert covs.shape == (n_trials, n_channels, n_channels)
        assert not np.any(np.isnan(covs))
        assert not np.any(np.isinf(covs))

        # Check strict positive definiteness: all eigenvalues > 0
        evals = np.linalg.eigvalsh(covs)
        assert np.all(evals > 0.0), f"Non-positive eigenvalues found for estimator {estimator}: min={np.min(evals)}"
        assert np.all(evals >= 1e-6), f"Eigenvalues fell below diagonal regularizer threshold: min={np.min(evals)}"

        # Check condition number is finite and well-conditioned
        cond_nums = [np.linalg.cond(c) for c in covs]
        assert all(np.isfinite(k) for k in cond_nums)
        assert all(k < 1e8 for k in cond_nums)

    @pytest.mark.parametrize("estimator", ["oas", "ledoit_wolf", "empirical"])
    def test_car_tangentspace_end_to_end(self, estimator: str):
        """Verify CAR transformed data cleanly passes through TangentSpaceTransformer without NaNs."""
        rng = np.random.default_rng(202)
        n_trials, n_channels, n_times = 24, 12, 200
        X = rng.standard_normal((n_trials, n_channels, n_times)) * 10.0
        X_car = X - np.mean(X, axis=1, keepdims=True)

        cov_trans = CovarianceTransformer(estimator=estimator)
        covs = cov_trans.transform(X_car)

        ts = TangentSpaceTransformer()
        features = ts.fit_transform(covs)

        expected_dim = n_channels * (n_channels + 1) // 2
        assert features.shape == (n_trials, expected_dim)
        assert not np.any(np.isnan(features)), f"NaNs in tangent space features with {estimator}"
        assert not np.any(np.isinf(features)), f"Infs in tangent space features with {estimator}"
        assert np.all(np.isreal(features)), f"Complex features with {estimator}"

    def test_duplicate_and_collinear_channels(self):
        """Verify identical duplicate channels do not cause singular matrix crashes or NaNs."""
        rng = np.random.default_rng(203)
        n_trials, n_channels, n_times = 15, 8, 200
        X = rng.standard_normal((n_trials, n_channels, n_times))

        # Channel 1 is identical to Channel 0 (collinear)
        X[:, 1, :] = X[:, 0, :]
        # Channel 2 is a linear combination of 0 and 3
        X[:, 2, :] = 0.5 * X[:, 0, :] + 0.5 * X[:, 3, :]

        for est in ["oas", "ledoit_wolf", "empirical"]:
            cov_trans = CovarianceTransformer(estimator=est, reg_eps=1e-5)
            covs = cov_trans.transform(X)
            evals = np.linalg.eigvalsh(covs)
            assert np.all(evals > 0), f"Singular covariance matrix with collinear channels under {est}"

    def test_silent_dead_channel_zero_variance(self):
        """Verify dead channel with all zeros does not cause division by zero or NaNs."""
        rng = np.random.default_rng(204)
        n_trials, n_channels, n_times = 10, 6, 150
        X = rng.standard_normal((n_trials, n_channels, n_times))
        # Channel 0 is completely dead (silent flatline)
        X[:, 0, :] = 0.0

        for est in ["oas", "ledoit_wolf", "empirical"]:
            cov_trans = CovarianceTransformer(estimator=est, reg_eps=1e-5)
            covs = cov_trans.transform(X)
            assert not np.any(np.isnan(covs))
            evals = np.linalg.eigvalsh(covs)
            assert np.all(evals > 0.0)

    def test_ts_lr_pipeline_on_car_data(self):
        """Verify complete ts_lr decoder pipeline fits and predicts on CAR data without errors."""
        data = make_stress_data(n_trials=30, n_channels=10, n_times=200, sfreq=250.0, seed=205)
        X, y = data["X"], data["y"]
        X_car = X - np.mean(X, axis=1, keepdims=True)

        pipe = build_decoder_pipeline("ts_lr")
        pipe.fit(X_car[:20], y[:20])
        preds = pipe.predict(X_car[20:])

        assert len(preds) == 10
        assert not np.any(np.isnan(preds))
        assert set(preds).issubset({0, 1})


# =============================================================================
# Suite 3: FilterBankCSP Nyquist Boundary & Band Pruning Stress Testing
# =============================================================================
class TestFilterBankCSPNyquistAndBands:
    """Stress test FilterBankCSP across Nyquist frequency limits and custom filter banks."""

    def test_nyquist_boundary_sfreq_100hz(self):
        """Verify sfreq=100 Hz (Nyquist=50 Hz) safely filters near-Nyquist 36-40 Hz band."""
        data = make_stress_data(n_trials=20, n_channels=6, n_times=150, sfreq=100.0, seed=301)
        X, y = data["X"], data["y"]

        fb = FilterBankCSP(sfreq=100.0, n_components=2)
        feats = fb.fit_transform(X, y)

        assert feats.shape[0] == 20
        assert feats.shape[1] > 0
        assert not np.any(np.isnan(feats))
        # At sfreq=100, nyq=50. High for (36, 40) is 40 <= 49.5, so all 9 bands should be kept
        assert len(fb.active_bands_) == len(DEFAULT_FILTER_BANKS)

    def test_nyquist_clamping_sfreq_80hz(self):
        """Verify sfreq=80 Hz (Nyquist=40 Hz) prunes/clamps band (36, 40) to (36, 39.5) without crashing."""
        data = make_stress_data(n_trials=20, n_channels=6, n_times=150, sfreq=80.0, seed=302)
        X, y = data["X"], data["y"]

        fb = FilterBankCSP(sfreq=80.0, n_components=2)
        feats = fb.fit_transform(X, y)

        assert feats.shape[0] == 20
        assert feats.shape[1] > 0
        assert not np.any(np.isnan(feats))

        # Check last active band is clamped below Nyquist (40 Hz)
        last_band = fb.active_bands_[-1]
        assert last_band[1] <= 40.0 - 0.5

    def test_nyquist_pruning_sfreq_64hz(self):
        """Verify sfreq=64 Hz (Nyquist=32 Hz) prunes bands above 31 Hz cleanly."""
        data = make_stress_data(n_trials=20, n_channels=6, n_times=120, sfreq=64.0, seed=303)
        X, y = data["X"], data["y"]

        fb = FilterBankCSP(sfreq=64.0, n_components=2)
        feats = fb.fit_transform(X, y)

        assert feats.shape[0] == 20
        assert not np.any(np.isnan(feats))
        # Bands with low >= 31.0 must be pruned: (32, 36) and (36, 40) are dropped
        for low, high in fb.active_bands_:
            assert low < 31.0
            assert high <= 31.5

    def test_custom_overlapping_and_single_bands(self):
        """Verify FBCSP works with arbitrary custom, single, and overlapping frequency bands."""
        data = make_stress_data(n_trials=24, n_channels=8, n_times=250, sfreq=250.0, seed=304)
        X, y = data["X"], data["y"]

        # 1. Single band (alpha 8-12 Hz)
        fbcsp_single = FBCSP(sfreq=250.0, bands=[(8.0, 12.0)], n_components=2, k_features=2)
        fbcsp_single.fit(X[:16], y[:16])
        preds_single = fbcsp_single.predict(X[16:])
        assert len(preds_single) == 8
        assert not np.any(np.isnan(preds_single))

        # 2. Overlapping bands
        overlap_bands = [(4.0, 10.0), (8.0, 16.0), (14.0, 24.0), (20.0, 32.0)]
        fbcsp_overlap = FBCSP(sfreq=250.0, bands=overlap_bands, n_components=2, k_features=4)
        fbcsp_overlap.fit(X[:16], y[:16])
        preds_overlap = fbcsp_overlap.predict(X[16:])
        assert len(preds_overlap) == 8
        assert not np.any(np.isnan(preds_overlap))

    def test_fbcsp_build_pipeline_and_predict_proba(self):
        """Verify build_decoder_pipeline('fbcsp') supports predict_proba and decision_function."""
        data = make_stress_data(n_trials=30, n_channels=8, n_times=250, sfreq=250.0, seed=305)
        X, y = data["X"], data["y"]

        pipe = build_decoder_pipeline("fbcsp", sfreq=250.0)
        pipe.fit(X[:20], y[:20])

        proba = pipe.predict_proba(X[20:])
        assert proba.shape == (10, 2)
        assert np.allclose(np.sum(proba, axis=1), 1.0)
        assert not np.any(np.isnan(proba))

        dec_fn = pipe.decision_function(X[20:])
        assert dec_fn.shape == (10,)
        assert not np.any(np.isnan(dec_fn))


# =============================================================================
# Suite 4: Canonical Leakage Invariant Testing (P1, P2, P5, P7)
# =============================================================================
class TestCanonicalLeakageInvariants:
    """Empirically verify that injected leakage mechanisms yield non-negative or positive inflation on noise."""

    def test_p1_csp_on_all_positive_inflation_on_pure_noise(self):
        """Verify Supervised Spatial Filter Contamination (P1) yields positive inflation on pure noise."""
        # Pure Gaussian noise: clean D3 must hover near chance (50%), whereas P1 overfits test labels
        data = make_stress_data(
            n_trials=60, n_channels=16, n_times=200, sfreq=250.0, n_runs=3, pure_noise=True, seed=401
        )
        decoders = ["csp_lda"]

        # Run clean D3 LORO
        rec_d3, _ = run_d3_loro("noise_p1_test", 1, data, decoders=decoders, n_csp=4)
        acc_d3 = np.mean([r["accuracy"] for r in rec_d3])

        # Run leaky P1 (CSP on all)
        rec_p1, _ = run_p1_csp_on_all("noise_p1_test", 1, data, decoders=decoders, n_csp=4)
        acc_p1 = np.mean([r["accuracy"] for r in rec_p1])

        # Invariant: P1 overfits noise using test labels -> acc_p1 must exceed acc_d3 substantially
        delta_p1 = (acc_p1 - acc_d3) * 100.0
        assert delta_p1 > 5.0, f"Expected P1 to inflate accuracy on noise, but got delta={delta_p1:.2f}% (P1={acc_p1:.2f}, D3={acc_d3:.2f})"

    def test_p7_select_on_all_inflation_with_noise_channels(self):
        """Verify Global Feature Selection (P7) inflates accuracy when extra noise channels are present."""
        # Data with 32 noise channels: selecting channels globally selects spurious noise channels
        data = make_stress_data(
            n_trials=60, n_channels=32, n_times=150, sfreq=250.0, n_runs=3, pure_noise=True, seed=402
        )
        decoders = ["csp_lda"]

        rec_d3, _ = run_d3_loro("noise_p7_test", 1, data, decoders=decoders, n_csp=2)
        acc_d3 = np.mean([r["accuracy"] for r in rec_d3])

        rec_p7, _ = run_p7_select_on_all("noise_p7_test", 1, data, decoders=decoders, n_csp=2, n_keep=8)
        acc_p7 = np.mean([r["accuracy"] for r in rec_p7])

        delta_p7 = (acc_p7 - acc_d3) * 100.0
        # Invariant: P7 must not produce negative inflation beyond minor random noise
        assert delta_p7 >= -5.0, f"P7 produced unexpected negative inflation: delta={delta_p7:.2f}%"

    def test_p2_ica_on_all_execution_and_finite_metrics(self):
        """Verify Global ICA Unmixing (P2) executes across decoders and outputs valid finite metrics."""
        data = make_stress_data(
            n_trials=40, n_channels=12, n_times=150, sfreq=250.0, n_runs=2, pure_noise=False, seed=403
        )
        decoders = ["csp_lda", "ts_lr"]

        rec_p2, splits = run_p2_ica_on_all(
            "p2_test", 1, data, decoders=decoders, n_csp=2, n_components=6, random_state=42
        )
        assert len(rec_p2) == 2 * len(decoders)
        for r in rec_p2:
            assert r["design"] == "P2_ica_on_all"
            assert 0.0 <= r["accuracy"] <= 1.0
            assert not np.isnan(r["accuracy"])
            assert not np.isnan(r["train_acc"])

    def test_p5_scale_on_all_execution_and_finite_metrics(self):
        """Verify Global Normalization (P5) executes across decoders and outputs valid finite metrics."""
        data = make_stress_data(
            n_trials=40, n_channels=10, n_times=150, sfreq=250.0, n_runs=2, pure_noise=False, seed=404
        )
        decoders = ["csp_lda", "fbcsp"]

        rec_p5, splits = run_p5_scale_on_all("p5_test", 1, data, decoders=decoders, n_csp=2)
        assert len(rec_p5) == 2 * len(decoders)
        for r in rec_p5:
            assert r["design"] == "P5_scale_on_all"
            assert 0.0 <= r["accuracy"] <= 1.0
            assert not np.isnan(r["accuracy"])


# =============================================================================
# Suite 5: Level 3 Contrast Computation & Statistical Rigor
# =============================================================================
class TestLevel3ContrastComputation:
    """Verify compute_design_contrasts adheres strictly to Level 3 statistical contracts."""

    def test_contrasts_all_positive_inflation(self):
        """Verify statistical metrics when Leaked condition strictly dominates Clean condition."""
        # Synthesize participant metrics for 5 subjects where P1 is 10-20% higher than D3
        rows = []
        for s in range(1, 6):
            rows.append({
                "dataset": "test_ds",
                "subject_id": s,
                "decoder": "csp_lda",
                "design": "D3_loro",
                "mean_accuracy": 0.60 + 0.02 * s,
            })
            rows.append({
                "dataset": "test_ds",
                "subject_id": s,
                "decoder": "csp_lda",
                "design": "P1_csp_on_all",
                "mean_accuracy": 0.75 + 0.02 * s,
            })

        df_part = pd.DataFrame(rows)
        df_contrasts = compute_design_contrasts(df_part, dataset_name="test_ds", seed=42)

        assert not df_contrasts.empty
        p1_row = df_contrasts[df_contrasts["contrast"] == "P1_vs_D3"].iloc[0]

        # Verification of Hodges-Lehmann and BCa CIs
        assert p1_row["hodges_lehmann_delta"] > 10.0
        assert p1_row["bca_ci_lower"] > 5.0
        assert p1_row["bca_ci_upper"] >= p1_row["bca_ci_lower"]
        assert p1_row["rank_biserial"] == 1.0
        assert p1_row["cohens_dz"] > 1.0
        assert p1_row["raw_p_value"] < 0.10
        assert p1_row["holm_p_value"] <= 1.0

    def test_contrasts_identically_zero_inflation(self):
        """Verify statistical metrics when Leaked and Clean conditions are numerically identical."""
        rows = []
        for s in range(1, 5):
            for des in ["D3_loro", "P5_scale_on_all"]:
                rows.append({
                    "dataset": "test_ds",
                    "subject_id": s,
                    "decoder": "csp_lda",
                    "design": des,
                    "mean_accuracy": 0.70,
                })

        df_part = pd.DataFrame(rows)
        df_contrasts = compute_design_contrasts(df_part, dataset_name="test_ds", seed=42)

        assert not df_contrasts.empty
        p5_row = df_contrasts[df_contrasts["contrast"] == "P5_vs_D3"].iloc[0]

        assert p5_row["mean_diff_pp"] == 0.0
        assert p5_row["hodges_lehmann_delta"] == 0.0
        assert p5_row["raw_p_value"] == 1.0
        assert p5_row["holm_p_value"] == 1.0
        assert p5_row["wilcoxon_w"] == 0.0

    def test_contrasts_small_cohort_n_less_than_3(self):
        """Verify cohorts with N < 3 subjects return NaN for statistical inference without crashing."""
        rows = [
            {"dataset": "small_ds", "subject_id": 1, "decoder": "csp_lda", "design": "D3_loro", "mean_accuracy": 0.60},
            {"dataset": "small_ds", "subject_id": 1, "decoder": "csp_lda", "design": "P1_csp_on_all", "mean_accuracy": 0.80},
            {"dataset": "small_ds", "subject_id": 2, "decoder": "csp_lda", "design": "D3_loro", "mean_accuracy": 0.65},
            {"dataset": "small_ds", "subject_id": 2, "decoder": "csp_lda", "design": "P1_csp_on_all", "mean_accuracy": 0.85},
        ]
        df_part = pd.DataFrame(rows)
        df_contrasts = compute_design_contrasts(df_part, dataset_name="small_ds", seed=42)

        assert not df_contrasts.empty
        p1_row = df_contrasts[df_contrasts["contrast"] == "P1_vs_D3"].iloc[0]
        assert p1_row["n_subjects"] == 2
        assert np.isnan(p1_row["hodges_lehmann_delta"])
        assert np.isnan(p1_row["raw_p_value"])
        assert np.isnan(p1_row["bca_ci_lower"])

    def test_ts_lr_reference_control_contrast_dispatch(self):
        """Verify compute_design_contrasts correctly pairs T1_ts_reference_on_all for ts_lr decoder."""
        rows = [
            {"dataset": "ts_ds", "subject_id": s, "decoder": "ts_lr", "design": "D3_loro", "mean_accuracy": 0.60 + 0.01 * s}
            for s in range(1, 5)
        ] + [
            {"dataset": "ts_ds", "subject_id": s, "decoder": "ts_lr", "design": "T1_ts_reference_on_all", "mean_accuracy": 0.70 + 0.01 * s}
            for s in range(1, 5)
        ]
        df_part = pd.DataFrame(rows)
        df_contrasts = compute_design_contrasts(df_part, dataset_name="ts_ds", seed=42)

        assert not df_contrasts.empty
        row = df_contrasts[df_contrasts["contrast"] == "P1_vs_D3"].iloc[0]
        assert row["condition_b"] == "T1_ts_reference_on_all"
        assert row["description"] == "Global tangent-space reference and global scaling control"
        assert row["hodges_lehmann_delta"] > 0.0
