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
import mne
import numpy as np
import pandas as pd
import scipy.io
from unittest.mock import patch

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
    parse_bnci_events_and_runs,
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


def test_bnci_event_parsing_integer_codes():
    """Verify BNCI event parsing maps integer event codes correctly without TypeError."""
    raw_info = mne.create_info(ch_names=["C3", "Cz", "C4"], sfreq=250.0, ch_types="eeg")
    raw = mne.io.RawArray(np.zeros((3, 5000)), raw_info, verbose="ERROR")

    # Case A: Integer codes mapped via event_id dictionary (e.g. '769': 1, '770': 2)
    events_mapped = np.array([
        [500, 0, 1],   # Left hand (event code 1)
        [1000, 0, 2],  # Right hand (event code 2)
        [1500, 0, 1],  # Left hand
        [2000, 0, 2],  # Right hand
    ])
    event_id = {"769": 1, "770": 2}
    target_ids = {"769": 1, "770": 2}
    epochs_mapped = mne.Epochs(raw, events_mapped, event_id=target_ids, tmin=0.0, tmax=1.0, baseline=None, preload=True, verbose="ERROR")

    y_mapped, runs_mapped = parse_bnci_events_and_runs(epochs_mapped, events_mapped, event_id, target_ids, default_n_runs=2)
    assert np.array_equal(y_mapped, [0, 1, 0, 1])
    assert y_mapped.dtype == int or np.issubdtype(y_mapped.dtype, np.integer)

    # Case B: Direct integer codes (769, 770) in epochs.events
    events_direct = np.array([
        [500, 0, 769],
        [1000, 0, 770],
        [1500, 0, 769],
        [2000, 0, 770],
    ])
    direct_ids = {"769": 769, "770": 770}
    epochs_direct = mne.Epochs(raw, events_direct, event_id=direct_ids, tmin=0.0, tmax=1.0, baseline=None, preload=True, verbose="ERROR")

    y_direct, runs_direct = parse_bnci_events_and_runs(epochs_direct, events_direct, direct_ids, direct_ids, default_n_runs=2)
    assert np.array_equal(y_direct, [0, 1, 0, 1])


def test_bnci_run_boundary_assignment_non_zero():
    """Verify that multi-run datasets receive non-zero run IDs partitioning trials across runs."""
    raw_info = mne.create_info(ch_names=["C3", "Cz", "C4"], sfreq=250.0, ch_types="eeg")
    raw = mne.io.RawArray(np.zeros((3, 200000)), raw_info, verbose="ERROR")

    # Case A: 144 trials partitioned across 6 standard runs (BCI Competition IV-2a)
    n_trials = 144
    samples = np.linspace(100, 150000, n_trials, dtype=int)
    events_144 = np.zeros((n_trials, 3), dtype=int)
    events_144[:, 0] = samples
    events_144[:, 2] = [1 if i % 2 == 0 else 2 for i in range(n_trials)]

    target_ids = {"769": 1, "770": 2}
    epochs_144 = mne.Epochs(raw, events_144, event_id=target_ids, tmin=0.0, tmax=0.5, baseline=None, preload=True, verbose="ERROR")

    y_144, runs_144 = parse_bnci_events_and_runs(epochs_144, events_144, target_ids, target_ids, default_n_runs=6)
    assert len(runs_144) == 144
    assert set(np.unique(runs_144)) == {0, 1, 2, 3, 4, 5}
    assert np.any(runs_144 > 0), "Non-zero run IDs must be populated"
    for r in range(6):
        assert np.sum(runs_144 == r) == 24

    # Case B: 120 trials partitioned across 3 standard runs (BCI Competition IV-2b session 1)
    n_trials_120 = 120
    samples_120 = np.linspace(100, 150000, n_trials_120, dtype=int)
    events_120 = np.zeros((n_trials_120, 3), dtype=int)
    events_120[:, 0] = samples_120
    events_120[:, 2] = [1 if i % 2 == 0 else 2 for i in range(n_trials_120)]

    epochs_120 = mne.Epochs(raw, events_120, event_id=target_ids, tmin=0.0, tmax=0.5, baseline=None, preload=True, verbose="ERROR")
    y_120, runs_120 = parse_bnci_events_and_runs(epochs_120, events_120, target_ids, target_ids, default_n_runs=3)
    assert len(runs_120) == 120
    assert set(np.unique(runs_120)) == {0, 1, 2}
    assert np.any(runs_120 > 0), "Non-zero run IDs must be populated"
    for r in range(3):
        assert np.sum(runs_120 == r) == 40

    # Case C: GDF run boundary markers present (event 32766)
    events_with_markers = np.array([
        [100, 0, 99],    # Run start 0 (event code 99 for 32766)
        [200, 0, 1],     # Trial 0 (run 0)
        [400, 0, 2],     # Trial 1 (run 0)
        [1000, 0, 99],   # Run start 1
        [1200, 0, 1],    # Trial 2 (run 1)
        [1400, 0, 2],    # Trial 3 (run 1)
    ])
    event_id_with_markers = {"769": 1, "770": 2, "32766": 99}
    epochs_markers = mne.Epochs(raw, events_with_markers, event_id=target_ids, tmin=0.0, tmax=0.5, baseline=None, preload=True, verbose="ERROR")
    y_m, runs_m = parse_bnci_events_and_runs(epochs_markers, events_with_markers, event_id_with_markers, target_ids, default_n_runs=6)
    assert np.array_equal(y_m, [0, 1, 0, 1])
    assert np.array_equal(runs_m, [0, 0, 1, 1])
    assert np.any(runs_m > 0)


