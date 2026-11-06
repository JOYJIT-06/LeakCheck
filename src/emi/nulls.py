"""Null label generators and the empirical p-value (numpy only)."""
import numpy as np


def permute_within_runs(y, runs, rng):
    """Shuffle labels inside each run. Keeps class counts per run; destroys any real signal."""
    y = np.asarray(y)
    out = y.copy()
    for r in np.unique(runs):
        idx = np.where(runs == r)[0]
        out[idx] = rng.permutation(y[idx])
    return out


def circular_shift_within_runs(y, runs, rng):
    """Circularly shift the label sequence inside each run, relative to the EEG.

    This keeps the label sequence's own structure (blocks, autocorrelation) and breaks only
    its alignment with the EEG. It is the right null when labels are not fully randomised,
    because a plain permutation would also destroy that structure.
    Each run is shifted by a random non-zero amount (when the run has more than one trial).
    """
    y = np.asarray(y)
    out = y.copy()
    for r in np.unique(runs):
        idx = np.where(runs == r)[0]
        if len(idx) > 1:
            k = int(rng.integers(1, len(idx)))
            out[idx] = np.roll(y[idx], k)
    return out


def empirical_p(observed, null_values):
    """(1 + number of null values at or above observed) / (1 + number of nulls)."""
    null_values = np.asarray(null_values, dtype=float)
    return float((1 + np.sum(null_values >= observed)) / (1 + len(null_values)))


NULL_GENERATORS = {"perm": permute_within_runs, "shift": circular_shift_within_runs}


def label_agreement(y, y_null):
    """Share of trials where the null labels equal the real labels (1.0 for the real labels themselves).

    Diagnostic for the circular-shift null: when the label order is (nearly) alternating, a shift by an even
    number of trials reproduces most of the real labels, so such 'null' sets are not really null and the p-value
    becomes conservative. Check this column before relying on the shift null.
    """
    return float(np.mean(np.asarray(y) == np.asarray(y_null)))
