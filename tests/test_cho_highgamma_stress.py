"""Empirical Stress & Adversarial Test Harness for Cho2017Adapter and HighGammaAdapter.

Tested by: teamwork_challenger (Agent: challenger_m2_1)
Target: Cho2017Adapter and HighGammaAdapter in src/emi/datasets_adapters.py
Branch: v2-dev
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pytest
import scipy.io
import mne

from emi.datasets_adapters import (
    Cho2017Adapter,
    HighGammaAdapter,
    _standardize_epoch_array,
    _partition_runs,
    _parse_binary_labels,
)


@pytest.fixture
def tmp_dir():
    td = Path(tempfile.mkdtemp(prefix="leakcheck_stress_"))
    yield td
    shutil.rmtree(td, ignore_errors=True)


# ======================================================================
# 1. Cho2017Adapter Empirical Stress Tests
# ======================================================================

def test_cho2017_missing_and_corrupt_files(tmp_dir):
    """Stress-test Cho2017 against missing, non-existent, and corrupt files."""
    adapter = Cho2017Adapter(tmp_dir)

    # 1. Subject out of range (1-52)
    for bad_subj in [0, 53, -1, 100]:
        is_valid, diag = adapter.validate_integrity(bad_subj)
        assert not is_valid
        assert diag["status"] == "EXCLUDED"
        assert "out of range" in diag["reason"]

    # 2. Non-existent file
    is_valid, diag = adapter.validate_integrity(1)
    assert not is_valid
    assert diag["status"] == "PENDING_ACQUISITION"

    with pytest.raises(FileNotFoundError, match="Cho2017 MAT file not found"):
        adapter.get_subject_epochs(1)

    # 3. Corrupt/garbage file content
    corrupt_path = tmp_dir / "s01.mat"
    corrupt_path.write_bytes(b"\x00\x01\x02CORRUPTED_NOT_A_MATLAB_FILE\xff\xfe")
    with pytest.raises(Exception):  # scipy.io.loadmat fails with MatReadError or IndexError
        adapter.get_subject_epochs(1)


def test_cho2017_missing_struct_fields(tmp_dir):
    """Stress-test Cho2017 MAT structs with missing fields or corrupt internal objects."""
    adapter = Cho2017Adapter(tmp_dir)

    # 1. Empty MAT file
    scipy.io.savemat(str(tmp_dir / "s01.mat"), {})
    with pytest.raises(ValueError, match="Could not find valid EEG data matrix"):
        adapter.get_subject_epochs(1)

    # 2. MAT with EEG object that is a scalar or string
    scipy.io.savemat(str(tmp_dir / "s02.mat"), {"eeg": "not_an_array_or_struct"})
    with pytest.raises(ValueError, match="Could not find valid EEG data matrix"):
        adapter.get_subject_epochs(2)

    # 3. Continuous struct missing srate (should gracefully fall back to 512.0)
    srate_default = 512.0
    n_samples = 4000
    im_l = np.random.randn(64, n_samples) * 10.0
    im_r = np.random.randn(64, n_samples) * 10.0
    trig_l = np.zeros(n_samples)
    trig_l[[500, 1500]] = 1.0
    trig_r = np.zeros(n_samples)
    trig_r[[500, 1500]] = 1.0

    scipy.io.savemat(str(tmp_dir / "s03.mat"), {
        "eeg": {
            "imagery_left": im_l,
            "imagery_right": im_r,
            "imagery_event": trig_l,
            "imagery_event_right": trig_r,
            # no srate field
        }
    })
    data = adapter.get_subject_epochs(3, target_fs=250.0, tmin=0.0, tmax=1.0)
    assert data["sfreq"] == 250.0
    assert data["X"].shape == (4, 64, 250)


def test_cho2017_boundary_triggers_and_empty_trials(tmp_dir):
    """Stress-test Cho2017 continuous triggers at boundaries, out-of-bounds, and all-zero triggers."""
    adapter = Cho2017Adapter(tmp_dir)
    n_samples = 4000
    im_l = np.random.randn(64, n_samples) * 10.0
    im_r = np.random.randn(64, n_samples) * 10.0

    # 1. All zero triggers
    scipy.io.savemat(str(tmp_dir / "s01.mat"), {
        "eeg": {
            "imagery_left": im_l,
            "imagery_right": im_r,
            "imagery_event": np.zeros(n_samples),
            "imagery_event_right": np.zeros(n_samples),
            "srate": 512.0,
        }
    })
    with pytest.raises(ValueError, match="No valid epochs extracted"):
        adapter.get_subject_epochs(1)

    # 2. Triggers out of bounds (beyond recording length when tmax added)
    trig_oob = np.zeros(n_samples)
    trig_oob[3950] = 1.0  # 3950 + 512 > 4000
    scipy.io.savemat(str(tmp_dir / "s02.mat"), {
        "eeg": {
            "imagery_left": im_l,
            "imagery_right": im_r,
            "imagery_event": trig_oob,
            "imagery_event_right": trig_oob,
            "srate": 512.0,
        }
    })
    with pytest.raises(ValueError, match="No valid epochs extracted"):
        adapter.get_subject_epochs(2, tmin=0.0, tmax=1.0)

    # 3. Triggers with one valid onset and one out-of-bounds onset
    trig_mixed = np.zeros(n_samples)
    trig_mixed[[100, 3950]] = 1.0
    scipy.io.savemat(str(tmp_dir / "s03.mat"), {
        "eeg": {
            "imagery_left": im_l,
            "imagery_right": im_r,
            "imagery_event": trig_mixed,
            "imagery_event_right": trig_mixed,
            "srate": 512.0,
        }
    })
    data = adapter.get_subject_epochs(3, target_fs=250.0, tmin=0.0, tmax=1.0)
    assert data["X"].shape[0] == 2, "Only the 2 in-bound trials (1 left, 1 right) should be retained"
    assert np.array_equal(data["y"], [0, 1])


def test_cho2017_transposed_and_irregular_dimensions(tmp_dir):
    """Stress-test array shape handling and dimension orderings in Cho2017."""
    adapter = Cho2017Adapter(tmp_dir)

    # 1. Continuous with transposed dimensions (n_samples, 64) and 68 channels (truncated to 64)
    n_samples = 4000
    im_l = np.random.randn(n_samples, 68) * 10.0
    im_r = np.random.randn(n_samples, 68) * 10.0
    trig = np.zeros(n_samples)
    trig[[500, 1500]] = 1.0

    scipy.io.savemat(str(tmp_dir / "s01.mat"), {
        "eeg": {
            "imagery_left": im_l,
            "imagery_right": im_r,
            "imagery_event": trig,
            "imagery_event_right": trig,
            "srate": 512.0,
        }
    })
    data = adapter.get_subject_epochs(1, target_fs=250.0, tmin=0.0, tmax=1.0)
    assert data["X"].shape == (4, 64, 250), "Must transpose and truncate channels to 64"

    # 2. Epoched array 3D permutations: (trials, channels, times) vs (channels, times, trials) vs (trials, times, channels)
    X_std = np.random.randn(10, 64, 200) * 10.0
    X_perm1 = np.transpose(X_std, (1, 2, 0))  # (64, 200, 10)
    X_perm2 = np.transpose(X_std, (0, 2, 1))  # (10, 200, 64)

    assert _standardize_epoch_array(X_std, expected_channels=64).shape == (10, 64, 200)
    assert _standardize_epoch_array(X_perm1, expected_channels=64).shape == (10, 64, 200)
    assert _standardize_epoch_array(X_perm2, expected_channels=64).shape == (10, 64, 200)

    # 3. Invalid array dimensions (2D or 4D) in epoched mode
    with pytest.raises(ValueError, match="Expected 3D epoched array"):
        _standardize_epoch_array(np.random.randn(64, 200))
    with pytest.raises(ValueError, match="Expected 3D epoched array"):
        _standardize_epoch_array(np.random.randn(2, 64, 200, 5))


def test_cho2017_nan_and_inf_detection(tmp_dir):
    """Stress-test Cho2017Adapter against NaN and Inf values in continuous and epoched data."""
    adapter = Cho2017Adapter(tmp_dir)
    n_samples = 4000
    im_l = np.random.randn(64, n_samples) * 10.0
    im_r = np.random.randn(64, n_samples) * 10.0
    trig = np.zeros(n_samples)
    trig[[500, 1500]] = 1.0

    # 1. NaN in continuous imagery_left
    im_l_nan = im_l.copy()
    im_l_nan[10, 600] = np.nan
    scipy.io.savemat(str(tmp_dir / "s01.mat"), {
        "eeg": {
            "imagery_left": im_l_nan,
            "imagery_right": im_r,
            "imagery_event": trig,
            "imagery_event_right": trig,
            "srate": 512.0,
        }
    })
    with pytest.raises(ValueError, match="has non-finite values"):
        adapter.get_subject_epochs(1)

    # 2. Inf in continuous imagery_right
    im_r_inf = im_r.copy()
    im_r_inf[5, 1600] = np.inf
    scipy.io.savemat(str(tmp_dir / "s02.mat"), {
        "eeg": {
            "imagery_left": im_l,
            "imagery_right": im_r_inf,
            "imagery_event": trig,
            "imagery_event_right": trig,
            "srate": 512.0,
        }
    })
    with pytest.raises(ValueError, match="has non-finite values"):
        adapter.get_subject_epochs(2)

    # 3. NaN in epoched data matrix
    X_epoched_nan = np.random.randn(6, 64, 250) * 10.0
    X_epoched_nan[0, 0, 10] = np.nan
    scipy.io.savemat(str(tmp_dir / "s03.mat"), {
        "eeg": X_epoched_nan,
        "y": np.array([0, 0, 0, 1, 1, 1]),
    })
    with pytest.raises(ValueError, match="has non-finite values"):
        adapter.get_subject_epochs(3)


def test_cho2017_runs_length_mismatch_behavior(tmp_dir):
    """Stress-test Cho2017Adapter behavior when mat contains runs with mismatched length."""
    adapter = Cho2017Adapter(tmp_dir)
    # 6 epoched trials, but 'runs' has 50 elements
    X = np.random.randn(6, 64, 250) * 10.0
    y = np.array([0, 0, 0, 1, 1, 1])
    mismatched_runs = np.repeat([0, 1], 25)  # len 50 != len(y) (6)

    scipy.io.savemat(str(tmp_dir / "s01.mat"), {
        "eeg": X,
        "y": y,
        "runs": mismatched_runs,
    })
    data = adapter.get_subject_epochs(1)

    # Verify adapter rejected mismatched runs and partitioned safely
    runs_len = len(data["runs"])
    y_len = len(data["y"])
    assert runs_len == y_len, f"Contract violation: len(runs)={runs_len} != len(y)={y_len}"
    assert len(np.unique(data["runs"])) > 1, "Must contain multi-run partition for LORO"


# ======================================================================
# 2. HighGammaAdapter Empirical Stress Tests
# ======================================================================

def test_highgamma_missing_and_corrupt_files(tmp_dir):
    """Stress-test HighGamma against non-existent and corrupt EDF files."""
    adapter = HighGammaAdapter(tmp_dir)

    # 1. Non-existent EDF file
    is_valid, diag = adapter.validate_integrity(1)
    assert not is_valid
    assert diag["status"] == "PENDING_ACQUISITION"
    with pytest.raises(FileNotFoundError, match="HighGamma EDF file not found"):
        adapter.get_subject_epochs(1)

    # 2. Corrupt / empty 0-byte EDF file
    (tmp_dir / "subject_1.edf").write_bytes(b"")
    with pytest.raises(Exception):
        adapter.get_subject_epochs(1)


def test_highgamma_unexpected_annotation_strings(tmp_dir):
    """Stress-test HighGamma annotation parsing with varied casing, whitespace, and fallback keys."""
    (tmp_dir / "subject_1.edf").touch()

    raw_info = mne.create_info(ch_names=[f"eeg_{i}" for i in range(1, 45)], sfreq=250.0, ch_types="eeg")
    raw = mne.io.RawArray(np.random.randn(44, 25000) * 1e-5, raw_info, verbose="ERROR")

    # 1. Case insensitive, whitespace, and GDF code annotations
    annots = mne.Annotations(
        onset=[1.0, 3.0, 5.0, 7.0, 9.0, 11.0, 13.0, 15.0],
        duration=[0.5] * 8,
        description=[
            "  LEFT_HAND  ", "2", "769", "left_movement",
            "  RIGHT_HAND ", "1", "770", "right_movement",
        ],
    )
    raw.set_annotations(annots)

    with patch("mne.io.read_raw_edf", return_value=raw):
        adapter = HighGammaAdapter(tmp_dir)
        data = adapter.get_subject_epochs(1, tmin=0.0, tmax=1.0)
        assert data["X"].shape[0] == 8
        assert np.array_equal(data["y"], [0, 0, 0, 0, 1, 1, 1, 1])

    # 2. Fallback to arbitrary event names when >= 2 classes exist
    annots_arbitrary = mne.Annotations(
        onset=[1.0, 3.0, 5.0, 7.0],
        duration=[0.5] * 4,
        description=["stimulus_alpha", "stimulus_beta", "stimulus_alpha", "stimulus_beta"],
    )
    raw.set_annotations(annots_arbitrary)
    with patch("mne.io.read_raw_edf", return_value=raw):
        adapter = HighGammaAdapter(tmp_dir)
        data = adapter.get_subject_epochs(1, tmin=0.0, tmax=1.0)
        assert data["X"].shape[0] == 4
        assert len(np.unique(data["y"])) == 2

    # 3. No annotations present at all
    raw.set_annotations(None)
    with patch("mne.io.read_raw_edf", return_value=raw):
        adapter = HighGammaAdapter(tmp_dir)
        with pytest.raises(ValueError, match="No trial events or annotations found"):
            adapter.get_subject_epochs(1)


def test_highgamma_non_monotonic_timestamps(tmp_dir):
    """Stress-test HighGamma with out-of-order / non-monotonic annotation timestamps."""
    (tmp_dir / "subject_1.edf").touch()
    raw_info = mne.create_info(ch_names=[f"eeg_{i}" for i in range(1, 45)], sfreq=250.0, ch_types="eeg")
    raw = mne.io.RawArray(np.random.randn(44, 25000) * 1e-5, raw_info, verbose="ERROR")

    # Scrambled onsets: 10.0, 2.0, 14.0, 6.0, 4.0, 12.0
    annots = mne.Annotations(
        onset=[10.0, 2.0, 14.0, 6.0, 4.0, 12.0],
        duration=[0.5] * 6,
        description=["left_hand", "left_hand", "right_hand", "right_hand", "left_hand", "right_hand"],
    )
    raw.set_annotations(annots)

    with patch("mne.io.read_raw_edf", return_value=raw):
        adapter = HighGammaAdapter(tmp_dir)
        data = adapter.get_subject_epochs(1, tmin=0.0, tmax=1.0)
        assert data["X"].shape[0] == 6
        # Chronological order of onsets: 2.0(L=0), 4.0(L=0), 6.0(R=1), 10.0(L=0), 12.0(R=1), 14.0(R=1)
        assert np.array_equal(data["y"], [0, 0, 1, 0, 1, 1])
        assert len(data["runs"]) == 6
        assert len(np.unique(data["runs"])) > 1


def test_highgamma_nan_and_inf_detection(tmp_dir):
    """Stress-test HighGamma against NaN and Inf values in raw recording."""
    (tmp_dir / "subject_1.edf").touch()
    raw_info = mne.create_info(ch_names=[f"eeg_{i}" for i in range(1, 45)], sfreq=250.0, ch_types="eeg")

    # NaN in raw array
    data_nan = np.random.randn(44, 25000) * 1e-5
    data_nan[5, 500] = np.nan
    raw_nan = mne.io.RawArray(data_nan, raw_info, verbose="ERROR")
    raw_nan.set_annotations(mne.Annotations(
        onset=[1.0, 3.0, 5.0, 7.0],
        duration=[0.5] * 4,
        description=["left_hand", "left_hand", "right_hand", "right_hand"]
    ))

    with patch("mne.io.read_raw_edf", return_value=raw_nan):
        adapter = HighGammaAdapter(tmp_dir)
        with pytest.raises(ValueError, match="has non-finite values"):
            adapter.get_subject_epochs(1)


def test_highgamma_run_boundaries_and_single_run_degeneracy(tmp_dir):
    """Stress-test HighGamma run boundary extraction when boundary markers cause single-run degeneracy."""
    (tmp_dir / "subject_1.edf").touch()
    raw_info = mne.create_info(ch_names=[f"eeg_{i}" for i in range(1, 45)], sfreq=250.0, ch_types="eeg")
    raw = mne.io.RawArray(np.random.randn(44, 25000) * 1e-5, raw_info, verbose="ERROR")

    # Scenario: Boundary markers exist at 8.0s and 15.0s, but all 4 trials occur before 6.0s
    annots = mne.Annotations(
        onset=[1.0, 2.5, 4.0, 5.5, 8.0, 15.0],
        duration=[0.5] * 6,
        description=["left_hand", "right_hand", "left_hand", "right_hand", "run_start", "run_start"],
    )
    raw.set_annotations(annots)

    with patch("mne.io.read_raw_edf", return_value=raw):
        adapter = HighGammaAdapter(tmp_dir)
        data = adapter.get_subject_epochs(1, tmin=0.0, tmax=1.0)
        assert data["X"].shape[0] == 4
        unique_runs = np.unique(data["runs"])
        # Check if single-run degeneracy occurs:
        # If len(unique_runs) <= 1, LORO cannot split folds!
        assert len(unique_runs) > 1, f"Degenerate single run detected: {unique_runs}, LORO will fail!"


def test_single_class_edge_cases(tmp_dir):
    """Verify that single-class extraction raises descriptive ValueError."""
    # 1. Cho2017 continuous with only left triggers
    adapter_cho = Cho2017Adapter(tmp_dir)
    n_samples = 4000
    im_l = np.random.randn(64, n_samples) * 10.0
    im_r = np.random.randn(64, n_samples) * 10.0
    trig_l = np.zeros(n_samples)
    trig_l[[500, 1500]] = 1.0
    trig_r = np.zeros(n_samples)  # Zero right triggers

    scipy.io.savemat(str(tmp_dir / "s01.mat"), {
        "eeg": {
            "imagery_left": im_l,
            "imagery_right": im_r,
            "imagery_event": trig_l,
            "imagery_event_right": trig_r,
            "srate": 512.0,
        }
    })
    with pytest.raises(ValueError, match="both left and right"):
        adapter_cho.get_subject_epochs(1, tmin=0.0, tmax=1.0)

    # 2. HighGamma with only left_hand annotations
    (tmp_dir / "subject_2.edf").touch()
    raw_info = mne.create_info(ch_names=[f"eeg_{i}" for i in range(1, 45)], sfreq=250.0, ch_types="eeg")
    raw = mne.io.RawArray(np.random.randn(44, 25000) * 1e-5, raw_info, verbose="ERROR")
    raw.set_annotations(mne.Annotations(
        onset=[1.0, 3.0],
        duration=[0.5, 0.5],
        description=["left_hand", "left_hand"]
    ))
    with patch("mne.io.read_raw_edf", return_value=raw):
        adapter_hg = HighGammaAdapter(tmp_dir)
        with pytest.raises(ValueError, match="both left_hand and right_hand"):
            adapter_hg.get_subject_epochs(2, tmin=0.0, tmax=1.0)
