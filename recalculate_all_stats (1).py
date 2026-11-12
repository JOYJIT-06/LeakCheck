#!/usr/bin/env python3
"""
recalculate_all_stats.py
========================
Standalone verification and statistical reconciliation script for the LeakCheck
PhysioNet EEGMMIDB V1.1 benchmark (N = 105 participants, 315 subject-contrast rows).

Works out-of-the-box from:
  1. The LeakCheck repository root (reads benchmark_results/physionet_v1_1/inflation_by_subject.csv)
  2. The same directory as inflation_by_subject.csv (reads ./inflation_by_subject.csv)
  3. Any custom path passed via CLI: python3 recalculate_all_stats.py /path/to/inflation_by_subject.csv

What this script verifies and reconciles:
  - Exact cohort accounting (105 retained subjects vs. 4 absent IDs: S044, S069, S086, S091;
    confirms S088, S092, S100, S104 are present in inflation_by_subject.csv).
  - Participant-level decoding accuracy distributions (Mean, SD, Median, IQR, Q1, Q3, Min, Max
    with exact Subject IDs) for D3_loro, D1s_size_matched, D1m_matched_k, and P1_csp_on_all.
  - Directional participant counts (higher +, lower -, tied 0) under BOTH raw floating-point
    equality (delta_pp == 0.0) and a documented floating-point tie tolerance (|delta_pp| <= 1e-9 pp),
    listing every tied or opposite-direction subject ID.
  - Paired location shifts (Hodges-Lehmann estimator), 95% BCa bootstrap CIs (10,000 resamples,
    seed = 0), Wilcoxon signed-rank tests under BOTH zero_method="wilcox" (SciPy default in
    src/emi/leakstats.py) and zero_method="pratt" (explaining the README vs. inflation_table.csv
    difference), Holm-Bonferroni multiplicity correction (m = 3 and m = 4), Cohen's d_z,
    rank-biserial correlation r_rb, logit paired t-test, and exploratory paired TOST (±2.0 pp).
  - Direct participant-joined contrast between D1s_size_matched and D1m_matched_k (joined by
    subject ID across N = 105 participants).
"""

import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats


def locate_csv() -> Path:
    """Locate inflation_by_subject.csv across CLI args, local dir, or repo structure."""
    candidates = []
    if len(sys.argv) > 1:
        candidates.append(Path(sys.argv[1]))
    script_dir = Path(__file__).resolve().parent
    cwd = Path.cwd()
    for base in [cwd, script_dir]:
        candidates.extend([
            base / "inflation_by_subject.csv",
            base / "benchmark_results" / "physionet_v1_1" / "inflation_by_subject.csv",
            base / "artifacts" / "file_generation" / "ttl=63d" / "intermediate" / "inflation_by_subject.csv",
        ])
    for cand in candidates:
        if cand.is_file():
            return cand
    raise FileNotFoundError(
        "Could not find 'inflation_by_subject.csv'. Place this script in the repository root "
        "or in the same folder as 'inflation_by_subject.csv', or pass its path as an argument."
    )


def hodges_lehmann(d: np.ndarray) -> float:
    """One-sample Hodges-Lehmann estimator (median of all N(N+1)/2 Walsh averages)."""
    d = np.asarray(d, dtype=float)
    n = len(d)
    idx_i, idx_j = np.triu_indices(n)
    return float(np.median(0.5 * (d[idx_i] + d[idx_j])))


def bca_ci(d: np.ndarray, seed: int = 0, n_resamples: int = 10000):
    """95% BCa bootstrap confidence interval with percentile fallback (matching src/emi/leakstats.py)."""
    d = np.asarray(d, dtype=float)
    try:
        res = stats.bootstrap(
            (d,),
            statistic=hodges_lehmann,
            n_resamples=n_resamples,
            confidence_level=0.95,
            method="BCa",
            random_state=seed,
        )
        low, high = float(res.confidence_interval.low), float(res.confidence_interval.high)
        if np.isnan(low) or np.isnan(high):
            raise ValueError("BCa returned NaN")
        return low, high, "BCa"
    except Exception:
        rng = np.random.default_rng(seed)
        boots = np.array([
            hodges_lehmann(rng.choice(d, size=len(d), replace=True))
            for _ in range(n_resamples)
        ])
        low, high = np.percentile(boots, [2.5, 97.5])
        return float(low), float(high), "percentile"


