"""Small numpy-only helpers (no MNE needed, easy to unit test).

All public functions validate their inputs and raise ValueError on bad input.
The scientific algorithms are unchanged from the original implementation.
"""
import re

import numpy as np

_INT64_MAX = int(np.iinfo(np.int64).max)


# ---------------------------------------------------------------- helpers

def _as_finite_real_array(values, name):
    """Return `values` as a float64 array; reject non-numeric, complex, bool and non-finite data."""
    try:
        arr = np.asarray(values)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must contain real numeric values") from exc
    if arr.dtype.kind not in "iuf":
        raise ValueError(f"{name} must contain real numeric values")
    arr = arr.astype(np.float64, copy=False)
    if not np.isfinite(arr).all():
        raise ValueError(f"{name} must contain only finite values")
    return arr


def _finite_number(value, name, minimum=None, maximum=None):
    """Validate a finite real scalar (bool rejected) and optional inclusive bounds."""
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f"{name} must be a finite real number")
    try:
        arr = np.asarray(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite real number") from exc
    if arr.ndim != 0 or arr.dtype.kind not in "iuf":
        raise ValueError(f"{name} must be a finite real number")
    out = float(arr)
    if not np.isfinite(out):
        raise ValueError(f"{name} must be a finite real number")
    if minimum is not None and out < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    if maximum is not None and out > maximum:
        raise ValueError(f"{name} must be <= {maximum}")
    return out


def _integer_array(values, name):
    """Validate integer-valued data (integral floats allowed) and return int64."""
    try:
        arr = np.asarray(values)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must contain integer values") from exc

    kind = arr.dtype.kind

    if kind in "iu":
        if kind == "u" and arr.size and int(arr.max()) > _INT64_MAX:
            raise ValueError(f"{name} contains values outside the int64 range")
        return arr.astype(np.int64)

    if kind != "f":
        raise ValueError(f"{name} must contain integer values")

    if not np.isfinite(arr).all():
        raise ValueError(f"{name} must contain finite integer values")

    if not np.equal(arr, np.floor(arr)).all():
        raise ValueError(f"{name} must contain integer values")

    if arr.size and (
        ((arr < -(2.0 ** 63)) | (arr >= 2.0 ** 63)).any()
    ):
        raise ValueError(f"{name} contains values outside the int64 range")

    return arr.astype(np.int64)

def _validated_range(bounds, name):
    """Validate a (lower, upper) pair of finite numbers with lower <= upper."""
    try:
        lo, hi = bounds
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a (lower, upper) pair") from None
    lo = _finite_number(lo, f"{name} lower bound")
    hi = _finite_number(hi, f"{name} upper bound")
    if lo > hi:
        raise ValueError(f"{name} lower bound ({lo}) must not exceed upper bound ({hi})")
    return lo, hi


def _epoch_array(data, name):
    """Validate (trials, channels, samples): finite, real, 3-D, no empty dimension."""
    arr = _as_finite_real_array(data, name)
    if arr.ndim != 3:
        raise ValueError(f"{name} must have shape (n_epochs, n_channels, n_times).")
    if any(size == 0 for size in arr.shape):
        raise ValueError(f"{name} must not have empty dimensions.")
    return arr


# ---------------------------------------------------------------- time-frequency

def percent_change(power: np.ndarray, times: np.ndarray, baseline: tuple) -> np.ndarray:
    """Convert power to percent change relative to a baseline window.

    power: array whose LAST axis is time.
    Negative values = power decrease (event-related desynchronisation, ERD).
    """
    power = _as_finite_real_array(power, "power")
    times = _as_finite_real_array(times, "times")
    if power.ndim < 1 or times.ndim != 1:
        raise ValueError("power must have a time axis and times must be one-dimensional.")
    if power.shape[-1] != times.size:
        raise ValueError(f"times length ({times.size}) must match the last axis of power ({power.shape[-1]}).")
    lo, hi = _validated_range(baseline, "baseline")
    mask = (times >= lo) & (times <= hi)
    if not mask.any():
        raise ValueError(f"Baseline {baseline} has no samples in the time axis.")
    ref = power[..., mask].mean(axis=-1, keepdims=True)
    if np.any(ref <= 0):
        raise ValueError("Baseline power must be positive.")
    return 100.0 * (power - ref) / ref


def band_timecourse(power: np.ndarray, freqs: np.ndarray, band: tuple) -> np.ndarray:
    """Average over frequencies inside `band`. power shape: (..., n_freqs, n_times)."""
    power = _as_finite_real_array(power, "power")
    freqs = _as_finite_real_array(freqs, "freqs")
    if power.ndim < 2 or freqs.ndim != 1:
        raise ValueError("power must have shape (..., n_freqs, n_times) and freqs must be one-dimensional.")
    if power.shape[-2] != freqs.size:
        raise ValueError(f"freqs length ({freqs.size}) must match the frequency axis of power ({power.shape[-2]}).")
    lo, hi = _validated_range(band, "band")
    mask = (freqs >= lo) & (freqs <= hi)
    if not mask.any():
        raise ValueError(f"No frequencies inside band {band}.")
    return power[..., mask, :].mean(axis=-2)


# ---------------------------------------------------------------- run metadata

_INT_TEXT = re.compile(r"[+-]?\d+")


def parse_run_lengths(description: str, tag: str) -> list:
    """Read the run lengths (in samples) that data.load_raw stored in raw.info['description']."""
    if not isinstance(description, str) or not description or not description.startswith(tag):
        raise ValueError("No run-length tag found. Load the data with emi.data.load_raw.")
    lengths = []
    for part in description[len(tag):].split(","):
        part = part.strip()
        if not _INT_TEXT.fullmatch(part):
            raise ValueError(f"Invalid run length {part!r} in run-length metadata.")
        value = int(part)
        if value <= 0:
            raise ValueError(f"Run lengths must be positive; got {value}.")
        lengths.append(value)
    return lengths


def trial_run_ids(sample_indices, run_lengths, first_samp: int = 0) -> np.ndarray:
    """Run index (0, 1, 2, ...) of each event, from its sample index in the joined recording.

    Runs are joined back to back, so run k covers
    [first_samp + sum(len[:k]), first_samp + sum(len[:k+1])).
    Events outside [first_samp, first_samp + sum(run_lengths)) raise ValueError.
    """
    lengths = _integer_array(run_lengths, "run_lengths")
    if lengths.ndim != 1 or lengths.size == 0:
        raise ValueError("run_lengths must be a non-empty one-dimensional sequence.")
    if (lengths <= 0).any():
        raise ValueError("run_lengths must all be positive.")
    first = _integer_array(first_samp, "first_samp")
    if first.ndim != 0:
        raise ValueError("first_samp must be a scalar integer.")
    first = int(first)
    if first + sum(int(v) for v in lengths) > _INT64_MAX:
        raise ValueError("run_lengths and first_samp exceed the int64 range.")

    samples = _integer_array(sample_indices, "sample_indices")
    if samples.ndim != 1:
        raise ValueError("sample_indices must be one-dimensional.")

    ends = first + np.cumsum(lengths)
    if samples.size and (samples.min() < first or samples.max() >= ends[-1]):
        raise ValueError(f"An event lies outside the recording [{first}, {int(ends[-1])}).")
    return np.searchsorted(ends, samples, side="right")


# ---------------------------------------------------------------- fixed-threshold rejection

def ptp_reject_indices(data, threshold_uv):
    """Return indices of epochs exceeding a peak-to-peak threshold (strict >, any channel).

    data: (n_epochs, n_channels, n_times), in volts.
    threshold_uv: threshold in microvolts.

    Numerics: the threshold is converted with threshold_uv / 1e6 (division by an exactly
    representable power of ten is correctly rounded, so 100 uV -> the same double as the literal
    100e-6; multiplying by the inexact 1e-6 gives 9.999999999999999e-05 and would wrongly reject
    an epoch exactly at 100 uV). max - min can still be off by a few ulps of the operands, so the
    comparison allows 4 * eps * max(|max|, |min|) per channel, i.e. the rounding error of the
    subtraction itself (~1e-13 uV at EEG scale), not a physical tolerance. With threshold 0 the
    comparison is exactly strict (any non-zero peak-to-peak rejects).
    """
    data = _epoch_array(data, "data")
    threshold_uv = _finite_number(threshold_uv, "threshold_uv", minimum=0.0)

    mx = data.max(axis=2)
    mn = data.min(axis=2)
    ptp = mx - mn
    threshold_v = threshold_uv / 1e6
    if threshold_v == 0.0:
        exceeds = ptp > 0.0
    else:
        slack = 4.0 * np.finfo(np.float64).eps * np.maximum(np.abs(mx), np.abs(mn))
        exceeds = ptp > threshold_v + slack
    return np.where(exceeds.any(axis=1))[0]


# ---------------------------------------------------------------- bad channels

def detect_bad_channels(data, z_thresh=4.0, corr_z_thresh=4.0, max_bad_fraction=0.15):
    """Label-blind bad-channel detection on continuous data (channels x samples). Returns (bad_indices, reasons).

    A channel is flagged when (a) it is flat, (b) its log-variance is a robust outlier across channels
    (median and MAD, |z| > z_thresh), or (c) its median absolute correlation with the other channels is a LOW
    robust outlier (z < -corr_z_thresh). The correlation rule is relative on purpose: absolute correlation levels
    depend on the reference and the montage, so a fixed cut-off would flag everything or nothing.
    Raises if more than max_bad_fraction of the channels would be flagged, because then the recording itself is
    suspect. Uses no labels and no accuracy.
    """
    data = _as_finite_real_array(data, "data")
    if data.ndim != 2:
        raise ValueError("data must have shape (n_channels, n_samples).")
    n_ch, n_samp = data.shape
    if n_ch < 3:
        raise ValueError("Bad-channel detection needs at least three channels.")
    if n_samp < 2:
        raise ValueError("Bad-channel detection needs at least two samples per channel.")
    z_thresh = _finite_number(z_thresh, "z_thresh", minimum=0.0)
    corr_z_thresh = _finite_number(corr_z_thresh, "corr_z_thresh", minimum=0.0)
    max_bad_fraction = _finite_number(max_bad_fraction, "max_bad_fraction", minimum=0.0, maximum=1.0)

    var = data.var(axis=1)
    reasons = {}
    flat = np.where(var <= 1e-12 * max(var.max(), 1e-30))[0]
    for i in flat:
        reasons[int(i)] = "flat"
    ok = np.setdiff1d(np.arange(n_ch), flat)
    if ok.size < 3:
        raise ValueError(f"Fewer than three non-flat channels ({ok.size} of {n_ch}); recording is unusable.")
    lv = np.log(var[ok])
    med = np.median(lv)
    mad = 1.4826 * np.median(np.abs(lv - med)) + 1e-12
    for i, zi in zip(ok, (lv - med) / mad):
        if abs(zi) > z_thresh:
            reasons.setdefault(int(i), f"variance z={zi:.1f}")
    step = max(1, n_samp // 5000)                        # subsample time for speed
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


# ---------------------------------------------------------------- adaptive rejection

def trial_artifact_statistic(epoch_data, q=95.0):
    """Per trial: the q-th percentile over channels of the peak-to-peak amplitude (robust to one bad channel).

    epoch_data: (trials, channels, samples). Returns an array of length trials, in the data's own units.
    """
    epoch_data = _epoch_array(epoch_data, "epoch_data")
    q = _finite_number(q, "q")
    if not 0.0 <= q <= 100.0:
        raise ValueError("q must be between 0 and 100.")
    ptp = np.ptp(epoch_data, axis=2)
    return np.percentile(ptp, q, axis=1)


def adaptive_reject_mask(stat, k=6.0, floor=None, cap=None):
    """Label-blind per-subject trial rejection. True = keep.

    Threshold = median(stat) + k * 1.4826 * MAD(stat), then clipped to [floor, cap] when those are given.
    The rule is fixed in advance and must never be tuned on accuracy. It uses all trials of the subject,
    including the ones later used as test data (label-blind, but not 'nested'); this is stated in the docs.
    """
    stat = _as_finite_real_array(stat, "stat")
    if stat.ndim != 1 or stat.size == 0:
        raise ValueError("stat must be a non-empty one-dimensional array.")
    k = _finite_number(k, "k", minimum=0.0)
    if floor is not None:
        floor = _finite_number(floor, "floor")
    if cap is not None:
        cap = _finite_number(cap, "cap")
    if floor is not None and cap is not None and floor > cap:
        raise ValueError(f"floor must be <= cap (got floor={floor}, cap={cap}).")

    med = np.median(stat)
    mad = 1.4826 * np.median(np.abs(stat - med))
    thr = med + k * mad
    if floor is not None:
        thr = max(thr, floor)
    if cap is not None:
        thr = min(thr, cap)
    return stat <= thr, float(thr)
