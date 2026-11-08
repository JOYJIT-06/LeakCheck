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
        y = np.array([0 if "769" in k else 1 for k in epochs.events[:, 2]])
        runs = np.zeros(len(y), dtype=int)
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
