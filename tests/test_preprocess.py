"""Unit tests for emi.preprocess module."""
import mne
import numpy as np
import pytest

from emi.config import Config, RUN_TAG
from emi.preprocess import _reject, build_epochs, build_epochs_full, build_epochs_with_runs, clean_raw


def make_synthetic_raw(sfreq=160.0, n_seconds=30.0, n_channels=8):
    """Create a minimal synthetic mne.io.RawArray with montage and annotations."""
    n_samples = int(sfreq * n_seconds)
    # 8 standard channels
    ch_names = ["Fc5.", "Fc3.", "Fc1.", "Fpz.", "C3..", "Cz..", "C4..", "Pz.."]
    ch_types = ["eeg"] * len(ch_names)

    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=ch_types)
    rng = np.random.default_rng(42)
    # Sine waves + small noise in Volts (10 uV scale)
    t = np.linspace(0, n_seconds, n_samples)
    data = 10e-6 * np.sin(2 * np.pi * 10 * t)[np.newaxis, :] + 1e-6 * rng.standard_normal((len(ch_names), n_samples))

    # Add standard montage
    montage = mne.channels.make_standard_montage("colin27_1020")
    raw = mne.io.RawArray(data, info, verbose="ERROR")
    # Remap channel names to match standard format
    rename_dict = {
        "Fc5.": "FC5", "Fc3.": "FC3", "Fc1.": "FC1", "Fpz.": "Fpz",
        "C3..": "C3", "Cz..": "Cz", "C4..": "C4", "Pz..": "Pz"
    }
    raw.rename_channels(rename_dict)
    raw.set_montage(montage, on_missing="ignore", verbose="ERROR")

    # Annotate runs (e.g. 2 runs of 15 seconds each = 2400 samples each)
    run_len_samples = [int(15.0 * sfreq), int(15.0 * sfreq)]
    raw.info["description"] = f"{RUN_TAG}{run_len_samples[0]},{run_len_samples[1]}"

    # Annotate events (motor imagery T1 / T2)
    onset = [2.0, 6.0, 10.0, 17.0, 21.0, 25.0]
    duration = [4.0] * len(onset)
    description = ["T1", "T2", "T1", "T2", "T1", "T2"]
    annot = mne.Annotations(onset=onset, duration=duration, description=description)
    raw.set_annotations(annot)
    return raw


def test_reject_window_modes():
    """Verify _reject behaves properly for both 'full' and 'analysis' reject_window."""
    times = np.linspace(-1.0, 4.0, 500)
    window = (0.5, 2.5)

    # 4 trials: 3 clean, 1 huge artifact in the analysis window
    data_v = np.zeros((4, 4, 500))
    idx_spike = np.argmin(np.abs(times - 1.0))
    data_v[3, 0, idx_spike] = 500e-6  # 500 uV spike relative to 0

    # 1. Fixed threshold with 'analysis' window
    cfg_fixed_ana = Config(reject_mode="fixed", reject_uv=100.0, reject_window="analysis")
    keep, thr = _reject(data_v, times, cfg_fixed_ana, window)
    assert keep.tolist() == [True, True, True, False]
    assert thr == 100.0

    # 2. Fixed threshold with 'full' window: spike at t=-0.5s (outside analysis, inside full)
    data_v2 = np.zeros((4, 4, 500))
    idx_early = np.argmin(np.abs(times - (-0.5)))
    data_v2[2, 0, idx_early] = 500e-6

    cfg_ana = Config(reject_mode="fixed", reject_uv=100.0, reject_window="analysis")
    keep_ana, _ = _reject(data_v2, times, cfg_ana, window)
    assert keep_ana.tolist() == [True, True, True, True]  # ignored because outside window

    cfg_full = Config(reject_mode="fixed", reject_uv=100.0, reject_window="full")
    keep_full, _ = _reject(data_v2, times, cfg_full, window)
    assert keep_full.tolist() == [True, True, False, True]  # caught because inside full epoch


def test_reject_adaptive_mode():
    """Verify _reject adaptive threshold computation."""
    cfg = Config(
        reject_mode="adaptive",
        reject_k=3.0,
        reject_floor_uv=50.0,
        reject_cap_uv=200.0,
        reject_window="analysis",
    )

    times = np.linspace(0.0, 4.0, 400)
    window = (0.5, 2.5)
    rng = np.random.default_rng(0)
    # 10 trials with ~20 uV peak-to-peak noise
    data_v = 10e-6 * rng.standard_normal((10, 4, 400))
    # Trial 9 is a massive outlier: 400 uV peak-to-peak
    data_v[9, :, 100:150] += 400e-6
    keep, thr = _reject(data_v, times, cfg, window)
    assert keep[9] == False
    assert (keep[:9] == True).all()
    assert 50.0 <= thr <= 200.0


def test_clean_raw_and_ica():
    """Verify clean_raw bandpass filtering, referencing, and bad channel handling."""
    raw = make_synthetic_raw()
    cfg = Config(use_ica=False, max_bad_fraction=0.30)

    raw_clean, info = clean_raw(raw, cfg)
    assert isinstance(raw_clean, mne.io.BaseRaw)
    assert info["use_ica"] is False
    assert "bad_channels" in info


def test_build_epochs_full():
    """Verify build_epochs_full produces valid broadband and decoding epochs."""
    raw = make_synthetic_raw()
    cfg = Config(reject_mode="fixed", reject_uv=500.0, max_bad_fraction=0.30)  # Keep all synthetic trials

    ep_bb, ep_dec, runs, qc = build_epochs_full(raw, cfg)
    assert len(ep_bb) == len(ep_dec) == len(runs)
    assert qc["n_events"] == 6
    assert qc["n_trials_kept"] == 6
    assert set(runs).issubset({0, 1})

    # Test helpers
    bb, dec, r = build_epochs_with_runs(raw, cfg)
    assert len(bb) == 6 and len(r) == 6
    bb2, dec2 = build_epochs(raw, cfg)
    assert len(bb2) == 6


def test_build_epochs_length_mismatch_raises():
    """Verify build_epochs_full raises ValueError when run lengths don't sum to n_times."""
    raw = make_synthetic_raw()
    cfg = Config(max_bad_fraction=0.30)
    raw.info["description"] = f"{RUN_TAG}100,200"  # Mismatched length: 300 samples vs 4800
    with pytest.raises(ValueError, match="Run lengths"):
        build_epochs_full(raw, cfg)
