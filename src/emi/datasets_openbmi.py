"""OpenBMI (Lee et al. 2019) Motor Imagery dataset adapter for LeakCheck V2.

Dataset citation:
    Lee, M.-H., Kwon, O.-Y., Kim, Y.-J., Kim, H.-K., Lee, Y.-E., Williamson, J., Fazli, S., & Lee, S.-W. (2019).
    EEG dataset and OpenBMI toolbox for three BCI paradigms: an investigation into BCI illiteracy.
    GigaScience, 8(5), giz002. DOI: 10.1093/gigascience/giz002.
"""
from pathlib import Path
import logging
import numpy as np
import scipy.io as sio
from scipy.signal import resample_poly

from .cache import save_cache, cache_path

log = logging.getLogger(__name__)

OPENBMI_FAILED_DOWNLOADS = {1, 4, 11, 40, 41}
OPENBMI_CHANNELS_62 = [
    'Fp1', 'Fp2', 'F7', 'F3', 'Fz', 'F4', 'F8', 'FC5', 'FC1', 'FC2', 'FC6',
    'T7', 'C3', 'Cz', 'C4', 'T8', 'TP9', 'CP5', 'CP1', 'CP2', 'CP6', 'TP10',
    'P7', 'P3', 'Pz', 'P4', 'P8', 'PO9', 'O1', 'Oz', 'O2', 'PO10', 'AF7',
    'AF3', 'AF4', 'AF8', 'F5', 'F1', 'F2', 'F6', 'FT9', 'FT7', 'FC3', 'FC4',
    'FT8', 'FT10', 'C5', 'C1', 'C2', 'C6', 'TP7', 'CP3', 'CPz', 'CP4', 'TP8',
    'P5', 'P1', 'P2', 'P6', 'PO7', 'PO3', 'POz'
]


def find_valid_openbmi_subjects(data_dir: Path | str) -> list[int]:
    """Return sorted list of intact OpenBMI subject IDs available in the dataset directory."""
    path = Path(data_dir) / "sourcedata" / "session1"
    if not path.is_dir():
        path = Path(data_dir)
    valid = []
    for d in sorted(path.glob("s*")):
        if d.is_dir() and d.name.startswith("s"):
            try:
                sub_id = int(d.name[1:])
            except ValueError:
                continue
            if sub_id not in OPENBMI_FAILED_DOWNLOADS:
                mat_file = d / f"sess01_subj{sub_id:02d}_EEG_MI.mat"
                if mat_file.is_file() and mat_file.stat().st_size > 1024 * 1024:
                    valid.append(sub_id)
    return sorted(valid)


