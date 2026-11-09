"""Empirical stress-testing harness for M2 Dataset Adapters (Shin2017A, Weibo2014, Zhou2016, Yang2025).

Authored by Challenger M2-2.
Adversarial stress-testing of BBCI structures, MAT orientations, run partitioning, and label parsing.
"""

import numpy as np
import pytest
import scipy.io

from emi.datasets_adapters import (
    Shin2017AAdapter,
    Weibo2014Adapter,
    Zhou2016Adapter,
    Yang2025Adapter,
    _standardize_epoch_array,
    _partition_runs,
    _parse_binary_labels,
)


# ======================================================================
# 1. Stress Tests: _partition_runs
# ======================================================================

class TestPartitionRunsStress:
    """Adversarial stress-testing of run partitioning."""

    def test_partition_runs_zero_trials(self):
        runs = _partition_runs(0, default_n_runs=3)
        assert len(runs) == 0
        assert isinstance(runs, np.ndarray)

    def test_partition_runs_single_trial(self):
        runs = _partition_runs(1, default_n_runs=6)
        assert len(runs) == 1
        assert runs[0] == 0

    def test_partition_runs_fewer_trials_than_runs(self):
        # 3 trials with 6 requested runs -> should cap at 3 runs
        runs = _partition_runs(3, default_n_runs=6)
        assert len(runs) == 3
        assert len(np.unique(runs)) == 3
        assert np.array_equal(runs, [0, 1, 2])

    def test_partition_runs_indivisible_trials(self):
        # 13 trials divided into 6 runs: splits should be size 3, 2, 2, 2, 2, 2
        runs = _partition_runs(13, default_n_runs=6)
        assert len(runs) == 13
        assert len(np.unique(runs)) == 6
        # Runs should be non-decreasing (contiguous blocks)
        assert np.all(np.diff(runs) >= 0)
        # Check trial counts per run
        counts = np.bincount(runs)
        assert np.max(counts) - np.min(counts) <= 1

    def test_partition_runs_large_even_split(self):
        runs = _partition_runs(120, default_n_runs=6)
        assert len(runs) == 120
        assert len(np.unique(runs)) == 6
        counts = np.bincount(runs)
        assert np.all(counts == 20)

    def test_partition_runs_deterministic(self):
        runs_1 = _partition_runs(47, default_n_runs=5)
        runs_2 = _partition_runs(47, default_n_runs=5)
        assert np.array_equal(runs_1, runs_2)


# ======================================================================
# 2. Stress Tests: _standardize_epoch_array
# ======================================================================

class TestStandardizeEpochArrayStress:
    """Stress tests on tensor orientation standardization."""

    def test_non_3d_raises(self):
        with pytest.raises(ValueError, match="Expected 3D epoched array"):
            _standardize_epoch_array(np.ones((10, 20)))
        with pytest.raises(ValueError, match="Expected 3D epoched array"):
            _standardize_epoch_array(np.ones((10, 20, 30, 40)))

    def test_already_standard(self):
        # (trials=10, channels=60, times=200)
        arr = np.random.randn(10, 60, 200)
        std = _standardize_epoch_array(arr, expected_channels=60)
        assert std.shape == (10, 60, 200)

    def test_channels_times_trials(self):
        # (channels=60, times=200, trials=10) -> (trials=10, channels=60, times=200)
        arr = np.random.randn(60, 200, 10)
        std = _standardize_epoch_array(arr, expected_channels=60)
        assert std.shape == (10, 60, 200)

    def test_trials_times_channels(self):
        # (trials=10, times=200, channels=60) -> (trials=10, channels=60, times=200)
        arr = np.random.randn(10, 200, 60)
        std = _standardize_epoch_array(arr, expected_channels=60)
        assert std.shape == (10, 60, 200)

    def test_symmetric_channels_trials(self):
        # Square dimensions: trials == channels (e.g., 60 trials, 60 channels, 200 times)
        arr = np.random.randn(60, 60, 200)
        std = _standardize_epoch_array(arr, expected_channels=60)
        assert std.shape == (60, 60, 200)

    def test_channels_trials_times_misclassified(self):
        # (channels=60, trials=12, times=200)
        arr = np.random.randn(60, 12, 200)
        std = _standardize_epoch_array(arr, expected_channels=60)
        # Expected: (trials=12, channels=60, times=200)
        # Actual: (times=200, channels=60, trials=12)
        assert std.shape == (12, 60, 200)

    def test_heuristic_fallback_unknown_channels(self):
        # When expected_channels doesn't match (e.g. 32 channels, expected 64)
        # (trials=15, times=300, channels=32)
        arr = np.random.randn(15, 300, 32)
        std = _standardize_epoch_array(arr, expected_channels=64)
        # Expected: (trials=15, channels=32, times=300)
        # Actual: (32, 15, 300)
        assert std.shape == (15, 32, 300)


