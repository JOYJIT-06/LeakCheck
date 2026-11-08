"""Per-subject cache of cleaned EEG epochs, with validation and provenance.

Cache file:
    <cache_dir>/<dataset>/sub-XXX_epochs.npz

Required arrays:
    X, y, runs, times, subject

Optional arrays:
    sessions, order, sfreq, ch_names, dataset, extra_json

Schema version 2 adds:
    cache_schema_version, provenance_json

Legacy schema-v1 caches remain readable.
"""

import json
import platform
from pathlib import Path

import numpy as np

from .config import EVENT_ID, Config

CACHE_WINDOW = (0.0, 4.0)
CACHE_SCHEMA_VERSION = 2


def _software_provenance():
    """Return software versions without requiring optional dependencies."""
    try:
        from importlib.metadata import version

        package_version = version("emi")
    except Exception:
        from . import __version__

        package_version = __version__

    try:
        import mne

        mne_version = mne.__version__
    except ImportError:
        mne_version = None

    return {
        "emi_version": package_version,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "mne_version": mne_version,
    }


def _numeric_array(values, name):
    """Convert input to an array and reject non-numeric data (booleans included)."""
    arr = np.asarray(values)

    if arr.dtype.kind not in "iuf":
        raise ValueError(f"{name} must contain numeric values")

    return arr


def _integer_array(values, name):
    """Validate integer-valued numeric identifiers before conversion."""
    arr = _numeric_array(values, name)
    limits = np.iinfo(np.int64)

    if arr.dtype.kind == "f":
        if not np.isfinite(arr).all():
            raise ValueError(f"{name} contains NaN or infinite values")

        if not np.equal(arr, np.floor(arr)).all():
            raise ValueError(f"{name} must contain integer values")

        # 2**63 is exact in float64; int64 max is not, so compare against the powers of two.
        if (arr < -(2.0**63)).any() or (arr >= 2.0**63).any():
            raise ValueError(f"{name} contains values outside the int64 range")
    elif arr.dtype.kind == "u" and arr.size and int(arr.max()) > limits.max:
        raise ValueError(f"{name} contains values outside the int64 range")

    return arr.astype(np.int64)


def _validate_labels(values):
    """Validate binary labels before any integer conversion."""
    arr = _numeric_array(values, "y")

    if not np.isfinite(arr).all():
        raise ValueError("Labels contain NaN or infinite values")

    if not np.isin(arr, [0, 1]).all():
        raise ValueError("Labels must be binary: 0 (left), 1 (right)")

    return arr.astype(np.int8)


def _validate_eeg(values):
    """Check dtype first, then convert to float32; reject non-finite and float32 overflow."""
    try:
        arr = np.asarray(values)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("X must contain numeric EEG values") from exc

    if arr.dtype.kind not in "iuf":
        raise ValueError(
            "X must contain numeric EEG values (real integer or floating-point)"
        )

    if not np.isfinite(arr).all():
        raise ValueError("X contains NaN or infinite values")

    with np.errstate(over="ignore", invalid="ignore"):
        out = arr.astype(np.float32)

    if not np.isfinite(out).all():
        raise ValueError("X contains values outside the float32 range")

    return out


def _validate_times(values, n_times):
    """Validate a finite, strictly increasing time vector."""
    try:
        arr = np.asarray(values, dtype=float)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("times must contain numeric values") from exc

    if arr.ndim != 1 or len(arr) != n_times or len(arr) < 2:
        raise ValueError(
            "times must match the time dimension of X and contain at least 2 points"
        )

    if not np.isfinite(arr).all():
        raise ValueError("times contains NaN or infinite values")

    if np.any(np.diff(arr) <= 0):
        raise ValueError("times must be strictly increasing")

    return arr


def _validate_metadata_json(value, field_name):
    """Decode JSON metadata and require a dictionary."""
    try:
        result = json.loads(str(value))
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Invalid cache metadata in {field_name}") from exc

    if not isinstance(result, dict):
        raise ValueError(f"{field_name} must contain a JSON object")

    return result


def _check_sampling_frequency(sfreq, times):
    """Require sfreq to agree with 1/median(diff(times)) within 0.1 % relative.

    Float time vectors agree to ~1e-12 and float32-stored ones to ~1e-4, so this accepts
    representation error but rejects clearly wrong metadata (e.g. 250 Hz vs 100 Hz).
    """
    implied = 1.0 / np.median(np.diff(times))
    if not np.isclose(sfreq, implied, rtol=1e-3, atol=0.0):
        raise ValueError(
            f"Invalid sampling frequency: sfreq={sfreq:g} Hz disagrees with the "
            f"{implied:g} Hz implied by times"
        )


