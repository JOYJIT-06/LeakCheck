import numpy as np
import pytest

from emi.signal_utils import band_timecourse, percent_change


def test_constant_power_gives_zero_change():
    times = np.linspace(-1, 4, 51)
    power = np.full((2, 3, 51), 5.0)
    out = percent_change(power, times, (-0.8, -0.1))
    assert np.allclose(out, 0.0)


def test_doubling_after_baseline_is_plus_100_percent():
    times = np.linspace(-1, 4, 501)
    power = np.where(times < 0, 1.0, 2.0)[None, None, :]
    out = percent_change(power, times, (-0.8, -0.1))
    assert np.allclose(out[0, 0, times >= 0], 100.0)
    assert np.allclose(out[0, 0, times < 0], 0.0)


def test_halving_is_minus_50_percent_erd():
    times = np.linspace(-1, 4, 501)
    power = np.where(times < 0, 4.0, 2.0)[None, None, :]
    out = percent_change(power, times, (-0.8, -0.1))
    assert np.allclose(out[0, 0, times >= 0], -50.0)


def test_empty_baseline_raises():
    with pytest.raises(ValueError):
        percent_change(np.ones((1, 1, 10)), np.linspace(0, 1, 10), (-5, -4))


def test_band_timecourse_averages_only_requested_band():
    freqs = np.array([4.0, 8.0, 10.0, 12.0, 20.0])
    power = np.zeros((1, 5, 3))
    power[0, 1:4, :] = 3.0   # 8-12 Hz rows
    power[0, 4, :] = 100.0   # 20 Hz should be ignored
    out = band_timecourse(power, freqs, (8.0, 12.0))
    assert out.shape == (1, 3)
    assert np.allclose(out, 3.0)


def test_band_with_no_frequencies_raises():
    with pytest.raises(ValueError):
        band_timecourse(np.ones((1, 3, 2)), np.array([1.0, 2.0, 3.0]), (8, 12))


# ---- label-blind quality control (v0.3) ----
from emi.signal_utils import adaptive_reject_mask, detect_bad_channels, trial_artifact_statistic  # noqa: E402


def _shared_signal_recording(seed=0, n_ch=32, n=20000):
    rng = np.random.default_rng(seed)
    return 1.0 * rng.standard_normal((n_ch, n)) + 1.6 * rng.standard_normal(n)     # channels share a signal


def test_bad_channel_detection_finds_loud_flat_and_disconnected_channels():
    d = _shared_signal_recording()
    rng = np.random.default_rng(1)
    d[5] *= 12
    d[9] = 0.0
    d[20] = rng.standard_normal(d.shape[1]) * 2.0
    bad, why = detect_bad_channels(d)
    assert bad == [5, 9, 20] and why[9] == "flat"


def test_bad_channel_detection_flags_nothing_on_a_clean_recording():
    assert detect_bad_channels(_shared_signal_recording(3))[0] == []


def test_bad_channel_detection_refuses_a_recording_where_too_many_channels_are_bad():
    d = _shared_signal_recording(4)
    d[:10] *= 15
    try:
        detect_bad_channels(d)
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_detection_uses_no_labels_and_is_deterministic():
    d = _shared_signal_recording(5)
    d[2] *= 20
    assert detect_bad_channels(d) == detect_bad_channels(d.copy())


def test_adaptive_rejection_removes_artifact_trials_and_respects_floor_and_cap():
    rng = np.random.default_rng(0)
    X = rng.standard_normal((45, 16, 320)) * 20
    X[17, 2, :50] += 3000
    X[30] *= 12
    keep, thr = adaptive_reject_mask(trial_artifact_statistic(X), k=6, floor=200, cap=800)
    assert (~keep).nonzero()[0].tolist() == [17, 30] and 200 <= thr <= 800
    _, thr_floor = adaptive_reject_mask(np.array([100.0] * 10 + [5000.0]), k=6, floor=200, cap=800)
    assert thr_floor == 200                                     # tiny spread -> the floor protects clean trials
    wide = np.linspace(100, 2000, 41)
    keep_w, thr_cap = adaptive_reject_mask(wide, k=6, floor=200, cap=800)
    assert thr_cap == 800 and not keep_w[-1] and keep_w[0]       # huge spread -> the cap still rejects gross artifacts


def test_adaptive_rejection_keeps_clean_subjects_whole():
    rng = np.random.default_rng(2)
    X = rng.standard_normal((45, 16, 320)) * 20
    keep, _ = adaptive_reject_mask(trial_artifact_statistic(X), k=6, floor=200, cap=800)
    assert keep.all()
