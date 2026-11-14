#!/usr/bin/env python3
"""
recalculate_all_stats.py — Validated Participant-Level Statistical Recalculation
and Sensitivity Audit Script for LeakCheck (PhysioNet EEGMMIDB Benchmark).

Usage:
    python3 recalculate_all_stats.py [path/to/inflation_by_subject.csv]
"""
import os
import platform
import sys
import numpy as np
import pandas as pd
import scipy
import scipy.stats as stats


REQUIRED_DESIGNS = ["D1s_size_matched", "D1m_matched_k", "P1_csp_on_all"]
REQUIRED_COLUMNS = {"subject", "design", "acc_ref", "acc_leaky", "delta_pp"}


def resolve_csv_path() -> str:
    if len(sys.argv) > 1:
        cand = sys.argv[1]
        if os.path.isfile(cand):
            return cand
        raise FileNotFoundError(f"Specified CSV file does not exist: {cand}")
    candidates = [
        "inflation_by_subject.csv",
        os.path.join("benchmark_results", "physionet_v1_1", "inflation_by_subject.csv"),
        os.path.join(os.path.dirname(__file__), "inflation_by_subject.csv"),
        "/working_dir/c_2e17a9d5e1c4bb66/artifacts/file_generation/ttl=63d/intermediate/inflation_by_subject.csv",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    raise FileNotFoundError(
        "Could not locate inflation_by_subject.csv. Pass its path as: "
        "python3 recalculate_all_stats.py /path/to/inflation_by_subject.csv"
    )


def validate_input_dataframe(df: pd.DataFrame) -> int:
    missing_cols = REQUIRED_COLUMNS - set(df.columns)
    if missing_cols:
        raise ValueError(f"Input CSV is missing required columns: {sorted(missing_cols)}")

    if df.empty:
        raise ValueError("Input CSV is empty.")

    for col in ["acc_ref", "acc_leaky", "delta_pp"]:
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise TypeError(f"Column '{col}' must be numeric, got {df[col].dtype}")
        if not np.all(np.isfinite(df[col].to_numpy())):
            raise ValueError(f"Column '{col}' contains NaN or infinite values.")

    for col in ["acc_ref", "acc_leaky"]:
        vals = df[col].to_numpy()
        if np.any((vals < 0.0) | (vals > 1.0)):
            raise ValueError(f"Column '{col}' has values outside [0.0, 1.0].")

    dup_mask = df.duplicated(subset=["subject", "design"], keep=False)
    if dup_mask.any():
        dups = df.loc[dup_mask, ["subject", "design"]].to_dict(orient="records")
        raise ValueError(f"Duplicate (subject, design) rows detected: {dups}")

    present_designs = sorted(df["design"].unique())
    for req_d in REQUIRED_DESIGNS:
        if req_d not in present_designs:
            raise ValueError(f"Required design '{req_d}' not found in CSV designs: {present_designs}")

    # Verify each design has the exact same set of participant IDs
    base_subjects = set(df[df["design"] == REQUIRED_DESIGNS[0]]["subject"].unique())
    for d_name in REQUIRED_DESIGNS[1:]:
        d_subjects = set(df[df["design"] == d_name]["subject"].unique())
        if d_subjects != base_subjects:
            diff_sym = base_subjects.symmetric_difference(d_subjects)
            raise ValueError(f"Subject ID mismatch between '{REQUIRED_DESIGNS[0]}' and '{d_name}': {sorted(diff_sym)}")

    # Verify delta_pp agrees with (acc_leaky - acc_ref) * 100 within tolerance
    computed_delta = (df["acc_leaky"].to_numpy() - df["acc_ref"].to_numpy()) * 100.0
    max_delta_err = float(np.max(np.abs(df["delta_pp"].to_numpy() - computed_delta)))
    if max_delta_err > 1e-6:
        raise ValueError(f"delta_pp disagrees with (acc_leaky - acc_ref)*100 by {max_delta_err:.3e} pp (> 1e-6 pp).")

    # Verify D3_loro reference accuracy (acc_ref) is identical across contrast rows for each subject
    ref_piv = df.pivot(index="subject", columns="design", values="acc_ref")
    max_ref_spread = float(np.max(ref_piv.max(axis=1) - ref_piv.min(axis=1)))
    if max_ref_spread > 1e-12:
        raise ValueError(f"Inconsistent acc_ref across designs for the same subject (max spread = {max_ref_spread:.3e}).")

    return len(base_subjects)


def hodges_lehmann(x: np.ndarray) -> float:
    x = np.asarray(x, dtype=np.float64)
    n = len(x)
    if n == 0:
        raise ValueError("Cannot compute Hodges-Lehmann on empty array.")
    i, j = np.triu_indices(n)
    return float(np.median((x[i] + x[j]) / 2.0))


def hl_stat_vectorized(x: np.ndarray, axis: int = -1) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        return np.asarray(hodges_lehmann(x))
    n = x.shape[-1]
    i, j = np.triu_indices(n)
    return np.median((x[..., i] + x[..., j]) / 2.0, axis=-1)


def compute_bca_ci(d: np.ndarray, seed: int = 0, n_resamples: int = 10000):
    d = np.asarray(d, dtype=np.float64)
    if np.all(d == d[0]):
        val = float(d[0])
        return val, val, "degenerate_constant"
    try:
        res = stats.bootstrap(
            (d,),
            hl_stat_vectorized,
            n_resamples=n_resamples,
            confidence_level=0.95,
            method="BCa",
            random_state=np.random.RandomState(seed),
        )
        low = float(res.confidence_interval.low)
        high = float(res.confidence_interval.high)
        if np.isnan(low) or np.isnan(high):
            raise FloatingPointError("BCa returned NaN bounds.")
        return low, high, "BCa"
    except (ValueError, FloatingPointError, ZeroDivisionError) as num_exc:
        rng = np.random.default_rng(seed)
        n = len(d)
        idx = rng.integers(0, n, size=(n_resamples, n))
        boots = hl_stat_vectorized(d[idx], axis=-1)
        low, high = np.percentile(boots, [2.5, 97.5])
        return float(low), float(high), f"percentile_fallback ({type(num_exc).__name__}: {num_exc})"


def safe_wilcoxon(d: np.ndarray, zero_method: str = "wilcox"):
    d = np.asarray(d, dtype=np.float64)
    if np.all(d == 0.0):
        return 0.0, 1.0
    res = stats.wilcoxon(d, zero_method=zero_method, alternative="two-sided")
    return float(res.statistic), float(res.pvalue)


def rank_biserial_paired(d: np.ndarray) -> float:
    d_nz = d[d != 0.0]
    n_eff = len(d_nz)
    if n_eff == 0:
        return 0.0
    ranks = stats.rankdata(np.abs(d_nz))
    w_pos = float(np.sum(ranks[d_nz > 0]))
    w_neg = float(np.sum(ranks[d_nz < 0]))
    return (w_pos - w_neg) / (n_eff * (n_eff + 1.0) / 2.0)


def tost_paired_mean(d: np.ndarray, margin: float = 2.0, alpha: float = 0.05):
    d = np.asarray(d, dtype=np.float64)
    n = len(d)
    mean_d = float(np.mean(d))
    sd_d = float(np.std(d, ddof=1))
    if sd_d == 0.0:
        in_bounds = abs(mean_d) < margin
        return (0.0 if in_bounds else 1.0), mean_d, mean_d
    se_d = sd_d / np.sqrt(n)
    df_t = n - 1
    t_low = (mean_d - (-margin)) / se_d
    p_low = float(1.0 - stats.t.cdf(t_low, df=df_t))
    t_high = (mean_d - margin) / se_d
    p_high = float(stats.t.cdf(t_high, df=df_t))
    p_tost = max(p_low, p_high)
    t_crit_90 = float(stats.t.ppf(1.0 - alpha, df=df_t))
    ci90_low = mean_d - t_crit_90 * se_d
    ci90_high = mean_d + t_crit_90 * se_d
    return p_tost, ci90_low, ci90_high


def holm_adjust(pvals):
    pvals = np.asarray(pvals, dtype=np.float64)
    m = len(pvals)
    order = np.argsort(pvals)
    adj = np.empty(m, dtype=np.float64)
    running_max = 0.0
    for rank_idx, orig_idx in enumerate(order):
        scaled = pvals[orig_idx] * (m - rank_idx)
        running_max = max(running_max, scaled)
        adj[orig_idx] = min(1.0, running_max)
    return adj


def main():
    csv_path = resolve_csv_path()
    df = pd.read_csv(csv_path)
    n_subjects = validate_input_dataframe(df)

    print("=" * 88)
    print("LEAKCHECK STATISTICAL RECALCULATION & VALIDATION REPORT")
    print("=" * 88)
    print(f"Input CSV Path      : {os.path.abspath(csv_path)}")
    print(f"Environment         : Python {platform.python_version()} | NumPy {np.__version__} | pandas {pd.__version__} | SciPy {scipy.__version__}")
    print(f"Validated Cohort N  : {n_subjects} unique participants ({len(df)} total subject-contrast rows)")
    print("Primary Conventions : Tie tolerance |Delta| <= 1e-9 pp | Wilcoxon zero_method='wilcox' | BCa bootstrap (10,000 resamples, seed=0) | Holm FWER (m=3 primary, m=4 exploratory)")
    print("-" * 88)

    # 1. Cohort membership audit against 1..109
    present_ids = sorted(int(x) for x in df["subject"].unique())
    expected_109 = set(range(1, 110))
    absent_ids = sorted(expected_109 - set(present_ids))
    print(f"1. COHORT AUDIT (vs. S001..S109):")
    print(f"   - Absent Subject IDs ({len(absent_ids)}): {[f'S{i:03d}' for i in absent_ids]}")
    for check_id in [88, 92, 100, 104]:
        rows = df[
            (df["subject"] == check_id)
            & (df["design"] == "D1s_size_matched")
        ]
        if rows.empty:
            print(f"   - Subject S{check_id:03d}: no matching D1s row")
        elif len(rows) > 1:
            raise ValueError(f"Duplicate D1s rows for S{check_id:03d}")
        else:
            ref_val = float(rows["acc_ref"].iloc[0]) * 100.0
            print(
                f"   - Subject S{check_id:03d}: present "
                f"(D3_loro accuracy = {ref_val:.2f}%)"
            )

    # 2. Protocol-level accuracy distributions
    print("\n2. PARTICIPANT-LEVEL DECODING ACCURACY DISTRIBUTIONS (N = " + str(n_subjects) + "):")
    d1s_df = df[df["design"] == "D1s_size_matched"].sort_values("subject").reset_index(drop=True)
    d1m_df = df[df["design"] == "D1m_matched_k"].sort_values("subject").reset_index(drop=True)
    p1_df  = df[df["design"] == "P1_csp_on_all"].sort_values("subject").reset_index(drop=True)

    prot_series = [
        ("D3_loro (Ref.)", d1s_df["subject"].to_numpy(), d1s_df["acc_ref"].to_numpy() * 100.0),
        ("D1s_size_matched", d1s_df["subject"].to_numpy(), d1s_df["acc_leaky"].to_numpy() * 100.0),
        ("D1m_matched_k", d1m_df["subject"].to_numpy(), d1m_df["acc_leaky"].to_numpy() * 100.0),
        ("P1_csp_on_all", p1_df["subject"].to_numpy(), p1_df["acc_leaky"].to_numpy() * 100.0),
    ]
    for pname, sids, vals in prot_series:
        mean_v = float(np.mean(vals))
        sd_v = float(np.std(vals, ddof=1))
        q25, med_v, q75 = [float(x) for x in np.percentile(vals, [25, 50, 75])]
        iqr_v = q75 - q25
        min_idx = int(np.argmin(vals))
        max_idx = int(np.argmax(vals))
        print(
            f"   - {pname:18s}: Mean={mean_v:6.2f}% (SD={sd_v:5.2f}%) | "
            f"Median={med_v:6.2f}% (IQR={iqr_v:5.2f}%: {q25:.2f}%-{q75:.2f}%) | "
            f"Min={vals[min_idx]:6.2f}% (S{int(sids[min_idx]):03d}) | "
            f"Max={vals[max_idx]:6.2f}% (S{int(sids[max_idx]):03d})"
        )

    # 3. Validated 1-to-1 join for exploratory D1s vs D1m contrast
    merged_d1 = pd.merge(
        d1s_df[["subject", "acc_leaky", "acc_ref"]],
        d1m_df[["subject", "acc_leaky"]],
        on="subject",
        how="inner",
        suffixes=("_d1s", "_d1m"),
        validate="one_to_one",
    )
    if len(merged_d1) != n_subjects:
        raise ValueError(f"1-to-1 merge produced {len(merged_d1)} rows, expected {n_subjects}.")
    merged_d1["delta_pp"] = (merged_d1["acc_leaky_d1s"] - merged_d1["acc_leaky_d1m"]) * 100.0

    contrasts = [
        ("D1s_size_matched vs. D3_loro", "Primary (m=3)", d1s_df["subject"].to_numpy(), d1s_df["delta_pp"].to_numpy(), d1s_df["acc_leaky"].to_numpy(), d1s_df["acc_ref"].to_numpy()),
        ("D1m_matched_k vs. D3_loro", "Primary (m=3)", d1m_df["subject"].to_numpy(), d1m_df["delta_pp"].to_numpy(), d1m_df["acc_leaky"].to_numpy(), d1m_df["acc_ref"].to_numpy()),
        ("P1_csp_on_all vs. D3_loro", "Primary (m=3)", p1_df["subject"].to_numpy(), p1_df["delta_pp"].to_numpy(), p1_df["acc_leaky"].to_numpy(), p1_df["acc_ref"].to_numpy()),
        ("D1s_size_matched vs. D1m_matched_k", "Exploratory", merged_d1["subject"].to_numpy(), merged_d1["delta_pp"].to_numpy(), merged_d1["acc_leaky_d1s"].to_numpy(), merged_d1["acc_leaky_d1m"].to_numpy()),
    ]

    results = []
    for cname, tier, sids, d_raw, acc_a, acc_b in contrasts:
        d_tol = np.where(np.abs(d_raw) <= 1e-9, 0.0, d_raw)
        n_pos_tol = int(np.sum(d_tol > 0.0))
        n_neg_tol = int(np.sum(d_tol < 0.0))
        n_tie_tol = int(np.sum(d_tol == 0.0))
        tie_ids_tol = [f"S{int(sids[i]):03d} ({d_raw[i]:+.2e} pp)" for i in range(len(sids)) if d_tol[i] == 0.0]

        n_pos_raw = int(np.sum(d_raw > 0.0))
        n_neg_raw = int(np.sum(d_raw < 0.0))
        n_tie_raw = int(np.sum(d_raw == 0.0))

        mean_d = float(np.mean(d_raw))
        sd_d = float(np.std(d_raw, ddof=1))
        med_d = float(np.median(d_raw))
        hl_d = hodges_lehmann(d_raw)
        bca_low, bca_high, ci_method = compute_bca_ci(d_raw, seed=0, n_resamples=10000)

        w_wilcox_tol, p_wilcox_tol = safe_wilcoxon(d_tol, zero_method="wilcox")
        w_pratt_tol, p_pratt_tol   = safe_wilcoxon(d_tol, zero_method="pratt")
        w_wilcox_raw, p_wilcox_raw = safe_wilcoxon(d_raw, zero_method="wilcox")

        dz = mean_d / sd_d if sd_d > 0 else 0.0
        rrb_tol = rank_biserial_paired(d_tol)
        rrb_raw = rank_biserial_paired(d_raw)

        p_tost, ci90_low, ci90_high = tost_paired_mean(d_raw, margin=2.0, alpha=0.05)

        eps = 1e-5
        pa = np.clip(acc_a, eps, 1.0 - eps)
        pb = np.clip(acc_b, eps, 1.0 - eps)
        logit_a = np.log(pa / (1.0 - pa))
        logit_b = np.log(pb / (1.0 - pb))
        _, p_logit_t = stats.ttest_rel(logit_a, logit_b)
        _, p_direct_t = stats.ttest_rel(acc_a * 100.0, acc_b * 100.0)

        results.append({
            "name": cname,
            "tier": tier,
            "mean": mean_d,
            "sd": sd_d,
            "median": med_d,
            "hl": hl_d,
            "bca_low": bca_low,
            "bca_high": bca_high,
            "ci_method": ci_method,
            "n_pos_tol": n_pos_tol,
            "n_neg_tol": n_neg_tol,
            "n_tie_tol": n_tie_tol,
            "tie_ids_tol": tie_ids_tol,
            "n_pos_raw": n_pos_raw,
            "n_neg_raw": n_neg_raw,
            "n_tie_raw": n_tie_raw,
            "w_wilcox_tol": w_wilcox_tol,
            "p_wilcox_tol": p_wilcox_tol,
            "w_pratt_tol": w_pratt_tol,
            "p_pratt_tol": p_pratt_tol,
            "w_wilcox_raw": w_wilcox_raw,
            "p_wilcox_raw": p_wilcox_raw,
            "dz": dz,
            "rrb_tol": rrb_tol,
            "rrb_raw": rrb_raw,
            "p_tost": p_tost,
            "ci90_low": ci90_low,
            "ci90_high": ci90_high,
            "p_logit_t": float(p_logit_t),
            "p_direct_t": float(p_direct_t),
        })

    # Holm adjustments for m=3 primary contrasts and m=4 extended contrasts
    p_m3_wilcox_tol = holm_adjust([r["p_wilcox_tol"] for r in results[:3]])
    p_m3_pratt_tol  = holm_adjust([r["p_pratt_tol"] for r in results[:3]])
    p_m3_wilcox_raw = holm_adjust([r["p_wilcox_raw"] for r in results[:3]])

    p_m4_wilcox_tol = holm_adjust([r["p_wilcox_tol"] for r in results])
    p_m4_pratt_tol  = holm_adjust([r["p_pratt_tol"] for r in results])
    p_m4_wilcox_raw = holm_adjust([r["p_wilcox_raw"] for r in results])

    print("\n3. PAIRED CONTRAST RESULTS (PRIMARY & SENSITIVITY):")
    for idx, r in enumerate(results):
        print("-" * 88)
        print(f"Contrast [{idx+1}] : {r['name']} ({r['tier']})")
        print(f"   - Counts (|Delta| <= 1e-9 pp) : {r['n_pos_tol']} higher (+), {r['n_neg_tol']} lower (-), {r['n_tie_tol']} tied (0) -> {r['tie_ids_tol']}")
        print(f"   - Counts (Raw float == 0)     : {r['n_pos_raw']} higher (+), {r['n_neg_raw']} lower (-), {r['n_tie_raw']} tied (0)")
        print(f"   - Mean Delta (SD) / Median    : {r['mean']:+.4f} pp (SD={r['sd']:.4f} pp) | Median={r['median']:+.4f} pp")
        print(f"   - Primary HL Shift & 95% CI   : {r['hl']:+.4f} pp [{r['bca_low']:+.4f}, {r['bca_high']:+.4f}] pp (method={r['ci_method']})")
        if idx < 3:
            print(f"   - Primary Wilcoxon (tol 1e-9) : W={r['w_wilcox_tol']:.1f}, p_raw={r['p_wilcox_tol']:.4e}, p_Holm(m=3)={p_m3_wilcox_tol[idx]:.4e}")
            print(f"   - Sensitivity Pratt (tol 1e-9): W={r['w_pratt_tol']:.1f}, p_raw={r['p_pratt_tol']:.4e}, p_Holm(m=3)={p_m3_pratt_tol[idx]:.4e}")
            print(f"   - Sensitivity Raw Float (==0) : W={r['w_wilcox_raw']:.1f}, p_raw={r['p_wilcox_raw']:.4e}, p_Holm(m=3)={p_m3_wilcox_raw[idx]:.4e}")
        else:
            print(f"   - Exploratory Wilcoxon (1e-9) : W={r['w_wilcox_tol']:.1f}, p_raw={r['p_wilcox_tol']:.4e}, p_Holm(m=4)={p_m4_wilcox_tol[idx]:.4e}")
            print(f"   - Sensitivity Pratt (tol 1e-9): W={r['w_pratt_tol']:.1f}, p_raw={r['p_pratt_tol']:.4e}, p_Holm(m=4)={p_m4_pratt_tol[idx]:.4e}")
            print(f"   - Sensitivity Raw Float (==0) : W={r['w_wilcox_raw']:.1f}, p_raw={r['p_wilcox_raw']:.4e}, p_Holm(m=4)={p_m4_wilcox_raw[idx]:.4e}")
        print(f"   - Effect Sizes & Parametric   : Cohen d_z={r['dz']:+.4f} | r_rb(1e-9)={r['rrb_tol']:+.4f} | r_rb(raw)={r['rrb_raw']:+.4f} | Logit t p={r['p_logit_t']:.4e} | Direct t p={r['p_direct_t']:.4e}")
        print(f"   - Exploratory TOST (+/-2.0pp) : p_TOST={r['p_tost']:.4f}, 90% Mean CI=[{r['ci90_low']:+.2f}, {r['ci90_high']:+.2f}] pp")
    print("=" * 88)


if __name__ == "__main__":
    main()
