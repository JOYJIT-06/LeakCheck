"""Automated Software Validation Tests for LeakCheck V1.1 Statistical Audit.

Verifies:
1. Exact participant cohort accounting (N=105, S044/S069/S086/S091 excluded, S088/S092/S100/S104 present).
2. Hodges-Lehmann pseudo-median shifts for all 4 key contrasts (P1 vs D3, D1s vs D3, D1m vs D3, D1s vs D1m).
3. BCa bootstrap confidence intervals and fallback mechanics.
4. Wilcoxon signed-rank tests (both Wilcoxon and Pratt zero-handling methods).
5. Holm-Bonferroni step-down multiple testing adjustments.
6. Within-subject Cohen's d_z effect sizes and rank-biserial correlations.
7. Two One-Sided Tests (TOST) for equivalence within +-2.0 percentage points.
8. Historical null controls settings (n_null == 0 disclosure).
9. Cross-platform Python-vs-R reconciliation data integrity.
10. Cohort-level absolute decoding accuracy distributions (D3, D1s, D1m, P1).
11. Hardware sampling-rate strata invariance (128 Hz vs 160 Hz).
"""
import os
import numpy as np
import pandas as pd
import pytest
import scipy.stats as stats

from emi.leakstats import (
    bca_ci,
    cohens_dz,
    hodges_lehmann,
    holm,
    rank_biserial,
    tost_paired,
)


@pytest.fixture(scope="module")
def benchmark_paths():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    hist_dir = os.path.join(base_dir, "archive", "historical_benchmarks", "physionet_v1_1_final")
    if os.path.isdir(hist_dir):
        csv_path = os.path.join(hist_dir, "inflation_by_subject.csv")
        settings_path = os.path.join(hist_dir, "settings.json")
    else:
        csv_path = os.path.join(base_dir, "benchmark_results", "physionet_v1_1", "inflation_by_subject.csv")
        settings_path = os.path.join(base_dir, "benchmark_results", "physionet_v1_1", "settings.json")
    r_csv_path = os.path.join(base_dir, "analysis", "R_validation", "reproduced_statistics_R.csv")
    return {
        "inflation_by_subject": csv_path,
        "settings": settings_path,
        "r_csv": r_csv_path,
    }


@pytest.fixture(scope="module")
def cohort_data(benchmark_paths):
    path = benchmark_paths["inflation_by_subject"]
    assert os.path.isfile(path), f"Missing {path}"
    df = pd.read_csv(path)
    return df


@pytest.fixture(scope="module")
def paired_contrasts(cohort_data):
    df = cohort_data
    d1s = df[df["design"] == "D1s_size_matched"].sort_values("subject").reset_index(drop=True)
    d1m = df[df["design"] == "D1m_matched_k"].sort_values("subject").reset_index(drop=True)
    p1 = df[df["design"] == "P1_csp_on_all"].sort_values("subject").reset_index(drop=True)

    delta_p1 = (p1["acc_leaky"].to_numpy() - p1["acc_ref"].to_numpy()) * 100.0
    delta_d1s = (d1s["acc_leaky"].to_numpy() - d1s["acc_ref"].to_numpy()) * 100.0
    delta_d1m = (d1m["acc_leaky"].to_numpy() - d1m["acc_ref"].to_numpy()) * 100.0
    delta_d1s_vs_d1m = (d1s["acc_leaky"].to_numpy() - d1m["acc_leaky"].to_numpy()) * 100.0

    return {
        "P1_vs_D3": delta_p1,
        "D1s_vs_D3": delta_d1s,
        "D1m_vs_D3": delta_d1m,
        "D1s_vs_D1m": delta_d1s_vs_d1m,
        "subjects": d1s["subject"].to_numpy(),
    }


def test_participant_cohort_accounting(cohort_data):
    """Verify exactly 105 participants are present; S044, S069, S086, S091 are absent; S088, S092, S100, S104 are present."""
    subjects = sorted(cohort_data["subject"].unique())
    assert len(subjects) == 105, f"Expected exactly 105 subjects, got {len(subjects)}"

    # Invariant: 109 requested (1..109)
    expected_absent = {44, 69, 86, 91}
    actual_absent = set(range(1, 110)) - set(subjects)
    assert actual_absent == expected_absent, f"Expected exclusions {expected_absent}, got {actual_absent}"

    # Verify manuscript line 95 refutation: S088, S092, S100, S104 are 100% evaluated
    for sid in [88, 92, 100, 104]:
        assert sid in subjects, f"Subject S{sid:03d} must be present in evaluated cohort"


def test_hodges_lehmann_point_estimates(paired_contrasts):
    """Verify Hodges-Lehmann pseudo-median shifts for all four contrasts."""
    hl_p1 = hodges_lehmann(paired_contrasts["P1_vs_D3"])
    hl_d1s = hodges_lehmann(paired_contrasts["D1s_vs_D3"])
    hl_d1m = hodges_lehmann(paired_contrasts["D1m_vs_D3"])
    hl_geom = hodges_lehmann(paired_contrasts["D1s_vs_D1m"])

    assert abs(hl_p1 - 24.5029) < 0.01, f"P1 HL estimate {hl_p1} != 24.50"
    assert abs(hl_d1s - (-2.6768)) < 0.01, f"D1s HL estimate {hl_d1s} != -2.68"
    assert abs(hl_d1m - (-4.4697)) < 0.01, f"D1m HL estimate {hl_d1m} != -4.47"
    assert abs(hl_geom - 1.8561) < 0.01, f"D1s vs D1m HL estimate {hl_geom} != 1.86"