def _validate_subject(value):
    """Python/NumPy integer scalars only (no bool, no float, no str)."""
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, np.integer)
    ):
        raise ValueError("subject must be an integer ID")

    value = int(value)
    limits = np.iinfo(np.int64)
    if not limits.min <= value <= limits.max:
        raise ValueError("subject is outside the int64 range")

    return value


def _stored_subject(raw):
    """Validate the stored subject field before conversion."""
    arr = np.asarray(raw)

    if arr.ndim != 0 or arr.dtype.kind not in "iu":
        raise ValueError("Stored subject must be a scalar integer")

    value = int(arr)
    if value > np.iinfo(np.int64).max:
        raise ValueError("Stored subject is outside the int64 range")

    return value


def cache_path(cache_dir, subject: int, dataset: str = "physionet") -> Path:
    return Path(cache_dir) / dataset / f"sub-{subject:03d}_epochs.npz"


def save_cache(
    path,
    X,
    y,
    runs,
    times,
    subject,
    dataset,
    sessions=None,
    order=None,
    sfreq=None,
    ch_names=(),
    extra=None,
):
    """Validate and write one subject's EEG cache."""
    subject = _validate_subject(subject)

    X = _validate_eeg(X)
    y = _validate_labels(y)
    runs = _integer_array(runs, "runs")
    times = np.asarray(times, dtype=float)

    if X.ndim != 3:
        raise ValueError("X must have shape (trials, channels, time)")

    if y.ndim != 1:
        raise ValueError("y must be a one-dimensional label array")

    n = len(y)

    if n == 0 or X.shape[0] != n:
        raise ValueError("X and y must contain the same non-zero number of trials")

    if X.shape[1] == 0 or X.shape[2] < 2:
        raise ValueError(f"Invalid EEG dimensions: {X.shape}")

    if runs.ndim != 1 or len(runs) != n:
        raise ValueError("runs must be one-dimensional and match y")

    times = _validate_times(times, X.shape[2])

    if sessions is None:
        sessions = np.zeros(n, dtype=np.int64)
    else:
        sessions = _integer_array(sessions, "sessions")

    if sessions.ndim != 1 or len(sessions) != n:
        raise ValueError("sessions must be one-dimensional and match y")

    if order is None:
        order = np.arange(n, dtype=np.int64)
    else:
        order = _integer_array(order, "order")

    if order.ndim != 1 or len(order) != n:
        raise ValueError("order must be one-dimensional and match y")

    if sfreq is None:
        sfreq = 1.0 / np.median(np.diff(times))

    try:
        sfreq = float(sfreq)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Invalid sampling frequency") from exc

    if not np.isfinite(sfreq) or sfreq <= 0:
        raise ValueError(f"Invalid sampling frequency: {sfreq}")

    _check_sampling_frequency(sfreq, times)

    ch_names = list(ch_names)
    if ch_names and len(ch_names) != X.shape[1]:
        raise ValueError("Number of channel names does not match X")

    if extra is None:
        extra = {}
    elif not isinstance(extra, dict):
        raise ValueError("extra metadata must be a dictionary")

    try:
        extra_json = json.dumps(extra)
    except (TypeError, ValueError) as exc:
        raise ValueError("extra metadata must be JSON serializable") from exc

    provenance_json = json.dumps(_software_provenance())

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    np.savez_compressed(
        path,
        X=X,
        y=y,
        runs=runs,
        sessions=sessions,
        order=order,
        times=times,
        sfreq=sfreq,
        ch_names=np.asarray(ch_names, dtype=str),
        subject=int(subject),
        dataset=str(dataset),
        extra_json=extra_json,
        cache_schema_version=CACHE_SCHEMA_VERSION,
        provenance_json=provenance_json,
    )


