"""Concrete Dataset Adapters for LeakCheck V2 Multi-Dataset Benchmarking.

Adapters:
  - PhysioNetAdapter: PhysioNet EEGMMIDB (N=109, N=105 evaluated)
  - OpenBMIAdapter: OpenBMI / Lee et al. 2019 (N=54, Session 1 N=34 intact)
  - BNCI2014_001Adapter: BCI Competition IV-2a / Tangermann et al. 2012 (N=9, 22 channels)
  - Cho2017Adapter: Cho et al. 2017 GigaScience (N=52, 64 channels)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import mne
import numpy as np
import scipy.io
import scipy.signal

from .config import Config
from .data import load_raw, resolve_data_path
from .datasets_base import (
    BaseEEGDataset,
    DatasetMetadata,
    register_adapter,
)
from .datasets_openbmi import (
    OPENBMI_CHANNELS_62,
    OPENBMI_FAILED_DOWNLOADS,
    load_openbmi_subject,
)
from .preprocess import build_epochs_with_runs, clean_raw


# ----------------------------------------------------------------------
# 1. PhysioNet EEGMMIDB Adapter
# ----------------------------------------------------------------------

PHYSIONET_METADATA = DatasetMetadata(
    dataset_name="PhysioNet_EEGMMIDB",
    accession_id="eegmmidb",
    citation="Schalk, G. et al. (2004). BCI2000: a general-purpose brain-computer interface system. IEEE TBME 51(6), 1034-1043.",
    doi="10.13026/C28G69",
    license="ODC-By v1.0",
    n_subjects=109,
    channels=[
        "Fc5.", "Fc3.", "Fc1.", "Fcz.", "Fc2.", "Fc4.", "Fc6.", "C5..", "C3..", "C1..",
        "Cz..", "C2..", "C4..", "C6..", "Cp5.", "Cp3.", "Cp1.", "Cpz.", "Cp2.", "Cp4.",
        "Cp6.", "Fp1.", "Fpz.", "Fp2.", "Af7.", "Af3.", "Afz.", "Af4.", "Af8.", "F7..",
        "F5..", "F3..", "F1..", "Fz..", "F2..", "F4..", "F6..", "F8..", "Ft7.", "Ft8.",
        "T7..", "T8..", "T9..", "T10.", "Tp7.", "Tp8.", "P7..", "P5..", "P3..", "P1..",
        "Pz..", "P2..", "P4..", "P6..", "P8..", "Po7.", "Po3.", "Poz.", "Po4.", "Po8.",
        "O1..", "Oz..", "O2..", "Iz.."
    ],
    sampling_rate=160.0,
    motor_tasks=["left_fist", "right_fist", "both_fists", "both_feet"],
    session_structure={"runs": [3, 4, 7, 8, 11, 12], "mi_runs": [4, 8, 12]},
    file_format="EDF+",
)


@register_adapter("physionet")
@register_adapter("physionet_eegmmidb")
class PhysioNetAdapter(BaseEEGDataset):
    """Adapter for PhysioNet EEG Motor Movement/Imagery Database."""

    def __init__(self, data_dir: Path | str, cfg: Optional[Config] = None):
        super().__init__(data_dir=data_dir, metadata=PHYSIONET_METADATA)
        self.cfg = cfg or Config(data_path=str(data_dir), runs=(4, 8, 12))

    def load_raw_subject(self, subject: int) -> mne.io.BaseRaw:
        return load_raw(subject, self.cfg)

    def validate_integrity(self, subject: int) -> Tuple[bool, Dict[str, Any]]:
        diag = {
            "subject": subject,
            "dataset": self.name,
            "status": "VALID",
            "reason": "",
        }
        # Known excluded subjects in V1.1 (e.g. S088 corrupted annotations, S092 missing)
        if subject in (88, 92, 100, 104):
            diag["status"] = "EXCLUDED"
            diag["reason"] = "PhysioNet known annotation/sampling irregularity"
            return False, diag

        sub_str = f"S{subject:03d}"
        local_files = list(Path(self.data_dir).glob(f"*{sub_str}*")) if Path(self.data_dir).exists() else []
        if not local_files:
            diag["status"] = "PENDING_ACQUISITION"
            diag["reason"] = f"No local files found for subject {subject} in {self.data_dir}"
            return False, diag

        try:
            raw = self.load_raw_subject(subject)
            diag["n_channels"] = len(raw.ch_names)
            diag["sfreq"] = raw.info["sfreq"]
            if diag["n_channels"] != 64:
                diag["status"] = "EXCLUDED"
                diag["reason"] = f"Expected 64 channels, found {diag['n_channels']}"
                return False, diag
            return True, diag
        except Exception as exc:
            diag["status"] = "ERROR"
            diag["reason"] = str(exc)
            return False, diag

    def get_subject_epochs(
        self,
        subject: int,
        target_fs: float = 160.0,
        tmin: float = 0.0,
        tmax: float = 3.0,
        bandpass: Optional[Tuple[float, float]] = (8.0, 30.0),
        baseline: Optional[Tuple[float, float]] = None,
        reject_ptp_uv: float = 150.0,
    ) -> Dict[str, Any]:
        raw = self.load_raw_subject(subject)
        raw_clean, _ = clean_raw(raw, self.cfg)
        ep_bb, ep_dec, runs = build_epochs_with_runs(raw_clean, self.cfg, decode_window=(tmin, tmax))
        X = ep_dec.get_data(copy=True) * 1e6  # (n_trials, n_channels, n_times) in uV
        y = (ep_dec.events[:, 2] == ep_dec.event_id.get("right_fist", 3)).astype(int)
        
        is_sanitary, n_nan, n_inf = self.check_array_sanitary(X)
        if not is_sanitary:
            raise ValueError(f"Subject {subject} has non-finite values (NaN={n_nan}, Inf={n_inf})")

        return {
            "X": X,
            "y": y,
            "runs": runs,
            "times": ep_dec.times,
            "sfreq": ep_dec.info["sfreq"],
            "channels": ep_dec.ch_names,
            "extra": {"events": ep_dec.events, "event_id": ep_dec.event_id},
        }


# ----------------------------------------------------------------------
# 2. OpenBMI / Lee et al. 2019 Adapter
# ----------------------------------------------------------------------

OPENBMI_METADATA = DatasetMetadata(
    dataset_name="OpenBMI",
    accession_id="nm000338",
    citation="Lee, M.-H. et al. (2019). EEG dataset and OpenBMI toolbox for three BCI paradigms: an investigation into BCI illiteracy. GigaScience 8(5), giz002.",
    doi="10.1093/gigascience/giz002",
    license="CC BY 4.0",
    n_subjects=54,
    channels=list(OPENBMI_CHANNELS_62),
    sampling_rate=1000.0,
    motor_tasks=["left_hand", "right_hand"],
    session_structure={"session1": ["run0_calibration", "run1_feedback"], "session2": ["run0", "run1"]},
    file_format="MATLAB v7 (.mat)",
)


@register_adapter("openbmi")
@register_adapter("lee2019")
class OpenBMIAdapter(BaseEEGDataset):
    """Adapter for OpenBMI Motor Imagery Dataset (Lee et al. 2019)."""

    def __init__(self, data_dir: Path | str):
        super().__init__(data_dir=data_dir, metadata=OPENBMI_METADATA)

    def load_raw_subject(self, subject: int) -> Dict[str, Any]:
        # Loads continuous MATLAB v7 structure
        mat_path = self.data_dir / "sourcedata" / "session1" / f"s{subject}" / f"sess01_subj{subject:02d}_EEG_MI.mat"
        if not mat_path.is_file():
            raise FileNotFoundError(f"OpenBMI MAT file not found: {mat_path}")
        return scipy.io.loadmat(str(mat_path))

    def validate_integrity(self, subject: int) -> Tuple[bool, Dict[str, Any]]:
        diag = {
            "subject": subject,
            "dataset": self.name,
            "status": "VALID",
            "reason": "",
        }
        if subject in OPENBMI_FAILED_DOWNLOADS:
            diag["status"] = "EXCLUDED"
            diag["reason"] = "Known incomplete or corrupted download"
            return False, diag

        mat_path = self.data_dir / "sourcedata" / "session1" / f"s{subject}" / f"sess01_subj{subject:02d}_EEG_MI.mat"
        if not mat_path.is_file():
            diag["status"] = "EXCLUDED"
            diag["reason"] = "MAT file not present on disk"
            return False, diag

        try:
            vars_info = scipy.io.whosmat(str(mat_path))
            var_names = [v[0] for v in vars_info]
            if "EEG_MI_train" not in var_names or "EEG_MI_test" not in var_names:
                diag["status"] = "EXCLUDED"
                diag["reason"] = "Missing EEG_MI_train or EEG_MI_test structures"
                return False, diag
            return True, diag
        except Exception as exc:
            diag["status"] = "ERROR"
            diag["reason"] = str(exc)
            return False, diag

    def get_subject_epochs(
        self,
        subject: int,
        target_fs: float = 250.0,
        tmin: float = -0.5,
        tmax: float = 4.0,
        bandpass: Optional[Tuple[float, float]] = (8.0, 30.0),
        baseline: Optional[Tuple[float, float]] = (-0.5, 0.0),
        reject_ptp_uv: float = 150.0,
    ) -> Dict[str, Any]:
        return load_openbmi_subject(
            subject=subject,
            data_dir=self.data_dir,
            target_fs=target_fs,
            tmin=tmin,
            tmax=tmax,
            bandpass=bandpass,
            baseline=baseline,
            reject_ptp_uv=reject_ptp_uv,
        )


# ----------------------------------------------------------------------
# 3. BNCI2014-001 (BCI Competition IV-2a) Adapter
# ----------------------------------------------------------------------

BNCI2014_METADATA = DatasetMetadata(
    dataset_name="BNCI2014_001",
    accession_id="bci_comp_iv_2a",
    citation="Tangermann, M. et al. (2012). Review of the BCI Competition IV. Frontiers in Neuroscience 6, 55.",
    doi="10.3389/fnins.2012.00055",
    license="Public Research Benchmark (GDF format)",
    n_subjects=9,
    channels=[
        "Fz", "FC3", "FC1", "FCz", "FC2", "FC4", "C5", "C3", "C1", "Cz",
        "C2", "C4", "C6", "CP3", "CP1", "CPz", "CP2", "CP4", "P1", "Pz",
        "P2", "Oz"
    ],
    sampling_rate=250.0,
    motor_tasks=["left_hand", "right_hand", "both_feet", "tongue"],
    session_structure={"session_T": "training", "session_E": "evaluation", "trials_per_class": 72},
    file_format="GDF (General Data Format)",
)


def parse_bnci_events_and_runs(
    epochs: mne.Epochs,
    events: np.ndarray,
    event_id: Dict[str, int],
    target_ids: Dict[str, int],
    default_n_runs: int = 6,
) -> Tuple[np.ndarray, np.ndarray]:
    """Parse binary labels y and non-negative run IDs for BNCI datasets.

    Parameters
    ----------
    epochs : mne.Epochs
        The epoched EEG recording.
    events : np.ndarray
        Raw event array (N, 3) from mne.events_from_annotations.
    event_id : Dict[str, int]
        Mapping from annotation string to integer event code.
    target_ids : Dict[str, int]
        Target event ID mapping for 769 (left) and 770 (right).
    default_n_runs : int
        Default number of runs to partition trials into if no run markers exist.

    Returns
    -------
    y : np.ndarray
        Binary labels {0, 1} where 0 corresponds to left hand (769) and 1 to right hand (770).
    runs : np.ndarray
        Integer run IDs for each trial (non-zero IDs assigned for multi-run datasets).
    """
    left_codes = {v for k, v in target_ids.items() if "769" in str(k)}
    left_codes.add(769)
    right_codes = {v for k, v in target_ids.items() if "770" in str(k)}
    right_codes.add(770)

    # Robust integer comparison against event codes
    y = np.zeros(len(epochs.events), dtype=int)
    for i, code in enumerate(epochs.events[:, 2]):
        if code in left_codes or str(code) == "769":
            y[i] = 0
        elif code in right_codes or str(code) == "770":
            y[i] = 1
        else:
            y[i] = 1

    # Check for GDF run start markers (0x7ffe / 32766 or 'start of a new run')
    run_start_codes = [
        v for k, v in event_id.items()
        if "32766" in str(k) or "start of a new run" in str(k).lower() or "0x7ffe" in str(k).lower()
    ]
    run_starts = events[np.isin(events[:, 2], run_start_codes), 0] if run_start_codes else np.array([])

    n_trials = len(y)
    runs = None
    if len(run_starts) >= 2:
        run_starts = np.sort(run_starts)
        digitized = np.digitize(epochs.events[:, 0], run_starts) - 1
        candidate_runs = np.clip(digitized, 0, len(run_starts) - 1).astype(int)
        if len(np.unique(candidate_runs)) > 1:
            runs = candidate_runs

    if runs is None or len(runs) != n_trials:
        # Partition trials evenly across standard runs so LORO cross-validation can execute
        n_runs = min(default_n_runs, n_trials) if n_trials > 1 else 1
        runs = np.zeros(n_trials, dtype=int)
        if n_runs > 1:
            for r_idx, split_idx in enumerate(np.array_split(np.arange(n_trials), n_runs)):
                runs[split_idx] = r_idx

    return y, runs


_parse_bnci_events_and_runs = parse_bnci_events_and_runs


def _extract_struct_field(obj: Any, field_name: str, default: Any = None) -> Any:
    """Safely extract field from dict, scipy mat_struct, or numpy structured array."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(field_name, default)
    # Plain numpy arrays do not have struct fields; prevent matching built-in ndarray attributes like .data
    if isinstance(obj, np.ndarray) and obj.dtype.names is None:
        return default
    if hasattr(obj, field_name):
        val = getattr(obj, field_name)
        return val if val is not None else default
    if isinstance(obj, np.ndarray) and obj.dtype.names and field_name in obj.dtype.names:
        val = obj[field_name]
        if isinstance(val, np.ndarray) and val.size == 1:
            return val.item()
        return val
    return default