def test_bnci_adapters_mocked_get_subject_epochs(tmp_path):
    """Verify BNCI2014_001Adapter and BNCI2014_004Adapter get_subject_epochs pipeline."""
    # Create fake GDF file in tmp_path
    (tmp_path / "A01T.gdf").touch()
    (tmp_path / "B0101T.gdf").touch()

    raw_info_22 = mne.create_info(ch_names=[f"EEG_{i}" for i in range(22)], sfreq=250.0, ch_types="eeg")
    raw_22 = mne.io.RawArray(np.zeros((22, 10000)), raw_info_22, verbose="ERROR")

    # Add annotations for 769 and 770
    annot_22 = mne.Annotations(onset=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0], duration=[0.1]*6, description=["769", "770", "769", "770", "769", "770"])
    raw_22.set_annotations(annot_22)

    with patch("mne.io.read_raw_gdf", return_value=raw_22):
        adapter_2a = BNCI2014_001Adapter(tmp_path)
        data_2a = adapter_2a.get_subject_epochs(1)
        assert data_2a["X"].shape[0] == 6
        assert len(data_2a["y"]) == 6
        assert len(data_2a["runs"]) == 6
        assert set(np.unique(data_2a["y"])).issubset({0, 1})
        assert np.any(data_2a["runs"] > 0), "BNCI 2a runs must contain non-zero IDs"

    raw_info_3 = mne.create_info(ch_names=["C3", "Cz", "C4"], sfreq=250.0, ch_types="eeg")
    raw_3 = mne.io.RawArray(np.zeros((3, 10000)), raw_info_3, verbose="ERROR")
    annot_3 = mne.Annotations(onset=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0], duration=[0.1]*6, description=["769", "770", "769", "770", "769", "770"])
    raw_3.set_annotations(annot_3)

    with patch("mne.io.read_raw_gdf", return_value=raw_3):
        adapter_2b = BNCI2014_004Adapter(tmp_path)
        data_2b = adapter_2b.get_subject_epochs(1)
        assert data_2b["X"].shape[0] == 6
        assert len(data_2b["y"]) == 6
        assert len(data_2b["runs"]) == 6
        assert set(np.unique(data_2b["y"])).issubset({0, 1})
        assert np.any(data_2b["runs"] > 0), "BNCI 2b runs must contain non-zero IDs"


