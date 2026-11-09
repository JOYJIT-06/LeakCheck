"""Empirical Adversarial Edge-Case Probes for Cho2017Adapter and HighGammaAdapter.

Verification suite authored by: teamwork_challenger (Agent: challenger_m2_round2_1)
Target: Cho2017Adapter and HighGammaAdapter in src/emi/datasets_adapters.py
Branch: v2-dev (Commit a37f63a)
Python environment: D:\anaconda\envs\leakcheck\python.exe
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
    _partition_runs,
    _standardize_epoch_array,
    _parse_binary_labels,
)
from emi.splitters import loro_splits, size_matched_random_repeats


@pytest.fixture
def tmp_dir():
    td = Path(tempfile.mkdtemp(prefix="leakcheck_adv_probes_"))
    yield td
    shutil.rmtree(td, ignore_errors=True)


# ======================================================================
# 1. Cho2017Adapter Adversarial Continuous & Epoched Probes
# ======================================================================

class TestCho2017AdversarialContinuous:
    """Stress-test Cho2017 continuous acquisition struct parsing and run assignments."""

    def test_cho2017_continuous_mismatched_runs_rejection(self, tmp_dir):
        """Continuous cue detection yields 6 epochs, but mat['runs'] has length 50.
        
        Contract requirement: Candidate runs whose length != len(y) must be rejected,
        falling back to deterministic _partition_runs(len(y)).
        """
        adapter = Cho2017Adapter(tmp_dir)
        n_samples = 4000
        im_l = np.random.randn(64, n_samples) * 10.0
        im_r = np.random.randn(64, n_samples) * 10.0
        trig_l = np.zeros(n_samples)
        trig_l[[500, 1500, 2500]] = 1.0  # 3 left trials
        trig_r = np.zeros(n_samples)
        trig_r[[600, 1600, 2600]] = 1.0  # 3 right trials

        # Mismatched runs: length 50 instead of 6
        mismatched_runs = np.repeat([1, 2], 25)

        scipy.io.savemat(str(tmp_dir / "s01.mat"), {
            "eeg": {
                "imagery_left": im_l,
                "imagery_right": im_r,
                "imagery_event": trig_l,
                "imagery_event_right": trig_r,
                "srate": 512.0,
            },
            "runs": mismatched_runs,
        })

        data = adapter.get_subject_epochs(1, tmin=0.0, tmax=1.0)
        assert data["X"].shape[0] == 6
        assert len(data["y"]) == 6
        assert len(data["runs"]) == 6, f"len(runs)={len(data['runs'])} must equal len(y)=6"
        assert len(np.unique(data["runs"])) > 1, "Must contain multi-run partition for LORO"

        # Downstream LORO split verification
        folds = loro_splits(data["runs"])[0]
        assert len(folds) >= 2
        for train_idx, test_idx in folds:
            assert len(train_idx) > 0 and len(test_idx) > 0
            assert set(train_idx).isdisjoint(set(test_idx))

        # Downstream size-matched random repeats verification
        sm_repeats = size_matched_random_repeats(data["y"], data["runs"], repeats=5, seed=42)
        assert len(sm_repeats) == 5

    def test_cho2017_continuous_all_zero_cue_raises_value_error(self, tmp_dir):
        """Continuous struct where triggers are all zero must raise ValueError."""
        adapter = Cho2017Adapter(tmp_dir)
        n_samples = 4000
        im_l = np.random.randn(64, n_samples) * 10.0
        im_r = np.random.randn(64, n_samples) * 10.0

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

    def test_cho2017_continuous_single_class_left_only_raises(self, tmp_dir):
        """Continuous struct where only left triggers exist must raise ValueError."""
        adapter = Cho2017Adapter(tmp_dir)
        n_samples = 4000
        im_l = np.random.randn(64, n_samples) * 10.0
        im_r = np.random.randn(64, n_samples) * 10.0
        trig_l = np.zeros(n_samples)
        trig_l[[500, 1500, 2500]] = 1.0

        scipy.io.savemat(str(tmp_dir / "s01.mat"), {
            "eeg": {
                "imagery_left": im_l,
                "imagery_right": im_r,
                "imagery_event": trig_l,
                "imagery_event_right": np.zeros(n_samples),
                "srate": 512.0,
            }
        })
        with pytest.raises(ValueError, match="Could not extract both left and right"):
            adapter.get_subject_epochs(1)

    def test_cho2017_continuous_single_class_right_only_raises(self, tmp_dir):
        """Continuous struct where only right triggers exist must raise ValueError."""
        adapter = Cho2017Adapter(tmp_dir)
        n_samples = 4000
        im_l = np.random.randn(64, n_samples) * 10.0
        im_r = np.random.randn(64, n_samples) * 10.0
        trig_r = np.zeros(n_samples)
        trig_r[[500, 1500, 2500]] = 1.0

        scipy.io.savemat(str(tmp_dir / "s01.mat"), {
            "eeg": {
                "imagery_left": im_l,
                "imagery_right": im_r,
                "imagery_event": np.zeros(n_samples),
                "imagery_event_right": trig_r,
                "srate": 512.0,
            }
        })
        with pytest.raises(ValueError, match="Could not extract both left and right"):
            adapter.get_subject_epochs(1)

    def test_cho2017_continuous_boundary_slicing_edge_cases(self, tmp_dir):
        """Probe boundary conditions in continuous trigger onset slicing:
        - Trigger at exact index 0 with tmin=0.0 (valid in-bounds)
        - Trigger at index 0 with tmin=-0.2 (negative start sample -> out of bounds, safely skipped)
        - Trigger near end of recording where onset + s_max > n_samples (safely skipped)
        - Sustained pulse triggers (multi-sample high) -> leading-edge detection
        """
        adapter = Cho2017Adapter(tmp_dir)
        n_samples = 4000
        im_l = np.random.randn(64, n_samples) * 10.0
        im_r = np.random.randn(64, n_samples) * 10.0

        # Pulse triggers with width = 10 samples
        trig_l = np.zeros(n_samples)
        trig_l[0:10] = 1.0          # Onset at 0
        trig_l[1000:1010] = 1.0    # Onset at 1000
        trig_l[3800:3810] = 1.0    # Onset at 3800 (with tmax=1.0 at 512Hz, 3800+512=4312 > 4000 -> OOB)

        trig_r = np.zeros(n_samples)
        trig_r[500:510] = 1.0      # Onset at 500
        trig_r[1500:1510] = 1.0    # Onset at 1500
        trig_r[3900:3910] = 1.0    # Onset at 3900 -> OOB

        scipy.io.savemat(str(tmp_dir / "s01.mat"), {
            "eeg": {
                "imagery_left": im_l,
                "imagery_right": im_r,
                "imagery_event": trig_l,
                "imagery_event_right": trig_r,
                "srate": 512.0,
            }
        })

        # tmin=0.0, tmax=1.0 with target_fs=250.0 (resampled):
        # Left valid onsets: 0, 1000. 3800 is dropped (OOB). Total left = 2.
        # Right valid onsets: 500, 1500. 3900 is dropped (OOB). Total right = 2.
        data_resampled = adapter.get_subject_epochs(1, target_fs=250.0, tmin=0.0, tmax=1.0)
        assert data_resampled["X"].shape == (4, 64, 250)
        assert np.array_equal(data_resampled["y"], [0, 0, 1, 1])

        # tmin=0.0, tmax=1.0 with target_fs=512.0 (native srate):
        data_native = adapter.get_subject_epochs(1, target_fs=512.0, tmin=0.0, tmax=1.0)
        assert data_native["X"].shape == (4, 64, 512)
        assert np.array_equal(data_native["y"], [0, 0, 1, 1])

        # Test with negative tmin = -0.2:
        # Onset at 0 gives st = 0 - 102 = -102 < 0 -> dropped!
        # Left valid onsets remaining: 1000. Total left = 1.
        # Right valid onsets remaining: 500, 1500. Total right = 2.
        data_neg = adapter.get_subject_epochs(1, tmin=-0.2, tmax=0.8)
        assert data_neg["X"].shape[0] == 3
        assert np.array_equal(data_neg["y"], [0, 1, 1])

    def test_cho2017_continuous_single_run_rejection(self, tmp_dir):
        """Candidate runs with len == len(y) but len(unique(candidate_runs)) == 1
        must be rejected in favor of _partition_runs.
        """
        adapter = Cho2017Adapter(tmp_dir)
        n_samples = 4000
        im_l = np.random.randn(64, n_samples) * 10.0
        im_r = np.random.randn(64, n_samples) * 10.0
        trig_l = np.zeros(n_samples)
        trig_l[[500, 1500]] = 1.0
        trig_r = np.zeros(n_samples)
        trig_r[[600, 1600]] = 1.0

        scipy.io.savemat(str(tmp_dir / "s01.mat"), {
            "eeg": {
                "imagery_left": im_l,
                "imagery_right": im_r,
                "imagery_event": trig_l,
                "imagery_event_right": trig_r,
                "srate": 512.0,
            },
            "runs": np.array([0, 0, 0, 0]),  # Single-run degenerate metadata
        })

        data = adapter.get_subject_epochs(1, tmin=0.0, tmax=1.0)
        assert len(data["runs"]) == 4
        assert len(np.unique(data["runs"])) > 1, "Single-run metadata must be rejected"

    def test_cho2017_continuous_string_run_labels_mapped_to_integers(self, tmp_dir):
        """String run labels in mat['runs'] matching len(y) must be converted to numeric integers."""
        adapter = Cho2017Adapter(tmp_dir)
        n_samples = 4000
        im_l = np.random.randn(64, n_samples) * 10.0
        im_r = np.random.randn(64, n_samples) * 10.0
        trig_l = np.zeros(n_samples)
        trig_l[[500, 1500]] = 1.0
        trig_r = np.zeros(n_samples)
        trig_r[[600, 1600]] = 1.0

        scipy.io.savemat(str(tmp_dir / "s01.mat"), {
            "eeg": {
                "imagery_left": im_l,
                "imagery_right": im_r,
                "imagery_event": trig_l,
                "imagery_event_right": trig_r,
                "srate": 512.0,
            },
            "runs": np.array(["runA", "runA", "runB", "runB"], dtype=object),
        })

        data = adapter.get_subject_epochs(1, tmin=0.0, tmax=1.0)
        assert np.issubdtype(data["runs"].dtype, np.integer)
        assert len(np.unique(data["runs"])) == 2
        assert len(data["runs"]) == 4


class TestCho2017AdversarialEpoched:
    """Stress-test Cho2017 epoched array handling and label extraction."""

    def test_cho2017_epoched_mismatched_runs_rejection(self, tmp_dir):
        """Epoched 3D matrix has 8 trials, but mat contains runs with 20 elements."""
        adapter = Cho2017Adapter(tmp_dir)
        X = np.random.randn(8, 64, 250) * 10.0
        y = np.array([0, 0, 0, 0, 1, 1, 1, 1])

        scipy.io.savemat(str(tmp_dir / "s01.mat"), {
            "eeg": X,
            "y": y,
            "runs": np.arange(20),  # len 20 != 8
        })

        data = adapter.get_subject_epochs(1)
        assert len(data["runs"]) == 8
        assert len(np.unique(data["runs"])) > 1

    def test_cho2017_epoched_single_class_y_handled_or_rejected(self, tmp_dir):
        """Verify behavior when epoched MAT contains single-class labels."""
        adapter = Cho2017Adapter(tmp_dir)
        X = np.random.randn(6, 64, 250) * 10.0
        y_single = np.zeros(6, dtype=int)

        scipy.io.savemat(str(tmp_dir / "s01.mat"), {
            "eeg": X,
            "y": y_single,
        })

        data = adapter.get_subject_epochs(1)
        # _parse_binary_labels falls back to balanced binary labels [0,0,0,1,1,1] when single class given
        assert len(np.unique(data["y"])) == 2
        assert len(data["runs"]) == 6


# ======================================================================
# 2. HighGammaAdapter Adversarial Probes
# ======================================================================

class TestHighGammaAdversarialDigitizeAndRuns:
    """Stress-test HighGamma run boundary digitization, edge cases, and fallbacks."""

    def test_highgamma_np_digitize_zero_boundary_markers(self, tmp_dir):
        """EDF with no boundary markers should safely fall back to _partition_runs."""
        (tmp_dir / "subject_1.edf").touch()
        raw_info = mne.create_info(ch_names=[f"eeg_{i}" for i in range(1, 45)], sfreq=250.0, ch_types="eeg")
        raw = mne.io.RawArray(np.random.randn(44, 25000) * 1e-5, raw_info, verbose="ERROR")

        annots = mne.Annotations(
            onset=[1.0, 3.0, 5.0, 7.0, 9.0, 11.0],
            duration=[0.5] * 6,
            description=["left_hand", "right_hand", "left_hand", "right_hand", "left_hand", "right_hand"],
        )
        raw.set_annotations(annots)

        with patch("mne.io.read_raw_edf", return_value=raw):
            adapter = HighGammaAdapter(tmp_dir)
            data = adapter.get_subject_epochs(1, tmin=0.0, tmax=1.0)
            assert data["X"].shape[0] == 6
            assert len(data["runs"]) == 6
            assert len(np.unique(data["runs"])) > 1

    def test_highgamma_np_digitize_single_boundary_marker(self, tmp_dir):
        """EDF with only 1 boundary marker (len(run_starts) < 2) must fall back to _partition_runs."""
        (tmp_dir / "subject_1.edf").touch()
        raw_info = mne.create_info(ch_names=[f"eeg_{i}" for i in range(1, 45)], sfreq=250.0, ch_types="eeg")
        raw = mne.io.RawArray(np.random.randn(44, 25000) * 1e-5, raw_info, verbose="ERROR")

        annots = mne.Annotations(
            onset=[1.0, 3.0, 5.0, 7.0, 10.0],
            duration=[0.5] * 5,
            description=["left_hand", "right_hand", "left_hand", "right_hand", "break"],
        )
        raw.set_annotations(annots)

        with patch("mne.io.read_raw_edf", return_value=raw):
            adapter = HighGammaAdapter(tmp_dir)
            data = adapter.get_subject_epochs(1, tmin=0.0, tmax=1.0)
            assert data["X"].shape[0] == 4
            assert len(data["runs"]) == 4
            assert len(np.unique(data["runs"])) > 1, "Must partition into multi-run for LORO"

    def test_highgamma_np_digitize_boundary_markers_all_after_trials(self, tmp_dir):
        """Boundary markers exist but are all chronologically AFTER the trials.
        
        Digitization: np.digitize returns 0 for all trials, digitized - 1 is -1,
        clipped to 0 -> single run degeneracy (unique=[0]).
        Contract requirement: Must detect len(np.unique(candidate_runs)) == 1
        and fall back to _partition_runs.
        """
        (tmp_dir / "subject_1.edf").touch()
        raw_info = mne.create_info(ch_names=[f"eeg_{i}" for i in range(1, 45)], sfreq=250.0, ch_types="eeg")
        raw = mne.io.RawArray(np.random.randn(44, 25000) * 1e-5, raw_info, verbose="ERROR")

        # Trials between 1.0s and 8.0s; run markers at 20.0s and 30.0s
        annots = mne.Annotations(
            onset=[1.0, 3.0, 5.0, 7.0, 20.0, 30.0],
            duration=[0.5] * 6,
            description=["left_hand", "right_hand", "left_hand", "right_hand", "run_start", "run_start"],
        )
        raw.set_annotations(annots)

        with patch("mne.io.read_raw_edf", return_value=raw):
            adapter = HighGammaAdapter(tmp_dir)
            data = adapter.get_subject_epochs(1, tmin=0.0, tmax=1.0)
            assert data["X"].shape[0] == 4
            assert len(data["runs"]) == 4
            assert len(np.unique(data["runs"])) > 1, "Must not degenerate into single run"

    def test_highgamma_np_digitize_boundary_markers_all_before_trials(self, tmp_dir):
        """Boundary markers exist but are all chronologically BEFORE all trials.
        
        Digitization: np.digitize returns len(run_starts) for all trials,
        clipped to len(run_starts)-1 -> single run degeneracy.
        Contract requirement: Must detect single-run and fall back to _partition_runs.
        """
        (tmp_dir / "subject_1.edf").touch()
        raw_info = mne.create_info(ch_names=[f"eeg_{i}" for i in range(1, 45)], sfreq=250.0, ch_types="eeg")
        raw = mne.io.RawArray(np.random.randn(44, 25000) * 1e-5, raw_info, verbose="ERROR")

        # Run markers at 0.5s and 1.0s; trials from 10.0s to 16.0s
        annots = mne.Annotations(
            onset=[0.5, 1.0, 10.0, 12.0, 14.0, 16.0],
            duration=[0.5] * 6,
            description=["run_start", "run_start", "left_hand", "right_hand", "left_hand", "right_hand"],
        )
        raw.set_annotations(annots)

        with patch("mne.io.read_raw_edf", return_value=raw):
            adapter = HighGammaAdapter(tmp_dir)
            data = adapter.get_subject_epochs(1, tmin=0.0, tmax=1.0)
            assert data["X"].shape[0] == 4
            assert len(data["runs"]) == 4
            assert len(np.unique(data["runs"])) > 1, "Must not degenerate into single run"

    def test_highgamma_np_digitize_authentic_run_splitting(self, tmp_dir):
        """When trials authentically span across boundary markers, genuine runs are preserved."""
        (tmp_dir / "subject_1.edf").touch()
        raw_info = mne.create_info(ch_names=[f"eeg_{i}" for i in range(1, 45)], sfreq=250.0, ch_types="eeg")
        raw = mne.io.RawArray(np.random.randn(44, 25000) * 1e-5, raw_info, verbose="ERROR")

        # Run 0: starts at 0.5s, trials at 1.0s, 3.0s
        # Run 1: starts at 5.0s, trials at 6.0s, 8.0s
        # Run 2: starts at 10.0s, trials at 11.0s, 13.0s
        annots = mne.Annotations(
            onset=[0.5, 1.0, 3.0, 5.0, 6.0, 8.0, 10.0, 11.0, 13.0],
            duration=[0.5] * 9,
            description=["run_start", "left_hand", "right_hand", "run_start", "left_hand", "right_hand", "run_start", "left_hand", "right_hand"],
        )
        raw.set_annotations(annots)

        with patch("mne.io.read_raw_edf", return_value=raw):
            adapter = HighGammaAdapter(tmp_dir)
            data = adapter.get_subject_epochs(1, tmin=0.0, tmax=1.0)
            assert data["X"].shape[0] == 6
            assert np.array_equal(data["runs"], [0, 0, 1, 1, 2, 2])
            assert len(np.unique(data["runs"])) == 3
            # Check fold validity in downstream loro_splits
            folds = loro_splits(data["runs"])[0]
            assert len(folds) == 3
            for tr, te in folds:
                assert len(tr) == 4 and len(te) == 2


class TestHighGammaAdversarialAnnotations:
    """Stress-test HighGamma annotation parsing and single-class protection."""

    def test_highgamma_single_class_left_only_raises(self, tmp_dir):
        """EDF with only left_hand annotations must raise descriptive ValueError."""
        (tmp_dir / "subject_1.edf").touch()
        raw_info = mne.create_info(ch_names=[f"eeg_{i}" for i in range(1, 45)], sfreq=250.0, ch_types="eeg")
        raw = mne.io.RawArray(np.random.randn(44, 25000) * 1e-5, raw_info, verbose="ERROR")

        annots = mne.Annotations(
            onset=[1.0, 3.0, 5.0],
            duration=[0.5] * 3,
            description=["left_hand", "left_hand", "left_hand"],
        )
        raw.set_annotations(annots)

        with patch("mne.io.read_raw_edf", return_value=raw):
            adapter = HighGammaAdapter(tmp_dir)
            with pytest.raises(ValueError, match="Could not identify both left_hand and right_hand"):
                adapter.get_subject_epochs(1)

    def test_highgamma_single_class_right_only_raises(self, tmp_dir):
        """EDF with only right_hand annotations must raise descriptive ValueError."""
        (tmp_dir / "subject_1.edf").touch()
        raw_info = mne.create_info(ch_names=[f"eeg_{i}" for i in range(1, 45)], sfreq=250.0, ch_types="eeg")
        raw = mne.io.RawArray(np.random.randn(44, 25000) * 1e-5, raw_info, verbose="ERROR")

        annots = mne.Annotations(
            onset=[1.0, 3.0, 5.0],
            duration=[0.5] * 3,
            description=["right_hand", "right_hand", "right_hand"],
        )
        raw.set_annotations(annots)

        with patch("mne.io.read_raw_edf", return_value=raw):
            adapter = HighGammaAdapter(tmp_dir)
            with pytest.raises(ValueError, match="Could not identify both left_hand and right_hand"):
                adapter.get_subject_epochs(1)

    def test_highgamma_single_class_arbitrary_single_key_raises(self, tmp_dir):
        """EDF with only 1 arbitrary event type must raise descriptive ValueError."""
        (tmp_dir / "subject_1.edf").touch()
        raw_info = mne.create_info(ch_names=[f"eeg_{i}" for i in range(1, 45)], sfreq=250.0, ch_types="eeg")
        raw = mne.io.RawArray(np.random.randn(44, 25000) * 1e-5, raw_info, verbose="ERROR")

        annots = mne.Annotations(
            onset=[1.0, 3.0],
            duration=[0.5, 0.5],
            description=["target_only", "target_only"],
        )
        raw.set_annotations(annots)

        with patch("mne.io.read_raw_edf", return_value=raw):
            adapter = HighGammaAdapter(tmp_dir)
            with pytest.raises(ValueError, match="Could not identify both left_hand and right_hand"):
                adapter.get_subject_epochs(1)

    def test_highgamma_diverse_run_boundary_keywords(self, tmp_dir):
        """Verify that all authentic run boundary keywords ('break', 'pause', 'rest', 'run', 'trial_start', '32766')
        are detected as run boundaries when multiple run starts are demarcated.
        """
        keywords = ["break", "pause", "rest", "run_transition", "trial_start_marker", "32766"]
        (tmp_dir / "subject_1.edf").touch()
        raw_info = mne.create_info(ch_names=[f"eeg_{i}" for i in range(1, 45)], sfreq=250.0, ch_types="eeg")
        raw = mne.io.RawArray(np.random.randn(44, 25000) * 1e-5, raw_info, verbose="ERROR")

        for kw in keywords:
            annots = mne.Annotations(
                onset=[0.5, 1.0, 2.0, 4.0, 5.0, 6.0],
                duration=[0.5] * 6,
                description=[kw, "left_hand", "right_hand", kw, "left_hand", "right_hand"],
            )
            raw.set_annotations(annots)
            with patch("mne.io.read_raw_edf", return_value=raw):
                adapter = HighGammaAdapter(tmp_dir)
                data = adapter.get_subject_epochs(1, tmin=0.0, tmax=1.0)
                assert data["X"].shape[0] == 4
                assert len(np.unique(data["runs"])) == 2, f"Keyword '{kw}' was not recognized as run boundary"
                assert np.array_equal(data["runs"], [0, 0, 1, 1])
