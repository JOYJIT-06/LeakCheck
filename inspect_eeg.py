"""Inspect raw PhysioNet EDF recordings."""
import argparse
import sys
from pathlib import Path
import mne
import numpy as np
from emi.config import Config
from emi.data import resolve_data_path

parser = argparse.ArgumentParser(description="Inspect raw PhysioNet EDF recordings.")
parser.add_argument(
    "--folder",
    type=Path,
    default=None,
    help="Path to folder containing subject .edf files (defaults to standard MNE dataset location)."
)
parser.add_argument(
    "--subject",
    type=int,
    default=1,
    help="PhysioNet subject number to inspect (default: 1)."
)
parser.add_argument(
    "--data-path",
    type=Path,
    default=None,
    help="Base directory for MNE data storage."
)
args = parser.parse_args()

if args.folder is not None:
    folder = args.folder
else:
    cfg = Config(data_path=str(args.data_path) if args.data_path else None)
    base_mne = Path(resolve_data_path(cfg))
    subj_folder = f"S{args.subject:03d}"
    folder = base_mne / "MNE-eegbci-data" / "files" / "eegmmidb" / "1.0.0" / subj_folder

if not folder.exists() or not list(folder.glob("*.edf")):
    print(f"Directory {folder} does not exist or contains no .edf files.")
    print("Attempting to download subject files via MNE eegbci.load_data...")
    try:
        cfg = Config(data_path=str(args.data_path) if args.data_path else None)
        paths = mne.datasets.eegbci.load_data(args.subject, [4, 8, 12], path=resolve_data_path(cfg))
        if paths:
            folder = Path(paths[0]).parent
    except Exception as exc:
        print(f"Could not automatically fetch EEG files: {exc}")
        print("Please specify --folder /path/to/edf/files")
        sys.exit(1)

edf_files = sorted(folder.glob("*.edf"))
if not edf_files:
    print(f"No .edf files found in {folder}")
    sys.exit(1)

for file in edf_files:
    print("\n" + "=" * 50)
    print("FILE:", file.name)

    raw = mne.io.read_raw_edf(
        file,
        preload=False,
        verbose="ERROR"
    )

    print("Channels:", raw.info["nchan"])
    print("Sampling rate:", raw.info["sfreq"], "Hz")
    print("Duration:", round(raw.n_times / raw.info["sfreq"], 2), "seconds")
    print("Annotations:", len(raw.annotations))

    descriptions, counts = np.unique(
        raw.annotations.description,
        return_counts=True
    )

    print("Annotation descriptions:", dict(zip(descriptions, counts)))

    events, event_id = mne.events_from_annotations(
        raw,
        verbose="ERROR"
    )

    print("Event IDs:", event_id)

    event_counts = {
        name: int((events[:, 2] == code).sum())
        for name, code in event_id.items()
    }

    print("Event counts:", event_counts)

    raw.close()