def load_cache(path) -> dict:
    """Load and validate a cache, including supported legacy caches."""
    path = Path(path)

    if not path.is_file():
        raise FileNotFoundError(f"Cache file not found: {path}")

    with np.load(path, allow_pickle=False) as z:
        required = {"X", "y", "runs", "times", "subject"}
        missing = required.difference(z.files)

        if missing:
            raise ValueError(
                f"Cache is missing required fields: {sorted(missing)}"
            )

        X = _validate_eeg(z["X"])

        if X.ndim != 3:
            raise ValueError(
                f"X must be 3D (trials, channels, time); got {X.shape}"
            )

        if X.shape[1] == 0 or X.shape[2] < 2:
            raise ValueError(f"Invalid EEG dimensions: {X.shape}")

        y = _validate_labels(z["y"])
        runs = _integer_array(z["runs"], "runs")
        times = _validate_times(z["times"], X.shape[2])

        n = len(y)

        if y.ndim != 1:
            raise ValueError("y must be one-dimensional")

        if n == 0 or X.shape[0] != n:
            raise ValueError(
                "X and y must contain the same non-zero number of trials"
            )

        if runs.ndim != 1 or len(runs) != n:
            raise ValueError("runs length does not match the number of trials")

        sessions = (
            _integer_array(z["sessions"], "sessions")
            if "sessions" in z.files
            else np.zeros(n, dtype=np.int64)
        )

        order = (
            _integer_array(z["order"], "order")
            if "order" in z.files
            else np.arange(n, dtype=np.int64)
        )

        if sessions.ndim != 1 or len(sessions) != n:
            raise ValueError("sessions must match the number of trials")

        if order.ndim != 1 or len(order) != n:
            raise ValueError("order must match the number of trials")

        ch_names = (
            list(z["ch_names"].astype(str))
            if "ch_names" in z.files
            else []
        )

        if ch_names and len(ch_names) != X.shape[1]:
            raise ValueError("Number of channel names does not match X")

        if "sfreq" in z.files:
            try:
                sfreq = float(z["sfreq"])
            except (TypeError, ValueError, OverflowError) as exc:
                raise ValueError("Invalid sampling frequency") from exc
        else:
            sfreq = float(1.0 / np.median(np.diff(times)))

        if not np.isfinite(sfreq) or sfreq <= 0:
            raise ValueError(f"Invalid sampling frequency: {sfreq}")

        _check_sampling_frequency(sfreq, times)

        if "extra_json" in z.files:
            extra = _validate_metadata_json(
                z["extra_json"].item(), "extra_json"
            )
        else:
            extra = {}

        if "cache_schema_version" in z.files:
            raw_version = np.asarray(z["cache_schema_version"])

            if raw_version.size != 1:
                raise ValueError("cache_schema_version must be a scalar")

            version_value = raw_version.item()

            if (
                not isinstance(version_value, (int, np.integer))
                or isinstance(version_value, (bool, np.bool_))
            ):
                raise ValueError("cache_schema_version must be an integer")

            schema_version = int(version_value)
        else:
            schema_version = 1

        if schema_version < 1 or schema_version > CACHE_SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported cache schema version: {schema_version}; "
                f"this software supports versions 1 to {CACHE_SCHEMA_VERSION}"
            )

        if "provenance_json" in z.files:
            provenance = _validate_metadata_json(
                z["provenance_json"].item(), "provenance_json"
            )
        else:
            provenance = {}

        return {
            "X": X.astype(np.float64),
            "y": y.astype(int),
            "runs": runs.astype(int),
            "sessions": sessions.astype(int),
            "order": order.astype(int),
            "times": times,
            "sfreq": sfreq,
            "subject": _stored_subject(z["subject"]),
            "ch_names": ch_names,
            "dataset": (
                str(z["dataset"].item())
                if "dataset" in z.files
                else "physionet"
            ),
            "extra": extra,
            "cache_schema_version": schema_version,
            "provenance": provenance,
        }


def build_subject_cache(
    subject: int,
    cfg: Config,
    cache_dir,
    window=CACHE_WINDOW,
) -> dict:
    """Preprocess one PhysioNet subject and save its epochs. Needs MNE."""
    from . import data, preprocess

    raw = data.load_raw(subject, cfg)
    raw_clean, prep = preprocess.clean_raw(raw, cfg)
    _, ep_dec, runs, qc = preprocess.build_epochs_full(
        raw_clean, cfg, decode_window=window
    )

    X = ep_dec.get_data()
    y = (ep_dec.events[:, 2] == EVENT_ID["right"]).astype(int)
    order = np.argsort(np.argsort(ep_dec.events[:, 0]))

    save_cache(
        cache_path(cache_dir, subject),
        X,
        y,
        runs,
        ep_dec.times,
        subject,
        "physionet",
        sessions=np.zeros(len(y)),
        order=order,
        sfreq=ep_dec.info["sfreq"],
        ch_names=ep_dec.ch_names,
        extra={
            "config": cfg.to_dict(),
            "preprocessing": prep,
            "trial_qc": qc,
        },
    )

    return {
        "subject": int(subject),
        "n_events": qc["n_events"],
        "n_trials": int(len(y)),
        "trials_lost": qc["n_events"] - int(len(y)),
        "reject_mode": qc["reject_mode"],
        "reject_threshold_uv": round(qc["threshold_uv"], 1),
        "trials_per_run": np.bincount(runs).tolist(),
        "shape": list(X.shape),
        "left": int((y == 0).sum()),
        "right": int((y == 1).sum()),
        "n_bad_channels": prep["n_bad_channels"],
        "bad_channels": ",".join(prep["bad_channels"]),
        "n_ica_removed": len(prep["ica_excluded"]),
        "use_ica": prep["use_ica"],
    }