def test_unified_benchmark_ts_lr_design_naming(tmp_path):
    """Verify that Riemannian TS-LR under global spatial contamination outputs design 'P1_ts_on_all'."""
    import subprocess
    import sys

    script_path = Path(__file__).resolve().parent.parent / "scripts" / "run_unified_benchmark.py"
    out_dir = tmp_path / "bench_ts_out"

    cmd = [
        sys.executable,
        str(script_path),
        "--dataset", "bnci2014_001",
        "--subjects", "1",
        "--decoders", "csp_lda,ts_lr",
        "--designs", "D3,D1s,P1",
        "--synthetic",
        "--outdir", str(out_dir),
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Benchmark script failed: {res.stderr}\n{res.stdout}"

    fold_df = pd.read_csv(out_dir / "fold_metrics.csv")
    csp_designs = set(fold_df[fold_df["decoder"] == "csp_lda"]["design"])
    ts_designs = set(fold_df[fold_df["decoder"] == "ts_lr"]["design"])

    assert "P1_csp_on_all" in csp_designs, "CSP-LDA must emit P1_csp_on_all"
    assert "P1_ts_on_all" in ts_designs, "Riemannian TS-LR must emit P1_ts_on_all"
    assert "P1_csp_on_all" not in ts_designs, "Riemannian TS-LR must NOT emit P1_csp_on_all"

    comp_df = pd.read_csv(out_dir / "design_comparisons.csv")
    ts_p1_comp = comp_df[(comp_df["decoder"] == "ts_lr") & (comp_df["contrast"] == "P1_vs_D3")]
    assert not ts_p1_comp.empty, "Level 3 contrast P1_vs_D3 for TS-LR must exist"
    assert ts_p1_comp["condition_b"].iloc[0] == "P1_ts_on_all"


def test_cho2017_adapter_continuous_parsing(tmp_path):
    """Verify Cho2017Adapter parses genuine continuous GigaDB struct with event triggers."""
    srate = 512.0
    n_samples = 5120
    imagery_l = np.random.randn(64, n_samples) * 10.0
    imagery_r = np.random.randn(64, n_samples) * 10.0

    triggers_l = np.zeros(n_samples)
    triggers_l[[512, 1536, 2560, 3584]] = 1.0

    triggers_r = np.zeros(n_samples)
    triggers_r[[512, 1536, 2560, 3584]] = 1.0

    cho_struct = {
        "eeg": {
            "srate": srate,
            "imagery_left": imagery_l,
            "imagery_right": imagery_r,
            "imagery_event": triggers_l,
            "imagery_event_right": triggers_r,
        }
    }
    scipy.io.savemat(str(tmp_path / "s01.mat"), cho_struct)

    adapter = Cho2017Adapter(tmp_path)
    is_valid, diag = adapter.validate_integrity(1)
    assert is_valid, f"Expected valid integrity: {diag}"

    data = adapter.get_subject_epochs(1, target_fs=250.0, tmin=0.0, tmax=1.0)
    assert data["X"].shape[0] == 8, f"Expected 8 trials (4 left + 4 right), got {data['X'].shape[0]}"
    assert data["X"].shape[1] == 64, f"Expected 64 channels, got {data['X'].shape[1]}"
    assert data["X"].shape[2] == 250, f"Expected 250 time points at 250Hz, got {data['X'].shape[2]}"
    assert np.array_equal(data["y"], [0, 0, 0, 0, 1, 1, 1, 1])
    assert len(data["runs"]) == 8
    assert len(np.unique(data["runs"])) > 1, "Run IDs must contain multi-run partition for LORO"
    assert data["sfreq"] == 250.0


def test_cho2017_adapter_epoched_mat_parsing(tmp_path):
    """Verify Cho2017Adapter parses pre-epoched 3D arrays and maps labels correctly."""
    X_epoched = np.random.randn(10, 64, 256) * 15.0
    y_raw = np.array([1, 1, 1, 1, 1, 2, 2, 2, 2, 2])

    scipy.io.savemat(str(tmp_path / "s02.mat"), {"eeg": X_epoched, "y": y_raw, "srate": 250.0})

    adapter = Cho2017Adapter(tmp_path)
    data = adapter.get_subject_epochs(2, target_fs=250.0)
    assert data["X"].shape == (10, 64, 256)
    assert np.array_equal(data["y"], [0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    assert len(data["runs"]) == 10
    assert len(np.unique(data["runs"])) > 1


def test_high_gamma_adapter_genuine_annotation_parsing(tmp_path):
    """Verify HighGammaAdapter extracts genuine MNE annotations without dummy alternating labels."""
    (tmp_path / "subject_1.edf").touch()

    raw_info = mne.create_info(ch_names=[f"eeg_{i}" for i in range(1, 45)], sfreq=250.0, ch_types="eeg")
    raw = mne.io.RawArray(np.random.randn(44, 25000) * 1e-5, raw_info, verbose="ERROR")

    annots = mne.Annotations(
        onset=[1.0, 3.0, 5.0, 7.0, 9.0, 11.0, 13.0, 15.0],
        duration=[0.5] * 8,
        description=["left_hand", "left_hand", "left_hand", "left_hand", "right_hand", "right_hand", "right_hand", "right_hand"],
    )
    raw.set_annotations(annots)

    with patch("mne.io.read_raw_edf", return_value=raw):
        adapter = HighGammaAdapter(tmp_path)
        is_valid, diag = adapter.validate_integrity(1)
        assert is_valid

        data = adapter.get_subject_epochs(1, tmin=0.0, tmax=1.0)
        assert data["X"].shape[0] == 8
        assert data["X"].shape[1] == 44
        assert np.array_equal(data["y"], [0, 0, 0, 0, 1, 1, 1, 1]), f"Expected [0,0,0,0,1,1,1,1], got {data['y']}"
        assert len(data["runs"]) == 8
        assert len(np.unique(data["runs"])) > 1, "Run IDs must contain multi-run partition for LORO"


def test_shin2017a_adapter_bbci_mat_parsing(tmp_path):
    """Verify Shin2017AAdapter parses BBCI cnt/mrk struct format with label mapping."""
    cnt = {
        "x": np.random.randn(8000, 30) * 10.0,
        "fs": 1000.0,
        "clab": [f"EEG_{i}" for i in range(30)],
    }
    mrk = {
        "pos": np.array([500, 1500, 2500, 3500, 4500, 5500]),
        "y": np.array([
            [1, 1, 1, 0, 0, 0],
            [0, 0, 0, 1, 1, 1],
        ]),
    }
    scipy.io.savemat(str(tmp_path / "VP001.mat"), {"cnt": cnt, "mrk": mrk})

    adapter = Shin2017AAdapter(tmp_path)
    is_valid, diag = adapter.validate_integrity(1)
    assert is_valid

    data = adapter.get_subject_epochs(1, target_fs=250.0, tmin=0.0, tmax=1.0)
    assert data["X"].shape[0] == 6
    assert data["X"].shape[1] == 30
    assert data["X"].shape[2] == 250
    assert np.array_equal(data["y"], [0, 0, 0, 1, 1, 1])
    assert len(data["runs"]) == 6
    assert len(np.unique(data["runs"])) > 1


def test_weibo2014_adapter_mat_parsing(tmp_path):
    """Verify Weibo2014Adapter parses 3D MAT array and maps labels and 6-run boundaries."""
    X_mat = np.random.randn(12, 60, 200) * 10.0
    labels = np.array([1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2])
    scipy.io.savemat(str(tmp_path / "subject_1.mat"), {"data": X_mat, "label": labels})

    adapter = Weibo2014Adapter(tmp_path)
    is_valid, diag = adapter.validate_integrity(1)
    assert is_valid

    data = adapter.get_subject_epochs(1)
    assert data["X"].shape == (12, 60, 200)
    assert np.array_equal(data["y"], [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1])
    assert len(data["runs"]) == 12
    assert len(np.unique(data["runs"])) > 1
    assert data["channels"] == [f"eeg_{i}" for i in range(1, 61)]


def test_zhou2016_and_yang2025_adapter_parsing(tmp_path):
    """Verify Zhou2016 and Yang2025 adapters parse structures and partition runs."""
    # Zhou2016: 16 channels
    scipy.io.savemat(str(tmp_path / "subject_1.mat"), {
        "eeg": np.random.randn(6, 16, 250),
        "y": np.array([1, 1, 1, 2, 2, 2]),
    })
    zhou = Zhou2016Adapter(tmp_path)
    data_z = zhou.get_subject_epochs(1)
    assert data_z["X"].shape[1] == 16
    assert np.array_equal(data_z["y"], [0, 0, 0, 1, 1, 1])
    assert len(np.unique(data_z["runs"])) > 1

    # Yang2025: 64 channels
    scipy.io.savemat(str(tmp_path / "sub-01.mat"), {
        "eeg": np.random.randn(8, 64, 250),
        "y": np.array([1, 1, 1, 1, 2, 2, 2, 2]),
    })
    yang = Yang2025Adapter(tmp_path)
    data_y = yang.get_subject_epochs(1)
    assert data_y["X"].shape[1] == 64
    assert np.array_equal(data_y["y"], [0, 0, 0, 0, 1, 1, 1, 1])
    assert len(np.unique(data_y["runs"])) > 1


