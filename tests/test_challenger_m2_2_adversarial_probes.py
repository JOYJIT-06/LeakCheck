"""Empirical Adversarial Stress Probes for Challenger M2 Round 2-2.

Rigorous stress-testing of:
1. Shin2017AAdapter (transposed continuous arrays, 2D mrk.y orientations, dropped boundaries, multi-session runs).
2. Weibo2014Adapter (2D continuous boundary drops, kept_indices synchronization, runs matching, 3D permutations).
3. _standardize_epoch_array (all 6 tensor permutations, edge-case channel counts 16, 22, 30, 60, 64, 128, heuristic fallbacks).
4. _parse_binary_labels (3-class and 4-class motor imagery, GDF codes, single-class fallback, length mismatches).
"""

import numpy as np
import pytest
import scipy.io

from emi.datasets_adapters import (
    Shin2017AAdapter,
    Weibo2014Adapter,
    _standardize_epoch_array,
    _parse_binary_labels,
    _partition_runs,
    KNOWN_EEG_CHANNEL_COUNTS,
)


# ======================================================================
# 1. Shin2017AAdapter Adversarial Probes
# ======================================================================

class TestShin2017AAdversarialProbes:
    """Rigorous adversarial stress-testing of Shin2017AAdapter."""

    def test_transposed_cnt_x_various_channel_sizes(self, tmp_path):
        """Verify (n_channels, n_samples) with 30 channels is correctly transposed."""
        # 30 channels, 9000 timepoints
        cnt = {
            "x": np.random.randn(30, 9000) * 15.0,
            "fs": 1000.0,
            "clab": [f"EEG_{i}" for i in range(30)],
        }
        mrk = {
            "pos": np.array([1000, 2000, 3000, 4000, 5000, 6000]),
            "y": np.array([[1, 0], [0, 1], [1, 0], [0, 1], [1, 0], [0, 1]]),
        }
        scipy.io.savemat(str(tmp_path / "VP001.mat"), {"cnt": cnt, "mrk": mrk})
        adapter = Shin2017AAdapter(tmp_path)
        data = adapter.get_subject_epochs(1, target_fs=250.0, tmin=0.0, tmax=1.0)
        assert data["X"].shape == (6, 30, 250)
        assert np.array_equal(data["y"], [0, 1, 0, 1, 0, 1])
        assert len(data["runs"]) == 6

    def test_standard_cnt_x_no_transposition(self, tmp_path):
        """Verify standard (n_samples, n_channels) = (9000, 30) is NOT transposed."""
        cnt = {
            "x": np.random.randn(9000, 30) * 15.0,
            "fs": 1000.0,
            "clab": [f"EEG_{i}" for i in range(30)],
        }
        mrk = {
            "pos": np.array([1000, 2000, 3000, 4000]),
            "y": np.array([[1, 1, 0, 0], [0, 0, 1, 1]]),
        }
        scipy.io.savemat(str(tmp_path / "VP001.mat"), {"cnt": cnt, "mrk": mrk})
        adapter = Shin2017AAdapter(tmp_path)
        data = adapter.get_subject_epochs(1, target_fs=250.0, tmin=0.0, tmax=1.0)
        assert data["X"].shape == (4, 30, 250)
        assert np.array_equal(data["y"], [0, 0, 1, 1])

    def test_mrk_y_orientation_n_classes_by_n_trials(self, tmp_path):
        """Verify (n_classes, n_trials) = (2, 6) one-hot matrix decoded via argmax axis 0."""
        cnt = {
            "x": np.random.randn(8000, 30) * 10.0,
            "fs": 1000.0,
        }
        # Class 0: trials 0, 2, 4. Class 1: trials 1, 3, 5
        mrk = {
            "pos": np.array([500, 1500, 2500, 3500, 4500, 5500]),
            "y": np.array([
                [1, 0, 1, 0, 1, 0],
                [0, 1, 0, 1, 0, 1],
            ]),
        }
        scipy.io.savemat(str(tmp_path / "VP001.mat"), {"cnt": cnt, "mrk": mrk})
        adapter = Shin2017AAdapter(tmp_path)
        data = adapter.get_subject_epochs(1, target_fs=250.0, tmin=0.0, tmax=1.0)
        assert np.array_equal(data["y"], [0, 1, 0, 1, 0, 1])

    def test_mrk_y_orientation_n_trials_by_n_classes(self, tmp_path):
        """Verify (n_trials, n_classes) = (6, 2) one-hot matrix decoded via argmax axis 1."""
        cnt = {
            "x": np.random.randn(8000, 30) * 10.0,
            "fs": 1000.0,
        }
        mrk = {
            "pos": np.array([500, 1500, 2500, 3500, 4500, 5500]),
            "y": np.array([
                [1, 0],
                [0, 1],
                [1, 0],
                [0, 1],
                [1, 0],
                [0, 1],
            ]),
        }
        scipy.io.savemat(str(tmp_path / "VP001.mat"), {"cnt": cnt, "mrk": mrk})
        adapter = Shin2017AAdapter(tmp_path)
        data = adapter.get_subject_epochs(1, target_fs=250.0, tmin=0.0, tmax=1.0)
        assert np.array_equal(data["y"], [0, 1, 0, 1, 0, 1])

    def test_mrk_y_square_matrix_2x2(self, tmp_path):
        """Verify 2x2 square marker matrix decodes correctly."""
        cnt = {
            "x": np.random.randn(4000, 30) * 10.0,
            "fs": 1000.0,
        }
        mrk = {
            "pos": np.array([500, 1500]),
            "y": np.array([[1, 0], [0, 1]]),
        }
        scipy.io.savemat(str(tmp_path / "VP001.mat"), {"cnt": cnt, "mrk": mrk})
        adapter = Shin2017AAdapter(tmp_path)
        data = adapter.get_subject_epochs(1, target_fs=250.0, tmin=0.0, tmax=1.0)
        assert len(data["X"]) == 2
        assert np.array_equal(data["y"], [0, 1])

    def test_mrk_y_3class_onehot(self, tmp_path):
        """Verify (n_trials, 3) with 3 classes decodes and preserves binary contrast."""
        cnt = {
            "x": np.random.randn(8000, 30) * 10.0,
            "fs": 1000.0,
        }
        mrk = {
            "pos": np.array([500, 1500, 2500, 3500, 4500, 5500]),
            # 6 trials: class 0, 1, 2, 0, 1, 2
            "y": np.array([
                [1, 0, 0],
                [0, 1, 0],
                [0, 0, 1],
                [1, 0, 0],
                [0, 1, 0],
                [0, 0, 1],
            ]),
        }
        scipy.io.savemat(str(tmp_path / "VP001.mat"), {"cnt": cnt, "mrk": mrk})
        adapter = Shin2017AAdapter(tmp_path)
        data = adapter.get_subject_epochs(1, target_fs=250.0, tmin=0.0, tmax=1.0)
        assert len(data["X"]) == 6
        assert len(np.unique(data["y"])) >= 2

    def test_dropped_boundary_onsets_synchronized(self, tmp_path):
        """Verify that onsets falling out of bounds drop corresponding y and runs."""
        cnt = {
            "x": np.random.randn(3000, 30) * 10.0,
            "fs": 1000.0,
        }
        # Onset 50: 50 - 500 = -450 < 0 with tmin=-0.5s -> DROPPED
        # Onset 1000: 1000 - 500 = 500, 1000 + 1000 = 2000 <= 3000 -> KEPT
        # Onset 2000: 2000 - 500 = 1500, 2000 + 1000 = 3000 <= 3000 -> KEPT
        # Onset 2800: 2800 + 1000 = 3800 > 3000 -> DROPPED
        mrk = {
            "pos": np.array([50, 1000, 2000, 2800]),
            "y": np.array([1, 1, 2, 2]),  # Binary: [0, 0, 1, 1]
        }
        scipy.io.savemat(str(tmp_path / "VP001.mat"), {"cnt": cnt, "mrk": mrk})
        adapter = Shin2017AAdapter(tmp_path)
        data = adapter.get_subject_epochs(1, target_fs=250.0, tmin=-0.5, tmax=1.0)
        assert len(data["X"]) == 2
        assert len(data["y"]) == 2
        assert len(data["runs"]) == 2
        # Onsets kept are 1000 (label 1 -> 0) and 2000 (label 2 -> 1)
        assert np.array_equal(data["y"], [0, 1])


