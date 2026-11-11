import numpy as np
import pytest

from emi.signal_utils import (
    adaptive_reject_mask,
    band_timecourse,
    detect_bad_channels,
    parse_run_lengths,
    percent_change,
    ptp_reject_indices,
    trial_artifact_statistic,
    trial_run_ids,
)


# ---- Time-frequency helpers ----

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


def test_percent_change_rejects_mismatched_time_axis():
    with pytest.raises(ValueError, match="match"):
        percent_change(np.ones((1, 1, 10)), np.arange(9), (1, 3))


@pytest.mark.parametrize(
    "baseline",
    [
        (3, 1),
        (np.nan, 2),
        (1, np.inf),
        (1,),
    ],
)
def test_percent_change_rejects_invalid_baseline(baseline):
    with pytest.raises(ValueError):
        percent_change(np.ones((1, 1, 10)), np.arange(10), baseline)


def test_percent_change_rejects_nonpositive_baseline_power():
    power = np.ones((1, 1, 10))
    power[..., 2:5] = 0
    with pytest.raises(ValueError, match="positive"):
        percent_change(power, np.arange(10), (2, 4))


def test_percent_change_rejects_nonfinite_power():
    power = np.ones((1, 1, 10))
    power[0, 0, 3] = np.nan
    with pytest.raises(ValueError, match="finite"):
        percent_change(power, np.arange(10), (1, 4))


def test_band_timecourse_averages_only_requested_band():
    freqs = np.array([4.0, 8.0, 10.0, 12.0, 20.0])
    power = np.zeros((1, 5, 3))
    power[0, 1:4, :] = 3.0
    power[0, 4, :] = 100.0
    out = band_timecourse(power, freqs, (8.0, 12.0))
    assert out.shape == (1, 3)
    assert np.allclose(out, 3.0)


def test_band_with_no_frequencies_raises():
    with pytest.raises(ValueError):
        band_timecourse(np.ones((1, 3, 2)), np.array([1.0, 2.0, 3.0]), (8, 12))


def test_band_timecourse_rejects_mismatched_frequency_axis():
    with pytest.raises(ValueError, match="match"):
        band_timecourse(np.ones((1, 3, 2)), np.array([1.0, 2.0]), (1, 2))


def test_band_timecourse_rejects_reversed_band():
    with pytest.raises(ValueError, match="lower bound"):
        band_timecourse(np.ones((1, 3, 2)), np.array([1.0, 2.0, 3.0]), (3, 1))


# ---- Run metadata and run assignment ----

def test_parse_run_lengths_reads_valid_metadata():
    assert parse_run_lengths("emi_run_lengths:100,200,300", "emi_run_lengths:") == [
        100, 200, 300
    ]


@pytest.mark.parametrize(
    "description",
    [
        None,
        "",
        "other_tag:100,200",
        "emi_run_lengths:",
        "emi_run_lengths:100,,200",
        "emi_run_lengths:100,abc,200",
        "emi_run_lengths:100,0,200",
        "emi_run_lengths:100,-5,200",
    ],
)
def test_parse_run_lengths_rejects_invalid_metadata(description):
    with pytest.raises(ValueError):
        parse_run_lengths(description, "emi_run_lengths:")


def test_trial_run_ids_assigns_events_at_run_boundaries_correctly():
    # Runs cover [50, 150), [150, 250), and [250, 350).
    samples = np.array([50, 149, 150, 249, 250, 349])
    result = trial_run_ids(samples, [100, 100, 100], first_samp=50)
    assert result.tolist() == [0, 0, 1, 1, 2, 2]


def test_trial_run_ids_supports_unsorted_events():
    samples = np.array([250, 50, 150, 149])
    result = trial_run_ids(samples, [100, 100, 100], first_samp=50)
    assert result.tolist() == [2, 0, 1, 0]


