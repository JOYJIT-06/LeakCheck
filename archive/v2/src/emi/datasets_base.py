"""Standardized Multi-Dataset Base Architecture for LeakCheck V2.

Provides:
  - DatasetMetadata: Dataclass capturing provenance, citation, licensing, montage, and structure.
  - BaseEEGDataset: Abstract base class enforcing uniform preprocessing, trial epoching,
    run/session isolation, and integrity validation across EEG motor imagery benchmarks.
  - Adapter registry for pluggable multi-dataset execution.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
import hashlib
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

import mne
import numpy as np
import pandas as pd


@dataclass
class DatasetMetadata:
    """Standardized metadata record for an EEG benchmark dataset."""
    dataset_name: str
    accession_id: str
    citation: str
    doi: str
    license: str
    n_subjects: int
    channels: List[str]
    sampling_rate: float
    motor_tasks: List[str]
    session_structure: Dict[str, Any]
    file_format: str
    checksum_manifest: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    @property
    def channel_count(self) -> int:
        return len(self.channels)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to a serializable dictionary."""
        d = asdict(self)
        d["channel_count"] = self.channel_count
        return d


class BaseEEGDataset(ABC):
    """Abstract base class for all LeakCheck V2 EEG dataset adapters."""

    def __init__(self, data_dir: Path | str, metadata: DatasetMetadata):
        self.data_dir = Path(data_dir)
        self.metadata = metadata

    @property
    def name(self) -> str:
        return self.metadata.dataset_name

    @abstractmethod
    def load_raw_subject(self, subject: int) -> Any:
        """Load continuous raw recordings for one subject."""
        pass

    @abstractmethod
    def validate_integrity(self, subject: int) -> Tuple[bool, Dict[str, Any]]:
        """Validate integrity, channel count, sampling rate, and non-corruption.

        Returns (is_valid, diagnostics_dict).
        """
        pass

    @abstractmethod
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
        """Load and preprocess epoched data for one subject.

        Returns dictionary with keys:
          - X: np.ndarray, shape (n_trials, n_channels, n_times)
          - y: np.ndarray, shape (n_trials,) binary {0, 1}
          - runs: np.ndarray, shape (n_trials,) run integer IDs
          - times: np.ndarray, shape (n_times,) time points in seconds
          - sfreq: float, effective sampling rate in Hz
          - channels: List[str], channel names
          - extra: Dict[str, Any], diagnostics and preprocessing metadata
        """
        pass

    def check_array_sanitary(self, X: np.ndarray) -> Tuple[bool, int, int]:
        """Check for NaN and infinite values in epoched data.

        Returns (is_sanitary, n_nan, n_inf).
        """
        n_nan = int(np.isnan(X).sum())
        n_inf = int(np.isinf(X).sum())
        return (n_nan == 0 and n_inf == 0), n_nan, n_inf


# ----------------------------------------------------------------------
# Pluggable Adapter Registry
# ----------------------------------------------------------------------

_DATASET_REGISTRY: Dict[str, Type[BaseEEGDataset]] = {}


def register_adapter(name: str) -> Callable[[Type[BaseEEGDataset]], Type[BaseEEGDataset]]:
    """Decorator to register a dataset adapter class."""
    def decorator(cls: Type[BaseEEGDataset]) -> Type[BaseEEGDataset]:
        _DATASET_REGISTRY[name.lower()] = cls
        return cls
    return decorator


def get_adapter(name: str, data_dir: Path | str, **kwargs) -> BaseEEGDataset:
    """Instantiate a registered dataset adapter by name."""
    key = name.lower()
    if key not in _DATASET_REGISTRY:
        raise KeyError(
            f"Dataset adapter '{name}' is not registered. Available: {list(_DATASET_REGISTRY.keys())}"
        )
    return _DATASET_REGISTRY[key](data_dir=data_dir, **kwargs)


def list_registered_adapters() -> List[str]:
    """Return list of all registered dataset adapter names."""
    return sorted(list(_DATASET_REGISTRY.keys()))
