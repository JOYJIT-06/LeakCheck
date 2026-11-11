"""Second-stage analysis of one or more LeakCheck result folders.

Example:  python scripts/analyze_leakcheck.py --results results_physionet results_bnci --out analysis
Writes: moderators (H2), random-effects meta-analysis across datasets, decoder ranking reversal,
performance strata (exploratory) and the subject count needed for a chosen smallest effect.
Every output is a CSV or JSON. Nothing here is a finding until you have run it on real data.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from emi import leakcheck as lc
from emi.leakstats import holm, random_effects_meta, ranking_reversal_bootstrap, required_subjects


def load(results):
    raws, infos = [], []
    for r in results:
        raws.append(pd.read_csv(Path(r) / "leakcheck_raw.csv"))
        infos.append(pd.read_csv(Path(r) / "subject_info.csv"))
    return pd.concat(raws, ignore_index=True), pd.concat(infos, ignore_index=True)


PRIMARY_MODERATOR = "label_lag1_autocorr"      # fixed in advance; the others are secondary and exploratory


def moderators(by, info):
    """H2: does inflation grow with label autocorrelation? Subject-level regression per contrast.

    Only `label_lag1_autocorr` is the pre-specified primary moderator. Holm correction is applied inside the
    primary family and inside the secondary family separately. Variables are subject-level, so n = subjects.
    """
    cols = ["dataset", "subject", PRIMARY_MODERATOR, "n_trials", "run_decode_acc", "dep_lag1"]
    m = by.merge(info[[c for c in cols if c in info.columns]], on=["dataset", "subject"], how="left")
    rows = []
    for (dec, design), g in m.groupby(["decoder", "design"]):
        for mod in (PRIMARY_MODERATOR, "n_trials", "run_decode_acc", "dep_lag1"):
            if mod not in g:
                continue
            h = g[["delta_pp", mod]].dropna()
            if len(h) >= 5 and h[mod].std() > 0:
                lr = stats.linregress(h[mod], h["delta_pp"])
                rows.append({"decoder": dec, "design": design, "moderator": mod, "primary": mod == PRIMARY_MODERATOR,
                             "n": len(h), "slope_pp_per_unit": lr.slope, "slope_se": lr.stderr, "p": lr.pvalue,
                             "spearman_rho": stats.spearmanr(h[mod], h["delta_pp"]).statistic})
    out = pd.DataFrame(rows)
    if len(out):
        out["p_holm"] = np.nan
        for flag in (True, False):
            idx = out.index[out["primary"] == flag]
            if len(idx):
                out.loc[idx, "p_holm"] = holm(out.loc[idx, "p"].to_numpy())
    return out


def meta(by):
    """Random-effects pooling across datasets (needs 2+ datasets with >= 3 subjects and non-zero variance).

    Uses the Hartung-Knapp interval (see leakstats). Datasets that are left out are reported in `skipped`.
    """
    rows = []
    for (dec, design), g in by.groupby(["decoder", "design"]):
        per = g.groupby("dataset")["delta_pp"].agg(["mean", "std", "count"])
        skipped = [f"{d}(n={int(r['count'])})" for d, r in per.iterrows() if r["count"] < 3 or not r["std"] > 0]
        per = per[(per["count"] >= 3) & (per["std"] > 0)]
        if len(per) >= 2:
            var = (per["std"] ** 2 / per["count"]).to_numpy()
            rows.append({"decoder": dec, "design": design, "skipped": ";".join(skipped),
                         **random_effects_meta(per["mean"].to_numpy(), var, hksj=True)})
    return pd.DataFrame(rows)


def ranking(raw, leaky="D1s_size_matched", clean="D3_loro"):
    """Do decoder rankings change between a leaky and a clean design? Bootstrap over subjects (needs 2+ decoders)."""
    real = raw[raw["label_type"] == "real"]
    rows = []
    for dataset, g in real.groupby("dataset"):
        pa = g[g["design"] == leaky].pivot_table(index="subject", columns="decoder", values="acc_pooled")
        pb = g[g["design"] == clean].pivot_table(index="subject", columns="decoder", values="acc_pooled")
        common = sorted(set(pa.columns) & set(pb.columns))
        subj = sorted(set(pa.index) & set(pb.index))
        if len(common) >= 2 and len(subj) >= 3:
            a = {d: pa.loc[subj, d].to_numpy() for d in common}
            b = {d: pb.loc[subj, d].to_numpy() for d in common}
            rows.append({"dataset": dataset, "leaky": leaky, "clean": clean, **ranking_reversal_bootstrap(a, b)})
    return pd.DataFrame(rows)


def strata(by, info):
    """M8 (EXPLORATORY): inflation by tertile of a subject characteristic that is NOT the accuracy being compared.

    v0.2 stratified by the reference accuracy itself, which mixes in regression to the mean (a subject who is
    low because of noise will look better under any other design). Here the strata are run-decodability and
    trial count. Subjects are never excluded.
    """
    m = by.merge(info[[c for c in ("dataset", "subject", "run_decode_acc", "n_trials") if c in info.columns]],
                 on=["dataset", "subject"], how="left")
    rows = []
    for (dataset, dec, design), g in m.groupby(["dataset", "decoder", "design"]):
        for var in ("run_decode_acc", "n_trials"):
            h = g.dropna(subset=[var])
            if len(h) >= 9 and h[var].nunique() >= 3:
                q = pd.qcut(h[var].rank(method="first"), 3, labels=["low", "middle", "high"])
                for lab, gg in h.groupby(q, observed=True):
                    rows.append({"dataset": dataset, "decoder": dec, "design": design, "stratified_by": var,
                                 "stratum": lab, "n": len(gg), "median_delta_pp": float(gg["delta_pp"].median())})
    return pd.DataFrame(rows)


def delta_vs_null_summary(raw):
    """Share of subjects whose design difference exceeds the same difference under null labels (p < 0.05)."""
    pd_null = lc.paired_delta_vs_null(raw)
    if not len(pd_null):
        return pd_null
    pd_null["reachable"] = pd_null["min_possible_p"] < 0.05
    rows = []
    for keys, g in pd_null.groupby(["dataset", "decoder", "design", "reference", "null_type"]):
        rows.append(dict(zip(["dataset", "decoder", "design", "reference", "null_type"], keys),
                         n_subjects=len(g), min_possible_p=float(g["min_possible_p"].max()),
                         n_p_below_005=int((g["empirical_p"] < 0.05).sum()) if (g["reachable"]).all() else None,
                         note="" if g["reachable"].all() else "n_null too small for p < 0.05"))
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", nargs="+", required=True)
    ap.add_argument("--out", default="analysis")
    ap.add_argument("--smallest-effect-pp", type=float, default=2.0, help="pre-specified smallest effect of interest")
    ap.add_argument("--exclude-subjects", default="", help="pilot subjects to leave out of the confirmatory analysis, "
                                                           "e.g. 1-10 (or dataset:1-10 is NOT supported; applies to all datasets)")
    ap.add_argument("--power-from", nargs="*", default=None,
                    help="result folders used ONLY to estimate the SD for the power calculation (the pilot)")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    raw, info = load(a.results)
    if a.exclude_subjects:
        drop = set()
        for part in a.exclude_subjects.split(","):
            lo, _, hi = part.partition("-")
            drop.update(range(int(lo), int(hi or lo) + 1))
        raw, info = raw[~raw["subject"].isin(drop)], info[~info["subject"].isin(drop)]
        print(f"excluded pilot subjects from the confirmatory analysis: {sorted(drop)}")
    by = lc.inflation_by_subject(raw)
    for name, tab in (("moderators", moderators(by, info)), ("meta_analysis", meta(by)),
                      ("ranking_reversal", ranking(raw)), ("strata_exploratory", strata(by, info)),
                      ("delta_vs_null", delta_vs_null_summary(raw))):
        if len(tab):
            tab.to_csv(out / f"{name}.csv", index=False)
        print(f"{name}: {len(tab)} rows" + ("" if len(tab) else "  (not enough data for this analysis; nothing written)"))

    power = {}
    pilot_by = by
    if a.power_from:
        pilot_raw, _ = load(a.power_from)
        pilot_by = lc.inflation_by_subject(pilot_raw)
    for (dec, design), g in pilot_by.groupby(["decoder", "design"]):
        sd = float(g["delta_pp"].std(ddof=1)) if len(g) > 2 else float("nan")
        power[f"{dec}|{design}"] = {"pilot_n": int(len(g)), "sd_delta_pp": sd,
                                    "required_subjects": required_subjects(sd, a.smallest_effect_pp) if sd > 0 else None}
    (out / "power_from_pilot.json").write_text(json.dumps(
        {"smallest_effect_pp": a.smallest_effect_pp,
         "sd_source": "pilot folders (--power-from)" if a.power_from else "THE SAME DATA AS THE ANALYSIS (not a clean pilot; use --power-from)",
         "note": "Estimate the SD from a small pilot, freeze the plan, then run the confirmatory set.", "by_contrast": power}, indent=2))


if __name__ == "__main__":
    main()