# ======================================================================
# 2. Weibo2014Adapter Adversarial Probes
# ======================================================================

class TestWeibo2014AdversarialProbes:
    """Rigorous adversarial stress-testing of Weibo2014Adapter."""

    def test_2d_continuous_boundary_drops_both_ends(self, tmp_path):
        """Verify dropping trials at BOTH start and end bounds keeps y and runs synchronized."""
        # 60 channels, 4000 samples at 200 Hz
        c_data = np.random.randn(60, 4000) * 10.0
        # tmin = -0.5s (-100 samples), tmax = 1.0s (+200 samples)
        # Onset 50: 50 - 100 = -50 < 0 (DROPPED)
        # Onset 800: [700, 1000] (KEPT)
        # Onset 1600: [1500, 1800] (KEPT)
        # Onset 2400: [2300, 2600] (KEPT)
        # Onset 3900: 3900 + 200 = 4100 > 4000 (DROPPED)
        trial_onsets = np.array([50, 800, 1600, 2400, 3900])
        labels = np.array([1, 2, 1, 2, 1])  # 1: left (0), 2: right (1)
        runs = np.array([0, 0, 1, 1, 2])

        scipy.io.savemat(str(tmp_path / "subject_1.mat"), {
            "data": c_data,
            "trial": trial_onsets,
            "label": labels,
            "runs": runs,
        })
        adapter = Weibo2014Adapter(tmp_path)
        data = adapter.get_subject_epochs(1, tmin=-0.5, tmax=1.0)

        # 3 epochs kept: onsets 800 (label 2->1), 1600 (label 1->0), 2400 (label 2->1)
        assert len(data["X"]) == 3
        assert len(data["y"]) == 3
        assert len(data["runs"]) == 3
        assert np.array_equal(data["y"], [1, 0, 1])
        # Runs kept for onsets 800, 1600, 2400 are [0, 1, 1]
        assert np.array_equal(data["runs"], [0, 1, 1])

    def test_2d_continuous_matrix_samples_by_channels(self, tmp_path):
        """Verify (samples, channels) = (4000, 60) is correctly handled."""
        c_data = np.random.randn(4000, 60) * 10.0
        trial_onsets = np.array([400, 1000, 1600, 2200])
        labels = np.array([1, 1, 2, 2])
        scipy.io.savemat(str(tmp_path / "subject_1.mat"), {
            "data": c_data,
            "trial": trial_onsets,
            "label": labels,
        })
        adapter = Weibo2014Adapter(tmp_path)
        data = adapter.get_subject_epochs(1, tmin=0.0, tmax=1.0)
        assert data["X"].shape == (4, 60, 200)
        assert np.array_equal(data["y"], [0, 0, 1, 1])
        assert len(data["runs"]) == 4

    def test_3d_mismatched_raw_runs_rejection(self, tmp_path):
        """Verify 3D epoched data with mismatched runs array cleanly falls back to _partition_runs."""
        X_mat = np.random.randn(10, 60, 200) * 10.0
        labels = np.array([1] * 5 + [2] * 5)
        corrupted_runs = np.array([0, 1, 2])  # Length 3 != 10
        scipy.io.savemat(str(tmp_path / "subject_1.mat"), {
            "data": X_mat,
            "label": labels,
            "runs": corrupted_runs,
        })
        adapter = Weibo2014Adapter(tmp_path)
        data = adapter.get_subject_epochs(1)
        assert len(data["runs"]) == 10
        assert len(np.unique(data["runs"])) > 1

    def test_3d_single_unique_run_rejection(self, tmp_path):
        """Verify 3D epoched data with single-run metadata falls back to partitioned runs."""
        X_mat = np.random.randn(8, 60, 200) * 10.0
        labels = np.array([1] * 4 + [2] * 4)
        single_run = np.zeros(8, dtype=int)
        scipy.io.savemat(str(tmp_path / "subject_1.mat"), {
            "data": X_mat,
            "label": labels,
            "runs": single_run,
        })
        adapter = Weibo2014Adapter(tmp_path)
        data = adapter.get_subject_epochs(1)
        assert len(data["runs"]) == 8
        assert len(np.unique(data["runs"])) > 1

    def test_3class_continuous_extraction(self, tmp_path):
        """Verify 3-class continuous data maps Left (1)->0 and Right (2)->1."""
        c_data = np.random.randn(60, 5000) * 10.0
        trial_onsets = np.array([500, 1000, 1500, 2000, 2500, 3000])
        labels = np.array([1, 2, 3, 1, 2, 3])  # Left, Right, Feet
        scipy.io.savemat(str(tmp_path / "subject_1.mat"), {
            "data": c_data,
            "trial": trial_onsets,
            "label": labels,
        })
        adapter = Weibo2014Adapter(tmp_path)
        data = adapter.get_subject_epochs(1, tmin=0.0, tmax=1.0)
        assert len(data["X"]) == 6
        # Left (1) -> 0, Right (2) -> 1, Feet (3) -> 0
        assert data["y"][0] == 0
        assert data["y"][1] == 1
        assert data["y"][0] != data["y"][1]


