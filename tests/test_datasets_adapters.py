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
import emi.datasets_adapters
from emi.datasets_adapters import (
    BNCI2014_001Adapter,
    BNCI2014_004Adapter,
    Cho2017Adapter,
    GrosseWentrup2009Adapter,
    HighGammaAdapter,
    OpenBMIAdapter,
    PhysioNetAdapter,
    Shin2017AAdapter,
    Weibo2014Adapter,
    Yang2025Adapter,
    Zhou2016Adapter,
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
    assert d["channels"] == ["C3", "Cz", "C4"]
    assert d["sampling_rate"] == 250.0


def test_adapter_registration():
    """Verify registry correctly lists and retrieves adapter classes."""
    adapters = list_registered_adapters()
    assert "physionet" in adapters
    assert "openbmi" in adapters
    assert "bnci2014_001" in adapters
    assert "cho2017" in adapters
    assert "bnci2014_004" in adapters
    assert "high_gamma" in adapters
    assert "shin2017a" in adapters
    assert "weibo2014" in adapters
    assert "grosse_wentrup2009" in adapters
    assert "zhou2016" in adapters
    assert "yang2025" in adapters

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


def test_all_11_candidate_adapters_metadata(tmp_path):
    """Verify all 11 candidate dataset adapters instantiate and enforce metadata invariants."""
    adapters_to_test = [
        (PhysioNetAdapter(tmp_path), 64, 160.0, 109),
        (OpenBMIAdapter(tmp_path), 62, 1000.0, 54),
        (Cho2017Adapter(tmp_path), 64, 512.0, 52),
        (BNCI2014_001Adapter(tmp_path), 22, 250.0, 9),
        (BNCI2014_004Adapter(tmp_path), 3, 250.0, 9),
        (HighGammaAdapter(tmp_path), 128, 500.0, 14),
        (Shin2017AAdapter(tmp_path), 30, 1000.0, 29),
        (Weibo2014Adapter(tmp_path), 60, 200.0, 10),
        (GrosseWentrup2009Adapter(tmp_path), 128, 500.0, 10),
        (Zhou2016Adapter(tmp_path), 16, 250.0, 4),
        (Yang2025Adapter(tmp_path), 64, 1000.0, 60),
    ]

    for adapter, exp_channels, exp_sfreq, exp_subjects in adapters_to_test:
        assert len(adapter.metadata.channels) == exp_channels
        assert adapter.metadata.sampling_rate == exp_sfreq
        assert adapter.metadata.n_subjects == exp_subjects
        # Missing local files must report PENDING_ACQUISITION gracefully
        is_valid, diag = adapter.validate_integrity(subject=1)
        assert not is_valid
        assert diag["status"] in ("PENDING_ACQUISITION", "EXCLUDED")


def test_registry_datasets_json_validity():
    """Verify registry/datasets.json matches required schema structure."""
    reg_path = Path(__file__).resolve().parent.parent / "registry" / "datasets.json"
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


def test_unified_benchmark_synthetic(tmp_path):
    """Verify scripts/run_unified_benchmark.py runs end-to-end in synthetic mode."""
    import subprocess
    import sys

    script_path = Path(__file__).resolve().parent.parent / "scripts" / "run_unified_benchmark.py"
    out_dir = tmp_path / "bench_out"

    cmd = [
        sys.executable,
        str(script_path),
        "--dataset", "bnci2014_001",
        "--subjects", "1",
        "--decoders", "csp_lda",
        "--designs", "D3,D1s,P1",
        "--synthetic",
        "--outdir", str(out_dir),
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Benchmark script failed: {res.stderr}\n{res.stdout}"

    # Verify generated artifacts
    assert (out_dir / "participant_eligibility.csv").is_file()
    assert (out_dir / "fold_metrics.csv").is_file()
    assert (out_dir / "participant_metrics.csv").is_file()
    assert (out_dir / "design_comparisons.csv").is_file()
    assert (out_dir / "benchmark_manifest.json").is_file()
    assert (out_dir / "fold_indices" / "sub-01_splits.json").is_file()

