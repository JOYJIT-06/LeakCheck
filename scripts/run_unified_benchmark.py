"""Unified Multi-Dataset EEG Leakage Auditing Benchmark CLI for LeakCheck V2.

Supports all 11 registered EEG motor imagery adapters:
  1. PhysioNet EEGMMIDB (N=109/105)
  2. OpenBMI / Lee et al. 2019 (N=54/34)
  3. Cho et al. 2017 (N=52)
  4. BNCI2014-001 / BCI Comp IV 2a (N=9)
  5. BNCI2014-004 / BCI Comp IV 2b (N=9)
  6. High-Gamma / Schirrmeister 2017 (N=14)
  7. Shin et al. 2017A (N=29)
  8. Weibo et al. 2014 (N=10)
  9. Grosse-Wentrup et al. 2009 (N=10)
  10. Zhou et al. 2016 (N=4)
  11. Yang et al. 2025 (N=60+)

Evaluates the canonical LeakCheck V2 hierarchy:
  Level 1: Fold-level trial metrics (accuracy, train_acc, split_hash)
  Level 2: Participant-level aggregate metrics and eligibility
  Level 3: Dataset-level Hodges-Lehmann differences, BCa 95% CIs, Wilcoxon p-values, Holm correction, Cohen's dz
  Level 4: Cross-dataset comparative synthesis

Usage:
  python scripts/run_unified_benchmark.py --dataset openbmi --data-dir data/OpenBMI --outdir results/openbmi
  python scripts/run_unified_benchmark.py --dataset cho2017 --synthetic --outdir results/cho2017_smoke
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import emi
from emi.datasets_base import get_adapter, list_registered_adapters
import emi.datasets_adapters  # Ensure adapters are registered
from emi.decoders import (
    CovarianceTransformer,
    TangentSpaceTransformer,
    get_csp_factory,
)
from emi.leakstats import bca_ci, cohens_dz, hodges_lehmann, holm, rank_biserial

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("unified_benchmark")


def compute_split_hash(train_idx: np.ndarray, test_idx: np.ndarray) -> str:
    """Compute SHA-256 digest of train/test indices."""
    payload = f"train:{list(train_idx)}|test:{list(test_idx)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def build_decoder_pipeline(decoder_name: str, n_csp: int = 6) -> Pipeline:
    """Build a standard decoder pipeline."""
    if decoder_name == "csp_lda":
        csp = get_csp_factory("mne", reg="oas")(n_csp)
        lda = LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")
        return Pipeline([("csp", csp), ("clf", lda)])

    if decoder_name == "ts_lr":
        return Pipeline([
            ("cov", CovarianceTransformer()),
            ("ts", TangentSpaceTransformer()),
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(C=1.0, max_iter=1000, solver="lbfgs")),
        ])

    raise ValueError(f"Unknown decoder: {decoder_name}")


def generate_synthetic_subject_epochs(
    adapter_name: str,
    subject: int,
    n_trials: int = 100,
    n_channels: int = 64,
    n_times: int = 750,
    sfreq: float = 250.0,
    seed: int = 42,
) -> Dict[str, Any]:
    """Generate reproducible synthetic EEG trials matching adapter montage for testing."""
    rng = np.random.RandomState(seed + subject)
    # Balanced classes
    y = np.array([0] * (n_trials // 2) + [1] * (n_trials // 2))
    # Two runs (Run 0 calibration, Run 1 feedback)
    runs = np.array([0] * (n_trials // 2) + [1] * (n_trials // 2))
    rng.shuffle(y)

    # Class-correlated ERP in specific channels to simulate genuine task signal
    X = rng.randn(n_trials, n_channels, n_times) * 20.0  # background noise in uV
    for i in range(n_trials):
        if y[i] == 1:
            X[i, 0, :] += np.sin(np.linspace(0, 4 * np.pi, n_times)) * 10.0
        else:
            X[i, 1, :] += np.sin(np.linspace(0, 4 * np.pi, n_times)) * 10.0

    times = np.linspace(0, n_times / sfreq, n_times)
    return {
        "X": X,
        "y": y,
        "runs": runs,
        "times": times,
        "sfreq": sfreq,
        "channels": [f"ch_{i}" for i in range(n_channels)],
        "extra": {"synthetic": True, "adapter": adapter_name},
    }


def run_d3_loro(
    subject: int,
    data: Dict[str, Any],
    decoders: List[str],
    n_csp: int = 6,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Run D3: Operational Leave-One-Run-Out partition."""
    X, y, runs = data["X"], data["y"], data["runs"]
    unique_runs = np.unique(runs)
    if len(unique_runs) < 2:
        # Fall back to 2 halves if only one run recorded
        n_half = len(y) // 2
        train_idx = np.arange(n_half)
        test_idx = np.arange(n_half, len(y))
        folds = [("half0_to_half1", train_idx, test_idx), ("half1_to_half0", test_idx, train_idx)]
    else:
        folds = [
            ("run0_to_run1", np.where(runs == unique_runs[0])[0], np.where(runs == unique_runs[1])[0]),
            ("run1_to_run0", np.where(runs == unique_runs[1])[0], np.where(runs == unique_runs[0])[0]),
        ]

    records: List[Dict[str, Any]] = []
    splits_manifest: Dict[str, Any] = {}

    for fold_idx, (fold_label, train_idx, test_idx) in enumerate(folds):
        shash = compute_split_hash(train_idx, test_idx)
        splits_manifest[f"fold_{fold_idx}"] = {
            "label": fold_label,
            "train_idx": train_idx.tolist(),
            "test_idx": test_idx.tolist(),
            "split_hash": shash,
        }

        X_tr, y_tr = X[train_idx], y[train_idx]
        X_te, y_te = X[test_idx], y[test_idx]

        for dec in decoders:
            pipe = build_decoder_pipeline(dec, n_csp=n_csp)
            pipe.fit(X_tr, y_tr)
            tr_acc = float(pipe.score(X_tr, y_tr))
            te_acc = float(pipe.score(X_te, y_te))

            records.append({
                "subject": subject,
                "decoder": dec,
                "design": "D3_loro",
                "repeat": 0,
                "fold": fold_idx,
                "fold_label": fold_label,
                "n_train": len(y_tr),
                "n_test": len(y_te),
                "accuracy": te_acc,
                "train_acc": tr_acc,
                "split_hash": shash,
            })

    return records, splits_manifest