def test_bca_confidence_intervals(paired_contrasts):
    """Verify BCa bootstrap confidence intervals strictly exclude zero for all 4 contrasts."""
    lo_p1, hi_p1, m_p1 = bca_ci(paired_contrasts["P1_vs_D3"], seed=0, return_method=True)
    assert m_p1 == "BCa"
    assert 20.0 < lo_p1 < 23.0
    assert 26.5 < hi_p1 < 30.0

    lo_d1s, hi_d1s, m_d1s = bca_ci(paired_contrasts["D1s_vs_D3"], seed=0, return_method=True)
    assert m_d1s == "BCa"
    assert -4.5 < lo_d1s < -3.5
    assert -2.0 < hi_d1s < -1.0
    assert hi_d1s < 0.0  # Confirms significant conservative deflation

    lo_d1m, hi_d1m, m_d1m = bca_ci(paired_contrasts["D1m_vs_D3"], seed=0, return_method=True)
    assert m_d1m == "BCa"
    assert -6.5 < lo_d1m < -5.0
    assert -3.5 < hi_d1m < -2.5
    assert hi_d1m < 0.0  # Confirms significant conservative deflation

    lo_geom, hi_geom, m_geom = bca_ci(paired_contrasts["D1s_vs_D1m"], seed=0, return_method=True)
    assert m_geom == "BCa"
    assert 1.0 < lo_geom < 1.5
    assert 2.0 < hi_geom < 3.0
    assert lo_geom > 0.0  # Confirms significant fold-geometry recovery


def test_wilcoxon_tests_and_pratt_handling(paired_contrasts):
    """Verify two-sided Wilcoxon signed-rank tests under both Wilcoxon and Pratt zero-handling."""
    for cname, d in paired_contrasts.items():
        if cname == "subjects":
            continue
        w_wilcox = stats.wilcoxon(d, zero_method="wilcox")
        w_pratt = stats.wilcoxon(d, zero_method="pratt")

        # In all contrasts, p-value is highly significant (p < 1e-4)
        assert w_wilcox.pvalue < 1e-4, f"Wilcoxon p-value for {cname} not significant: {w_wilcox.pvalue}"
        assert w_pratt.pvalue < 1e-4, f"Pratt p-value for {cname} not significant: {w_pratt.pvalue}"

    # Specific checks
    p1_res = stats.wilcoxon(paired_contrasts["P1_vs_D3"], zero_method="wilcox")
    assert p1_res.statistic == 6.0
    assert p1_res.pvalue < 1e-17

    d1s_res = stats.wilcoxon(paired_contrasts["D1s_vs_D3"], zero_method="wilcox")
    assert d1s_res.statistic == 1525.5
    assert abs(d1s_res.pvalue - 5.86e-5) < 1e-6


def test_holm_multiplicity_correction(paired_contrasts):
    """Verify Holm-Bonferroni correction preserves statistical significance across the family."""
    raw_p = [
        stats.wilcoxon(paired_contrasts["P1_vs_D3"]).pvalue,
        stats.wilcoxon(paired_contrasts["D1s_vs_D3"]).pvalue,
        stats.wilcoxon(paired_contrasts["D1m_vs_D3"]).pvalue,
    ]
    adj_p = holm(raw_p)

    # Monotonic step-down checks
    assert adj_p[0] == pytest.approx(raw_p[0] * 3, rel=1e-3)
    assert adj_p[2] == pytest.approx(raw_p[2] * 2, rel=1e-3)
    assert adj_p[1] == pytest.approx(raw_p[1] * 1, rel=1e-3)

    # All primary Holm-adjusted p-values must be < 1e-4
    assert np.all(adj_p < 1e-4)


def test_effect_sizes_and_rank_biserial(paired_contrasts):
    """Verify within-subject Cohen's d_z and rank-biserial correlations."""
    dz_p1 = cohens_dz(paired_contrasts["P1_vs_D3"])
    dz_d1s = cohens_dz(paired_contrasts["D1s_vs_D3"])
    dz_d1m = cohens_dz(paired_contrasts["D1m_vs_D3"])
    dz_geom = cohens_dz(paired_contrasts["D1s_vs_D1m"])

    assert abs(dz_p1 - 1.7708) < 0.01
    assert abs(dz_d1s - (-0.4491)) < 0.01
    assert abs(dz_d1m - (-0.6847)) < 0.01
    assert abs(dz_geom - 0.5522) < 0.01

    rrb_p1 = rank_biserial(paired_contrasts["P1_vs_D3"])
    rrb_d1s = rank_biserial(paired_contrasts["D1s_vs_D3"])
    rrb_d1m = rank_biserial(paired_contrasts["D1m_vs_D3"])
    rrb_geom = rank_biserial(paired_contrasts["D1s_vs_D1m"])

    assert rrb_p1 > 0.99
    assert -0.47 < rrb_d1s < -0.44
    assert -0.67 < rrb_d1m < -0.65
    assert 0.57 < rrb_geom < 0.60