# ======================================================================
# 3. Stress Tests: _parse_binary_labels
# ======================================================================

class TestParseBinaryLabelsStress:
    """Stress tests on label extraction and mapping."""

    def test_none_label_fallback(self):
        y = _parse_binary_labels(None, 10)
        assert np.array_equal(y, [0, 0, 0, 0, 0, 1, 1, 1, 1, 1])

    def test_1_2_mapping(self):
        raw = np.array([1, 1, 2, 2, 1, 2])
        y = _parse_binary_labels(raw, 6)
        assert np.array_equal(y, [0, 0, 1, 1, 0, 1])

    def test_0_1_mapping(self):
        raw = np.array([0, 0, 1, 1, 0, 1])
        y = _parse_binary_labels(raw, 6)
        assert np.array_equal(y, [0, 0, 1, 1, 0, 1])

    def test_arbitrary_integers_mapping(self):
        # e.g., trigger codes 16 (left) and 32 (right)
        raw = np.array([16, 16, 32, 32, 16, 32])
        y = _parse_binary_labels(raw, 6)
        assert np.array_equal(y, [0, 0, 1, 1, 0, 1])

    def test_strings_mapping(self):
        raw = np.array(["left_hand", "LEFT", "right_hand", "Right"])
        y = _parse_binary_labels(raw, 4)
        assert np.array_equal(y, [0, 0, 1, 1])

    def test_single_class_fallback(self):
        # All one class -> fallback to balanced split to avoid single-class failure
        raw = np.array([1, 1, 1, 1])
        y = _parse_binary_labels(raw, 4)
        assert np.array_equal(y, [0, 0, 1, 1])

    def test_longer_raw_labels_truncated(self):
        raw = np.array([1, 1, 2, 2, 1, 2, 1, 2])
        y = _parse_binary_labels(raw, 4)
        assert len(y) == 4
        assert np.array_equal(y, [0, 0, 1, 1])

    def test_three_class_left_vs_right_discrimination(self):
        # 1: left, 2: right, 3: feet
        raw = np.array([1, 1, 2, 2, 3, 3])
        y = _parse_binary_labels(raw, 6)
        # Left (1) should differ from Right (2)
        assert y[0] != y[2]


# ======================================================================
# 4. Stress Tests: Shin2017AAdapter (BBCI Format Anomalies)
# ======================================================================

