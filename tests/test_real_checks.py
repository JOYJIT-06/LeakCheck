"""Checks against the real-data tables supplied with the code review (docs/real_eeg_checks)."""
from pathlib import Path

import pandas as pd

from emi import diagnostics as dg

HERE = Path(__file__).resolve().parents[1] / "docs" / "real_eeg_checks"


def test_exact_runs_test_matches_the_real_permutation_p_values():
    df = pd.read_csv(HERE / "label_runs_test_real.csv")
    for _, r in df.iterrows():
        # exact p from the distribution of the number of runs given (n1, n0) and the observed number of runs
        n1, n0, obs = int(r["n1"]), int(r["n"]) - int(r["n1"]), int(r["runs"])
        pm = dg._runs_pmf(n1, n0)
        mean = sum(k * v for k, v in pm.items())
        p = sum(v for k, v in pm.items() if abs(k - mean) >= abs(obs - mean) - 1e-12)
        assert abs(p - r["p_perm"]) < 0.005, (r["subject"], r["run"], p, r["p_perm"])


def test_review_table_statements_hold():
    df = pd.read_csv(HERE / "label_runs_test_real.csv")
    assert int((df["p_normal"] < 0.05).sum()) == 5 and int((df["p_perm"] < 0.05).sum()) == 5 and len(df) == 15
    c = pd.read_csv(HERE / "csp_implementation_loro_accuracy_real.csv")
    assert abs(c["rank_safe_CSP"].mean() - 0.644) < 0.002 and abs(c["MNE_CSP"].mean() - 0.643) < 0.002
    spread = (c[["numpy_SimpleCSP", "rank_safe_CSP", "MNE_CSP"]].max(axis=1)
              - c[["numpy_SimpleCSP", "rank_safe_CSP", "MNE_CSP"]].min(axis=1))
    assert spread.max() > 0.25          # single subjects differ by about 30 points between implementations
