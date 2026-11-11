"""Time-frequency analysis: event-related desynchronisation (ERD)."""
import numpy as np

from .config import Config
from .signal_utils import percent_change


def _morlet_power(epochs, freqs, n_cycles):
    """Trial-averaged Morlet power: array (n_channels, n_freqs, n_times)."""
    try:
        tfr = epochs.compute_tfr("morlet", freqs, n_cycles=n_cycles, average=True, verbose="ERROR")
    except (AttributeError, TypeError):  # older MNE
        from mne.time_frequency import tfr_morlet
        tfr = tfr_morlet(epochs, freqs, n_cycles=n_cycles, return_itc=False, average=True, verbose="ERROR")
    return tfr.data, np.asarray(tfr.times)


def compute_erd(epochs, cfg: Config):
    """ERD (percent change from baseline) for the left and right condition.

    Returns (erd dict {"left": array, "right": array}, times, freqs, ch_names).
    Each array has shape (n_channels, n_freqs, n_times).
    """
    freqs = np.arange(cfg.erd_freqs[0], cfg.erd_freqs[1] + 1.0, 1.0)
    n_cycles = freqs / 2.0
    erd = {}
    times = None
    for cond in ("left", "right"):
        power, times = _morlet_power(epochs[cond], freqs, n_cycles)
        erd[cond] = percent_change(power, times, cfg.baseline)
    return erd, times, freqs, list(epochs.ch_names)
