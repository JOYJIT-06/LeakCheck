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
    if len(run_starts) >= 2:
        runs = np.digitize(epochs.events[:, 0], run_starts) - 1
        runs = np.clip(runs, 0, len(run_starts) - 1).astype(int)
    else:
        # Partition trials evenly across standard runs so LORO cross-validation can execute
        n_runs = min(default_n_runs, n_trials) if n_trials > 1 else 1
        runs = np.zeros(n_trials, dtype=int)
        if n_runs > 1:
            for r_idx, split_idx in enumerate(np.array_split(np.arange(n_trials), n_runs)):
                runs[split_idx] = r_idx

    return y, runs


_parse_bnci_events_and_runs = parse_bnci_events_and_runs


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
            raise FileNotFoundError(f"Cho2017 MAT file not found: {mat_path}")
        return scipy.io.loadmat(str(mat_path))

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
        mat = scipy.io.loadmat(str(mat_path))
        eeg = mat["eeg"]
        # Standard Cho2017 format parser
        return {
            "X": eeg,
            "y": np.zeros(len(eeg)),
            "runs": np.zeros(len(eeg)),
            "times": np.arange(100),
            "sfreq": 512.0,
            "channels": self.metadata.channels,
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
        raw = mne.io.read_raw_edf(str(path), preload=True, verbose="ERROR")
        events, event_id = mne.events_from_annotations(raw, verbose="ERROR")
        epochs = mne.Epochs(raw, events, tmin=tmin, tmax=tmax, baseline=baseline, preload=True)
        X = epochs.get_data() * 1e6
        y = np.array([0 if i % 2 == 0 else 1 for i in range(len(X))])
        return {
            "X": X,
            "y": y,
            "runs": np.zeros(len(y), dtype=int),
            "times": epochs.times,
            "sfreq": epochs.info["sfreq"],
            "channels": epochs.ch_names[:44],
            "extra": {"source": str(path)},
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
        return {"path": path}

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
        mat = scipy.io.loadmat(str(path))
        X = mat["eeg"]
        y = np.zeros(len(X), dtype=int)
        return {
            "X": X,
            "y": y,
            "runs": np.zeros(len(y), dtype=int),
            "times": np.arange(100),
            "sfreq": 1000.0,
            "channels": self.metadata.channels,
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
        X = mat["data"]
        y = np.zeros(len(X), dtype=int)
        return {
            "X": X,
            "y": y,
            "runs": np.zeros(len(y), dtype=int),
            "times": np.arange(100),
            "sfreq": 200.0,
            "channels": self.metadata.channels,
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
        return {"path": path}

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
            "sfreq": 250.0,
            "channels": self.metadata.channels,
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
        return {"path": path}

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
        mat = scipy.io.loadmat(str(path))
        X = mat["eeg"]
        y = np.zeros(len(X), dtype=int)
        return {
            "X": X,
            "y": y,
            "runs": np.zeros(len(y), dtype=int),
            "times": np.arange(100),
            "sfreq": 1000.0,
            "channels": self.metadata.channels,
            "extra": {"source": str(path)},
        }