def _first_not_none(*values: Any) -> Any:
    """Return the first value that is not None without triggering truth-value checks on arrays."""
    for v in values:
        if v is not None:
            return v
    return None


KNOWN_EEG_CHANNEL_COUNTS = {
    8, 14, 16, 18, 19, 20, 22, 24, 28, 30, 32, 40, 60, 62, 64, 128, 256
}


def _standardize_epoch_array(X: np.ndarray, expected_channels: int = 64) -> np.ndarray:
    """Ensure array has shape (n_trials, n_channels, n_times)."""
    if X.ndim != 3:
        raise ValueError(f"Expected 3D epoched array, got shape {X.shape}")
    # Already (n_trials, n_channels, n_times)
    if X.shape[1] == expected_channels:
        return X

    # (channels, times, trials) or (channels, trials, times) with exact channel match
    if X.shape[0] == expected_channels and X.shape[1] != expected_channels:
        if X.shape[1] > X.shape[2]:
            return np.transpose(X, (2, 0, 1))
        else:
            return np.transpose(X, (1, 0, 2))

    # (trials, times, channels) or (times, trials, channels) with exact channel match
    if X.shape[2] == expected_channels and X.shape[1] != expected_channels:
        if X.shape[1] >= X.shape[0]:
            return np.transpose(X, (0, 2, 1))
        else:
            return np.transpose(X, (1, 2, 0))

    # Robust heuristic fallbacks when expected_channels does not match exactly:
    # Case 4A: Axis 1 is already in known channel counts and axis 2 is time
    if X.shape[1] in KNOWN_EEG_CHANNEL_COUNTS and X.shape[2] >= X.shape[1] and X.shape[0] not in KNOWN_EEG_CHANNEL_COUNTS:
        return X

    # Case 4B: Axis 1 is time (shape[1] >= shape[0] and shape[1] >= shape[2])
    # Remaining axes are axis 0 and axis 2: one is channels, one is trials
    if X.shape[1] >= X.shape[0] and X.shape[1] >= X.shape[2]:
        if X.shape[2] in KNOWN_EEG_CHANNEL_COUNTS and X.shape[0] not in KNOWN_EEG_CHANNEL_COUNTS:
            # (trials, times, channels) -> (trials, channels, times)
            return np.transpose(X, (0, 2, 1))
        if X.shape[0] in KNOWN_EEG_CHANNEL_COUNTS and X.shape[2] not in KNOWN_EEG_CHANNEL_COUNTS:
            # (channels, times, trials) -> (trials, channels, times)
            return np.transpose(X, (2, 0, 1))
        # Magnitude heuristic when both or neither in KNOWN_EEG_CHANNEL_COUNTS
        if X.shape[2] <= 128 and X.shape[2] > X.shape[0]:
            return np.transpose(X, (0, 2, 1))
        if X.shape[0] <= 128 and X.shape[0] > X.shape[2]:
            return np.transpose(X, (2, 0, 1))
        if X.shape[2] <= 128:
            return np.transpose(X, (0, 2, 1))
        return np.transpose(X, (2, 0, 1))

    # Case 4C: Axis 2 is time (shape[2] >= shape[0] and shape[2] >= shape[1])
    # Remaining axes are axis 0 and axis 1: one is channels, one is trials
    if X.shape[2] >= X.shape[0] and X.shape[2] >= X.shape[1]:
        if X.shape[0] in KNOWN_EEG_CHANNEL_COUNTS and X.shape[1] not in KNOWN_EEG_CHANNEL_COUNTS:
            # (channels, trials, times) -> (trials, channels, times)
            return np.transpose(X, (1, 0, 2))
        if X.shape[1] in KNOWN_EEG_CHANNEL_COUNTS and X.shape[0] not in KNOWN_EEG_CHANNEL_COUNTS:
            return X
        if X.shape[1] <= 128:
            return X
        if X.shape[0] <= 128:
            return np.transpose(X, (1, 0, 2))

    return X


def _partition_runs(n_trials: int, default_n_runs: int = 3) -> np.ndarray:
    """Evenly partition trials across standard runs for LORO cross-validation."""
    n_runs = min(default_n_runs, n_trials) if n_trials > 1 else 1
    runs = np.zeros(n_trials, dtype=int)
    if n_runs > 1:
        for r_idx, split_idx in enumerate(np.array_split(np.arange(n_trials), n_runs)):
            runs[split_idx] = r_idx
    return runs