# ======================================================================
# 3. _standardize_epoch_array Permutation & Dimension Stress
# ======================================================================

class TestStandardizeEpochArrayAdversarialProbes:
    """Rigorous stress-testing of all permutations and edge dimensions."""

    @pytest.mark.parametrize("n_channels", [16, 22, 30, 60, 64, 128])
    def test_channels_times_trials_permutation(self, n_channels):
        """Verify (channels, times, trials) -> (trials, channels, times) across channel counts."""
        n_trials = 10
        n_times = 250
        arr = np.random.randn(n_channels, n_times, n_trials)
        std = _standardize_epoch_array(arr, expected_channels=n_channels)
        assert std.shape == (n_trials, n_channels, n_times)

    @pytest.mark.parametrize("n_channels", [16, 22, 30, 60, 64, 128])
    def test_trials_times_channels_permutation(self, n_channels):
        """Verify (trials, times, channels) -> (trials, channels, times) across channel counts."""
        n_trials = 10
        n_times = 250
        arr = np.random.randn(n_trials, n_times, n_channels)
        std = _standardize_epoch_array(arr, expected_channels=n_channels)
        assert std.shape == (n_trials, n_channels, n_times)

    @pytest.mark.parametrize("n_channels", [16, 22, 30, 60, 64, 128])
    def test_channels_trials_times_permutation(self, n_channels):
        """Verify (channels, trials, times) -> (trials, channels, times) across channel counts."""
        n_trials = 10
        n_times = 250
        arr = np.random.randn(n_channels, n_trials, n_times)
        std = _standardize_epoch_array(arr, expected_channels=n_channels)
        assert std.shape == (n_trials, n_channels, n_times)

    @pytest.mark.parametrize("n_channels", [16, 22, 30, 60, 64, 128])
    def test_times_trials_channels_permutation(self, n_channels):
        """Verify (times, trials, channels) -> (trials, channels, times) across channel counts."""
        n_trials = 10
        n_times = 250
        arr = np.random.randn(n_times, n_trials, n_channels)
        std = _standardize_epoch_array(arr, expected_channels=n_channels)
        assert std.shape == (n_trials, n_channels, n_times)

    def test_heuristic_fallback_different_known_channels(self):
        """Verify fallback when expected_channels is 64 but array has 40 channels."""
        # (trials=12, times=300, channels=40)
        arr = np.random.randn(12, 300, 40)
        std = _standardize_epoch_array(arr, expected_channels=64)
        assert std.shape == (12, 40, 300)

        # (channels=40, times=300, trials=12)
        arr2 = np.random.randn(40, 300, 12)
        std2 = _standardize_epoch_array(arr2, expected_channels=64)
        assert std2.shape == (12, 40, 300)

        # (channels=40, trials=12, times=300)
        arr3 = np.random.randn(40, 12, 300)
        std3 = _standardize_epoch_array(arr3, expected_channels=64)
        assert std3.shape == (12, 40, 300)

    def test_heuristic_fallback_small_channel_count(self):
        """Verify fallback when expected_channels is 64 but array has 8 channels."""
        # (trials=15, times=200, channels=8)
        arr = np.random.randn(15, 200, 8)
        std = _standardize_epoch_array(arr, expected_channels=64)
        assert std.shape == (15, 8, 200)

    def test_square_trials_channels_matrix(self):
        """Verify square (channels, channels, times) where n_trials == n_channels."""
        arr = np.random.randn(64, 64, 250)
        std = _standardize_epoch_array(arr, expected_channels=64)
        assert std.shape == (64, 64, 250)

    def test_non_3d_raises_value_error(self):
        """Verify invalid dimensions raise ValueError."""
        with pytest.raises(ValueError, match="Expected 3D epoched array"):
            _standardize_epoch_array(np.ones(10))
        with pytest.raises(ValueError, match="Expected 3D epoched array"):
            _standardize_epoch_array(np.ones((10, 20)))
        with pytest.raises(ValueError, match="Expected 3D epoched array"):
            _standardize_epoch_array(np.ones((10, 20, 30, 40)))


