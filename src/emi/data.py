"""Load the PhysioNet EEG Motor Movement/Imagery data through MNE."""
import mne
from mne.datasets import eegbci

from .config import RUN_TAG, Config


def resolve_data_path(cfg: Config) -> str:
    """Folder for the PhysioNet files, chosen without any interactive prompt.

    Order: cfg.data_path, then the MNE_DATA setting/environment variable, then ~/mne_data.
    (Without this, the first download asks a question on stdin and hangs batch jobs.)
    """
    import os
    from pathlib import Path
    path = cfg.data_path or mne.get_config("MNE_DATA") or os.path.join(str(Path.home()), "mne_data")
    os.makedirs(path, exist_ok=True)
    return str(path)


def load_raw(subject: int, cfg: Config) -> mne.io.BaseRaw:
    """Download (first time only) and load the chosen runs for one subject.

    The runs are concatenated into one Raw object. Channel names are
    standardised and the standard 10-05 montage is attached, so topographic
    plots work. The length of each run is stored in raw.info['description'],
    so each trial can later be assigned to its run.
    """
    paths = eegbci.load_data(subject, list(cfg.runs), path=resolve_data_path(cfg))
    raws = [mne.io.read_raw_edf(p, preload=True, verbose="ERROR") for p in paths]
    lengths = [r.n_times for r in raws]
    raw = mne.concatenate_raws(raws)
    eegbci.standardize(raw)
    montage = mne.channels.make_standard_montage("standard_1005")
    raw.set_montage(montage, match_case=False, on_missing="ignore")
    raw.info["description"] = RUN_TAG + ",".join(str(n) for n in lengths)
    return raw
