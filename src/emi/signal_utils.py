"""Small numpy-only helpers (no MNE needed, easy to unit test)."""
import numpy as np


def percent_change(power: np.ndarray, times: np.ndarray, baseline: tuple) -> np.ndarray:
    """Convert power to percent change relative to a baseline window.

    power: array whose LAST axis is time.
    Negative values = power decrease (event-related desynchronisation, ERD).
    """
    times = np.asarray(times)
    mask = (times >= baseline[0]) & (times <= baseline[1])
    if not mask.any():
        raise ValueError(f"Baseline {baseline} has no samples in the time axis.")
    ref = power[..., mask].mean(axis=-1, keepdims=True)
    if np.any(ref <= 0):
        raise ValueError("Baseline power must be positive.")
    return 100.0 * (power - ref) / ref


def band_timecourse(power: np.ndarray, freqs: np.ndarray, band: tuple) -> np.ndarray:
    """Average over frequencies inside `band`. power shape: (..., n_freqs, n_times)."""
    freqs = np.asarray(freqs)
    mask = (freqs >= band[0]) & (freqs <= band[1])
    if not mask.any():
        raise ValueError(f"No frequencies inside band {band}.")
    return power[..., mask, :].mean(axis=-2)


def parse_run_lengths(description: str, tag: str) -> list:
    """Read the run lengths (in samples) that data.load_raw stored in raw.info['description']."""
    if not description or not description.startswith(tag):
        raise ValueError("No run-length tag found. Load the data with emi.data.load_raw.")
    return [int(v) for v in description[len(tag):].split(",")]


def trial_run_ids(sample_indices, run_lengths, first_samp: int = 0) -> np.ndarray:
    """Run index (0, 1, 2, ...) of each event, from its sample index in the joined recording.

    Runs are joined back to back, so run k covers
    [first_samp + sum(len[:k]), first_samp + sum(len[:k+1])).
    """
    ends = first_samp + np.cumsum(np.asarray(run_lengths))
    ids = np.searchsorted(ends, np.asarray(sample_indices), side="right")
    if ids.size and ids.max() >= len(run_lengths):
        raise ValueError("An event lies beyond the end of the last run.")
    return ids


def ptp_reject_indices(data, threshold_uv):
    """Indices of epochs whose peak-to-peak amplitude exceeds `threshold_uv` (microvolts) on any channel.

    data: array (n_epochs, n_channels, n_times) in volts. Pure numpy, so it is easy to test.
    """
    ptp = data.max(axis=2) - data.min(axis=2)
    return np.where((ptp > threshold_uv * 1e-6).any(axis=1))[0]


def detect_bad_channels(data, z_thresh=4.0, corr_z_thresh=4.0, max_bad_fraction=0.15):
    """Label-blind bad-channel detection on continuous data (channels x samples). Returns (bad_indices, reasons).

    A channel is flagged when (a) it is flat, (b) its log-variance is a robust outlier across channels
    (median and MAD, |z| > z_thresh), or (c) its median absolute correlation with the other channels is a LOW
    robust outlier (z < -corr_z_thresh). The correlation rule is relative on purpose: absolute correlation levels
    depend on the reference and the montage, so a fixed cut-off would flag everything or nothing.
    Raises if more than max_bad_fraction of the channels would be flagged, because then the recording itself is
    suspect. Uses no labels and no accuracy.
    """
    data = np.asarray(data, float)
    n_ch = data.shape[0]
    var = data.var(axis=1)
    reasons = {}
    flat = np.where(var <= 1e-12 * max(var.max(), 1e-30))[0]
    for i in flat:
        reasons[int(i)] = "flat"
    ok = np.setdiff1d(np.arange(n_ch), flat)
    lv = np.log(var[ok])
    med = np.median(lv)
    mad = 1.4826 * np.median(np.abs(lv - med)) + 1e-12
    for i, zi in zip(ok, (lv - med) / mad):
        if abs(zi) > z_thresh:
            reasons.setdefault(int(i), f"variance z={zi:.1f}")
    step = max(1, data.shape[1] // 5000)                 # subsample time for speed
    C = np.corrcoef(data[ok][:, ::step])               # flat channels are left out (their correlation is undefined)
    np.fill_diagonal(C, np.nan)
    mc_ok = np.nanmedian(np.abs(C), axis=1)
    cmed = np.median(mc_ok)
    cmad = 1.4826 * np.median(np.abs(mc_ok - cmed)) + 1e-12
    for i, zi in zip(ok, (mc_ok - cmed) / cmad):
        if zi < -corr_z_thresh:
            reasons.setdefault(int(i), f"low correlation z={zi:.1f}")
    bad = sorted(reasons)
    if len(bad) > max_bad_fraction * n_ch:
        raise ValueError(f"{len(bad)} of {n_ch} channels flagged bad (> {max_bad_fraction:.0%}); recording is suspect.")
    return bad, {i: reasons[i] for i in bad}


def trial_artifact_statistic(epoch_data, q=95.0):
    """Per trial: the q-th percentile over channels of the peak-to-peak amplitude (robust to one bad channel).

    epoch_data: (trials, channels, samples). Returns an array of length trials, in the data's own units.
    """
    ptp = np.ptp(np.asarray(epoch_data, float), axis=2)
    return np.percentile(ptp, q, axis=1)


def adaptive_reject_mask(stat, k=6.0, floor=None, cap=None):
    """Label-blind per-subject trial rejection. True = keep.

    Threshold = median(stat) + k * 1.4826 * MAD(stat), then clipped to [floor, cap] when those are given.
    The rule is fixed in advance and must never be tuned on accuracy. It uses all trials of the subject,
    including the ones later used as test data (label-blind, but not 'nested'); this is stated in the docs.
    """
    stat = np.asarray(stat, float)
    med = np.median(stat)
    mad = 1.4826 * np.median(np.abs(stat - med))
    thr = med + k * mad
    if floor is not None:
        thr = max(thr, floor)
    if cap is not None:
        thr = min(thr, cap)
    return stat <= thr, float(thr)