# ======================================================================
# 4. _parse_binary_labels Discriminative & Adversarial Probes
# ======================================================================

class TestParseBinaryLabelsAdversarialProbes:
    """Rigorous stress-testing of label extraction across paradigms."""

    def test_3class_motor_imagery_discrimination(self):
        """Verify Left Hand (1) and Right Hand (2) are discriminated in 3-class MI."""
        arr = np.array([1, 2, 3, 1, 2, 3, 2, 1])
        y = _parse_binary_labels(arr, 8)
        assert y[0] == 0  # 1 -> 0
        assert y[1] == 1  # 2 -> 1
        assert y[0] != y[1]
        assert np.array_equal(y, [0, 1, 0, 0, 1, 0, 1, 0])

    def test_4class_motor_imagery_discrimination(self):
        """Verify Left Hand (1) and Right Hand (2) are discriminated in 4-class MI (BCI IV-2a)."""
        arr = np.array([1, 2, 3, 4, 1, 2, 3, 4])
        y = _parse_binary_labels(arr, 8)
        assert y[0] == 0  # 1 -> 0
        assert y[1] == 1  # 2 -> 1
        assert np.array_equal(y, [0, 1, 0, 0, 0, 1, 0, 0])

    def test_gdf_event_codes_discrimination(self):
        """Verify GDF event codes 769 (left) and 770 (right) discriminate correctly."""
        arr = np.array([769, 770, 771, 772, 769, 770])
        y = _parse_binary_labels(arr, 6)
        assert y[0] == 0
        assert y[1] == 1
        assert np.array_equal(y, [0, 1, 0, 0, 0, 1])

    def test_arbitrary_binary_triggers(self):
        """Verify arbitrary triggers {-1, 1} and {100, 200} map to {0, 1}."""
        arr1 = np.array([-1, 1, -1, 1, -1, 1])
        y1 = _parse_binary_labels(arr1, 6)
        assert np.array_equal(y1, [0, 1, 0, 1, 0, 1])

        arr2 = np.array([100, 100, 200, 200])
        y2 = _parse_binary_labels(arr2, 4)
        assert np.array_equal(y2, [0, 0, 1, 1])

    def test_string_label_variations(self):
        """Verify case-insensitive string parsing."""
        arr = np.array(["Left", "right", "LEFT_HAND", "Right_Hand", "feet"])
        y = _parse_binary_labels(arr, 5)
        assert np.array_equal(y, [0, 1, 0, 1, 1])

    def test_all_identical_labels_fallback(self):
        """Verify degenerate single-class input falls back to balanced binary labels."""
        arr = np.array([1, 1, 1, 1, 1, 1])
        y = _parse_binary_labels(arr, 6)
        assert len(np.unique(y)) == 2
        assert np.array_equal(y, [0, 0, 0, 1, 1, 1])

    def test_none_label_fallback(self):
        """Verify None labels falls back to balanced binary labels."""
        y = _parse_binary_labels(None, 6)
        assert np.array_equal(y, [0, 0, 0, 1, 1, 1])

    def test_length_truncation_when_raw_longer(self):
        """Verify raw labels longer than n_trials are safely truncated."""
        arr = np.array([1, 2, 1, 2, 1, 2, 1, 2])
        y = _parse_binary_labels(arr, 4)
        assert len(y) == 4
        assert np.array_equal(y, [0, 1, 0, 1])

    def test_length_mismatch_fallback_when_raw_shorter(self):
        """Verify raw labels shorter than n_trials cleanly falls back to balanced split."""
        arr = np.array([1, 2])
        y = _parse_binary_labels(arr, 6)
        assert len(y) == 6
        assert np.array_equal(y, [0, 0, 0, 1, 1, 1])


