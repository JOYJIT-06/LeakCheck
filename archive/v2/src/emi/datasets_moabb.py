"""Adapter that turns MOABB datasets into the LeakCheck cache format.

UNTESTED in the environment where this was written (no network, MOABB not installed).
It follows MOABB's documented interface from memory. Before any real use:
  * check the installed MOABB version's documentation for `LeftRightImagery` and `paradigm.get_data`;
  * check each dataset's availability, licence, sessions and trial timing;
  * run one subject and look at the printed counts.

Runs are defined as session + run (or block) so that leave-one-run-out never mixes a run.
"""
import numpy as np
import pandas as pd

from .cache import cache_path, save_cache

# Names to try; availability is NOT verified. Check MOABB's dataset list.
CANDIDATE_DATASETS = ("BNCI2014_001", "Cho2017", "Lee2019_MI", "Schirrmeister2017", "Weibo2014", "Zhou2016")


def build_moabb_cache(dataset_name, subject, cache_dir, fmin=8.0, fmax=30.0, tmin=0.0, tmax=4.0, resample=None):
    """Load left-vs-right imagery for one subject through MOABB and save it in the cache format."""
    import moabb.datasets as mds
    from moabb.paradigms import LeftRightImagery

    dataset = getattr(mds, dataset_name)()
    paradigm = LeftRightImagery(fmin=fmin, fmax=fmax, tmin=tmin, tmax=tmax, resample=resample)
    X, labels, meta = paradigm.get_data(dataset=dataset, subjects=[subject])

    y = (np.asarray(labels) == "right_hand").astype(int)
    if y.sum() == 0 or y.sum() == len(y):
        raise ValueError(f"Labels {sorted(set(labels))} do not contain both left_hand and right_hand.")
    session = meta["session"].astype(str).to_numpy() if "session" in meta else np.zeros(len(y)).astype(str)
    run = meta["run"].astype(str).to_numpy() if "run" in meta else np.zeros(len(y)).astype(str)
    runs = pd.factorize(pd.Series(session + "|" + run))[0]
    sessions = pd.factorize(pd.Series(session))[0]

    n_times = X.shape[2]
    sfreq = n_times / (tmax - tmin)                           # approximate; check against the dataset
    times = tmin + np.arange(n_times) / sfreq
    save_cache(cache_path(cache_dir, subject, dataset_name), X, y, runs, times, subject, dataset_name,
               sessions=sessions, order=np.arange(len(y)), sfreq=sfreq,
               extra={"fmin": fmin, "fmax": fmax, "tmin": tmin, "tmax": tmax, "resample": resample,
                      "note": "trial order = order returned by MOABB; verify it is chronological"})
    return {"dataset": dataset_name, "subject": int(subject), "n_trials": int(len(y)),
            "n_runs": int(len(np.unique(runs))), "n_sessions": int(len(np.unique(sessions))),
            "trials_per_run": np.bincount(runs).tolist(), "shape": list(X.shape)}