class TestShin2017AAdapterStress:
    """Stress tests on Shin2017A BBCI struct parsing."""

    def test_shin2017a_missing_fs_defaults_gracefully(self, tmp_path):
        cnt = {
            "x": np.random.randn(8000, 30) * 10.0,
            "clab": [f"EEG_{i}" for i in range(30)],
        }
        mrk = {
            "pos": np.array([500, 1500, 2500, 3500]),
            "y": np.array([[1, 1, 0, 0], [0, 0, 1, 1]]),
        }
        scipy.io.savemat(str(tmp_path / "VP001.mat"), {"cnt": cnt, "mrk": mrk})
        adapter = Shin2017AAdapter(tmp_path)
        data = adapter.get_subject_epochs(1, target_fs=250.0, tmin=0.0, tmax=1.0)
        assert data["X"].shape == (4, 30, 250)
        assert np.array_equal(data["y"], [0, 0, 1, 1])

    def test_shin2017a_integer_marker_codes(self, tmp_path):
        cnt = {
            "x": np.random.randn(8000, 30) * 10.0,
            "fs": 1000.0,
        }
        mrk = {
            "pos": np.array([500, 1500, 2500, 3500]),
            "y": np.array([16, 16, 32, 32]),
        }
        scipy.io.savemat(str(tmp_path / "VP001.mat"), {"cnt": cnt, "mrk": mrk})
        adapter = Shin2017AAdapter(tmp_path)
        data = adapter.get_subject_epochs(1, target_fs=250.0, tmin=0.0, tmax=1.0)
        assert np.array_equal(data["y"], [0, 0, 1, 1])

    def test_shin2017a_alternative_mrk_fields(self, tmp_path):
        cnt = {
            "x": np.random.randn(8000, 30) * 10.0,
            "fs": 1000.0,
        }
        mrk = {
            "time": np.array([500, 1500, 2500, 3500]),
            "toe": np.array([1, 1, 2, 2]),
        }
        scipy.io.savemat(str(tmp_path / "VP001.mat"), {"cnt": cnt, "mrk": mrk})
        adapter = Shin2017AAdapter(tmp_path)
        data = adapter.get_subject_epochs(1, target_fs=250.0, tmin=0.0, tmax=1.0)
        assert data["X"].shape[0] == 4
        assert np.array_equal(data["y"], [0, 0, 1, 1])

    def test_shin2017a_multi_session_run_partitioning(self, tmp_path):
        cnt_1 = {"x": np.random.randn(5000, 30) * 10.0, "fs": 1000.0}
        mrk_1 = {"pos": np.array([500, 1500, 2500]), "y": np.array([[1, 1, 0], [0, 0, 1]])}
        cnt_2 = {"x": np.random.randn(5000, 30) * 10.0, "fs": 1000.0}
        mrk_2 = {"pos": np.array([500, 1500, 2500]), "y": np.array([[0, 1, 1], [1, 0, 0]])}

        scipy.io.savemat(str(tmp_path / "VP001.mat"), {
            "cnt": np.array([cnt_1, cnt_2], dtype=object),
            "mrk": np.array([mrk_1, mrk_2], dtype=object),
        })
        adapter = Shin2017AAdapter(tmp_path)
        data = adapter.get_subject_epochs(1, target_fs=250.0, tmin=0.0, tmax=1.0)
        assert data["X"].shape[0] == 6
        assert np.array_equal(data["runs"], [0, 0, 0, 1, 1, 1])

    def test_shin2017a_epoched_mat_fallback(self, tmp_path):
        X_mat = np.random.randn(8, 30, 250) * 10.0
        scipy.io.savemat(str(tmp_path / "VP001.mat"), {
            "data": X_mat,
            "y": np.array([1, 1, 1, 1, 2, 2, 2, 2]),
            "fs": 250.0,
        })
        adapter = Shin2017AAdapter(tmp_path)
        data = adapter.get_subject_epochs(1, target_fs=250.0)
        assert data["X"].shape == (8, 30, 250)
        assert np.array_equal(data["y"], [0, 0, 0, 0, 1, 1, 1, 1])
        assert len(np.unique(data["runs"])) > 1

    def test_shin2017a_transposed_cnt_x(self, tmp_path):
        # BBCI struct where cnt.x is (n_channels, n_samples) = (30, 8000)
        cnt = {
            "x": np.random.randn(30, 8000) * 10.0,
            "fs": 1000.0,
            "clab": [f"EEG_{i}" for i in range(30)],
        }
        mrk = {
            "pos": np.array([500, 1500, 2500, 3500]),
            "y": np.array([[1, 1, 0, 0], [0, 0, 1, 1]]),
        }
        scipy.io.savemat(str(tmp_path / "VP001.mat"), {"cnt": cnt, "mrk": mrk})
        adapter = Shin2017AAdapter(tmp_path)
        data = adapter.get_subject_epochs(1, target_fs=250.0, tmin=0.0, tmax=1.0)
        assert data["X"].shape[1] == 30

    def test_shin2017a_nx2_onehot_markers_preservation(self, tmp_path):
        # mrk.y is (n_trials, n_classes) = (4, 2) with alternating pattern [0, 1, 0, 1]
        cnt = {
            "x": np.random.randn(8000, 30) * 10.0,
            "fs": 1000.0,
        }
        mrk = {
            "pos": np.array([500, 1500, 2500, 3500]),
            "y": np.array([
                [1, 0],
                [0, 1],
                [1, 0],
                [0, 1],
            ]),
        }
        scipy.io.savemat(str(tmp_path / "VP001.mat"), {"cnt": cnt, "mrk": mrk})
        adapter = Shin2017AAdapter(tmp_path)
        data = adapter.get_subject_epochs(1, target_fs=250.0, tmin=0.0, tmax=1.0)
        # Expected alternating labels: [0, 1, 0, 1]
        # Actual corrupted labels: [0, 0, 1, 1] (due to dummy fallback)
        assert np.array_equal(data["y"], [0, 1, 0, 1])


# ======================================================================
# 5. Stress Tests: Weibo2014Adapter (MAT Orientations & Runs)
# ======================================================================