def run_d1s_size_matched(
    subject: int,
    data: Dict[str, Any],
    decoders: List[str],
    n_csp: int = 6,
    n_repeats: int = 20,
    base_seed: int = 0,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Run D1s: Size- and class-matched pooled random partition."""
    X, y = data["X"], data["y"]
    c0_idx = np.where(y == 0)[0]
    c1_idx = np.where(y == 1)[0]

    records: List[Dict[str, Any]] = []
    splits_manifest: Dict[str, Any] = {}

    for rep in range(n_repeats):
        rng = np.random.RandomState(base_seed + rep)
        shuffled_c0 = rng.permutation(c0_idx)
        shuffled_c1 = rng.permutation(c1_idx)

        half0_c0 = shuffled_c0[: len(shuffled_c0) // 2]
        half1_c0 = shuffled_c0[len(shuffled_c0) // 2 :]
        half0_c1 = shuffled_c1[: len(shuffled_c1) // 2]
        half1_c1 = shuffled_c1[len(shuffled_c1) // 2 :]

        f0_tr = np.sort(np.concatenate([half0_c0, half0_c1]))
        f0_te = np.sort(np.concatenate([half1_c0, half1_c1]))
        f1_tr = f0_te
        f1_te = f0_tr

        for f_idx, (tr_idx, te_idx) in enumerate([(f0_tr, f0_te), (f1_tr, f1_te)]):
            shash = compute_split_hash(tr_idx, te_idx)
            splits_manifest[f"rep_{rep}_fold_{f_idx}"] = {
                "train_idx": tr_idx.tolist(),
                "test_idx": te_idx.tolist(),
                "split_hash": shash,
            }

            X_tr, y_tr = X[tr_idx], y[tr_idx]
            X_te, y_te = X[te_idx], y[te_idx]

            for dec in decoders:
                pipe = build_decoder_pipeline(dec, n_csp=n_csp)
                pipe.fit(X_tr, y_tr)
                tr_acc = float(pipe.score(X_tr, y_tr))
                te_acc = float(pipe.score(X_te, y_te))

                records.append({
                    "subject": subject,
                    "decoder": dec,
                    "design": "D1s_size_matched",
                    "repeat": rep,
                    "fold": f_idx,
                    "fold_label": f"rep{rep}_fold{f_idx}",
                    "n_train": len(y_tr),
                    "n_test": len(y_te),
                    "accuracy": te_acc,
                    "train_acc": tr_acc,
                    "split_hash": shash,
                })

    return records, splits_manifest


def run_p1_csp_on_all(
    subject: int,
    data: Dict[str, Any],
    decoders: List[str],
    n_csp: int = 6,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Run P1: Supervised Spatial Filter Contamination under D3 partition."""
    X, y, runs = data["X"], data["y"], data["runs"]
    unique_runs = np.unique(runs)
    if len(unique_runs) < 2:
        n_half = len(y) // 2
        train_idx = np.arange(n_half)
        test_idx = np.arange(n_half, len(y))
        folds = [("half0_to_half1", train_idx, test_idx), ("half1_to_half0", test_idx, train_idx)]
    else:
        folds = [
            ("run0_to_run1", np.where(runs == unique_runs[0])[0], np.where(runs == unique_runs[1])[0]),
            ("run1_to_run0", np.where(runs == unique_runs[1])[0], np.where(runs == unique_runs[0])[0]),
        ]

    records: List[Dict[str, Any]] = []
    splits_manifest: Dict[str, Any] = {}

    for fold_idx, (fold_label, train_idx, test_idx) in enumerate(folds):
        splits_manifest[f"fold_{fold_idx}"] = {
            "label": fold_label,
            "train_idx": train_idx.tolist(),
            "test_idx": test_idx.tolist(),
            "split_hash": compute_split_hash(train_idx, test_idx),
        }

    # Evaluate CSP-LDA with Global CSP contamination
    if "csp_lda" in decoders:
        global_csp = get_csp_factory("mne", reg="oas")(n_csp)
        # Spatial filter contaminated with all trials and labels
        global_csp.fit(X, y)
        Z_all = global_csp.transform(X)

        for fold_idx, (fold_label, train_idx, test_idx) in enumerate(folds):
            shash = splits_manifest[f"fold_{fold_idx}"]["split_hash"]
            Z_tr, y_tr = Z_all[train_idx], y[train_idx]
            Z_te, y_te = Z_all[test_idx], y[test_idx]

            # Inviolable safeguard: Classifier fitted strictly on training fold features
            clf = LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")
            clf.fit(Z_tr, y_tr)
            tr_acc = float(clf.score(Z_tr, y_tr))
            te_acc = float(clf.score(Z_te, y_te))

            records.append({
                "subject": subject,
                "decoder": "csp_lda",
                "design": "P1_csp_on_all",
                "repeat": 0,
                "fold": fold_idx,
                "fold_label": fold_label,
                "n_train": len(y_tr),
                "n_test": len(y_te),
                "accuracy": te_acc,
                "train_acc": tr_acc,
                "split_hash": shash,
            })

    # Evaluate TS-LR with Global Tangent Space contamination
    if "ts_lr" in decoders:
        cov_trans = CovarianceTransformer()
        cov_all = cov_trans.transform(X)
        global_ts = TangentSpaceTransformer()
        global_ts.fit(cov_all)
        T_all = global_ts.transform(cov_all)
        scaler = StandardScaler()
        T_all_scaled = scaler.fit_transform(T_all)

        for fold_idx, (fold_label, train_idx, test_idx) in enumerate(folds):
            shash = splits_manifest[f"fold_{fold_idx}"]["split_hash"]
            T_tr, y_tr = T_all_scaled[train_idx], y[train_idx]
            T_te, y_te = T_all_scaled[test_idx], y[test_idx]

            clf = LogisticRegression(C=1.0, max_iter=1000, solver="lbfgs")
            clf.fit(T_tr, y_tr)
            tr_acc = float(clf.score(T_tr, y_tr))
            te_acc = float(clf.score(T_te, y_te))

            records.append({
                "subject": subject,
                "decoder": "ts_lr",
                "design": "P1_ts_on_all",
                "repeat": 0,
                "fold": fold_idx,
                "fold_label": fold_label,
                "n_train": len(y_tr),
                "n_test": len(y_te),
                "accuracy": te_acc,
                "train_acc": tr_acc,
                "split_hash": shash,
            })

    return records, splits_manifest


def compute_design_contrasts(participant_df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """Compute Level 3 dataset contrasts: Hodges-Lehmann difference, BCa CI, Wilcoxon p, Holm correction."""
    results: List[Dict[str, Any]] = []
    for dec in participant_df["decoder"].unique():
        sub_df = participant_df[participant_df["decoder"] == dec]
        contrast_rows: List[Dict[str, Any]] = []
        raw_pvals: List[float] = []

        p1_cond = "P1_ts_on_all" if "P1_ts_on_all" in sub_df["design"].values else "P1_csp_on_all"
        p1_desc = "Supervised Tangent Space Contamination Effect" if p1_cond == "P1_ts_on_all" else "Supervised Spatial Contamination Effect"
        contrast_defs = [
            ("D1s_vs_D3", "D1s_size_matched", "D3_loro", "Pooled Random Partitioning Effect"),
            ("P1_vs_D3", p1_cond, "D3_loro", p1_desc),
        ]

        for contrast_name, cond_b, cond_a, desc in contrast_defs:
            df_b = sub_df[sub_df["design"] == cond_b].set_index("subject")["mean_accuracy"]
            df_a = sub_df[sub_df["design"] == cond_a].set_index("subject")["mean_accuracy"]
            common = df_b.index.intersection(df_a.index)

            d = (df_b.loc[common] - df_a.loc[common]).values * 100.0  # in percentage points
            n = len(d)

            row: Dict[str, Any] = {
                "decoder": dec,
                "contrast": contrast_name,
                "description": desc,
                "condition_a": cond_a,
                "condition_b": cond_b,
                "n_subjects": n,
                "mean_diff_pp": float(np.mean(d)) if n > 0 else np.nan,
                "std_diff_pp": float(np.std(d, ddof=1)) if n > 1 else np.nan,
                "median_diff_pp": float(np.median(d)) if n > 0 else np.nan,
                "n_deflated": int(np.sum(d < 0)),
                "pct_deflated": float(np.mean(d < 0) * 100.0) if n > 0 else np.nan,
                "n_inflated": int(np.sum(d > 0)),
                "pct_inflated": float(np.mean(d > 0) * 100.0) if n > 0 else np.nan,
                "hl_pp": np.nan,
                "hl_ci_low_pp": np.nan,
                "hl_ci_high_pp": np.nan,
                "hl_ci_method": "none",
                "wilcoxon_p": np.nan,
                "wilcoxon_p_holm": np.nan,
                "rank_biserial": np.nan,
                "cohens_dz": np.nan,
            }

            if n >= 3:
                row["hl_pp"] = hodges_lehmann(d)
                ci_lo, ci_hi, ci_meth = bca_ci(d, n_resamples=2000, seed=seed, return_method=True)
                row["hl_ci_low_pp"] = ci_lo
                row["hl_ci_high_pp"] = ci_hi
                row["hl_ci_method"] = ci_meth

                if np.allclose(d, 0):
                    p_val = 1.0
                else:
                    try:
                        res = stats.wilcoxon(d, zero_method="pratt")
                        p_val = float(res.pvalue)
                    except Exception:
                        p_val = 1.0
                row["wilcoxon_p"] = p_val
                raw_pvals.append(p_val)
                row["rank_biserial"] = rank_biserial(d)
                row["cohens_dz"] = cohens_dz(d)
            else:
                raw_pvals.append(np.nan)

            contrast_rows.append(row)

        # Holm adjustment
        if len(raw_pvals) == 2 and not any(np.isnan(p) for p in raw_pvals):
            adj = holm(raw_pvals)
            contrast_rows[0]["wilcoxon_p_holm"] = float(adj[0])
            contrast_rows[1]["wilcoxon_p_holm"] = float(adj[1])

        results.extend(contrast_rows)

    return pd.DataFrame(results)


def main():
    parser = argparse.ArgumentParser(description="Unified Multi-Dataset LeakCheck V2 Benchmark Runner")
    parser.add_argument("--dataset", required=True, help="Registered dataset name (e.g. physionet, openbmi, cho2017, bnci2014_001, etc.)")
    parser.add_argument("--data-dir", default="data", help="Directory where dataset recordings are stored")
    parser.add_argument("--outdir", required=True, help="Directory to save benchmark metrics and manifests")
    parser.add_argument("--subjects", default="all", help="Subjects list, e.g. '1-10' or '1,2,3' or 'all'")
    parser.add_argument("--decoders", default="csp_lda,ts_lr", help="Comma-separated decoders")
    parser.add_argument("--designs", default="D3,D1s,P1", help="Comma-separated designs (D3, D1s, P1)")
    parser.add_argument("--synthetic", action="store_true", help="Generate synthetic test data matching adapter montage")
    parser.add_argument("--n-csp", type=int, default=6, help="Number of CSP filters")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    t_start = time.time()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    splits_dir = outdir / "fold_indices"
    splits_dir.mkdir(parents=True, exist_ok=True)

    adapter = get_adapter(args.dataset, data_dir=args.data_dir)
    log.info("Initialized adapter: %s (%s)", adapter.name, adapter.metadata.citation)

    # Determine subjects
    if args.subjects == "all":
        subjects = list(range(1, adapter.metadata.n_subjects + 1))
    elif "-" in args.subjects:
        lo, hi = args.subjects.split("-", 1)
        subjects = list(range(int(lo), int(hi) + 1))
    else:
        subjects = [int(s.strip()) for s in args.subjects.split(",") if s.strip()]

    decoders = [d.strip() for d in args.decoders.split(",") if d.strip()]
    designs = [d.strip() for d in args.designs.split(",") if d.strip()]

    log.info("Running benchmark on %d subjects: %s", len(subjects), subjects)
    log.info("Decoders: %s | Designs: %s | Synthetic: %s", decoders, designs, args.synthetic)

    eligibility_rows: List[Dict[str, Any]] = []
    all_fold_rows: List[Dict[str, Any]] = []
    eligible_subjects: List[int] = []

    for sub in subjects:
        if args.synthetic:
            is_ok = True
            row = {
                "subject": sub,
                "status": "ELIGIBLE",
                "rejection_reason": "Synthetic test cohort",
                "n_trials": 100,
                "n_channels": adapter.metadata.channel_count,
            }
            data = generate_synthetic_subject_epochs(
                adapter_name=adapter.name,
                subject=sub,
                n_trials=100,
                n_channels=adapter.metadata.channel_count,
                n_times=750,
                sfreq=adapter.metadata.sampling_rate,
                seed=args.seed,
            )
        else:
            is_ok, diag = adapter.validate_integrity(sub)
            row = {
                "subject": sub,
                "status": diag.get("status", "UNKNOWN"),
                "rejection_reason": diag.get("reason", ""),
                "n_channels": diag.get("n_channels", adapter.metadata.channel_count),
            }
            data = None
            if is_ok:
                try:
                    data = adapter.get_subject_epochs(sub)
                except Exception as exc:
                    is_ok = False
                    row["status"] = "ERROR"
                    row["rejection_reason"] = str(exc)

        eligibility_rows.append(row)
        if not is_ok or data is None:
            log.warning("Subject %d excluded (%s): %s", sub, row["status"], row["rejection_reason"])
            continue

        eligible_subjects.append(sub)
        sub_manifest: Dict[str, Any] = {}

        # 1. D3
        if "D3" in designs:
            d3_records, d3_splits = run_d3_loro(sub, data, decoders=decoders, n_csp=args.n_csp)
            all_fold_rows.extend(d3_records)
            sub_manifest["D3_loro"] = d3_splits

        # 2. D1s
        if "D1s" in designs:
            d1s_records, d1s_splits = run_d1s_size_matched(sub, data, decoders=decoders, n_csp=args.n_csp, n_repeats=20, base_seed=args.seed)
            all_fold_rows.extend(d1s_records)
            sub_manifest["D1s_size_matched"] = d1s_splits

        # 3. P1
        if "P1" in designs:
            p1_records, p1_splits = run_p1_csp_on_all(sub, data, decoders=decoders, n_csp=args.n_csp)
            all_fold_rows.extend(p1_records)
            sub_manifest["P1_csp_on_all"] = p1_splits

        # Write subject splits
        with open(splits_dir / f"sub-{sub:02d}_splits.json", "w", encoding="utf-8") as f:
            json.dump(sub_manifest, f, indent=2)

    # Convert results
    elig_df = pd.DataFrame(eligibility_rows)
    elig_df.to_csv(outdir / "participant_eligibility.csv", index=False)

    if not all_fold_rows:
        log.warning("No eligible subjects evaluated. Wrote eligibility table. Exiting.")
        return

    fold_df = pd.DataFrame(all_fold_rows)
    fold_df.to_csv(outdir / "fold_metrics.csv", index=False)

    # Participant-level aggregation
    part_df = (
        fold_df.groupby(["subject", "decoder", "design"])
        .agg(
            mean_accuracy=("accuracy", "mean"),
            std_accuracy=("accuracy", "std"),
            median_accuracy=("accuracy", "median"),
            mean_train_accuracy=("train_acc", "mean"),
            n_evaluations=("accuracy", "count"),
        )
        .reset_index()
    )
    part_df.to_csv(outdir / "participant_metrics.csv", index=False)

    # Design comparisons
    comp_df = compute_design_contrasts(part_df, seed=args.seed)
    comp_df.to_csv(outdir / "design_comparisons.csv", index=False)

    duration = time.time() - t_start

    manifest = {
        "dataset": adapter.name,
        "accession": adapter.metadata.accession_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "execution_duration_seconds": round(duration, 2),
        "host_platform": platform.platform(),
        "python_version": platform.python_version(),
        "package_versions": {
            "emi": emi.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        "total_requested_subjects": len(subjects),
        "eligible_subjects_count": len(eligible_subjects),
        "synthetic": args.synthetic,
        "decoders": decoders,
        "designs": designs,
        "sha256_metrics": {
            "fold_metrics": hashlib.sha256(open(outdir / "fold_metrics.csv", "rb").read()).hexdigest(),
            "participant_metrics": hashlib.sha256(open(outdir / "participant_metrics.csv", "rb").read()).hexdigest(),
            "design_comparisons": hashlib.sha256(open(outdir / "design_comparisons.csv", "rb").read()).hexdigest(),
        },
    }
    with open(outdir / "benchmark_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    log.info("Benchmark complete in %.2f s. Results written to %s", duration, outdir)


if __name__ == "__main__":
    main()