def rank_biserial_signed_rank(d: np.ndarray, tol: float = 0.0) -> float:
    """Matched-pairs rank-biserial correlation r_rb = (W+ - W-) / (n_nz * (n_nz + 1) / 2)."""
    d = np.asarray(d, dtype=float)
    d_nz = d[np.abs(d) > tol]
    n_nz = len(d_nz)
    if n_nz == 0:
        return 0.0
    ranks = stats.rankdata(np.abs(d_nz))
    w_pos = float(np.sum(ranks[d_nz > 0]))
    w_neg = float(np.sum(ranks[d_nz < 0]))
    return (w_pos - w_neg) / (n_nz * (n_nz + 1) / 2.0)


def logit_paired_t(acc_leaky: np.ndarray, acc_ref: np.ndarray, eps: float = 0.005) -> float:
    """Paired t-test on logit-transformed accuracies (matching src/emi/leakstats.py)."""
    p1 = np.clip(np.asarray(acc_leaky, dtype=float), eps, 1.0 - eps)
    p0 = np.clip(np.asarray(acc_ref, dtype=float), eps, 1.0 - eps)
    l1 = np.log(p1 / (1.0 - p1))
    l0 = np.log(p0 / (1.0 - p0))
    return float(stats.ttest_rel(l1, l0).pvalue)


def tost_paired(d: np.ndarray, margin: float = 2.0):
    """Exploratory paired Two One-Sided Tests (TOST) on arithmetic mean difference (±margin pp)."""
    d = np.asarray(d, dtype=float)
    n = len(d)
    se = d.std(ddof=1) / np.sqrt(n)
    p_lower = float(1.0 - stats.t.cdf((d.mean() + margin) / se, n - 1))
    p_upper = float(stats.t.cdf((d.mean() - margin) / se, n - 1))
    t_crit90 = float(stats.t.ppf(0.95, n - 1))
    ci90 = (float(d.mean() - t_crit90 * se), float(d.mean() + t_crit90 * se))
    return max(p_lower, p_upper), ci90