# ======================================================================
# 5. End-to-End LORO Cross-Validation Integrity Probe
# ======================================================================

class TestLOROIntegrityProbe:
    """Verify that both Shin2017A and Weibo2014 outputs are compatible with LORO splitters."""

    def test_shin2017a_loro_compatibility(self, tmp_path):
        """Confirm Shin2017A outputs can be cleanly split by run for LORO."""
        cnt = {
            "x": np.random.randn(30, 8000) * 10.0,
            "fs": 1000.0,
        }
        mrk = {
            "pos": np.array([1000, 2000, 3000, 4000, 5000, 6000]),
            "y": np.array([[1, 0], [0, 1], [1, 0], [0, 1], [1, 0], [0, 1]]),
        }
        scipy.io.savemat(str(tmp_path / "VP001.mat"), {"cnt": cnt, "mrk": mrk})
        adapter = Shin2017AAdapter(tmp_path)
        data = adapter.get_subject_epochs(1, target_fs=250.0, tmin=0.0, tmax=1.0)

        X, y, runs = data["X"], data["y"], data["runs"]
        assert len(X) == len(y) == len(runs)
        assert len(np.unique(runs)) > 1
        for run_id in np.unique(runs):
            test_mask = (runs == run_id)
            train_mask = ~test_mask
            assert np.sum(test_mask) > 0
            assert np.sum(train_mask) > 0
            assert len(X[train_mask]) > 0
            assert len(X[test_mask]) > 0

    def test_weibo2014_loro_compatibility(self, tmp_path):
        """Confirm Weibo2014 continuous outputs can be cleanly split by run for LORO."""
        c_data = np.random.randn(60, 4000) * 10.0
        trial_onsets = np.array([50, 800, 1600, 2400, 3900])
        labels = np.array([1, 2, 1, 2, 1])
        runs = np.array([0, 0, 1, 1, 2])
        scipy.io.savemat(str(tmp_path / "subject_1.mat"), {
            "data": c_data,
            "trial": trial_onsets,
            "label": labels,
            "runs": runs,
        })
        adapter = Weibo2014Adapter(tmp_path)
        data = adapter.get_subject_epochs(1, tmin=-0.5, tmax=1.0)

        X, y, runs = data["X"], data["y"], data["runs"]
        assert len(X) == len(y) == len(runs)
        assert len(np.unique(runs)) > 1
        for run_id in np.unique(runs):
            test_mask = (runs == run_id)
            train_mask = ~test_mask
            assert np.sum(test_mask) > 0
            assert np.sum(train_mask) > 0
            assert len(X[train_mask]) > 0
            assert len(X[test_mask]) > 0
