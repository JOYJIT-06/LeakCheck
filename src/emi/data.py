"""Load the PhysioNet EEG Motor Movement/Imagery data through MNE."""
import mne
from mne.datasets import eegbci

from .config import RUN_TAG, Config


def resolve_data_path(cfg: Config) -> str:
    """Folder for the PhysioNet files, chosen without any interactive prompt.

    Order: cfg.data_path (if populated with EEGBCI .edf data), then MNE_DATASETS_EEGBCI_PATH,
    then MNE_DATA, then ~/mne_data.
    """
    import os
    from pathlib import Path

    if cfg.data_path:
        dp = Path(cfg.data_path)
        if dp.exists():
            if (dp / "MNE-eegbci-data").is_dir() and list((dp / "MNE-eegbci-data").glob("**/*.edf")):
                return str(dp)
            if list(dp.glob("*S001*.edf")) or list(dp.glob("**/*S001*.edf")):
                return str(dp)

    mne_eegbci = mne.get_config("MNE_DATASETS_EEGBCI_PATH")
    if mne_eegbci and Path(mne_eegbci).exists() and list(Path(mne_eegbci).glob("**/*.edf")):
        return str(mne_eegbci)

    mne_data = mne.get_config("MNE_DATA")
    if mne_data and Path(mne_data).exists() and list(Path(mne_data).glob("**/*.edf")):
        return str(mne_data)

    home_mne = Path.home() / "mne_data"
    if home_mne.exists() and list(home_mne.glob("**/*.edf")):
        return str(home_mne)

    path = cfg.data_path or str(home_mne)
    os.makedirs(path, exist_ok=True)
    return str(path)


def load_raw(subject: int, cfg: Config) -> mne.io.BaseRaw:
    """Download (first time only) and load the chosen runs for one subject.

    The runs are concatenated into one Raw object. Channel names are
    standardised and the standard 10-05 montage is attached, so topographic
    plots work. The length of each run is stored in raw.info['description'],
    so each trial can later be assigned to its run.
    """
    paths = eegbci.load_data(subject, list(cfg.runs), path=resolve_data_path(cfg), update_path=False)
    raws = [mne.io.read_raw_edf(p, preload=True, verbose="ERROR") for p in paths]
    lengths = [r.n_times for r in raws]
    raw = mne.concatenate_raws(raws)
    eegbci.standardize(raw)
    montage = mne.channels.make_standard_montage("standard_1005")
    raw.set_montage(montage, match_case=False, on_missing="ignore")
    raw.info["description"] = RUN_TAG + ",".join(str(n) for n in lengths)
    return raw