def load_openbmi_subject(
    subject: int,
    data_dir: Path | str,
    target_fs: float = 160.0,
    tmin: float = 0.0,
    tmax: float = 4.0,
    bandpass: tuple[float, float] | None = None,
    baseline: tuple[float, float] | None = None,
    reject_ptp_uv: float | None = None,
) -> dict:
    """Load and epoch one OpenBMI subject from raw MATLAB session-1 file.

    Parameters
    ----------
    subject : int
        Subject ID (1 to 54).
    data_dir : Path or str
        Base directory of OpenBMI (containing sourcedata/session1/sX/...).
    target_fs : float
        Desired downsampled sampling frequency in Hz (original is 1000 Hz).
    tmin, tmax : float
        Epoch time boundaries in seconds relative to cue onset.
    bandpass : tuple of (float, float), optional
        (l_freq, h_freq) for run-isolated zero-phase FIR bandpass filter.
    baseline : tuple of (float, float), optional
        (bmin, bmax) interval in seconds for baseline mean subtraction.
    reject_ptp_uv : float, optional
        Threshold in microvolts to flag artifact trials non-destructively.

    Returns
    -------
    dict with keys: X, y, runs, times, subject, ch_names, sfreq, extra, and optional artifact_mask
    """
    if subject in OPENBMI_FAILED_DOWNLOADS:
        raise ValueError(f"OpenBMI subject {subject} is known to be incomplete or corrupted.")

    path = Path(data_dir) / "sourcedata" / "session1" / f"s{subject}" / f"sess01_subj{subject:02d}_EEG_MI.mat"
    if not path.is_file():
        alt = Path(data_dir) / "OpenBMI" / "sourcedata" / "session1" / f"s{subject}" / f"sess01_subj{subject:02d}_EEG_MI.mat"
        if alt.is_file():
            path = alt
        else:
            alt2 = Path(r"D:\my lab\LeakCheck\data\OpenBMI\sourcedata\session1") / f"s{subject}" / f"sess01_subj{subject:02d}_EEG_MI.mat"
            if alt2.is_file():
                path = alt2
    if not path.is_file():
        raise FileNotFoundError(f"OpenBMI file not found: {path}")

    mat = sio.loadmat(str(path))
    if "EEG_MI_train" not in mat or "EEG_MI_test" not in mat:
        raise ValueError(f"Expected EEG_MI_train and EEG_MI_test in {path}")

    blocks = [("train", mat["EEG_MI_train"][0, 0], 0), ("test", mat["EEG_MI_test"][0, 0], 1)]

    all_epochs = []
    all_labels = []
    all_runs = []
    ch_names = []

    orig_fs = float(blocks[0][1]["fs"][0, 0])
    down_factor = int(round(orig_fs / target_fs))
    actual_fs = orig_fs / down_factor

    # Compute epoch window in samples relative to cue
    s_min = int(round(tmin * orig_fs))
    s_max = int(round(tmax * orig_fs))
    expected_n_samples = s_max - s_min

    for block_name, struct, run_id in blocks:
        continuous_x = struct["x"]  # shape (n_samples, n_channels)
        cues = struct["t"][0]       # sample onsets of cues
        labels_raw = struct["y_dec"][0]  # 1 = right, 2 = left

        if not ch_names and "chan" in struct.dtype.names:
            ch_names = [str(c[0]) for c in struct["chan"][0]]

        if down_factor > 1:
            # Polyphase decimation on continuous recording
            cx_proc = resample_poly(continuous_x, up=1, down=down_factor, axis=0)
        else:
            cx_proc = continuous_x

        # Apply run-isolated zero-phase FIR bandpass filtering if requested
        if bandpass is not None:
            import mne
            cx_proc = mne.filter.filter_data(
                cx_proc.T, actual_fs, bandpass[0], bandpass[1],
                fir_design="firwin", verbose="ERROR"
            ).T

        s_min_proc = int(round(tmin * actual_fs))
        s_max_proc = int(round(tmax * actual_fs))

        for cue_idx, label_val in zip(cues, labels_raw):
            onset = int(round((int(cue_idx) - 1) / down_factor))
            start = onset + s_min_proc
            end = onset + s_max_proc

            if start >= 0 and end <= cx_proc.shape[0]:
                epoch = cx_proc[start:end, :].T  # channels x samples

                if baseline is not None:
                    epoch_times = np.linspace(tmin, tmax, epoch.shape[-1], endpoint=False)
                    bmask = (epoch_times >= baseline[0]) & (epoch_times < baseline[1])
                    if np.any(bmask):
                        epoch = epoch - epoch[:, bmask].mean(axis=-1, keepdims=True)

                all_epochs.append(epoch)
                # Map labels: 1 (right) -> 1, 2 (left) -> 0
                binary_label = 1 if label_val == 1 else 0
                all_labels.append(binary_label)
                all_runs.append(run_id)

    if not all_epochs:
        raise ValueError(f"No valid epochs extracted for subject {subject}")

    X = np.stack(all_epochs, axis=0).astype(np.float64)  # (trials, channels, times)
    y = np.array(all_labels, dtype=np.int8)
    runs = np.array(all_runs, dtype=np.int64)
    times = np.linspace(tmin, tmax, X.shape[2], endpoint=False)

    artifact_mask = None
    if reject_ptp_uv is not None:
        ptp = (X.max(axis=-1) - X.min(axis=-1)).max(axis=-1)
        artifact_mask = (ptp > reject_ptp_uv)

    out_dict = {
        "X": X,
        "y": y,
        "runs": runs,
        "times": times,
        "subject": subject,
        "ch_names": ch_names or OPENBMI_CHANNELS_62[:X.shape[1]],
        "sfreq": actual_fs,
        "extra": {
            "dataset": "openbmi",
            "source_file": str(path),
            "orig_fs": orig_fs,
            "target_fs": actual_fs,
            "tmin": tmin,
            "tmax": tmax,
            "bandpass": bandpass,
            "baseline": baseline,
        }
    }
    if artifact_mask is not None:
        out_dict["artifact_mask"] = artifact_mask
        out_dict["extra"]["n_artifact_flagged"] = int(np.sum(artifact_mask))

    return out_dict


def cache_openbmi_subject(
    subject: int,
    data_dir: Path | str,
    cache_dir: Path | str,
    target_fs: float = 160.0,
    tmin: float = 0.0,
    tmax: float = 4.0,
) -> Path:
    """Preprocess and write one OpenBMI subject to standard LeakCheck schema-v2 cache."""
    data = load_openbmi_subject(subject, data_dir, target_fs=target_fs, tmin=tmin, tmax=tmax)
    dest_path = cache_path(cache_dir, subject, dataset="openbmi")
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    save_cache(
        dest_path,
        data["X"],
        data["y"],
        data["runs"],
        data["times"],
        subject=subject,
        dataset="openbmi",
        sessions=np.zeros(len(data["y"]), dtype=np.int64),
        order=np.arange(len(data["y"]), dtype=np.int64),
        sfreq=data["sfreq"],
        ch_names=data["ch_names"],
        extra=data["extra"],
    )
    log.info("Cached OpenBMI subject %d to %s (%d trials, shape %s)", subject, dest_path, len(data["y"]), data["X"].shape)
    return dest_path