class TestWeibo2014AdapterStress:
    """Stress tests on Weibo2014 MAT variations and run partitioning."""

    def test_weibo2014_transposed_3d_channels_times_trials(self, tmp_path):
        X_mat = np.random.randn(60, 200, 12) * 10.0
        labels = np.array([1] * 6 + [2] * 6)
        scipy.io.savemat(str(tmp_path / "subject_1.mat"), {"data": X_mat, "label": labels})
        adapter = Weibo2014Adapter(tmp_path)
        data = adapter.get_subject_epochs(1)
        assert data["X"].shape == (12, 60, 200)
        assert np.array_equal(data["y"], [0] * 6 + [1] * 6)

    def test_weibo2014_transposed_3d_trials_times_channels(self, tmp_path):
        X_mat = np.random.randn(12, 200, 60) * 10.0
        labels = np.array([1] * 6 + [2] * 6)
        scipy.io.savemat(str(tmp_path / "subject_1.mat"), {"data": X_mat, "label": labels})
        adapter = Weibo2014Adapter(tmp_path)
        data = adapter.get_subject_epochs(1)
        assert data["X"].shape == (12, 60, 200)

    def test_weibo2014_2d_continuous_matrix_transposed(self, tmp_path):
        c_data = np.random.randn(3000, 60) * 10.0
        trial_onsets = np.array([200, 600, 1000, 1400, 1800, 2200])
        labels = np.array([1, 1, 1, 2, 2, 2])
        scipy.io.savemat(str(tmp_path / "subject_1.mat"), {
            "data": c_data,
            "trial": trial_onsets,
            "label": labels,
        })
        adapter = Weibo2014Adapter(tmp_path)
        data = adapter.get_subject_epochs(1, tmin=0.0, tmax=1.0)
        assert data["X"].shape == (6, 60, 200)
        assert np.array_equal(data["y"], [0, 0, 0, 1, 1, 1])

    def test_weibo2014_indivisible_run_partitioning(self, tmp_path):
        X_mat = np.random.randn(11, 60, 200) * 10.0
        labels = np.array([1] * 5 + [2] * 6)
        scipy.io.savemat(str(tmp_path / "subject_1.mat"), {"data": X_mat, "label": labels})
        adapter = Weibo2014Adapter(tmp_path)
        data = adapter.get_subject_epochs(1)
        assert data["X"].shape == (11, 60, 200)
        assert len(data["runs"]) == 11
        assert len(np.unique(data["runs"])) == 6

    def test_weibo2014_fewer_trials_than_runs(self, tmp_path):
        X_mat = np.random.randn(4, 60, 200) * 10.0
        labels = np.array([1, 1, 2, 2])
        scipy.io.savemat(str(tmp_path / "subject_1.mat"), {"data": X_mat, "label": labels})
        adapter = Weibo2014Adapter(tmp_path)
        data = adapter.get_subject_epochs(1)
        assert data["X"].shape == (4, 60, 200)
        assert len(data["runs"]) == 4
        assert len(np.unique(data["runs"])) == 4

    def test_weibo2014_2d_dropped_onset_label_alignment(self, tmp_path):
        c_data = np.random.randn(60, 4000) * 10.0
        # Onset 50 dropped because 50 - 100 < 0 with tmin=-0.5s
        trial_onsets = np.array([50, 500, 1000, 1500, 2000])
        labels = np.array([1, 2, 1, 1, 2])  # Binary: [0, 1, 0, 0, 1]
        scipy.io.savemat(str(tmp_path / "subject_1.mat"), {
            "data": c_data,
            "trial": trial_onsets,
            "label": labels,
        })
        adapter = Weibo2014Adapter(tmp_path)
        data = adapter.get_subject_epochs(1, tmin=-0.5, tmax=1.0)
        # 4 epochs kept (onsets 500, 1000, 1500, 2000). Expected labels: [1, 0, 0, 1]
        # Actual assigned labels: [0, 1, 0, 0] (due to slicing labels[:4])
        assert np.array_equal(data["y"], [1, 0, 0, 1])

    def test_weibo2014_2d_dropped_onset_runs_length_match(self, tmp_path):
        c_data = np.random.randn(60, 4000) * 10.0
        trial_onsets = np.array([50, 500, 1000, 1500, 2000])
        labels = np.array([1, 2, 1, 1, 2])
        raw_runs = np.array([0, 0, 1, 1, 2])
        scipy.io.savemat(str(tmp_path / "subject_1.mat"), {
            "data": c_data,
            "trial": trial_onsets,
            "label": labels,
            "runs": raw_runs,
        })
        adapter = Weibo2014Adapter(tmp_path)
        data = adapter.get_subject_epochs(1, tmin=-0.5, tmax=1.0)
        # Expected: len(runs) == len(X) == 4
        # Actual: len(runs) == 5, len(X) == 4 -> causes IndexError in boolean indexing
        assert len(data["runs"]) == len(data["X"])


# ======================================================================
# 6. Stress Tests: Zhou2016Adapter & Yang2025Adapter
# ======================================================================

