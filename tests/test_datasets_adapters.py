"""Unit and regression tests for LeakCheck V2 Multi-Dataset Adapters and Registry."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

pytestmark = pytest.mark.v2

from emi.datasets_base import (
    BaseEEGDataset,
    DatasetMetadata,
    get_adapter,
    list_registered_adapters,
    register_adapter,
)
from emi.datasets_adapters import (
    BNCI2014_001Adapter,
    Cho2017Adapter,
    OpenBMIAdapter,
    PhysioNetAdapter,
)


def test_metadata_dataclass():
    """Verify DatasetMetadata serializes to dictionary cleanly."""
    meta = DatasetMetadata(
        dataset_name="TestDataset",
        accession_id="test_01",
        citation="Test et al. (2026)",
        doi="10.1234/test",
        license="MIT",
        n_subjects=10,
        channels=["C3", "Cz", "C4"],
        sampling_rate=250.0,
        motor_tasks=["left", "right"],
        session_structure={"runs": 2},
        file_format="EDF",
    )
    d = meta.to_dict()
    assert d["dataset_name"] == "TestDataset"
    assert d["channel_count"] is None or d["channels"] == ["C3", "Cz", "C4"]
    assert d["sampling_rate"] == 250.0


def test_adapter_registration():
    """Verify registry correctly lists and retrieves adapter classes."""
    adapters = list_registered_adapters()
    assert "physionet" in adapters
    assert "openbmi" in adapters
    assert "bnci2014_001" in adapters
    assert "cho2017" in adapters

    # Instantiate via registry
    adapter = get_adapter("openbmi", data_dir="data/OpenBMI")
    assert isinstance(adapter, OpenBMIAdapter)
    assert adapter.name == "OpenBMI"
    assert adapter.metadata.n_subjects == 54


def test_openbmi_adapter_metadata():
    """Verify OpenBMI metadata contracts."""
    adapter = OpenBMIAdapter(data_dir="data/OpenBMI")
    assert adapter.metadata.channel_count == 62 or len(adapter.metadata.channels) == 62
    assert adapter.metadata.sampling_rate == 1000.0
    assert "left_hand" in adapter.metadata.motor_tasks
    assert "right_hand" in adapter.metadata.motor_tasks


def test_physionet_adapter_metadata():
    """Verify PhysioNet metadata contracts."""
    adapter = PhysioNetAdapter(data_dir="data/cache")
    assert len(adapter.metadata.channels) == 64
    assert adapter.metadata.sampling_rate == 160.0
    assert adapter.metadata.accession_id == "eegmmidb"


def test_missing_data_integrity_handling(tmp_path):
    """Verify adapters report PENDING_ACQUISITION or EXCLUDED on missing files without throwing."""
    bnci = BNCI2014_001Adapter(data_dir=tmp_path)
    is_valid, diag = bnci.validate_integrity(subject=1)
    assert not is_valid
    assert diag["status"] == "PENDING_ACQUISITION"

    cho = Cho2017Adapter(data_dir=tmp_path)
    is_valid, diag = cho.validate_integrity(subject=1)
    assert not is_valid
    assert diag["status"] == "PENDING_ACQUISITION"


def test_registry_datasets_json_validity():
    """Verify registry/datasets.json matches required schema structure."""
    reg_path = Path("registry/datasets.json")
    assert reg_path.is_file(), "registry/datasets.json must exist"

    with open(reg_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["version"] == "2.0.0"
    assert len(data["datasets"]) >= 4

    dataset_ids = [d["dataset_id"] for d in data["datasets"]]
    assert "physionet_eegmmidb" in dataset_ids
    assert "openbmi_lee2019" in dataset_ids
    assert "bnci2014_001" in dataset_ids
    assert "cho2017" in dataset_ids
