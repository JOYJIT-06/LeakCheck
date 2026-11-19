"""Unit tests for OpenBMI dataset adapter in LeakCheck V2."""
import numpy as np
import pytest
from pathlib import Path

pytestmark = pytest.mark.v2

from emi.datasets_openbmi import (
    OPENBMI_FAILED_DOWNLOADS,
    OPENBMI_CHANNELS_62,
    find_valid_openbmi_subjects,
    load_openbmi_subject,
)


def test_failed_downloads_list():
    """Verify known corrupted/interrupted OpenBMI subjects are flagged."""
    assert OPENBMI_FAILED_DOWNLOADS == {1, 4, 11, 40, 41}
    assert len(OPENBMI_CHANNELS_62) == 62


def test_find_valid_openbmi_subjects():
    """Verify detection of intact OpenBMI subject folders."""
    data_dir = Path(r"D:\my lab\LeakCheck\data\OpenBMI")
    if not data_dir.is_dir():
        pytest.skip("OpenBMI dataset directory not found on host.")

    valid = find_valid_openbmi_subjects(data_dir)
    # Ensure none of the failed downloads are in valid
    assert set(valid).isdisjoint(OPENBMI_FAILED_DOWNLOADS)
    assert 2 in valid
    assert 3 in valid


def test_load_openbmi_subject_2():
    """Verify loading real subject 2 from OpenBMI."""
    data_dir = Path(r"D:\my lab\LeakCheck\data\OpenBMI")
    if not (data_dir / "sourcedata" / "session1" / "s2").is_dir():
        pytest.skip("OpenBMI subject 2 not present.")

    d = load_openbmi_subject(2, data_dir, target_fs=100.0, tmin=0.0, tmax=3.0)
    assert d["subject"] == 2
    assert d["X"].ndim == 3
    assert d["X"].shape[1] == 62  # 62 channels
    assert len(d["y"]) == len(d["runs"]) == d["X"].shape[0]
    assert set(np.unique(d["y"])).issubset({0, 1})
    assert set(np.unique(d["runs"])).issubset({0, 1})
    assert len(d["times"]) == d["X"].shape[2]