class TestZhouAndYangStress:
    """Stress tests on Zhou2016 and Yang2025 adapters."""

    def test_zhou2016_standard_orientation(self, tmp_path):
        X_mat = np.random.randn(6, 16, 250) * 10.0
        scipy.io.savemat(str(tmp_path / "subject_1.mat"), {
            "eeg": X_mat,
            "y": np.array([1, 1, 1, 2, 2, 2]),
        })
        adapter = Zhou2016Adapter(tmp_path)
        data = adapter.get_subject_epochs(1)
        assert data["X"].shape == (6, 16, 250)
        assert np.array_equal(data["y"], [0, 0, 0, 1, 1, 1])
        assert len(np.unique(data["runs"])) == 3

    def test_zhou2016_transposed_orientation_channels_times_trials(self, tmp_path):
        # (channels=16, times=250, trials=6)
        X_mat = np.random.randn(16, 250, 6) * 10.0
        scipy.io.savemat(str(tmp_path / "subject_1.mat"), {
            "eeg": X_mat,
            "y": np.array([1, 1, 1, 2, 2, 2]),
        })
        adapter = Zhou2016Adapter(tmp_path)
        data = adapter.get_subject_epochs(1)
        assert data["X"].shape == (6, 16, 250)
        assert np.array_equal(data["y"], [0, 0, 0, 1, 1, 1])

    def test_zhou2016_transposed_orientation_trials_times_channels(self, tmp_path):
        # (trials=6, times=250, channels=16)
        X_mat = np.random.randn(6, 250, 16) * 10.0
        scipy.io.savemat(str(tmp_path / "subject_1.mat"), {
            "eeg": X_mat,
            "y": np.array([1, 1, 1, 2, 2, 2]),
        })
        adapter = Zhou2016Adapter(tmp_path)
        data = adapter.get_subject_epochs(1)
        assert data["X"].shape == (6, 16, 250)

    def test_yang2025_standard_orientation(self, tmp_path):
        X_mat = np.random.randn(8, 64, 250) * 10.0
        scipy.io.savemat(str(tmp_path / "sub-01.mat"), {
            "eeg": X_mat,
            "y": np.array([1, 1, 1, 1, 2, 2, 2, 2]),
            "sfreq": 250.0,
        })
        adapter = Yang2025Adapter(tmp_path)
        data = adapter.get_subject_epochs(1, target_fs=250.0)
        assert data["X"].shape == (8, 64, 250)
        assert np.array_equal(data["y"], [0, 0, 0, 0, 1, 1, 1, 1])
        assert len(np.unique(data["runs"])) == 4

    def test_yang2025_transposed_orientation_trials_times_channels(self, tmp_path):
        # (trials=8, times=250, channels=64)
        X_mat = np.random.randn(8, 250, 64) * 10.0
        scipy.io.savemat(str(tmp_path / "sub-01.mat"), {
            "data": X_mat,
            "labels": np.array([0, 0, 0, 0, 1, 1, 1, 1]),
            "sfreq": 250.0,
        })
        adapter = Yang2025Adapter(tmp_path)
        data = adapter.get_subject_epochs(1, target_fs=250.0)
        assert data["X"].shape == (8, 64, 250)

    def test_yang2025_sfreq_resampling_behavior(self, tmp_path):
        # Native 1000 Hz data with 1000 samples -> resampled to 250 Hz (250 samples)
        X_mat = np.random.randn(4, 64, 1000) * 10.0
        scipy.io.savemat(str(tmp_path / "sub-01.mat"), {
            "data": X_mat,
            "y": np.array([1, 1, 2, 2]),
        })
        adapter = Yang2025Adapter(tmp_path)
        data = adapter.get_subject_epochs(1, target_fs=250.0)
        assert data["X"].shape == (4, 64, 250)
        assert data["sfreq"] == 250.0

    def test_integrity_validation_all_four_adapters(self, tmp_path):
        shin = Shin2017AAdapter(tmp_path)
        weibo = Weibo2014Adapter(tmp_path)
        zhou = Zhou2016Adapter(tmp_path)
        yang = Yang2025Adapter(tmp_path)

        assert shin.validate_integrity(0)[0] is False
        assert shin.validate_integrity(30)[0] is False
        assert weibo.validate_integrity(0)[0] is False
        assert weibo.validate_integrity(11)[0] is False
        assert zhou.validate_integrity(0)[0] is False
        assert zhou.validate_integrity(5)[0] is False
        assert yang.validate_integrity(0)[0] is False
        assert yang.validate_integrity(61)[0] is False
