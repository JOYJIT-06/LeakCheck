"""Adversarial challenger test probes for Milestone M3.

Focus areas:
- Multi-run LORO generalization across arbitrary K runs (K=2, 3, 4, 6, 8) with zero dropped runs.
- Unbalanced run sizes and non-contiguous run identifiers.
- Size-matched random repeats: strict invariance of fold sizes, class counts, and disjoint partition coverage.
- Structural alignment between D3 (LORO) and D1s (size-matched random).
- Edge cases: K=1 single-run cohorts, 2 trials per run, zero-trial/empty datasets, and extreme within-run class imbalance.
- Unified benchmark runner integration with all 5 decoders.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.pipeline import Pipeline

from emi.decoders import DECODERS, build_decoder_pipeline
from emi.splitters import (
    loro_splits,
    size_matched_random_repeats,
    validate_splits,
)
from scripts.run_unified_benchmark import (
    compute_split_hash,
    evaluate_fold,
    get_loro_folds,
    run_d1s_size_matched,
    run_d3_loro,
    run_p1_csp_on_all,
    run_p2_ica_on_all,
    run_p5_scale_on_all,
    run_p7_select_on_all,
)


# =============================================================================
# Helper Fixtures & Data Generators
# =============================================================================
def make_synthetic_multirun_data(
    run_sizes: dict[int, int] | list[int],
    class_ratios: dict[int, float] | None = None,
    n_channels: int = 8,
    n_times: int = 150,
    sfreq: float = 250.0,
    seed: int = 42,
) -> dict:
    """Generate synthetic EEG data with specified run sizes and class distributions."""
    rng = np.random.default_rng(seed)
    if isinstance(run_sizes, list):
        run_sizes = {r: size for r, size in enumerate(run_sizes)}

    runs_list = []
    y_list = []
    for r, n_r in run_sizes.items():
        runs_list.extend([r] * n_r)
        if class_ratios is not None and r in class_ratios:
            ratio = class_ratios[r]
            n_c0 = int(round(n_r * ratio))
            n_c1 = n_r - n_c0
            y_r = [0] * n_c0 + [1] * n_c1
        else:
            n_c0 = n_r // 2
            n_c1 = n_r - n_c0
            y_r = [0] * n_c0 + [1] * n_c1
        y_list.extend(y_r)

    runs = np.array(runs_list, dtype=int)
    y = np.array(y_list, dtype=int)
    n_trials = len(runs)

    # Synthetic signal: ERP burst in ch 0 for class 0, ch 1 for class 1
    X = rng.standard_normal((n_trials, n_channels, n_times)) * 10.0
    for i in range(n_trials):
        if y[i] == 1:
            X[i, 1, :] += np.sin(np.linspace(0, 4 * np.pi, n_times)) * 6.0
        else:
            X[i, 0, :] += np.sin(np.linspace(0, 4 * np.pi, n_times)) * 6.0

    times = np.linspace(0, n_times / sfreq, n_times)
    return {
        "X": X,
        "y": y,
        "runs": runs,
        "times": times,
        "sfreq": sfreq,
        "channels": [f"ch_{c}" for c in range(n_channels)],
    }


# =============================================================================
# Suite 1: Multi-Run LORO Generalization (K = 2, 3, 4, 6, 8)
# =============================================================================
class TestMultiRunLOROGeneralization:
    """Stress-test LORO partitioning across cohort run counts K = 2, 3, 4, 6, 8."""

    @pytest.mark.parametrize("k_runs", [2, 3, 4, 6, 8])
    def test_loro_folds_exhaustiveness_no_dropped_runs(self, k_runs: int):
        """Verify that get_loro_folds produces exactly K folds with 100% trial and run coverage."""
        trials_per_run = 20
        data = make_synthetic_multirun_data([trials_per_run] * k_runs, seed=100 + k_runs)
        runs, y = data["runs"], data["y"]
        unique_runs = np.unique(runs)

        folds = get_loro_folds(runs, y)
        assert len(folds) == k_runs, f"Expected {k_runs} folds, got {len(folds)}"

        tested_runs = []
        all_tested_indices = []

        for fold_idx, (fold_label, train_idx, test_idx) in enumerate(folds):
            # Check fold label format
            expected_run = unique_runs[fold_idx]
            assert fold_label == f"leave_out_run_{expected_run}"

            # Check test set contains only the held out run
            test_runs = np.unique(runs[test_idx])
            assert len(test_runs) == 1, f"Fold {fold_idx} test set contains multiple runs: {test_runs}"
            held_out = test_runs[0]
            assert held_out == expected_run
            tested_runs.append(held_out)

            # Check training set contains all other runs and zero held-out trials
            train_runs = np.unique(runs[train_idx])
            assert held_out not in train_runs
            assert set(train_runs) == set(unique_runs) - {held_out}

            # Check disjointness and coverage within fold
            assert len(np.intersect1d(train_idx, test_idx)) == 0, "Train and test overlap"
            assert len(train_idx) + len(test_idx) == len(runs)
            all_tested_indices.extend(test_idx)

        # Invariant: Every run is held out exactly once
        assert sorted(tested_runs) == sorted(unique_runs)

        # Invariant: Every trial is tested exactly once across folds (no dropped trials!)
        assert sorted(all_tested_indices) == list(range(len(runs)))

    @pytest.mark.parametrize("k_runs", [2, 3, 4, 6, 8])
    def test_run_d3_loro_execution_all_decoders(self, k_runs: int):
        """Verify run_d3_loro executes all 5 decoders across K folds without dropping any runs."""
        trials_per_run = 16
        data = make_synthetic_multirun_data([trials_per_run] * k_runs, seed=200 + k_runs)
        decoders = ["csp_lda", "csp_svm", "csp_lr", "ts_lr", "fbcsp"]

        records, splits_manifest = run_d3_loro(
            dataset_name=f"synth_k{k_runs}",
            subject=1,
            data=data,
            decoders=decoders,
            n_csp=4,
        )

        # Total records = K folds * len(decoders)
        expected_records = k_runs * len(decoders)
        assert len(records) == expected_records

        # Splits manifest has exactly K folds
        assert len(splits_manifest) == k_runs
        for k in range(k_runs):
            assert f"fold_{k}" in splits_manifest
            assert splits_manifest[f"fold_{k}"]["label"] == f"leave_out_run_{k}"

        df = pd.DataFrame(records)
        assert df["fold"].nunique() == k_runs
        assert set(df["decoder"].unique()) == set(decoders)
        assert (df["n_test"] == trials_per_run).all()
        assert (df["n_train"] == len(data["runs"]) - trials_per_run).all()
        assert df["accuracy"].between(0.0, 1.0).all()
        assert df["train_time_s"].gt(0.0).all()
        assert df["test_time_s"].gt(0.0).all()


# =============================================================================
# Suite 2: Unbalanced Run Sizes & Non-Contiguous Run Identifiers
# =============================================================================
class TestUnbalancedRunSizes:
    """Stress-test LORO and size-matched splitting on cohorts with unequal run lengths."""

    def test_loro_unbalanced_run_lengths(self):
        """Verify LORO fold sizes strictly match held-out run lengths when run sizes differ widely."""
        run_dict = {0: 15, 1: 55, 2: 30}
        data = make_synthetic_multirun_data(run_dict, seed=301)
        runs, y = data["runs"], data["y"]

        folds = get_loro_folds(runs, y)
        assert len(folds) == 3

        for fold_idx, (label, tr, te) in enumerate(folds):
            expected_test_size = run_dict[fold_idx]
            expected_train_size = len(runs) - expected_test_size

            assert len(te) == expected_test_size
            assert len(tr) == expected_train_size
            assert (runs[te] == fold_idx).all()
            assert fold_idx not in runs[tr]

    def test_loro_non_contiguous_run_ids(self):
        """Verify LORO properly handles non-contiguous run IDs (e.g. runs [2, 5, 9])."""
        run_dict = {2: 25, 5: 45, 9: 30}
        data = make_synthetic_multirun_data(run_dict, seed=302)
        runs, y = data["runs"], data["y"]

        folds = get_loro_folds(runs, y)
        assert len(folds) == 3

        expected_labels = ["leave_out_run_2", "leave_out_run_5", "leave_out_run_9"]
        assert [f[0] for f in folds] == expected_labels

        records, splits = run_d3_loro("unbalanced_ds", 1, data, decoders=["csp_lda"], n_csp=4)
        assert len(records) == 3
        df = pd.DataFrame(records)
        assert list(df["n_test"]) == [25, 45, 30]
        assert list(df["n_train"]) == [75, 55, 70]
        assert list(df["fold_label"]) == expected_labels


# =============================================================================
# Suite 3: Size-Matched Random Repeats Strict Invariance
# =============================================================================
class TestSizeMatchedRandomRepeatsInvariance:
    """Verify that size_matched_random_repeats strictly mirrors LORO fold structure."""

    @pytest.mark.parametrize("k_runs", [2, 3, 4, 6])
    def test_size_matched_balanced_fidelity_across_repeats(self, k_runs: int):
        """Verify test sizes and class balances match LORO across multiple repeats."""
        trials_per_run = 24
        data = make_synthetic_multirun_data([trials_per_run] * k_runs, seed=400 + k_runs)
        runs, y = data["runs"], data["y"]
        n_repeats = 15

        repeats = size_matched_random_repeats(y, runs, repeats=n_repeats, seed=42)
        assert len(repeats) == n_repeats

        for rep_idx, folds in enumerate(repeats):
            assert len(folds) == k_runs
            all_tested = []
            for fold_idx, (tr, te) in enumerate(folds):
                assert len(te) == trials_per_run
                assert len(tr) == len(runs) - trials_per_run
                assert len(np.intersect1d(tr, te)) == 0

                # Check class balance strictly matches LORO
                real_run = fold_idx
                real_c0 = int(((runs == real_run) & (y == 0)).sum())
                real_c1 = int(((runs == real_run) & (y == 1)).sum())
                assert int((y[te] == 0).sum()) == real_c0
                assert int((y[te] == 1).sum()) == real_c1

                all_tested.extend(te)

            # In each repeat, test sets must form a complete partition of all trials
            assert sorted(all_tested) == list(range(len(runs)))

    def test_size_matched_unbalanced_sizes_and_classes_invariance(self):
        """Verify strict size and class count matching when runs have unequal sizes and imbalanced classes."""
        run_dict = {0: 20, 1: 50, 2: 30}
        # Run 0: 6 class 0 (30%), 14 class 1 (70%)
        # Run 1: 35 class 0 (70%), 15 class 1 (30%)
        # Run 2: 15 class 0 (50%), 15 class 1 (50%)
        class_ratios = {0: 0.30, 1: 0.70, 2: 0.50}
        data = make_synthetic_multirun_data(run_dict, class_ratios=class_ratios, seed=501)
        runs, y = data["runs"], data["y"]

        n_repeats = 20
        repeats = size_matched_random_repeats(y, runs, repeats=n_repeats, seed=999)

        for rep_idx, folds in enumerate(repeats):
            assert len(folds) == 3
            rep_tested = []
            for fold_idx, (tr, te) in enumerate(folds):
                expected_size = run_dict[fold_idx]
                assert len(te) == expected_size
                assert len(tr) == len(runs) - expected_size

                # Verify exact class count invariance
                for c in (0, 1):
                    expected_c = int(((runs == fold_idx) & (y == c)).sum())
                    actual_c = int((y[te] == c).sum())
                    assert actual_c == expected_c, (
                        f"Repeat {rep_idx} fold {fold_idx} class {c} count mismatch: "
                        f"got {actual_c}, expected {expected_c}"
                    )
                rep_tested.extend(te)
            assert sorted(rep_tested) == list(range(len(runs)))

    def test_d3_vs_d1s_structural_parity(self):
        """Verify that D3 LORO and D1s size-matched produce identical test fold sizes."""
        run_dict = {0: 22, 1: 44, 2: 34}
        data = make_synthetic_multirun_data(run_dict, seed=502)

        records_d3, _ = run_d3_loro("parity_ds", 1, data, decoders=["csp_lda"], n_csp=4)
        records_d1s, _ = run_d1s_size_matched("parity_ds", 1, data, decoders=["csp_lda"], n_csp=4, n_repeats=5)

        df_d3 = pd.DataFrame(records_d3)
        df_d1s = pd.DataFrame(records_d1s)

        # Check each fold size in D3 matches every repeat in D1s
        for f in range(3):
            d3_n_test = df_d3[df_d3["fold"] == f]["n_test"].iloc[0]
            d1s_n_tests = df_d1s[df_d1s["fold"] == f]["n_test"].unique()
            assert len(d1s_n_tests) == 1
            assert d1s_n_tests[0] == d3_n_test

    @pytest.mark.parametrize("k_runs", [2, 3, 4, 6, 8])
    def test_run_d1s_size_matched_all_decoders_k_runs(self, k_runs: int):
        """Verify run_d1s_size_matched executes all 5 decoders across K runs with exact record counts."""
        trials_per_run = 16
        data = make_synthetic_multirun_data([trials_per_run] * k_runs, seed=450 + k_runs)
        decoders = ["csp_lda", "csp_svm", "csp_lr", "ts_lr", "fbcsp"]
        n_repeats = 2
        records, splits = run_d1s_size_matched(
            dataset_name=f"synth_k{k_runs}",
            subject=1,
            data=data,
            decoders=decoders,
            n_csp=4,
            n_repeats=n_repeats,
        )
        expected_count = n_repeats * k_runs * len(decoders)
        assert len(records) == expected_count
        df = pd.DataFrame(records)
        assert set(df["decoder"].unique()) == set(decoders)
        assert (df["n_test"] == trials_per_run).all()
        assert df["accuracy"].between(0.0, 1.0).all()


# =============================================================================
# Suite 4: Edge Cases & Adversarial Boundaries
# =============================================================================
class TestEdgeCasesAndBoundaries:
    """Stress-test edge cases: K=1 single-run, 2 trials per run, zero-trial runs, and extreme class imbalance."""

    def test_k1_single_run_interleaved_classes_behavior(self):
        """Verify K=1 single run with interleaved classes triggers chronological half-split fallback."""
        n_trials = 40
        data = make_synthetic_multirun_data({0: n_trials}, seed=601)
        # Interleave classes so both halves have both classes
        data["y"] = np.array([0, 1] * (n_trials // 2), dtype=int)
        runs, y = data["runs"], data["y"]

        # 1. get_loro_folds on K=1
        folds = get_loro_folds(runs, y)
        assert len(folds) == 2
        assert folds[0][0] == "half0_to_half1"
        assert folds[1][0] == "half1_to_half0"
        assert len(folds[0][1]) == 20  # train
        assert len(folds[0][2]) == 20  # test

        # 2. run_d3_loro on K=1 with interleaved classes
        rec_d3, splits_d3 = run_d3_loro("k1_ds", 1, data, decoders=["csp_lda"], n_csp=4)
        assert len(rec_d3) == 2
        assert all(r["accuracy"] >= 0.0 for r in rec_d3)

        # 3. run_d1s_size_matched on K=1
        rec_d1s, splits_d1s = run_d1s_size_matched("k1_ds", 1, data, decoders=["csp_lda"], n_csp=4, n_repeats=3)
        assert len(rec_d1s) == 3 * 2  # 3 repeats * 2 folds

        # 4. In contrast, splitters.loro_splits directly with K=1 is detected by validate_splits
        raw_repeats = loro_splits(runs)
        with pytest.raises(ValueError):
            validate_splits(raw_repeats, y)

    def test_k1_single_run_block_design_unhandled_crash(self):
        """Document and verify vulnerability: K=1 unstratified half-split produces single-class training fold.
        When a single-run cohort has block-ordered trials (all class 0 followed by all class 1),
        get_loro_folds blindly splits indices in half without class stratification.
        This produces a training set with only one class (0), causing all 5 decoders to crash
        with uncaught LinAlgError or ValueError instead of raising a clean informative exception.
        """
        n_trials = 40
        data = make_synthetic_multirun_data({0: n_trials}, seed=601)
        # Block-ordered classes: first 20 trials class 0, next 20 trials class 1
        data["y"] = np.array([0] * 20 + [1] * 20, dtype=int)
        runs, y = data["runs"], data["y"]

        folds = get_loro_folds(runs, y)
        train_idx, test_idx = folds[0][1], folds[0][2]
        # Invariant check: training fold contains ONLY ONE class
        assert len(np.unique(y[train_idx])) == 1, "Expected single-class training fold"

        # Verify that run_d3_loro crashes on this unstratified split
        with pytest.raises((np.linalg.LinAlgError, ValueError)):
            run_d3_loro("k1_block_ds", 1, data, decoders=["csp_lda"], n_csp=4)

    def test_two_trials_per_run_minimal_viable_cohort(self):
        """Verify all 5 decoders survive a minimal cohort of K=3 runs with only 2 trials per run (total 6 trials)."""
        run_dict = {0: 2, 1: 2, 2: 2}
        data = make_synthetic_multirun_data(run_dict, seed=602)
        decoders = ["csp_lda", "csp_svm", "csp_lr", "ts_lr", "fbcsp"]

        # Run D3 LORO
        rec_d3, splits_d3 = run_d3_loro("min_trials_ds", 1, data, decoders=decoders, n_csp=2)
        assert len(rec_d3) == 3 * len(decoders)
        for r in rec_d3:
            assert r["n_train"] == 4
            assert r["n_test"] == 2
            assert 0.0 <= r["accuracy"] <= 1.0

        # Run D1s size-matched
        rec_d1s, splits_d1s = run_d1s_size_matched(
            "min_trials_ds", 1, data, decoders=decoders, n_csp=2, n_repeats=2
        )
        assert len(rec_d1s) == 2 * 3 * len(decoders)

    def test_zero_trial_runs_empty_input(self):
        """Verify empty input handling in splitters without uncaught crashes."""
        empty_runs = np.array([], dtype=int)
        empty_y = np.array([], dtype=int)

        loro_out = loro_splits(empty_runs)
        assert loro_out == [[]]

        d1s_out = size_matched_random_repeats(empty_y, empty_runs, repeats=2)
        assert d1s_out == [[], []]

    def test_extreme_within_run_class_imbalance(self):
        """Verify that size_matched_random_repeats and run_d3_loro handle runs containing 0 trials of one class."""
        # Run 0: 20 trials of class 0, 0 trials of class 1
        # Run 1: 0 trials of class 0, 20 trials of class 1
        # Run 2: 15 trials of class 0, 15 trials of class 1
        # Total = 70 trials, 35 class 0, 35 class 1
        runs = np.array([0] * 20 + [1] * 20 + [2] * 30)
        y = np.array([0] * 20 + [1] * 20 + [0] * 15 + [1] * 15)

        # 1. size_matched_random_repeats must handle n_c = 0 without index out of bounds
        repeats = size_matched_random_repeats(y, runs, repeats=10, seed=777)
        for rep in repeats:
            assert len(rep) == 3
            # Fold 0: must have 20 class 0, 0 class 1
            te_0 = rep[0][1]
            assert (y[te_0] == 0).sum() == 20
            assert (y[te_0] == 1).sum() == 0

            # Fold 1: must have 0 class 0, 20 class 1
            te_1 = rep[1][1]
            assert (y[te_1] == 0).sum() == 0
            assert (y[te_1] == 1).sum() == 20

            # Fold 2: must have 15 class 0, 15 class 1
            te_2 = rep[2][1]
            assert (y[te_2] == 0).sum() == 15
            assert (y[te_2] == 1).sum() == 15

        # 2. evaluate_fold on a test fold with single class produces valid accuracy and np.nan balanced_accuracy
        data = make_synthetic_multirun_data({0: 20, 1: 20, 2: 30}, seed=778)
        data["runs"] = runs
        data["y"] = y

        rec_d3, _ = run_d3_loro("imbalance_ds", 1, data, decoders=["csp_lda"], n_csp=2)
        assert len(rec_d3) == 3
        # Fold 0 has single-class test set -> bal_acc and f1 must be nan, but accuracy is valid
        assert np.isnan(rec_d3[0]["balanced_accuracy"])
        assert np.isnan(rec_d3[0]["f1"])
        assert 0.0 <= rec_d3[0]["accuracy"] <= 1.0

    def test_empty_trials_benchmark_crashes_with_linalgerror(self):
        """Document and verify vulnerability: empty dataset (0 trials) crashes with LinAlgError.
        Neither run_d3_loro nor run_d1s_size_matched guards against empty input (len(y) == 0),
        raising unhandled LinAlgError: 0-dimensional array given.
        """
        empty_data = {
            "X": np.empty((0, 8, 100)),
            "y": np.array([], dtype=int),
            "runs": np.array([], dtype=int),
            "sfreq": 250.0,
        }
        with pytest.raises(np.linalg.LinAlgError):
            run_d3_loro("empty_ds", 1, empty_data, decoders=["csp_lda"])

        with pytest.raises(np.linalg.LinAlgError):
            run_d1s_size_matched("empty_ds", 1, empty_data, decoders=["csp_lda"])


# =============================================================================
# Suite 5: Canonical Leakage Mechanisms on Multi-Run Cohorts
# =============================================================================
class TestCanonicalLeakageMultiRun:
    """Verify canonical leakage mechanisms (P1, P2, P5, P7) on multi-run cohorts."""

    def test_canonical_leakage_mechanisms_unbalanced_multi_run(self):
        """Verify P1, P2, P5, P7 execute on an unbalanced 4-run cohort."""
        data = make_synthetic_multirun_data({0: 16, 1: 32, 2: 24, 3: 28}, seed=801)
        decoders = ["csp_lda", "ts_lr", "fbcsp"]

        p1_recs, p1_splits = run_p1_csp_on_all("ds", 1, data, decoders=decoders, n_csp=4)
        assert len(p1_recs) == 4 * len(decoders)

        p2_recs, p2_splits = run_p2_ica_on_all("ds", 1, data, decoders=decoders, n_csp=4)
        assert len(p2_recs) == 4 * len(decoders)

        p5_recs, p5_splits = run_p5_scale_on_all("ds", 1, data, decoders=decoders, n_csp=4)
        assert len(p5_recs) == 4 * len(decoders)

        p7_recs, p7_splits = run_p7_select_on_all("ds", 1, data, decoders=decoders, n_csp=4)
        assert len(p7_recs) == 4 * len(decoders)


# =============================================================================
# Suite 6: Full Benchmark Runner Integration Smoke Test
# =============================================================================
class TestBenchmarkRunnerMultiRunIntegration:
    """Verify scripts/run_unified_benchmark.py produces compliant Level 1-3 artifacts with arbitrary K runs."""

    def test_cli_execution_with_k6_simulation(self, tmp_path):
        """Run CLI benchmark on BNCI2014-001 (K=6 runs) with synthetic data and verify all levels."""
        import subprocess
        import sys
        from pathlib import Path

        repo_root = Path(__file__).resolve().parent.parent
        script_path = repo_root / "scripts" / "run_unified_benchmark.py"
        out_dir = tmp_path / "k6_test_out"

        cmd = [
            sys.executable,
            str(script_path),
            "--dataset", "bnci2014_001",
            "--subjects", "1",
            "--decoders", "csp_lda,ts_lr",
            "--designs", "D3,D1s",
            "--synthetic",
            "--smoke",
            "--outdir", str(out_dir),
        ]

        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode == 0, f"Benchmark CLI failed: {res.stderr}\n{res.stdout}"

        # Level 1 check
        fold_csv = out_dir / "fold_metrics.csv"
        assert fold_csv.is_file()
        f_df = pd.read_csv(fold_csv)
        assert not f_df.empty
        assert set(f_df["design"].unique()) == {"D3_loro", "D1s_size_matched"}

        # Level 2 check
        part_csv = out_dir / "participant_metrics.csv"
        assert part_csv.is_file()
        p_df = pd.read_csv(part_csv)
        assert not p_df.empty
        assert "mean_accuracy" in p_df.columns

        # Level 3 check
        comp_csv = out_dir / "design_comparisons.csv"
        assert comp_csv.is_file()
        c_df = pd.read_csv(comp_csv)
        assert not c_df.empty
        assert "D1s_vs_D3" in c_df["contrast"].values