def holm_adjust(pvals: dict) -> dict:
    """Holm-Bonferroni step-down adjustment across a dictionary of p-values."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    adj = {}
    running_max = 0.0
    for idx, (k, p) in enumerate(items):
        val = min(1.0, p * (m - idx))
        running_max = max(running_max, val)
        adj[k] = running_max
    return adj


def main():
    csv_path = locate_csv()
    df = pd.read_csv(csv_path)
    print("=" * 88)
    print(f"LEAKCHECK PHYSIONET V1.1 STATISTICAL VERIFICATION REPORT")
    print(f"Source file: {csv_path}")
    print(f"Total rows: {len(df)} | Unique participants: {df['subject'].nunique()}")
    print("=" * 88)

    # 1. Cohort Accounting
    present_ids = set(df["subject"].unique())
    missing_ids = sorted(set(range(1, 110)) - present_ids)
    print("\n1. COHORT ACCOUNTING (109 REQUESTED -> 105 ANALYZED)")
    print(f"   - Absent subject IDs (n = {len(missing_ids)}): {[f'S{i:03d}' for i in missing_ids]}")
    for check_id in [88, 92, 100, 104]:
        is_in = check_id in present_ids
        ref_val = df[(df["subject"] == check_id) & (df["design"] == "D1s_size_matched")]["acc_ref"].iloc[0] * 100.0
        print(f"   - Subject S{check_id:03d} present in inflation_by_subject.csv? {is_in} (D3_loro acc = {ref_val:.2f}%)")

    # 2. Protocol-Level Accuracy Distributions
    print("\n2. PARTICIPANT-LEVEL DECODING ACCURACY DISTRIBUTIONS (N = 105)")
    d1s_df = df[df["design"] == "D1s_size_matched"].sort_values("subject").reset_index(drop=True)
    d1m_df = df[df["design"] == "D1m_matched_k"].sort_values("subject").reset_index(drop=True)
    p1_df  = df[df["design"] == "P1_csp_on_all"].sort_values("subject").reset_index(drop=True)

    protocols = [
        ("D3_loro (Reference)", d1s_df["acc_ref"].to_numpy() * 100.0, d1s_df["subject"].to_numpy()),
        ("D1s_size_matched",    d1s_df["acc_leaky"].to_numpy() * 100.0, d1s_df["subject"].to_numpy()),
        ("D1m_matched_k",       d1m_df["acc_leaky"].to_numpy() * 100.0, d1m_df["subject"].to_numpy()),
        ("P1_csp_on_all",       p1_df["acc_leaky"].to_numpy() * 100.0,  p1_df["subject"].to_numpy()),
    ]
    for name, acc, subs in protocols:
        q25, q75 = np.percentile(acc, [25, 75])
        min_idx, max_idx = int(np.argmin(acc)), int(np.argmax(acc))
        max_subs = [f"S{int(s):03d}" for s in subs[np.isclose(acc, acc[max_idx], atol=1e-9)]]
        print(
            f"   - {name:20s}: Mean = {acc.mean():6.2f}% (SD = {acc.std(ddof=1):5.2f}%) | "
            f"Median = {np.median(acc):6.2f}% (IQR = {q75-q25:5.2f}%: {q25:5.2f}%-{q75:5.2f}%) | "
            f"Min = {acc[min_idx]:5.2f}% (S{int(subs[min_idx]):03d}) | "
            f"Max = {acc[max_idx]:6.2f}% ({', '.join(max_subs)})"
        )

    # 3. Paired Contrasts vs. D3_loro + Direct ID-Joined D1s vs. D1m
    assert (d1s_df["subject"].to_numpy() == d1m_df["subject"].to_numpy()).all()
    diff_d1s_d1m = (d1s_df["acc_leaky"].to_numpy() - d1m_df["acc_leaky"].to_numpy()) * 100.0

    contrasts = [
        ("D1s_size_matched vs. D3_loro", d1s_df["delta_pp"].to_numpy(), d1s_df["acc_leaky"].to_numpy(), d1s_df["acc_ref"].to_numpy(), d1s_df["subject"].to_numpy()),
        ("D1m_matched_k vs. D3_loro",    d1m_df["delta_pp"].to_numpy(), d1m_df["acc_leaky"].to_numpy(), d1m_df["acc_ref"].to_numpy(), d1m_df["subject"].to_numpy()),
        ("P1_csp_on_all vs. D3_loro",    p1_df["delta_pp"].to_numpy(),  p1_df["acc_leaky"].to_numpy(),  p1_df["acc_ref"].to_numpy(),  p1_df["subject"].to_numpy()),
        ("D1s vs. D1m (Direct Joined)",  diff_d1s_d1m,                  d1s_df["acc_leaky"].to_numpy(), d1m_df["acc_leaky"].to_numpy(), d1s_df["subject"].to_numpy()),
    ]

    tol = 1e-9
    raw_wilcox_p = {}
    tol_wilcox_p = {}
    tol_pratt_p = {}
    results_cache = {}

    for label, d, a_l, a_r, subs in contrasts:
        d_clean = np.where(np.abs(d) <= tol, 0.0, d)
        w_raw_w = stats.wilcoxon(d, zero_method="wilcox")
        w_raw_p = stats.wilcoxon(d, zero_method="pratt")
        w_tol_w = stats.wilcoxon(d_clean, zero_method="wilcox")
        w_tol_p = stats.wilcoxon(d_clean, zero_method="pratt")

        raw_wilcox_p[label] = float(w_raw_w.pvalue)
        tol_wilcox_p[label] = float(w_tol_w.pvalue)
        tol_pratt_p[label]  = float(w_tol_p.pvalue)

        hl = hodges_lehmann(d)
        ci_l, ci_h, ci_meth = bca_ci(d, seed=0)
        tost_p, ci90 = tost_paired(d, margin=2.0)
        dz = float(d.mean() / d.std(ddof=1))
        r_rb = rank_biserial_signed_rank(d, tol=tol)
        p_logit = logit_paired_t(a_l, a_r)
        p_ttest = float(stats.ttest_1samp(d, 0.0).pvalue)

        pos_raw, neg_raw, tie_raw = int(np.sum(d > 0)), int(np.sum(d < 0)), int(np.sum(d == 0))
        pos_tol, neg_tol, tie_tol = int(np.sum(d > tol)), int(np.sum(d < -tol)), int(np.sum(np.abs(d) <= tol))
        tie_sub_ids = [f"S{int(s):03d} ({val:+.2e} pp)" for s, val in zip(subs[np.abs(d) <= tol], d[np.abs(d) <= tol])]
        neg_sub_ids = [f"S{int(s):03d} ({val:+.2f} pp)" for s, val in zip(subs[d < -tol], d[d < -tol])]

        results_cache[label] = {
            "mean": float(d.mean()), "sd": float(d.std(ddof=1)), "median": float(np.median(d)),
            "hl": hl, "ci_l": ci_l, "ci_h": ci_h, "ci_meth": ci_meth,
            "dz": dz, "r_rb": r_rb, "p_logit": p_logit, "p_ttest": p_ttest,
            "tost_p": tost_p, "ci90": ci90,
            "w_raw_w": w_raw_w, "w_raw_p": w_raw_p, "w_tol_w": w_tol_w, "w_tol_p": w_tol_p,
            "counts_raw": (pos_raw, neg_raw, tie_raw),
            "counts_tol": (pos_tol, neg_tol, tie_tol),
            "tie_sub_ids": tie_sub_ids,
            "neg_sub_ids": neg_sub_ids,
        }

    # Holm adjustments for m=3 (primary contrasts vs D3) and m=4 (including direct D1s vs D1m)
    m3_keys = [c[0] for c in contrasts[:3]]
    holm3_raw_w = holm_adjust({k: raw_wilcox_p[k] for k in m3_keys})
    holm3_tol_w = holm_adjust({k: tol_wilcox_p[k] for k in m3_keys})
    holm3_tol_p = holm_adjust({k: tol_pratt_p[k]  for k in m3_keys})

    holm4_tol_w = holm_adjust(tol_wilcox_p)
    holm4_tol_p = holm_adjust(tol_pratt_p)

    print("\n3. PAIRED CONTRASTS, DIRECTIONAL COUNTS & WILCOXON RECONCILIATION (N = 105)")
    for label, _, _, _, _ in contrasts:
        r = results_cache[label]
        p_pos, p_neg, p_tie = r["counts_tol"]
        r_pos, r_neg, r_tie = r["counts_raw"]
        print("-" * 88)
        print(f"   CONTRAST: {label}")
        print(f"   - Directional Counts (|d| <= 1e-9 pp): {p_pos} higher (+), {p_neg} lower (-), {p_tie} tied (0)")
        print(f"     Tied subject IDs (|d| <= 1e-9 pp):  {r['tie_sub_ids']}")
        if label == "P1_csp_on_all vs. D3_loro":
            print(f"     Lower subject IDs in P1 (d < 0):    {r['neg_sub_ids']}")
        print(f"   - Directional Counts (Raw float == 0): {r_pos} higher (+), {r_neg} lower (-), {r_tie} tied (0)")
        print(f"   - Mean diff = {r['mean']:+.4f} pp (SD = {r['sd']:.4f} pp) | Median diff = {r['median']:+.4f} pp")
        print(f"   - Hodges-Lehmann Shift = {r['hl']:+.4f} pp | 95% {r['ci_meth']} CI (seed=0) = [{r['ci_l']:+.4f}, {r['ci_h']:+.4f}] pp")
        print(f"   - Effect Sizes: Cohen's d_z = {r['dz']:+.4f} | Rank-Biserial r_rb = {r['r_rb']:+.4f}")
        print(f"   - Parametric Tests: Paired t-test p = {r['p_ttest']:.4e} | Logit paired t-test p = {r['p_logit']:.4e}")
        print(f"   - Exploratory TOST (±2.0 pp): p_TOST = {r['tost_p']:.4f} | 90% Mean-Diff CI = [{r['ci90'][0]:+.2f}, {r['ci90'][1]:+.2f}] pp")
        if label in m3_keys:
            print(f"   - Wilcoxon (raw float, wilcox): W = {r['w_raw_w'].statistic:6.1f}, p_raw = {r['w_raw_w'].pvalue:.4e}, p_Holm(m=3) = {holm3_raw_w[label]:.4e}")
            print(f"   - Wilcoxon (tol 1e-9,  wilcox): W = {r['w_tol_w'].statistic:6.1f}, p_raw = {r['w_tol_w'].pvalue:.4e}, p_Holm(m=3) = {holm3_tol_w[label]:.4e}")
            print(f"   - Wilcoxon (tol 1e-9,  pratt):  W = {r['w_tol_p'].statistic:6.1f}, p_raw = {r['w_tol_p'].pvalue:.4e}, p_Holm(m=3) = {holm3_tol_p[label]:.4e}")
        else:
            print(f"   - Wilcoxon (tol 1e-9,  wilcox): W = {r['w_tol_w'].statistic:6.1f}, p_raw = {r['w_tol_w'].pvalue:.4e}, p_Holm(m=4) = {holm4_tol_w[label]:.4e}")
            print(f"   - Wilcoxon (tol 1e-9,  pratt):  W = {r['w_tol_p'].statistic:6.1f}, p_raw = {r['w_tol_p'].pvalue:.4e}, p_Holm(m=4) = {holm4_tol_p[label]:.4e}")


if __name__ == "__main__":
    main()