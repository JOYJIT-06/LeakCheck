import numpy as np
import json
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description="Inspect a LeakCheck EEG cache file.")
parser.add_argument("cache_file", type=Path, help="Path to the EEG .npz cache file")
args = parser.parse_args()
path = args.cache_file

with np.load(path, allow_pickle=True) as data:
    print("CACHE KEYS:", data.files)

    for key in data.files:
        arr = data[key]
        print(f"\n{key}: shape={arr.shape}, dtype={arr.dtype}")

    X = data["X"]
    y = data["y"]
    runs = data["runs"]

    print("\n--- EEG VALIDATION ---")
    print("Number of trials:", len(y))
    print("EEG shape:", X.shape)
    print("All EEG values finite:", np.isfinite(X).all())
    print("Labels:", dict(zip(*np.unique(y, return_counts=True))))
    print("Runs:", np.unique(runs, return_counts=True))

    print("\n--- CLASS COUNTS PER RUN ---")
    for run in np.unique(runs):
        mask = runs == run
        print(
            f"Run {run}:",
            dict(zip(*np.unique(y[mask], return_counts=True)))
        )

    if "sfreq" in data:
        print("\nSampling frequency:", data["sfreq"])

    if "times" in data:
        times = data["times"]
        print("Time range:", times.min(), "to", times.max())
        print("Number of time points:", len(times))

    if "ch_names" in data:
        print("Number of channels:", len(data["ch_names"]))
        print("Channels:", data["ch_names"])

    if "extra_json" in data:
        extra = data["extra_json"].item()
        if isinstance(extra, bytes):
            extra = extra.decode("utf-8")
        print("\n--- PREPROCESSING METADATA ---")
        try:
            print(json.dumps(json.loads(extra), indent=2))
        except (TypeError, ValueError):
            print(extra)
