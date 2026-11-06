
"""Per-subject cache of cleaned epochs, so the audit never repeats the slow steps.

Cache file (one per subject, in <cache_dir>/<dataset>/sub-XXX_epochs.npz):
  X (trials, channels, time) float32, y (0 = left, 1 = right), runs (run or block id),
  sessions, order (chronological trial index), times, sfreq, ch_names, subject, dataset.
"""
import json
from pathlib import Path

import numpy as np

from .config import EVENT_ID, Config

CACHE_WINDOW = (0.0, 4.0)


def cache_path(cache_dir, subject: int, dataset: str = "physionet") -> Path:
    return Path(cache_dir) / dataset / f"sub-{subject:03d}_epochs.npz"


def save_cache(path, X, y, runs, times, subject, dataset, sessions=None, order=None,
               sfreq=None, ch_names=(), extra=None):
    """Write one subject's arrays in the cache format (used by every dataset adapter)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    X = np.asarray(X, dtype=np.float32)
    y = np.asarray(y, dtype=np.int8)
    runs = np.asarray(runs, dtype=np.int16)
    times = np.asarray(times, dtype=float)

    n = len(y)

    if X.ndim != 3 or X.shape[0] != n:
        raise ValueError("X must have shape (trials, channels, time) matching y")

    if len(runs) != n:
        raise ValueError("runs length must match y")

    if len(times) != X.shape[2] or len(times) < 2:
        raise ValueError("times must match the time dimension of X and contain at least 2 points")

    if sfreq is None:
        sfreq = 1.0 / np.median(np.diff(times))

    np.savez_compressed(
        path,
        X=X,
        y=y,
        runs=runs,
        sessions=np.zeros(n, np.int16) if sessions is None else np.asarray(sessions, dtype=np.int16),
        order=np.arange(n) if order is None else np.asarray(order),
        times=times,
        sfreq=float(sfreq),
        ch_names=np.array(list(ch_names)),
        subject=int(subject),
        dataset=str(dataset),
        extra_json=json.dumps(extra or {}),
    )


def load_cache(path) -> dict:
    """Load and validate one cached subject, supporting older cache files."""
    path = Path(path)

    if not path.is_file():
        raise FileNotFoundError(f"Cache file not found: {path}")

    with np.load(path, allow_pickle=False) as z:
        required = {"X", "y", "runs", "times", "subject"}
        missing = required.difference(z.files)

        if missing:
            raise ValueError(f"Cache is missing required fields: {sorted(missing)}")

        X = z["X"].astype(np.float64)
        y = z["y"].astype(int)
        runs = z["runs"].astype(int)
        times = z["times"].astype(float)

        n = len(y)

        if X.ndim != 3:
            raise ValueError(f"X must be 3D (trials, channels, time); got {X.shape}")

        if n == 0 or X.shape[0] != n:
            raise ValueError("X and y must contain the same non-zero number of trials")

        if X.shape[1] == 0 or X.shape[2] < 2:
            raise ValueError(f"Invalid EEG dimensions: {X.shape}")

        if len(runs) != n:
            raise ValueError("runs length does not match the number of trials")

        if not np.isin(y, [0, 1]).all():
            raise ValueError("Labels must be binary: 0 (left), 1 (right)")

        if not np.isfinite(X).all():
            raise ValueError("X contains NaN or infinite values")

        if not np.isfinite(times).all() or len(times) != X.shape[2]:
            raise ValueError("times must be finite and match the time dimension of X")

        if np.any(np.diff(times) <= 0):
            raise ValueError("times must be strictly increasing")

        sessions = (
            z["sessions"].astype(int)
            if "sessions" in z.files
            else np.zeros(n, dtype=int)
        )

        order = (
            z["order"].astype(int)
            if "order" in z.files
            else np.arange(n)
        )

        if len(sessions) != n or len(order) != n:
            raise ValueError("sessions and order must match the number of trials")

        ch_names = (
            list(z["ch_names"].astype(str))
            if "ch_names" in z.files
            else []
        )

        if ch_names and len(ch_names) != X.shape[1]:
            raise ValueError("Number of channel names does not match X")

        if "sfreq" in z.files:
            sfreq = float(z["sfreq"])
        else:
            sfreq = float(1.0 / np.median(np.diff(times)))

        if not np.isfinite(sfreq) or sfreq <= 0:
            raise ValueError(f"Invalid sampling frequency: {sfreq}")

        if "extra_json" in z.files:
            try:
                extra = json.loads(str(z["extra_json"].item()))
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                raise ValueError("Invalid cache metadata in extra_json") from exc
        else:
            extra = {}

        return {
            "X": X,
            "y": y,
            "runs": runs,
            "sessions": sessions,
            "order": order,
            "times": times,
            "sfreq": sfreq,
            "subject": int(z["subject"]),
            "ch_names": ch_names,
            "dataset": str(z["dataset"].item()) if "dataset" in z.files else "physionet",
            "extra": extra,
        }


def build_subject_cache(subject: int, cfg: Config, cache_dir, window=CACHE_WINDOW) -> dict:
    """Preprocess one PhysioNet subject and save its 8-30 Hz epochs. Needs MNE."""
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