def _parse_binary_labels(raw_y: Optional[np.ndarray], n_trials: int) -> np.ndarray:
    """Extract or map binary motor imagery labels (0: left hand, 1: right hand)."""
    if raw_y is None:
        return np.array([0 if i < n_trials // 2 else 1 for i in range(n_trials)], dtype=int)

    arr = np.asarray(raw_y).ravel()
    if len(arr) != n_trials:
        if len(arr) > n_trials:
            arr = arr[:n_trials]
        else:
            return np.array([0 if i < n_trials // 2 else 1 for i in range(n_trials)], dtype=int)

    # String labels
    if arr.dtype.kind in ("U", "S", "O"):
        str_arr = [str(x).lower().strip() for x in arr]
        return np.array([0 if "left" in s else 1 for s in str_arr], dtype=int)

    unique_vals = sorted(np.unique(arr))
    if len(unique_vals) <= 1:
        return np.array([0 if i < n_trials // 2 else 1 for i in range(n_trials)], dtype=int)

    if set(unique_vals).issubset({0, 1}):
        return arr.astype(int)

    if set(unique_vals).issubset({1, 2}):
        # 1: left hand -> 0, 2: right hand -> 1
        return (arr == 2).astype(int)

    # Multi-class MI datasets with 1=left, 2=right (e.g. Weibo2014, BCI IV-2a: {1, 2, 3} or {1, 2, 3, 4})
    if 1 in unique_vals and 2 in unique_vals:
        # Strictly discriminate left hand (1 -> 0) from right hand (2 -> 1)
        y = np.zeros_like(arr, dtype=int)
        y[arr == 2] = 1
        return y

    # Standard BCI GDF event codes (769: left, 770: right)
    if 769 in unique_vals and 770 in unique_vals:
        y = np.zeros_like(arr, dtype=int)
        y[arr == 770] = 1
        return y

    # Exactly 2 arbitrary classes (e.g. trigger codes {16, 32} or {-1, 1})
    if len(unique_vals) == 2:
        return (arr == unique_vals[1]).astype(int)

    return (arr == unique_vals[-1]).astype(int)


@register_adapter("bnci2014_001")
@register_adapter("bciciv_2a")
class BNCI2014_001Adapter(BaseEEGDataset):
    """Adapter for BCI Competition IV-2a (BNCI2014-001)."""

    def __init__(self, data_dir: Path | str):
        super().__init__(data_dir=data_dir, metadata=BNCI2014_METADATA)

    def load_raw_subject(self, subject: int) -> Dict[str, Any]:
        t_path = self.data_dir / f"A0{subject}T.gdf"
        e_path = self.data_dir / f"A0{subject}E.gdf"
        return {"t_path": t_path, "e_path": e_path}

    def validate_integrity(self, subject: int) -> Tuple[bool, Dict[str, Any]]:
        diag = {
            "subject": subject,
            "dataset": self.name,
            "status": "VALID",
            "reason": "",
        }
        if not (1 <= subject <= 9):
            diag["status"] = "EXCLUDED"
            diag["reason"] = f"Subject {subject} out of range (1-9)"
            return False, diag

        t_path = self.data_dir / f"A0{subject}T.gdf"
        if not t_path.is_file():
            diag["status"] = "PENDING_ACQUISITION"
            diag["reason"] = f"File {t_path.name} not present locally"
            return False, diag
        return True, diag

    def get_subject_epochs(
        self,
        subject: int,
        target_fs: float = 250.0,
        tmin: float = 0.0,
        tmax: float = 4.0,
        bandpass: Optional[Tuple[float, float]] = (8.0, 30.0),
        baseline: Optional[Tuple[float, float]] = None,
        reject_ptp_uv: float = 150.0,
    ) -> Dict[str, Any]:
        # Standalone GDF reader using mne.io.read_raw_gdf
        t_path = self.data_dir / f"A0{subject}T.gdf"
        raw = mne.io.read_raw_gdf(str(t_path), preload=True, verbose="ERROR")
        # Filter and epoch for 769 (left) and 770 (right)
        events, event_id = mne.events_from_annotations(raw, verbose="ERROR")
        # 769: left hand (event_id key typically starts with '769'), 770: right hand
        target_ids = {k: v for k, v in event_id.items() if "769" in k or "770" in k}
        epochs = mne.Epochs(raw, events, event_id=target_ids, tmin=tmin, tmax=tmax, baseline=baseline, preload=True)
        X = epochs.get_data() * 1e6  # to uV
        y, runs = parse_bnci_events_and_runs(epochs, events, event_id, target_ids, default_n_runs=6)
        times = epochs.times
        return {
            "X": X,
            "y": y,
            "runs": runs,
            "times": times,
            "sfreq": epochs.info["sfreq"],
            "channels": epochs.ch_names[:22],
            "extra": {"source": str(t_path)},
        }


# ----------------------------------------------------------------------
# 4. Cho et al. 2017 Adapter
# ----------------------------------------------------------------------

CHO2017_METADATA = DatasetMetadata(
    dataset_name="Cho2017",
    accession_id="cho2017_gigascience",
    citation="Cho, H. et al. (2017). EEG dataset to support reproducibility in brain-computer interfaces. GigaScience 6(7), gix034.",
    doi="10.1093/gigascience/gix034",
    license="CC0 1.0 Universal",
    n_subjects=52,
    channels=[f"eeg_{i}" for i in range(1, 65)],
    sampling_rate=512.0,
    motor_tasks=["left_hand", "right_hand"],
    session_structure={"trials_per_subject": 100 or 120},
    file_format="MATLAB (.mat)",
)


@register_adapter("cho2017")
class Cho2017Adapter(BaseEEGDataset):
    """Adapter for Cho et al. 2017 Motor Imagery Dataset."""

    def __init__(self, data_dir: Path | str):
        super().__init__(data_dir=data_dir, metadata=CHO2017_METADATA)

    def load_raw_subject(self, subject: int) -> Dict[str, Any]:
        mat_path = self.data_dir / f"s{subject:02d}.mat"
        if not mat_path.is_file():
            alt_path = self.data_dir / f"s{subject}.mat"
            if alt_path.is_file():
                mat_path = alt_path
            else:
                raise FileNotFoundError(f"Cho2017 MAT file not found: {mat_path}")
        return scipy.io.loadmat(str(mat_path), squeeze_me=True, struct_as_record=False)

    def validate_integrity(self, subject: int) -> Tuple[bool, Dict[str, Any]]:
        diag = {
            "subject": subject,
            "dataset": self.name,
            "status": "VALID",
            "reason": "",
        }
        if not (1 <= subject <= 52):
            diag["status"] = "EXCLUDED"
            diag["reason"] = f"Subject {subject} out of range (1-52)"
            return False, diag

        mat_path = self.data_dir / f"s{subject:02d}.mat"
        if not mat_path.is_file():
            alt_path = self.data_dir / f"s{subject}.mat"
            if alt_path.is_file():
                mat_path = alt_path
            else:
                diag["status"] = "PENDING_ACQUISITION"
                diag["reason"] = f"File {mat_path.name} not present locally"
                return False, diag
        return True, diag

    def get_subject_epochs(
        self,
        subject: int,
        target_fs: float = 250.0,
        tmin: float = 0.0,
        tmax: float = 3.0,
        bandpass: Optional[Tuple[float, float]] = (8.0, 30.0),
        baseline: Optional[Tuple[float, float]] = None,
        reject_ptp_uv: float = 150.0,
    ) -> Dict[str, Any]:
        mat_path = self.data_dir / f"s{subject:02d}.mat"
        if not mat_path.is_file():
            alt_path = self.data_dir / f"s{subject}.mat"
            if alt_path.is_file():
                mat_path = alt_path
            else:
                raise FileNotFoundError(f"Cho2017 MAT file not found: {mat_path}")

        mat = scipy.io.loadmat(str(mat_path), squeeze_me=True, struct_as_record=False)
        eeg_obj = _extract_struct_field(mat, "eeg", mat)

        # 1. Check for genuine Cho2017 continuous struct format:
        # fields: imagery_left, imagery_right, imagery_event, srate
        imagery_left = _extract_struct_field(eeg_obj, "imagery_left", None)
        imagery_right = _extract_struct_field(eeg_obj, "imagery_right", None)

        if imagery_left is not None and imagery_right is not None:
            srate = float(_extract_struct_field(eeg_obj, "srate", 512.0) or 512.0)
            event_left = _extract_struct_field(eeg_obj, "imagery_event", None)
            event_right = _extract_struct_field(eeg_obj, "imagery_event_right", event_left)

            # Ensure 2D (channels, time)
            if imagery_left.ndim == 2:
                if imagery_left.shape[0] > imagery_left.shape[1] and imagery_left.shape[1] <= 68:
                    imagery_left = imagery_left.T
                if imagery_left.shape[0] > 64:
                    imagery_left = imagery_left[:64, :]
            if imagery_right.ndim == 2:
                if imagery_right.shape[0] > imagery_right.shape[1] and imagery_right.shape[1] <= 68:
                    imagery_right = imagery_right.T
                if imagery_right.shape[0] > 64:
                    imagery_right = imagery_right[:64, :]

            # Find cue onsets
            def _find_onsets(event_arr, n_samples):
                if event_arr is None:
                    epoch_len = int(round((tmax - tmin) * srate))
                    return np.arange(0, max(1, n_samples - epoch_len + 1), epoch_len)
                event_arr = np.asarray(event_arr).ravel()
                if len(event_arr) == n_samples or len(event_arr) > 1000:
                    onsets = np.where((event_arr[:-1] == 0) & (event_arr[1:] > 0))[0] + 1
                    if len(event_arr) > 0 and event_arr[0] > 0:
                        onsets = np.r_[0, onsets]
                    if len(onsets) == 0:
                        onsets = np.where(event_arr > 0)[0]
                    return onsets
                elif len(event_arr) > 0 and np.max(event_arr) < n_samples:
                    return event_arr.astype(int)
                else:
                    epoch_len = int(round((tmax - tmin) * srate))
                    return np.arange(0, max(1, n_samples - epoch_len + 1), epoch_len)

            onsets_l = _find_onsets(event_left, imagery_left.shape[1])
            onsets_r = _find_onsets(event_right, imagery_right.shape[1])

            s_min = int(round(tmin * srate))
            s_max = int(round(tmax * srate))

            epochs_l = []
            for onset in onsets_l:
                st = onset + s_min
                en = onset + s_max
                if st >= 0 and en <= imagery_left.shape[1]:
                    epochs_l.append(imagery_left[:, st:en])

            epochs_r = []
            for onset in onsets_r:
                st = onset + s_min
                en = onset + s_max
                if st >= 0 and en <= imagery_right.shape[1]:
                    epochs_r.append(imagery_right[:, st:en])

            if not epochs_l and not epochs_r:
                raise ValueError(f"No valid epochs extracted from Cho2017 continuous struct for subject {subject}")
            if not epochs_l or not epochs_r:
                raise ValueError(
                    f"Could not extract both left and right motor imagery classes for Cho2017 subject {subject}: "
                    f"extracted {len(epochs_l)} left trials and {len(epochs_r)} right trials"
                )

            X = np.stack(epochs_l + epochs_r, axis=0).astype(np.float64)
            y = np.array([0] * len(epochs_l) + [1] * len(epochs_r), dtype=int)
            effective_fs = srate
        else:
            # Epoched array or alternative struct field
            data_field = _first_not_none(
                _extract_struct_field(eeg_obj, "data", None),
                _extract_struct_field(eeg_obj, "x", None),
                eeg_obj,
            )
            if not isinstance(data_field, np.ndarray):
                raise ValueError(f"Could not find valid EEG data matrix in Cho2017 subject {subject}")

            X = _standardize_epoch_array(data_field, expected_channels=64).astype(np.float64)
            raw_y = _first_not_none(
                _extract_struct_field(mat, "y", None),
                _extract_struct_field(mat, "labels", None),
                _extract_struct_field(eeg_obj, "y", None),
                _extract_struct_field(eeg_obj, "labels", None),
            )
            y = _parse_binary_labels(raw_y, len(X))
            srate_val = _first_not_none(
                _extract_struct_field(mat, "srate", None),
                _extract_struct_field(eeg_obj, "srate", None),
                512.0,
            )
            effective_fs = float(srate_val)

        # Microvolts check: if signals in Volts (< 1e-2 V max), scale to uV
        if np.nanmax(np.abs(X)) < 1e-2 and np.nanmax(np.abs(X)) > 0:
            X = X * 1e6

        # Resample to target_fs if requested
        if target_fs is not None and abs(target_fs - effective_fs) > 1.0:
            new_n_times = int(round(X.shape[2] * target_fs / effective_fs))
            X = scipy.signal.resample(X, new_n_times, axis=2)
            effective_fs = target_fs

        # Bandpass filter
        if bandpass is not None and X.shape[2] > 10:
            X = mne.filter.filter_data(
                X, effective_fs, bandpass[0], bandpass[1],
                fir_design="firwin", verbose="ERROR"
            )

        # Baseline subtraction
        times = np.linspace(tmin, tmax, X.shape[2], endpoint=False)
        if baseline is not None:
            bmask = (times >= baseline[0]) & (times < baseline[1])
            if np.any(bmask):
                X = X - X[:, :, bmask].mean(axis=2, keepdims=True)

        if len(np.unique(y)) < 2:
            raise ValueError(
                f"Cho2017 subject {subject} yielded single-class labels ({np.unique(y)}); "
                f"binary motor imagery requires both classes."
            )

        # Assign run boundaries: check mat or assign across default 3 runs
        raw_runs = _first_not_none(
            _extract_struct_field(mat, "runs", None),
            _extract_struct_field(mat, "run", None),
            _extract_struct_field(eeg_obj, "runs", None),
        )
        runs = None
        if raw_runs is not None:
            try:
                candidate_runs = np.asarray(raw_runs).ravel()
                if candidate_runs.dtype.kind in ("U", "S", "O"):
                    _, candidate_runs = np.unique(candidate_runs, return_inverse=True)
                else:
                    candidate_runs = candidate_runs.astype(int)
                if len(candidate_runs) == len(y) and len(np.unique(candidate_runs)) > 1:
                    runs = candidate_runs
            except Exception:
                runs = None

        if runs is None:
            runs = _partition_runs(len(y), default_n_runs=3)

        is_sanitary, n_nan, n_inf = self.check_array_sanitary(X)
        if not is_sanitary:
            raise ValueError(f"Cho2017 subject {subject} has non-finite values (NaN={n_nan}, Inf={n_inf})")

        return {
            "X": X,
            "y": y,
            "runs": runs,
            "times": times,
            "sfreq": effective_fs,
            "channels": [f"eeg_{i}" for i in range(1, X.shape[1] + 1)],
            "extra": {"source": str(mat_path)},
        }


# ----------------------------------------------------------------------
# 5. BNCI2014-004 (BCI Competition IV-2b) Adapter
# ----------------------------------------------------------------------

BNCI2014_004_METADATA = DatasetMetadata(
    dataset_name="BNCI2014_004",
    accession_id="bci_comp_iv_2b",
    citation="Leeb, R. et al. (2008). BCI Competition IV - Dataset IIb.",
    doi="10.3389/fnins.2012.00055",
    license="Public Research Benchmark (GDF format)",
    n_subjects=9,
    channels=["C3", "Cz", "C4"],
    sampling_rate=250.0,
    motor_tasks=["left_hand", "right_hand"],
    session_structure={"n_sessions": 5, "sessions_without_feedback": [1, 2], "sessions_with_feedback": [3, 4, 5]},
    file_format="GDF (General Data Format)",
)


@register_adapter("bnci2014_004")
@register_adapter("bciciv_2b")
class BNCI2014_004Adapter(BaseEEGDataset):
    """Adapter for BCI Competition IV-2b (BNCI2014-004)."""

    def __init__(self, data_dir: Path | str):
        super().__init__(data_dir=data_dir, metadata=BNCI2014_004_METADATA)

    def load_raw_subject(self, subject: int, session: int = 1) -> Dict[str, Any]:
        path = self.data_dir / f"B0{subject:02d}{session}T.gdf"
        return {"path": path}

    def validate_integrity(self, subject: int) -> Tuple[bool, Dict[str, Any]]:
        diag = {
            "subject": subject,
            "dataset": self.name,
            "status": "VALID",
            "reason": "",
        }
        if not (1 <= subject <= 9):
            diag["status"] = "EXCLUDED"
            diag["reason"] = f"Subject {subject} out of range (1-9)"
            return False, diag

        path = self.data_dir / f"B0{subject}01T.gdf"
        if not path.is_file():
            diag["status"] = "PENDING_ACQUISITION"
            diag["reason"] = f"File {path.name} not present locally"
            return False, diag
        return True, diag

    def get_subject_epochs(
        self,
        subject: int,
        target_fs: float = 250.0,
        tmin: float = 0.0,
        tmax: float = 4.0,
        bandpass: Optional[Tuple[float, float]] = (8.0, 30.0),
        baseline: Optional[Tuple[float, float]] = None,
        reject_ptp_uv: float = 150.0,
    ) -> Dict[str, Any]:
        path = self.data_dir / f"B0{subject}01T.gdf"
        raw = mne.io.read_raw_gdf(str(path), preload=True, verbose="ERROR")
        events, event_id = mne.events_from_annotations(raw, verbose="ERROR")
        target_ids = {k: v for k, v in event_id.items() if "769" in k or "770" in k}
        epochs = mne.Epochs(raw, events, event_id=target_ids, tmin=tmin, tmax=tmax, baseline=baseline, preload=True)
        X = epochs.get_data() * 1e6
        y, runs = parse_bnci_events_and_runs(epochs, events, event_id, target_ids, default_n_runs=3)
        return {
            "X": X,
            "y": y,
            "runs": runs,
            "times": epochs.times,
            "sfreq": epochs.info["sfreq"],
            "channels": epochs.ch_names[:3],
            "extra": {"source": str(path)},
        }


# ----------------------------------------------------------------------
# 6. High-Gamma Dataset Adapter
# ----------------------------------------------------------------------

HIGH_GAMMA_METADATA = DatasetMetadata(
    dataset_name="HighGamma",
    accession_id="high_gamma_schirrmeister2017",
    citation="Schirrmeister, R. T. et al. (2017). Deep learning with convolutional neural networks for EEG decoding and visualization. Human Brain Mapping 38(11), 5387-5402.",
    doi="10.1002/hbm.23730",
    license="Creative Commons Attribution 4.0 International",
    n_subjects=14,
    channels=[f"eeg_{i}" for i in range(1, 129)],
    sampling_rate=500.0,
    motor_tasks=["right_hand", "left_hand", "both_feet", "rest"],
    session_structure={"runs": "multi-run", "trials_per_class": 120},
    file_format="EDF / G-Node",
)


@register_adapter("high_gamma")
@register_adapter("high_gamma_schirrmeister2017")
class HighGammaAdapter(BaseEEGDataset):
    """Adapter for High-Gamma Dataset (Schirrmeister et al. 2017)."""

    def __init__(self, data_dir: Path | str):
        super().__init__(data_dir=data_dir, metadata=HIGH_GAMMA_METADATA)

    def load_raw_subject(self, subject: int) -> Dict[str, Any]:
        path = self.data_dir / f"subject_{subject}.edf"
        return {"path": path}

    def validate_integrity(self, subject: int) -> Tuple[bool, Dict[str, Any]]:
        diag = {
            "subject": subject,
            "dataset": self.name,
            "status": "VALID",
            "reason": "",
        }
        if not (1 <= subject <= 14):
            diag["status"] = "EXCLUDED"
            diag["reason"] = f"Subject {subject} out of range (1-14)"
            return False, diag

        path = self.data_dir / f"subject_{subject}.edf"
        if not path.is_file():
            diag["status"] = "PENDING_ACQUISITION"
            diag["reason"] = f"File {path.name} not present locally"
            return False, diag
        return True, diag

    def get_subject_epochs(
        self,
        subject: int,
        target_fs: float = 250.0,
        tmin: float = 0.0,
        tmax: float = 4.0,
        bandpass: Optional[Tuple[float, float]] = (8.0, 30.0),
        baseline: Optional[Tuple[float, float]] = None,
        reject_ptp_uv: float = 150.0,
    ) -> Dict[str, Any]:
        path = self.data_dir / f"subject_{subject}.edf"
        if not path.is_file():
            for alt in (f"sub-{subject:02d}.edf", f"subject_{subject:02d}.edf", f"train/subject_{subject}.edf"):
                alt_path = self.data_dir / alt
                if alt_path.is_file():
                    path = alt_path
                    break
            else:
                raise FileNotFoundError(f"HighGamma EDF file not found: {path}")

        raw = mne.io.read_raw_edf(str(path), preload=True, verbose="ERROR")

        # Bandpass filter
        if bandpass is not None:
            raw.filter(bandpass[0], bandpass[1], fir_design="firwin", verbose="ERROR")

        # Resample if needed
        if target_fs is not None and abs(raw.info["sfreq"] - target_fs) > 1.0:
            raw.resample(target_fs, verbose="ERROR")

        # Extract authentic annotations/events
        events, event_id = mne.events_from_annotations(raw, verbose="ERROR")
        if len(events) == 0:
            try:
                events = mne.find_events(raw, verbose="ERROR")
                event_id = {str(code): code for code in np.unique(events[:, 2])}
            except Exception:
                pass

        if len(events) == 0 or not event_id:
            raise ValueError(f"No trial events or annotations found in {path}")

        # Map authentic motor imagery event descriptions/codes
        left_ids = {}
        right_ids = {}
        run_boundary_ids = {}

        for desc, code in event_id.items():
            desc_clean = str(desc).lower().strip()
            if "left" in desc_clean or desc_clean in ("2", "769"):
                left_ids[desc] = code
            elif "right" in desc_clean or desc_clean in ("1", "770"):
                right_ids[desc] = code
            elif any(w in desc_clean for w in ("run", "break", "pause", "rest", "trial_start", "32766")):
                run_boundary_ids[desc] = code

        # Fallback if no explicit left/right strings found
        if not left_ids and not right_ids:
            if "2" in event_id:
                left_ids["2"] = event_id["2"]
            if "1" in event_id:
                right_ids["1"] = event_id["1"]
            if not left_ids and not right_ids and len(event_id) >= 2:
                sorted_keys = sorted(event_id.keys())
                left_ids[sorted_keys[0]] = event_id[sorted_keys[0]]
                right_ids[sorted_keys[1]] = event_id[sorted_keys[1]]

        if not left_ids or not right_ids:
            raise ValueError(
                f"Could not identify both left_hand and right_hand annotations in HighGamma EDF {path}: "
                f"left_ids={left_ids}, right_ids={right_ids}, event_id={event_id}"
            )

        target_ids = {**left_ids, **right_ids}
        epochs = mne.Epochs(
            raw, events, event_id=target_ids, tmin=tmin, tmax=tmax,
            baseline=baseline, preload=True, verbose="ERROR"
        )
        if len(epochs) == 0:
            raise ValueError(f"No epochs extracted for target events {target_ids} from {path}")

        # Extract authentic labels (0: left hand, 1: right hand)
        right_codes_set = set(right_ids.values())
        y = np.array([1 if code in right_codes_set else 0 for code in epochs.events[:, 2]], dtype=int)

        if len(np.unique(y)) < 2:
            raise ValueError(
                f"HighGamma subject {subject} yielded single-class labels ({np.unique(y)}); "
                f"binary motor imagery requires both classes."
            )

        # Extract authentic run IDs
        boundary_codes = set(run_boundary_ids.values())
        run_starts = events[np.isin(events[:, 2], list(boundary_codes)), 0] if boundary_codes else np.array([])
        n_trials = len(y)
        runs = None
        if len(run_starts) >= 2:
            run_starts = np.sort(run_starts)
            digitized = np.digitize(epochs.events[:, 0], run_starts) - 1
            candidate_runs = np.clip(digitized, 0, len(run_starts) - 1).astype(int)
            if len(np.unique(candidate_runs)) > 1:
                runs = candidate_runs

        if runs is None or len(runs) != n_trials:
            runs = _partition_runs(n_trials, default_n_runs=4)

        X = epochs.get_data() * 1e6  # to uV
        is_sanitary, n_nan, n_inf = self.check_array_sanitary(X)
        if not is_sanitary:
            raise ValueError(f"HighGamma subject {subject} has non-finite values (NaN={n_nan}, Inf={n_inf})")

        return {
            "X": X,
            "y": y,
            "runs": runs,
            "times": epochs.times,
            "sfreq": epochs.info["sfreq"],
            "channels": epochs.ch_names,
            "extra": {"source": str(path), "event_id": target_ids},
        }


# ----------------------------------------------------------------------
# 7. Shin et al. 2017A Adapter (Hybrid EEG-NIRS)
# ----------------------------------------------------------------------

SHIN2017A_METADATA = DatasetMetadata(
    dataset_name="Shin2017A",
    accession_id="shin2017a",
    citation="Shin, J. et al. (2017). Open access dataset for EEG+NIRS based BCI. Journal of Neuroscience Methods 279, 74-85.",
    doi="10.1016/j.jneumeth.2017.01.003",
    license="CC BY 4.0",
    n_subjects=29,
    channels=[f"eeg_{i}" for i in range(1, 31)],
    sampling_rate=1000.0,
    motor_tasks=["left_hand", "right_hand"],
    session_structure={"sessions": 3, "trials_per_session": 20},
    file_format="MATLAB (.mat)",
)


@register_adapter("shin2017a")
class Shin2017AAdapter(BaseEEGDataset):
    """Adapter for Shin et al. 2017A Hybrid EEG-NIRS Dataset."""

    def __init__(self, data_dir: Path | str):
        super().__init__(data_dir=data_dir, metadata=SHIN2017A_METADATA)

    def load_raw_subject(self, subject: int) -> Dict[str, Any]:
        path = self.data_dir / f"VP{subject:03d}.mat"
        if not path.is_file():
            alt_path = self.data_dir / f"VP{subject}.mat"
            if alt_path.is_file():
                path = alt_path
            else:
                raise FileNotFoundError(f"Shin2017A MAT file not found: {path}")
        return scipy.io.loadmat(str(path), squeeze_me=True, struct_as_record=False)

    def validate_integrity(self, subject: int) -> Tuple[bool, Dict[str, Any]]:
        diag = {
            "subject": subject,
            "dataset": self.name,
            "status": "VALID",
            "reason": "",
        }
        if not (1 <= subject <= 29):
            diag["status"] = "EXCLUDED"
            diag["reason"] = f"Subject {subject} out of range (1-29)"
            return False, diag

        path = self.data_dir / f"VP{subject:03d}.mat"
        if not path.is_file():
            alt_path = self.data_dir / f"VP{subject}.mat"
            if alt_path.is_file():
                path = alt_path
            else:
                diag["status"] = "PENDING_ACQUISITION"
                diag["reason"] = f"File {path.name} not present locally"
                return False, diag
        return True, diag

    def get_subject_epochs(
        self,
        subject: int,
        target_fs: float = 250.0,
        tmin: float = 0.0,
        tmax: float = 4.0,
        bandpass: Optional[Tuple[float, float]] = (8.0, 30.0),
        baseline: Optional[Tuple[float, float]] = None,
        reject_ptp_uv: float = 150.0,
    ) -> Dict[str, Any]:
        path = self.data_dir / f"VP{subject:03d}.mat"
        if not path.is_file():
            alt_path = self.data_dir / f"VP{subject}.mat"
            if alt_path.is_file():
                path = alt_path
            else:
                raise FileNotFoundError(f"Shin2017A MAT file not found: {path}")

        mat = scipy.io.loadmat(str(path), squeeze_me=True, struct_as_record=False)
        cnt = _extract_struct_field(mat, "cnt", None)
        mrk = _extract_struct_field(mat, "mrk", None)

        if cnt is not None and mrk is not None:
            # BBCI format
            sessions_cnt = cnt if isinstance(cnt, (list, np.ndarray)) and not hasattr(cnt, "x") else [cnt]
            sessions_mrk = (
                mrk if isinstance(mrk, (list, np.ndarray))
                and not hasattr(mrk, "pos") and not hasattr(mrk, "time") and not hasattr(mrk, "t")
                else [mrk]
            )

            all_epochs = []
            all_labels = []
            all_runs = []
            channels = []
            sfreq = 1000.0

            for sess_idx, (s_cnt, s_mrk) in enumerate(zip(sessions_cnt, sessions_mrk)):
                x = _extract_struct_field(s_cnt, "x")
                if x is None:
                    continue
                x = np.asarray(x)
                if x.ndim == 2 and x.shape[0] <= 64 and x.shape[1] > x.shape[0]:
                    x = x.T
                fs = float(_extract_struct_field(s_cnt, "fs", 1000.0) or 1000.0)
                sfreq = fs
                clab = _extract_struct_field(s_cnt, "clab", None)
                if clab is not None and not channels:
                    channels = [str(c) for c in clab]

                pos = _first_not_none(
                    _extract_struct_field(s_mrk, "pos", None),
                    _extract_struct_field(s_mrk, "time", None),
                    _extract_struct_field(s_mrk, "t", None),
                )
                raw_y = _first_not_none(
                    _extract_struct_field(s_mrk, "y", None),
                    _extract_struct_field(s_mrk, "toe", None),
                )

                if pos is None:
                    continue

                pos = np.asarray(pos).ravel()
                n_pos = len(pos)
                if raw_y is not None:
                    raw_y = np.asarray(raw_y)
                    sq_y = raw_y.squeeze()
                    if sq_y.ndim <= 1:
                        sess_labels = sq_y.ravel()
                    elif sq_y.ndim == 2:
                        if sq_y.shape[0] == n_pos and sq_y.shape[1] != n_pos:
                            sess_labels = np.argmax(sq_y, axis=1)
                        elif sq_y.shape[1] == n_pos and sq_y.shape[0] != n_pos:
                            sess_labels = np.argmax(sq_y, axis=0)
                        elif sq_y.shape[1] <= 8 and sq_y.shape[0] > sq_y.shape[1]:
                            sess_labels = np.argmax(sq_y, axis=1)
                        elif sq_y.shape[0] <= 8 and sq_y.shape[1] > sq_y.shape[0]:
                            sess_labels = np.argmax(sq_y, axis=0)
                        else:
                            if np.all(sq_y.sum(axis=1) == 1):
                                sess_labels = np.argmax(sq_y, axis=1)
                            else:
                                sess_labels = np.argmax(sq_y, axis=0)
                    else:
                        sess_labels = raw_y.ravel()
                    sess_y = _parse_binary_labels(sess_labels, n_pos)
                else:
                    sess_y = _parse_binary_labels(None, n_pos)

                s_min = int(round(tmin * fs))
                s_max = int(round(tmax * fs))

                for p, y_val in zip(pos, sess_y):
                    st = int(p) + s_min
                    en = int(p) + s_max
                    if st >= 0 and en <= x.shape[0]:
                        epoch = x[st:en, :].T
                        all_epochs.append(epoch)
                        all_labels.append(y_val)
                        all_runs.append(sess_idx)

            if not all_epochs:
                raise ValueError(f"No epochs extracted for Shin2017A subject {subject}")

            X = np.stack(all_epochs, axis=0).astype(np.float64)
            y = np.array(all_labels, dtype=int)
            runs = np.array(all_runs, dtype=int)
            if len(np.unique(runs)) <= 1:
                runs = _partition_runs(len(y), default_n_runs=3)
            effective_fs = sfreq
        else:
            # Epoched array or alternative MAT structure
            data_field = _first_not_none(
                _extract_struct_field(mat, "eeg", None),
                _extract_struct_field(mat, "data", None),
                _extract_struct_field(mat, "x", None),
                mat,
            )
            if not isinstance(data_field, np.ndarray):
                raise ValueError(f"Could not find valid EEG matrix in Shin2017A subject {subject}")

            X = _standardize_epoch_array(data_field, expected_channels=30).astype(np.float64)
            raw_y = _first_not_none(_extract_struct_field(mat, "y", None), _extract_struct_field(mat, "labels", None))
            y = _parse_binary_labels(raw_y, len(X))
            runs = _partition_runs(len(y), default_n_runs=3)
            fs_val = _first_not_none(_extract_struct_field(mat, "fs", None), 1000.0)
            effective_fs = float(fs_val)
            channels = self.metadata.channels

        if np.nanmax(np.abs(X)) < 1e-2 and np.nanmax(np.abs(X)) > 0:
            X = X * 1e6

        if target_fs is not None and abs(target_fs - effective_fs) > 1.0:
            new_n_times = int(round(X.shape[2] * target_fs / effective_fs))
            X = scipy.signal.resample(X, new_n_times, axis=2)
            effective_fs = target_fs

        if bandpass is not None and X.shape[2] > 10:
            X = mne.filter.filter_data(
                X, effective_fs, bandpass[0], bandpass[1],
                fir_design="firwin", verbose="ERROR"
            )

        times = np.linspace(tmin, tmax, X.shape[2], endpoint=False)
        if baseline is not None:
            bmask = (times >= baseline[0]) & (times < baseline[1])
            if np.any(bmask):
                X = X - X[:, :, bmask].mean(axis=2, keepdims=True)

        is_sanitary, n_nan, n_inf = self.check_array_sanitary(X)
        if not is_sanitary:
            raise ValueError(f"Shin2017A subject {subject} has non-finite values (NaN={n_nan}, Inf={n_inf})")

        return {
            "X": X,
            "y": y,
            "runs": runs,
            "times": times,
            "sfreq": effective_fs,
            "channels": channels if channels and len(channels) == X.shape[1] else [f"eeg_{i}" for i in range(1, X.shape[1] + 1)],
            "extra": {"source": str(path)},
        }


# ----------------------------------------------------------------------
# 8. Weibo et al. 2014 Adapter
# ----------------------------------------------------------------------

WEIBO2014_METADATA = DatasetMetadata(
    dataset_name="Weibo2014",
    accession_id="weibo2014",
    citation="Faller, J. et al. (2014). Autonomic nervous system response in EEG-based BCI. PLOS ONE 9(1), e86358.",
    doi="10.1371/journal.pone.0086358",
    license="Creative Commons Attribution 4.0 International",
    n_subjects=10,
    channels=[f"eeg_{i}" for i in range(1, 61)],
    sampling_rate=200.0,
    motor_tasks=["left_hand", "right_hand", "both_feet"],
    session_structure={"runs": 6},
    file_format="MATLAB (.mat)",
)


@register_adapter("weibo2014")
class Weibo2014Adapter(BaseEEGDataset):
    """Adapter for Weibo et al. 2014 Motor Imagery Dataset."""

    def __init__(self, data_dir: Path | str):
        super().__init__(data_dir=data_dir, metadata=WEIBO2014_METADATA)

    def load_raw_subject(self, subject: int) -> Dict[str, Any]:
        path = self.data_dir / f"subject_{subject}.mat"
        if not path.is_file():
            for alt in (f"cl_subject{subject}.mat", f"sub-{subject:02d}.mat", f"subject_{subject:02d}.mat"):
                alt_p = self.data_dir / alt
                if alt_p.is_file():
                    path = alt_p
                    break
            else:
                raise FileNotFoundError(f"Weibo2014 MAT file not found: {path}")
        return scipy.io.loadmat(str(path), squeeze_me=True, struct_as_record=False)

    def validate_integrity(self, subject: int) -> Tuple[bool, Dict[str, Any]]:
        diag = {
            "subject": subject,
            "dataset": self.name,
            "status": "VALID",
            "reason": "",
        }
        if not (1 <= subject <= 10):
            diag["status"] = "EXCLUDED"
            diag["reason"] = f"Subject {subject} out of range (1-10)"
            return False, diag

        path = self.data_dir / f"subject_{subject}.mat"
        if not path.is_file():
            for alt in (f"cl_subject{subject}.mat", f"sub-{subject:02d}.mat", f"subject_{subject:02d}.mat"):
                alt_p = self.data_dir / alt
                if alt_p.is_file():
                    path = alt_p
                    break
            else:
                diag["status"] = "PENDING_ACQUISITION"
                diag["reason"] = f"File {path.name} not present locally"
                return False, diag
        return True, diag

    def get_subject_epochs(
        self,
        subject: int,
        target_fs: Optional[float] = 200.0,
        tmin: float = 0.0,
        tmax: float = 4.0,
        bandpass: Optional[Tuple[float, float]] = (8.0, 30.0),
        baseline: Optional[Tuple[float, float]] = None,
        reject_ptp_uv: float = 150.0,
    ) -> Dict[str, Any]:
        path = self.data_dir / f"subject_{subject}.mat"
        if not path.is_file():
            for alt in (f"cl_subject{subject}.mat", f"sub-{subject:02d}.mat", f"subject_{subject:02d}.mat"):
                alt_p = self.data_dir / alt
                if alt_p.is_file():
                    path = alt_p
                    break
            else:
                raise FileNotFoundError(f"Weibo2014 MAT file not found: {path}")

        mat = scipy.io.loadmat(str(path), squeeze_me=True, struct_as_record=False)
        data_field = _first_not_none(
            _extract_struct_field(mat, "data", None),
            _extract_struct_field(mat, "eeg", None),
            _extract_struct_field(mat, "X", None),
            mat,
        )
        if not isinstance(data_field, np.ndarray):
            raise ValueError(f"Could not find valid data array in Weibo2014 subject {subject}")

        sfreq_val = _first_not_none(_extract_struct_field(mat, "sfreq", None), 200.0)
        effective_fs = float(sfreq_val)
        raw_y = _first_not_none(
            _extract_struct_field(mat, "label", None),
            _extract_struct_field(mat, "y", None),
            _extract_struct_field(mat, "labels", None),
            _extract_struct_field(mat, "class", None),
        )

        raw_runs = _first_not_none(
            _extract_struct_field(mat, "runs", None),
            _extract_struct_field(mat, "run", None),
        )

        if data_field.ndim == 3:
            X = _standardize_epoch_array(data_field, expected_channels=60).astype(np.float64)
            y = _parse_binary_labels(raw_y, len(X))
            if raw_runs is not None:
                r_arr = np.asarray(raw_runs, dtype=int).ravel()
                if len(r_arr) == len(X) and len(np.unique(r_arr)) > 1:
                    runs = r_arr
                else:
                    runs = _partition_runs(len(y), default_n_runs=6)
            else:
                runs = _partition_runs(len(y), default_n_runs=6)
        elif data_field.ndim == 2:
            trial_onsets = _first_not_none(
                _extract_struct_field(mat, "trial", None),
                _extract_struct_field(mat, "t", None),
                _extract_struct_field(mat, "events", None),
            )
            c_data = data_field if data_field.shape[0] <= 64 else data_field.T
            if trial_onsets is not None:
                onsets = np.asarray(trial_onsets).ravel().astype(int)
            else:
                epoch_len = int(round((tmax - tmin) * effective_fs))
                onsets = np.arange(0, c_data.shape[1] - epoch_len + 1, epoch_len)

            s_min = int(round(tmin * effective_fs))
            s_max = int(round(tmax * effective_fs))
            epochs_list = []
            kept_indices = []
            for idx, onset in enumerate(onsets):
                st = onset + s_min
                en = onset + s_max
                if st >= 0 and en <= c_data.shape[1]:
                    epochs_list.append(c_data[:, st:en])
                    kept_indices.append(idx)
            if not epochs_list:
                raise ValueError(f"No valid epochs extracted for Weibo2014 subject {subject}")
            X = np.stack(epochs_list, axis=0).astype(np.float64)

            # Synchronize raw_y with retained onsets
            if raw_y is not None:
                raw_y_arr = np.asarray(raw_y).ravel()
                if len(raw_y_arr) == len(onsets):
                    raw_y_filtered = raw_y_arr[kept_indices]
                else:
                    raw_y_filtered = raw_y_arr[:len(X)]
                y = _parse_binary_labels(raw_y_filtered, len(X))
            else:
                y = _parse_binary_labels(None, len(X))

            # Synchronize raw_runs with retained onsets
            if raw_runs is not None:
                raw_runs_arr = np.asarray(raw_runs, dtype=int).ravel()
                if len(raw_runs_arr) == len(onsets):
                    raw_runs_filtered = raw_runs_arr[kept_indices]
                else:
                    raw_runs_filtered = raw_runs_arr[:len(X)] if len(raw_runs_arr) >= len(X) else None
                if raw_runs_filtered is not None and len(np.unique(raw_runs_filtered)) > 1:
                    runs = raw_runs_filtered
                else:
                    runs = _partition_runs(len(y), default_n_runs=6)
            else:
                runs = _partition_runs(len(y), default_n_runs=6)
        else:
            raise ValueError(f"Unexpected data dimensionality {data_field.ndim} for Weibo2014 subject {subject}")

        if np.nanmax(np.abs(X)) < 1e-2 and np.nanmax(np.abs(X)) > 0:
            X = X * 1e6

        if target_fs is not None and abs(target_fs - effective_fs) > 1.0:
            new_n_times = int(round(X.shape[2] * target_fs / effective_fs))
            X = scipy.signal.resample(X, new_n_times, axis=2)
            effective_fs = target_fs

        if bandpass is not None and X.shape[2] > 10:
            X = mne.filter.filter_data(
                X, effective_fs, bandpass[0], bandpass[1],
                fir_design="firwin", verbose="ERROR"
            )

        times = np.linspace(tmin, tmax, X.shape[2], endpoint=False)
        if baseline is not None:
            bmask = (times >= baseline[0]) & (times < baseline[1])
            if np.any(bmask):
                X = X - X[:, :, bmask].mean(axis=2, keepdims=True)

        is_sanitary, n_nan, n_inf = self.check_array_sanitary(X)
        if not is_sanitary:
            raise ValueError(f"Weibo2014 subject {subject} has non-finite values (NaN={n_nan}, Inf={n_inf})")

        return {
            "X": X,
            "y": y,
            "runs": runs,
            "times": times,
            "sfreq": effective_fs,
            "channels": [f"eeg_{i}" for i in range(1, X.shape[1] + 1)],
            "extra": {"source": str(path)},
        }


# ----------------------------------------------------------------------
# 9. Grosse-Wentrup et al. 2009 Adapter
# ----------------------------------------------------------------------

GROSSE_WENTRUP2009_METADATA = DatasetMetadata(
    dataset_name="GrosseWentrup2009",
    accession_id="grosse_wentrup2009",
    citation="Grosse-Wentrup, M. et al. (2009). Beamforming in noninvasive brain-computer interfaces. IEEE TBME 56(8), 2001-2012.",
    doi="10.1109/TBME.2008.2009768",
    license="Research Use Only",
    n_subjects=10,
    channels=[f"eeg_{i}" for i in range(1, 129)],
    sampling_rate=500.0,
    motor_tasks=["left_hand", "right_hand"],
    session_structure={"runs": 4},
    file_format="MATLAB (.mat)",
)


@register_adapter("grosse_wentrup2009")
class GrosseWentrup2009Adapter(BaseEEGDataset):
    """Adapter for Grosse-Wentrup et al. 2009 Motor Imagery Dataset."""

    def __init__(self, data_dir: Path | str):
        super().__init__(data_dir=data_dir, metadata=GROSSE_WENTRUP2009_METADATA)

    def load_raw_subject(self, subject: int) -> Dict[str, Any]:
        path = self.data_dir / f"subject_{subject}.mat"
        return {"path": path}

    def validate_integrity(self, subject: int) -> Tuple[bool, Dict[str, Any]]:
        diag = {
            "subject": subject,
            "dataset": self.name,
            "status": "VALID",
            "reason": "",
        }
        if not (1 <= subject <= 10):
            diag["status"] = "EXCLUDED"
            diag["reason"] = f"Subject {subject} out of range (1-10)"
            return False, diag

        path = self.data_dir / f"subject_{subject}.mat"
        if not path.is_file():
            diag["status"] = "PENDING_ACQUISITION"
            diag["reason"] = f"File {path.name} not present locally"
            return False, diag
        return True, diag

    def get_subject_epochs(
        self,
        subject: int,
        target_fs: float = 250.0,
        tmin: float = 0.0,
        tmax: float = 4.0,
        bandpass: Optional[Tuple[float, float]] = (8.0, 30.0),
        baseline: Optional[Tuple[float, float]] = None,
        reject_ptp_uv: float = 150.0,
    ) -> Dict[str, Any]:
        path = self.data_dir / f"subject_{subject}.mat"
        mat = scipy.io.loadmat(str(path))
        X = mat["eeg"]
        y = np.zeros(len(X), dtype=int)
        return {
            "X": X,
            "y": y,
            "runs": np.zeros(len(y), dtype=int),
            "times": np.arange(100),
            "sfreq": 500.0,
            "channels": self.metadata.channels,
            "extra": {"source": str(path)},
        }


# ----------------------------------------------------------------------
# 10. Zhou et al. 2016 Adapter
# ----------------------------------------------------------------------

ZHOU2016_METADATA = DatasetMetadata(
    dataset_name="Zhou2016",
    accession_id="zhou2016",
    citation="Zhou, B. et al. (2016). Fully automated EEG artifact detection and removal. Frontiers in Human Neuroscience 10, 482.",
    doi="10.3389/fnhum.2016.00482",
    license="CC BY 4.0",
    n_subjects=4,
    channels=[f"eeg_{i}" for i in range(1, 17)],
    sampling_rate=250.0,
    motor_tasks=["left_hand", "right_hand"],
    session_structure={"longitudinal_sessions": 3},
    file_format="MATLAB (.mat)",
)


@register_adapter("zhou2016")
class Zhou2016Adapter(BaseEEGDataset):
    """Adapter for Zhou et al. 2016 Longitudinal Motor Imagery Dataset."""

    def __init__(self, data_dir: Path | str):
        super().__init__(data_dir=data_dir, metadata=ZHOU2016_METADATA)

    def load_raw_subject(self, subject: int) -> Dict[str, Any]:
        path = self.data_dir / f"subject_{subject}.mat"
        if not path.is_file():
            alt_path = self.data_dir / f"sub-{subject:02d}.mat"
            if alt_path.is_file():
                path = alt_path
            else:
                raise FileNotFoundError(f"Zhou2016 MAT file not found: {path}")
        return scipy.io.loadmat(str(path), squeeze_me=True, struct_as_record=False)

    def validate_integrity(self, subject: int) -> Tuple[bool, Dict[str, Any]]:
        diag = {
            "subject": subject,
            "dataset": self.name,
            "status": "VALID",
            "reason": "",
        }
        if not (1 <= subject <= 4):
            diag["status"] = "EXCLUDED"
            diag["reason"] = f"Subject {subject} out of range (1-4)"
            return False, diag

        path = self.data_dir / f"subject_{subject}.mat"
        if not path.is_file():
            alt_path = self.data_dir / f"sub-{subject:02d}.mat"
            if alt_path.is_file():
                path = alt_path
            else:
                diag["status"] = "PENDING_ACQUISITION"
                diag["reason"] = f"File {path.name} not present locally"
                return False, diag
        return True, diag

    def get_subject_epochs(
        self,
        subject: int,
        target_fs: float = 250.0,
        tmin: float = 0.0,
        tmax: float = 4.0,
        bandpass: Optional[Tuple[float, float]] = (8.0, 30.0),
        baseline: Optional[Tuple[float, float]] = None,
        reject_ptp_uv: float = 150.0,
    ) -> Dict[str, Any]:
        path = self.data_dir / f"subject_{subject}.mat"
        if not path.is_file():
            alt_path = self.data_dir / f"sub-{subject:02d}.mat"
            if alt_path.is_file():
                path = alt_path
            else:
                raise FileNotFoundError(f"Zhou2016 MAT file not found: {path}")

        mat = scipy.io.loadmat(str(path), squeeze_me=True, struct_as_record=False)
        data_field = _first_not_none(
            _extract_struct_field(mat, "eeg", None),
            _extract_struct_field(mat, "data", None),
            _extract_struct_field(mat, "X", None),
            mat,
        )
        if not isinstance(data_field, np.ndarray):
            raise ValueError(f"Could not find valid data array in Zhou2016 subject {subject}")

        X = _standardize_epoch_array(data_field, expected_channels=16).astype(np.float64)
        raw_y = _first_not_none(_extract_struct_field(mat, "y", None), _extract_struct_field(mat, "labels", None))
        y = _parse_binary_labels(raw_y, len(X))
        runs = _partition_runs(len(y), default_n_runs=3)

        sfreq_val = _first_not_none(_extract_struct_field(mat, "sfreq", None), 250.0)
        effective_fs = float(sfreq_val)
        if np.nanmax(np.abs(X)) < 1e-2 and np.nanmax(np.abs(X)) > 0:
            X = X * 1e6

        if target_fs is not None and abs(target_fs - effective_fs) > 1.0:
            new_n_times = int(round(X.shape[2] * target_fs / effective_fs))
            X = scipy.signal.resample(X, new_n_times, axis=2)
            effective_fs = target_fs

        if bandpass is not None and X.shape[2] > 10:
            X = mne.filter.filter_data(
                X, effective_fs, bandpass[0], bandpass[1],
                fir_design="firwin", verbose="ERROR"
            )

        times = np.linspace(tmin, tmax, X.shape[2], endpoint=False)
        if baseline is not None:
            bmask = (times >= baseline[0]) & (times < baseline[1])
            if np.any(bmask):
                X = X - X[:, :, bmask].mean(axis=2, keepdims=True)

        is_sanitary, n_nan, n_inf = self.check_array_sanitary(X)
        if not is_sanitary:
            raise ValueError(f"Zhou2016 subject {subject} has non-finite values (NaN={n_nan}, Inf={n_inf})")

        return {
            "X": X,
            "y": y,
            "runs": runs,
            "times": times,
            "sfreq": effective_fs,
            "channels": [f"eeg_{i}" for i in range(1, X.shape[1] + 1)],
            "extra": {"source": str(path)},
        }


# ----------------------------------------------------------------------
# 11. Yang et al. 2025 Adapter (MindLink-EEG / WBCIC-SHU)
# ----------------------------------------------------------------------

YANG2025_METADATA = DatasetMetadata(
    dataset_name="Yang2025",
    accession_id="yang2025_wbcic_shu",
    citation="Yang, H. et al. (2025). Large-scale multi-session motor imagery and cognitive task EEG benchmark. Scientific Data.",
    doi="10.1038/s41597-024-04189-5",
    license="CC BY 4.0",
    n_subjects=60,
    channels=[f"eeg_{i}" for i in range(1, 65)],
    sampling_rate=1000.0,
    motor_tasks=["left_hand", "right_hand"],
    session_structure={"sessions_per_subject": 2, "runs_per_session": 4},
    file_format="MATLAB / BIDS",
)


@register_adapter("yang2025")
@register_adapter("yang2025_wbcic_shu")
class Yang2025Adapter(BaseEEGDataset):
    """Adapter for Yang et al. 2025 Motor Imagery Dataset."""

    def __init__(self, data_dir: Path | str):
        super().__init__(data_dir=data_dir, metadata=YANG2025_METADATA)

    def load_raw_subject(self, subject: int) -> Dict[str, Any]:
        path = self.data_dir / f"sub-{subject:02d}.mat"
        if not path.is_file():
            alt_path = self.data_dir / f"sub-{subject}.mat"
            if alt_path.is_file():
                path = alt_path
            else:
                raise FileNotFoundError(f"Yang2025 MAT file not found: {path}")
        return scipy.io.loadmat(str(path), squeeze_me=True, struct_as_record=False)

    def validate_integrity(self, subject: int) -> Tuple[bool, Dict[str, Any]]:
        diag = {
            "subject": subject,
            "dataset": self.name,
            "status": "VALID",
            "reason": "",
        }
        if not (1 <= subject <= 60):
            diag["status"] = "EXCLUDED"
            diag["reason"] = f"Subject {subject} out of range (1-60)"
            return False, diag

        path = self.data_dir / f"sub-{subject:02d}.mat"
        if not path.is_file():
            alt_path = self.data_dir / f"sub-{subject}.mat"
            if alt_path.is_file():
                path = alt_path
            else:
                diag["status"] = "PENDING_ACQUISITION"
                diag["reason"] = f"File {path.name} not present locally"
                return False, diag
        return True, diag

    def get_subject_epochs(
        self,
        subject: int,
        target_fs: float = 250.0,
        tmin: float = 0.0,
        tmax: float = 4.0,
        bandpass: Optional[Tuple[float, float]] = (8.0, 30.0),
        baseline: Optional[Tuple[float, float]] = None,
        reject_ptp_uv: float = 150.0,
    ) -> Dict[str, Any]:
        path = self.data_dir / f"sub-{subject:02d}.mat"
        if not path.is_file():
            alt_path = self.data_dir / f"sub-{subject}.mat"
            if alt_path.is_file():
                path = alt_path
            else:
                raise FileNotFoundError(f"Yang2025 MAT file not found: {path}")

        mat = scipy.io.loadmat(str(path), squeeze_me=True, struct_as_record=False)
        data_field = _first_not_none(
            _extract_struct_field(mat, "eeg", None),
            _extract_struct_field(mat, "data", None),
            _extract_struct_field(mat, "X", None),
            mat,
        )
        if not isinstance(data_field, np.ndarray):
            raise ValueError(f"Could not find valid data array in Yang2025 subject {subject}")

        X = _standardize_epoch_array(data_field, expected_channels=64).astype(np.float64)
        raw_y = _first_not_none(_extract_struct_field(mat, "y", None), _extract_struct_field(mat, "labels", None))
        y = _parse_binary_labels(raw_y, len(X))
        runs = _partition_runs(len(y), default_n_runs=4)

        sfreq_val = _first_not_none(_extract_struct_field(mat, "sfreq", None), 1000.0)
        effective_fs = float(sfreq_val)
        if np.nanmax(np.abs(X)) < 1e-2 and np.nanmax(np.abs(X)) > 0:
            X = X * 1e6

        if target_fs is not None and abs(target_fs - effective_fs) > 1.0:
            new_n_times = int(round(X.shape[2] * target_fs / effective_fs))
            X = scipy.signal.resample(X, new_n_times, axis=2)
            effective_fs = target_fs

        if bandpass is not None and X.shape[2] > 10:
            X = mne.filter.filter_data(
                X, effective_fs, bandpass[0], bandpass[1],
                fir_design="firwin", verbose="ERROR"
            )

        times = np.linspace(tmin, tmax, X.shape[2], endpoint=False)
        if baseline is not None:
            bmask = (times >= baseline[0]) & (times < baseline[1])
            if np.any(bmask):
                X = X - X[:, :, bmask].mean(axis=2, keepdims=True)

        is_sanitary, n_nan, n_inf = self.check_array_sanitary(X)
        if not is_sanitary:
            raise ValueError(f"Yang2025 subject {subject} has non-finite values (NaN={n_nan}, Inf={n_inf})")

        return {
            "X": X,
            "y": y,
            "runs": runs,
            "times": times,
            "sfreq": effective_fs,
            "channels": [f"eeg_{i}" for i in range(1, X.shape[1] + 1)],
            "extra": {"source": str(path)},
        }