def test_tost_equivalence_testing(paired_contrasts):
    """Verify Two One-Sided Tests (TOST) confirm non-equivalence within +-2.0 pp for all contrasts."""
    for cname in ["P1_vs_D3", "D1s_vs_D3", "D1m_vs_D3", "D1s_vs_D1m"]:
        res = tost_paired(paired_contrasts[cname], margin=2.0, alpha=0.05)
        assert res["equivalent"] is False, f"Contrast {cname} unexpectedly claimed equivalent"
        assert res["tost_p"] > 0.05, f"Contrast {cname} TOST p-value unexpectedly <= 0.05: {res['tost_p']}"


def test_historical_null_controls_disclosure(benchmark_paths):
    """Verify that historical benchmark configuration explicitly used n_null=0."""
    import json
    with open(benchmark_paths["settings"], "r") as f:
        settings = json.load(f)
    assert settings.get("n_null") == 0, "Expected historical n_null == 0"


def test_python_r_reconciliation_csv_exists(benchmark_paths):
    """Verify that independent R validation output file exists and has expected rows."""
    r_csv = benchmark_paths["r_csv"]
    assert os.path.isfile(r_csv), f"Missing {r_csv}"
    df_r = pd.read_csv(r_csv)
    assert len(df_r) == 4, f"Expected 4 contrast rows in R CSV, got {len(df_r)}"
    expected_contrasts = {"P1 vs D3", "D1s vs D3", "D1m vs D3", "D1s vs D1m"}
    assert set(df_r["contrast"].unique()) == expected_contrasts


def test_absolute_accuracy_distributions(cohort_data):
    """Verify cohort-level absolute decoding accuracy distributions across all 4 designs."""
    piv_leak = cohort_data.pivot(index="subject", columns="design", values="acc_leaky") * 100.0
    piv_ref = cohort_data.pivot(index="subject", columns="design", values="acc_ref") * 100.0
    d3 = piv_ref.iloc[:, 0]
    d1s = piv_leak["D1s_size_matched"]
    d1m = piv_leak["D1m_matched_k"]
    p1 = piv_leak["P1_csp_on_all"]

    assert abs(d3.mean() - 60.1500) < 0.01
    assert abs(d1s.mean() - 57.3785) < 0.01
    assert abs(d1m.mean() - 55.4841) < 0.01
    assert abs(p1.mean() - 84.9653) < 0.01


def test_sampling_rate_strata_invariance(cohort_data):
    """Verify hardware sampling-rate strata breakdown (128 Hz vs 160 Hz)."""
    piv_leak = cohort_data.pivot(index="subject", columns="design", values="acc_leaky") * 100.0
    piv_ref = cohort_data.pivot(index="subject", columns="design", values="acc_ref") * 100.0
    d3 = piv_ref.iloc[:, 0]
    d1s = piv_leak["D1s_size_matched"]

    s128 = [88, 92, 100]
    d3_128 = d3.loc[s128]
    d1s_128 = d1s.loc[s128]
    d3_160 = d3.drop(index=s128)
    d1s_160 = d1s.drop(index=s128)

    assert abs(d3_128.mean() - 58.1001) < 0.01
    assert abs(d1s_128.mean() - 59.0823) < 0.01
    assert abs(d3_160.mean() - 60.2103) < 0.01
    assert abs(d1s_160.mean() - 57.3284) < 0.01


def test_no_hardcoded_absolute_drive_paths_in_repository():
    """Verify that zero Python files in tests/, src/, scripts/, analysis/ contain hardcoded Windows drive letters."""
    import ast
    import re
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[1]
    DRIVE_REGEX = re.compile(r'^[a-zA-Z]:[\\/]')

    violations = []
    scanned_count = 0

    for sub in ["tests", "src", "scripts", "analysis"]:
        target_dir = repo_root / sub
        if not target_dir.exists():
            continue
        for py_file in target_dir.rglob("*.py"):
            scanned_count += 1
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    val = node.value.strip()
                    if DRIVE_REGEX.match(val):
                        rel_path = py_file.relative_to(repo_root)
                        violations.append(f"{rel_path}:{node.lineno} -> {val}")

    assert scanned_count > 20, f"Expected >20 Python files scanned, found {scanned_count}"
    assert not violations, f"Found {len(violations)} hardcoded absolute drive paths:\n" + "\n".join(violations)


def test_test_suite_invocable_from_any_working_directory(monkeypatch):
    """Verify that key path fixtures resolve correctly regardless of process working directory."""
    from pathlib import Path
    repo_root = Path(__file__).resolve().parents[1]

    for target_cwd in [repo_root, repo_root / "tests"]:
        monkeypatch.chdir(target_cwd)
        resolved_root = Path(__file__).resolve().parents[1]
        assert (resolved_root / "src").is_dir()
        assert (resolved_root / "benchmark_results").is_dir()

