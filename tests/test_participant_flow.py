"""Validation tests for PhysioNet participant flow, inclusion accounting, and historical draft refutation."""
import json
import os
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

BENCHMARK_DIR = Path(__file__).resolve().parent.parent / "benchmark_results" / "physionet_v1_1"
MANIFEST_PATH = BENCHMARK_DIR / "participant_flow_manifest.json"
EXCLUDED_CSV = BENCHMARK_DIR / "excluded_or_failed_subjects.csv"
INFLATION_CSV = BENCHMARK_DIR / "inflation_by_subject.csv"
SUBJECT_INFO_CSV = BENCHMARK_DIR / "subject_info.csv"


def test_participant_flow_cohort_counts():
    """Verify total requested (109), included (105), and excluded (4) cohort accounting."""
    assert MANIFEST_PATH.is_file(), f"Manifest file missing: {MANIFEST_PATH}"
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["requested_subjects_total"] == 109
    assert manifest["included_subjects_total"] == 105
    assert manifest["excluded_subjects_total"] == 4
    assert len(manifest["subjects"]) == 109

    included = [s for s, data in manifest["subjects"].items() if data["status"] == "INCLUDED"]
    excluded = [s for s, data in manifest["subjects"].items() if data["status"] == "EXCLUDED"]

    assert len(included) == 105
    assert len(excluded) == 4
    assert sorted(excluded) == ["S044", "S069", "S086", "S091"]


def test_excluded_subjects_ledger_consistency():
    """Verify excluded subjects ledger matches manifest exactly."""
    assert EXCLUDED_CSV.is_file()
    df = pd.read_csv(EXCLUDED_CSV)
    assert len(df) == 4

    excluded_ids = sorted([f"S{s:03d}" for s in df["subject"]])
    assert excluded_ids == ["S044", "S069", "S086", "S091"]

    # Verify specific reasons
    s44_row = df[df["subject"] == 44].iloc[0]
    assert "sub-044_epochs.npz" in s44_row["reason"]

    s69_row = df[df["subject"] == 69].iloc[0]
    assert "sub-069_epochs.npz" in s69_row["reason"]

    s86_row = df[df["subject"] == 86].iloc[0]
    assert "24 trials" in s86_row["reason"] and "< 30" in s86_row["reason"]

    s91_row = df[df["subject"] == 91].iloc[0]
    assert "sub-091_epochs.npz" in s91_row["reason"]


def test_refutation_of_historical_manuscript_draft_line_95():
    """Formally refute the claim that S088, S092, S100, S104 were excluded.

    Verify that S088, S092, S100, and S104 are fully included and evaluated in the benchmark.
    """
    assert INFLATION_CSV.is_file()
    df_inf = pd.read_csv(INFLATION_CSV)
    assert SUBJECT_INFO_CSV.is_file()
    df_info = pd.read_csv(SUBJECT_INFO_CSV)

    eval_subjects = set(df_inf["subject"].unique())
    info_subjects = set(df_info["subject"].unique())

    target_subjects = [88, 92, 100, 104]
    for s in target_subjects:
        assert s in eval_subjects, f"Subject S{s:03d} must be present in inflation_by_subject.csv"
        assert s in info_subjects, f"Subject S{s:03d} must be present in subject_info.csv"

        # Check that evaluations exist for all 3 contrasts (D1m, D1s, P1)
        sub_df = df_inf[df_inf["subject"] == s]
        assert len(sub_df) == 3, f"Subject S{s:03d} must have exactly 3 contrast rows"
        designs = set(sub_df["design"])
        assert designs == {"D1m_matched_k", "D1s_size_matched", "P1_csp_on_all"}

        # Verify trial counts exceed minimum threshold (> 30)
        s_row = df_info[df_info["subject"] == s].iloc[0]
        assert s_row["n_trials"] >= 30, f"Subject S{s:03d} trial count {s_row['n_trials']} must be >= 30"

    # Verify sampling rates (hardware variation: S088, S092, S100 = 128Hz, S104 = 160Hz)
    assert df_info[df_info["subject"] == 88].iloc[0]["sfreq"] == 128.0
    assert df_info[df_info["subject"] == 92].iloc[0]["sfreq"] == 128.0
    assert df_info[df_info["subject"] == 100].iloc[0]["sfreq"] == 128.0
    assert df_info[df_info["subject"] == 104].iloc[0]["sfreq"] == 160.0


def test_s086_trial_threshold_exclusion():
    """Verify S086 has only 24 trials across 3 runs and was excluded strictly by sample size."""
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    s86_meta = manifest["subjects"]["S086"]
    assert s86_meta["status"] == "EXCLUDED"
    assert s86_meta["n_trials"] == 24
    assert s86_meta["trials_per_run"] == [5, 4, 15]
    assert "24 trials < minimum 30" in s86_meta["rejection_rationale"]


def test_all_105_included_participants_complete():
    """Verify all 105 included participants have valid trial counts and positive sampling rates."""
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    for s_id, data in manifest["subjects"].items():
        if data["status"] == "INCLUDED":
            assert data["n_trials"] >= 30, f"{s_id} has fewer than 30 trials"
            assert data["n_runs"] == 3, f"{s_id} does not have 3 runs"
            assert data["sfreq"] in (128.0, 160.0), f"{s_id} unexpected sfreq: {data['sfreq']}"
            assert data["n_channels"] == 64, f"{s_id} unexpected channel count"
            assert len(data["accuracies"]) == 3, f"{s_id} missing contrast evaluations"