@pytest.mark.parametrize(
    "samples",
    [
        np.array([49]),
        np.array([350]),
    ],
)
def test_trial_run_ids_rejects_events_outside_recording(samples):
    with pytest.raises(ValueError):
        trial_run_ids(samples, [100, 100, 100], first_samp=50)


def test_trial_run_ids_rejects_noninteger_event_samples():
    with pytest.raises(ValueError, match="integer"):
        trial_run_ids(np.array([50.5]), [100, 100], first_samp=50)


@pytest.mark.parametrize(
    "lengths",
    [
        [],
        [100, 0, 100],
        [100, -1, 100],
        [100.5, 100],
    ],
)
def test_trial_run_ids_rejects_invalid_run_lengths(lengths):
    with pytest.raises(ValueError):
        trial_run_ids(np.array([10]), lengths)


# ---- Fixed-threshold rejection ----

def test_ptp_reject_indices_uses_microvolt_threshold():
    data = np.zeros((3, 2, 5))

    # Exactly 100 uV peak-to-peak.
    data[1, 0, 1] = 100e-6

    # 200 uV peak-to-peak.
    data[2, 1, 0] = -100e-6
    data[2, 1, 1] = 100e-6

    # The strict > rule should retain trial 1 and reject trial 2.
    assert ptp_reject_indices(data, threshold_uv=100).tolist() == [2]

def test_ptp_reject_indices_rejects_if_any_channel_exceeds_threshold():
    data = np.zeros((2, 3, 5))
    data[1, 2, 0] = -150e-6
    data[1, 2, 1] = 150e-6
    assert ptp_reject_indices(data, threshold_uv=200).tolist() == [1]


@pytest.mark.parametrize(
    "data",
    [
        np.ones((2, 5)),
        np.ones((2, 3, 0)),
        np.full((2, 3, 5), np.nan),
    ],
)
def test_ptp_reject_indices_rejects_invalid_data(data):
    with pytest.raises(ValueError):
        ptp_reject_indices(data, threshold_uv=100)


def test_ptp_reject_indices_rejects_negative_threshold():
    with pytest.raises(ValueError):
        ptp_reject_indices(np.zeros((2, 3, 5)), threshold_uv=-1)


# ---- Label-blind bad-channel quality control ----

def _shared_signal_recording(seed=0, n_ch=32, n=20000):
    rng = np.random.default_rng(seed)
    return (
        1.0 * rng.standard_normal((n_ch, n))
        + 1.6 * rng.standard_normal(n)
    )


def test_bad_channel_detection_finds_loud_flat_and_disconnected_channels():
    d = _shared_signal_recording()
    rng = np.random.default_rng(1)
    d[5] *= 12
    d[9] = 0.0
    d[20] = rng.standard_normal(d.shape[1]) * 2.0

    bad, why = detect_bad_channels(d)

    assert bad == [5, 9, 20]
    assert why[9] == "flat"


def test_bad_channel_detection_flags_nothing_on_a_clean_recording():
    assert detect_bad_channels(_shared_signal_recording(3))[0] == []


def test_bad_channel_detection_refuses_too_many_bad_channels():
    d = _shared_signal_recording(4)
    d[:10] *= 15

    with pytest.raises(ValueError, match="recording is suspect"):
        detect_bad_channels(d)


def test_detection_is_deterministic():
    d = _shared_signal_recording(5)
    d[2] *= 20
    assert detect_bad_channels(d) == detect_bad_channels(d.copy())


def test_bad_channel_detection_rejects_nonfinite_data():
    d = _shared_signal_recording()
    d[0, 10] = np.nan

    with pytest.raises(ValueError, match="finite"):
        detect_bad_channels(d)


def test_bad_channel_detection_rejects_all_flat_channels():
    with pytest.raises(ValueError):
        detect_bad_channels(np.zeros((8, 1000)))


def test_bad_channel_detection_rejects_too_few_channels():
    with pytest.raises(ValueError, match="three channels"):
        detect_bad_channels(np.ones((2, 1000)))


def test_bad_channel_detection_rejects_invalid_fraction():
    d = _shared_signal_recording()

    with pytest.raises(ValueError, match="max_bad_fraction"):
        detect_bad_channels(d, max_bad_fraction=1.5)


# ---- Adaptive trial rejection ----

def test_adaptive_rejection_removes_artifact_trials_and_respects_floor_and_cap():
    rng = np.random.default_rng(0)
    X = rng.standard_normal((45, 16, 320)) * 20
    X[17, 2, :50] += 3000
    X[30] *= 12

    keep, thr = adaptive_reject_mask(
        trial_artifact_statistic(X), k=6, floor=200, cap=800
    )

    assert (~keep).nonzero()[0].tolist() == [17, 30]
    assert 200 <= thr <= 800

    _, thr_floor = adaptive_reject_mask(
        np.array([100.0] * 10 + [5000.0]), k=6, floor=200, cap=800
    )
    assert thr_floor == 200

    wide = np.linspace(100, 2000, 41)
    keep_w, thr_cap = adaptive_reject_mask(wide, k=6, floor=200, cap=800)
    assert thr_cap == 800
    assert not keep_w[-1]
    assert keep_w[0]


def test_adaptive_rejection_keeps_clean_subjects_whole():
    rng = np.random.default_rng(2)
    X = rng.standard_normal((45, 16, 320)) * 20
    keep, _ = adaptive_reject_mask(
        trial_artifact_statistic(X), k=6, floor=200, cap=800
    )
    assert keep.all()


def test_adaptive_rejection_rejects_empty_statistic():
    with pytest.raises(ValueError, match="non-empty"):
        adaptive_reject_mask(np.array([]))


def test_adaptive_rejection_rejects_nonfinite_statistic():
    with pytest.raises(ValueError, match="finite"):
        adaptive_reject_mask(np.array([1.0, np.nan, 2.0]))


def test_adaptive_rejection_rejects_negative_k():
    with pytest.raises(ValueError, match="k"):
        adaptive_reject_mask(np.array([1.0, 2.0]), k=-1)


def test_adaptive_rejection_rejects_floor_above_cap():
    with pytest.raises(ValueError, match="floor must be <="):
        adaptive_reject_mask(np.array([1.0, 2.0]), floor=300, cap=200)


def test_adaptive_rejection_threshold_is_clipped_to_floor_and_cap():
    keep_floor, threshold_floor = adaptive_reject_mask(
        np.ones(10), floor=200, cap=800
    )
    keep_cap, threshold_cap = adaptive_reject_mask(
        np.linspace(100, 2000, 41), floor=200, cap=800
    )

    assert threshold_floor == 200
    assert keep_floor.all()
    assert threshold_cap == 800
    assert not keep_cap[-1]


# ---- Trial artifact statistic ----

def test_trial_artifact_statistic_returns_one_value_per_trial():
    X = np.zeros((4, 3, 10))
    X[:, :, 0] = -1.0
    X[:, :, 1] = 1.0

    result = trial_artifact_statistic(X)
    assert result.shape == (4,)
    assert np.allclose(result, 2.0)


def test_trial_artifact_statistic_rejects_invalid_dimensions():
    with pytest.raises(ValueError):
        trial_artifact_statistic(np.ones((4, 10)))


def test_trial_artifact_statistic_rejects_empty_dimensions():
    with pytest.raises(ValueError):
        trial_artifact_statistic(np.ones((4, 3, 0)))


def test_trial_artifact_statistic_rejects_nonfinite_data():
    X = np.ones((4, 3, 10))
    X[0, 0, 0] = np.inf

    with pytest.raises(ValueError, match="finite"):
        trial_artifact_statistic(X)


def test_trial_artifact_statistic_rejects_invalid_percentile():
    with pytest.raises(ValueError, match="between 0 and 100"):
        trial_artifact_statistic(np.ones((4, 3, 10)), q=101)