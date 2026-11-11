"""OpenBMI (Lee et al. 2019) Motor Imagery Replication Benchmark for LeakCheck V2.

Evaluates:
  1. D3 (Leave-One-Run-Out): Operational transfer across Run 0 (calibration) and Run 1 (feedback).
  2. D1s (Size- and Class-Matched Pooled Random Partition): 2 folds, 20 repeats (seeds 0-19),
     exactly 100 train / 100 test trials, 50 Left / 50 Right per fold.
  3. P1 (Positive Control - Supervised Spatial Contamination): Global CSP fitted on all 200 trials;
     classifier trained strictly on training-fold features.
  4. D1m (Secondary Sensitivity): Stratified 2-fold cross-validation, 5 repeats.

Reference:
  Lee, M.-H. et al. (2019). GigaScience 8(5), giz002.
  NEMAR accession: nm000338, version 1.0.5.
  Protocol Review: docs/V2/OPENBMI_PILOT_PROTOCOL_REVIEW.md
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

import mne
import numpy as np
import pandas as pd
import scipy
from scipy import stats
import sklearn
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import emi
from emi.datasets_openbmi import (
    OPENBMI_CHANNELS_62,
    OPENBMI_FAILED_DOWNLOADS,
    load_openbmi_subject,
)
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
log = logging.getLogger("openbmi_benchmark")

INTACT_SUBJECTS_34 = [2, 3, 10] + list(range(12, 40)) + [42, 43, 44]


def parse_subjects(subjects_str: str) -> List[int]:
    """Parse comma-separated subject IDs and ranges, or 'intact' / 'all'."""
    s = subjects_str.strip().lower()
    if s in ("intact", "all", "cohort"):
        return list(INTACT_SUBJECTS_34)
    
    out: List[int] = []
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = part.split("-", 1)
            out.extend(range(int(lo), int(hi) + 1))
        else:
            out.append(int(part))
    return sorted(list(set(out)))


def sha256_file(path: Path | str, chunk_size: int = 1024 * 1024) -> str:
    """Compute SHA-256 hexadecimal digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_split_hash(train_idx: np.ndarray, test_idx: np.ndarray) -> str:
    """Compute SHA-256 digest of train/test indices."""
    payload = f"train:{list(train_idx)}|test:{list(test_idx)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


# ----------------------------------------------------------------------
# Automated Eligibility Check
# ----------------------------------------------------------------------

def verify_subject_eligibility(
    subject: int,
    data_dir: Path,
    target_fs: float = 250.0,
    tmin: float = -0.5,
    tmax: float = 4.0,
    bandpass: Optional[Tuple[float, float]] = (8.0, 30.0),
    baseline: Optional[Tuple[float, float]] = (-0.5, 0.0),
    reject_ptp_uv: float = 150.0,
) -> Tuple[bool, Dict[str, Any], Optional[Dict[str, Any]]]:
    """Verify participant data meets all protocol eligibility criteria.

    Returns (is_eligible, metrics_dict, loaded_data_dict_or_None).
    """
    row: Dict[str, Any] = {
        "subject": subject,
        "n_trials": 0,
        "n_run0": 0,
        "n_run1": 0,
        "n_left": 0,
        "n_right": 0,
        "n_channels": 0,
        "sfreq_orig": 0.0,
        "sfreq_target": target_fs,
        "n_nan": 0,
        "n_inf": 0,
        "n_artifacts_flagged": 0,
        "status": "PENDING",
        "rejection_reason": "",
    }

    if subject in OPENBMI_FAILED_DOWNLOADS:
        row["status"] = "EXCLUDED"
        row["rejection_reason"] = "Known corrupted or incomplete download"
        return False, row, None

    mat_path = data_dir / "sourcedata" / "session1" / f"s{subject}" / f"sess01_subj{subject:02d}_EEG_MI.mat"
    if not mat_path.is_file():
        row["status"] = "EXCLUDED"
        row["rejection_reason"] = f"MATLAB file not found: {mat_path.name}"
        return False, row, None

    file_size = mat_path.stat().st_size
    if file_size < 1024 * 1024:
        row["status"] = "EXCLUDED"
        row["rejection_reason"] = f"File too small ({file_size} bytes)"
        return False, row, None

    try:
        data = load_openbmi_subject(
            subject=subject,
            data_dir=data_dir,
            target_fs=target_fs,
            tmin=tmin,
            tmax=tmax,
            bandpass=bandpass,
            baseline=baseline,
            reject_ptp_uv=reject_ptp_uv,
        )
    except Exception as exc:
        row["status"] = "EXCLUDED"
        row["rejection_reason"] = f"Loading failed: {exc}"
        return False, row, None

    X, y, runs = data["X"], data["y"], data["runs"]
    row["n_trials"] = len(y)
    row["n_run0"] = int(np.sum(runs == 0))
    row["n_run1"] = int(np.sum(runs == 1))
    row["n_left"] = int(np.sum(y == 0))
    row["n_right"] = int(np.sum(y == 1))
    row["n_channels"] = X.shape[1]
    row["sfreq_orig"] = data["extra"].get("orig_fs", 1000.0)
    row["n_nan"] = int(np.isnan(X).sum())
    row["n_inf"] = int(np.isinf(X).sum())
    row["n_artifacts_flagged"] = data.get("extra", {}).get("n_artifact_flagged", 0)

    # Invariants verification
    if row["n_trials"] != 200:
        row["status"] = "EXCLUDED"
        row["rejection_reason"] = f"Trial count {row['n_trials']} != 200"
        return False, row, None

    if row["n_run0"] != 100 or row["n_run1"] != 100:
        row["status"] = "EXCLUDED"
        row["rejection_reason"] = f"Run imbalance: Run 0={row['n_run0']}, Run 1={row['n_run1']}"
        return False, row, None

    if row["n_left"] != 100 or row["n_right"] != 100:
        row["status"] = "EXCLUDED"
        row["rejection_reason"] = f"Class imbalance: Left={row['n_left']}, Right={row['n_right']}"
        return False, row, None

    if row["n_channels"] != 62:
        row["status"] = "EXCLUDED"
        row["rejection_reason"] = f"Channel count {row['n_channels']} != 62"
        return False, row, None

    if row["n_nan"] > 0 or row["n_inf"] > 0:
        row["status"] = "EXCLUDED"
        row["rejection_reason"] = f"Non-finite values present (NaN={row['n_nan']}, Inf={row['n_inf']})"
        return False, row, None

    row["status"] = "ELIGIBLE"
    row["rejection_reason"] = "All protocol criteria satisfied"
    return True, row, data


# ----------------------------------------------------------------------
# Evaluator Factory
# ----------------------------------------------------------------------

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


# ----------------------------------------------------------------------
# Design Implementations
# ----------------------------------------------------------------------

def run_d3_loro_for_subject(
    subject: int,
    data: Dict[str, Any],
    decoders: List[str],
    n_csp: int = 6,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Run D3 Leave-One-Run-Out (Run 0 vs Run 1)."""
    X, y, runs = data["X"], data["y"], data["runs"]
    folds = [
        ("run0_to_run1", np.where(runs == 0)[0], np.where(runs == 1)[0]),
        ("run1_to_run0", np.where(runs == 1)[0], np.where(runs == 0)[0]),
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


def run_d1s_size_matched_for_subject(
    subject: int,
    data: Dict[str, Any],
    decoders: List[str],
    n_csp: int = 6,
    n_repeats: int = 20,
    base_seed: int = 0,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Run D1s: Size- and class-matched pooled random partition (20 repeats, 2 folds per repeat)."""
    X, y = data["X"], data["y"]
    left_indices = np.where(y == 0)[0]
    right_indices = np.where(y == 1)[0]

    records: List[Dict[str, Any]] = []
    splits_manifest: Dict[str, Any] = {}

    for r in range(n_repeats):
        rng = np.random.default_rng(base_seed + r)
        shuffled_left = rng.permutation(left_indices)
        shuffled_right = rng.permutation(right_indices)

        # Disjoint halves: 50 Left + 50 Right each
        half0 = np.sort(np.concatenate([shuffled_left[:50], shuffled_right[:50]]))
        half1 = np.sort(np.concatenate([shuffled_left[50:], shuffled_right[50:]]))

        folds = [
            (half0, half1),  # Train half0, Test half1
            (half1, half0),  # Train half1, Test half0
        ]

        splits_manifest[f"repeat_{r}"] = {}

        for fold_idx, (train_idx, test_idx) in enumerate(folds):
            shash = compute_split_hash(train_idx, test_idx)
            splits_manifest[f"repeat_{r}"][f"fold_{fold_idx}"] = {
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
                    "design": "D1s_size_matched",
                    "repeat": r,
                    "fold": fold_idx,
                    "fold_label": f"rep{r}_fold{fold_idx}",
                    "n_train": len(y_tr),
                    "n_test": len(y_te),
                    "accuracy": te_acc,
                    "train_acc": tr_acc,
                    "split_hash": shash,
                })

    return records, splits_manifest


def run_p1_csp_on_all_for_subject(
    subject: int,
    data: Dict[str, Any],
    decoders: List[str],
    n_csp: int = 6,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Run P1 Positive Control (Supervised Spatial Contamination).

    Spatial filter fitted on all 200 trials and labels.
    Classifier fitted strictly on training fold features; never receives test labels.
    Evaluated under the D3 Leave-One-Run-Out partition.
    """
    X, y, runs = data["X"], data["y"], data["runs"]
    folds = [
        ("run0_to_run1", np.where(runs == 0)[0], np.where(runs == 1)[0]),
        ("run1_to_run0", np.where(runs == 1)[0], np.where(runs == 0)[0]),
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

    # 1. Evaluate CSP-LDA with Global CSP contamination
    if "csp_lda" in decoders:
        global_csp = get_csp_factory("mne", reg="oas")(n_csp)
        # Contaminate spatial filter with all 200 trials and labels
        global_csp.fit(X, y)
        Z_all = global_csp.transform(X)

        for fold_idx, (fold_label, train_idx, test_idx) in enumerate(folds):
            shash = splits_manifest[f"fold_{fold_idx}"]["split_hash"]
            Z_tr, y_tr = Z_all[train_idx], y[train_idx]
            Z_te, y_te = Z_all[test_idx], y[test_idx]

            # Inviolable safeguard: Classifier fitted strictly on training-fold features
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

    # 2. Evaluate TS-LR with Global Tangent Space contamination
    if "ts_lr" in decoders:
        cov_trans = CovarianceTransformer()
        cov_all = cov_trans.transform(X)
        global_ts = TangentSpaceTransformer()
        # Contaminate reference matrix with all 200 covariance matrices
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
                "design": "T1_ts_reference_on_all",
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


def run_d1m_stratified_for_subject(
    subject: int,
    data: Dict[str, Any],
    decoders: List[str],
    n_csp: int = 6,
    n_repeats: int = 5,
    base_seed: int = 0,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Run D1m Secondary Sensitivity (Stratified 2-fold, 5 repeats)."""
    X, y = data["X"], data["y"]
    records: List[Dict[str, Any]] = []
    splits_manifest: Dict[str, Any] = {}

    for r in range(n_repeats):
        skf = StratifiedKFold(n_splits=2, shuffle=True, random_state=base_seed + r)
        splits_manifest[f"repeat_{r}"] = {}

        for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X, y)):
            shash = compute_split_hash(train_idx, test_idx)
            splits_manifest[f"repeat_{r}"][f"fold_{fold_idx}"] = {
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
                    "design": "D1m_stratified",
                    "repeat": r,
                    "fold": fold_idx,
                    "fold_label": f"rep{r}_fold{fold_idx}",
                    "n_train": len(y_tr),
                    "n_test": len(y_te),
                    "accuracy": te_acc,
                    "train_acc": tr_acc,
                    "split_hash": shash,
                })

    return records, splits_manifest


# ----------------------------------------------------------------------
# Statistical Contrasts & Multiplicity Control
# ----------------------------------------------------------------------

def compute_design_contrasts(
    participant_df: pd.DataFrame,
    seed: int = 0,
) -> pd.DataFrame:
    """Compute prespecified paired statistical contrasts per decoder family."""
    results = []

    for decoder in sorted(participant_df["decoder"].unique()):
        dec_df = participant_df[participant_df["decoder"] == decoder]
        piv = dec_df.pivot(index="subject", columns="design", values="accuracy")

        # Contrasts to run
        contrast_defs = []
        if "D1s_size_matched" in piv.columns and "D3_loro" in piv.columns:
            contrast_defs.append(("D1s_vs_D3", "D1s_size_matched", "D3_loro", "size_matched_divergence"))
        if decoder == "csp_lda" and "P1_csp_on_all" in piv.columns and "D3_loro" in piv.columns:
            contrast_defs.append(("P1_vs_D3", "P1_csp_on_all", "D3_loro", "supervised_contamination"))
        if decoder == "ts_lr" and "T1_ts_reference_on_all" in piv.columns and "D3_loro" in piv.columns:
            contrast_defs.append(("T1_ts_reference_vs_D3", "T1_ts_reference_on_all", "D3_loro", "unsupervised_reference_contamination"))
        if "D1m_stratified" in piv.columns and "D3_loro" in piv.columns:
            contrast_defs.append(("D1m_vs_D3", "D1m_stratified", "D3_loro", "secondary_sensitivity"))

        raw_pvals = []
        contrast_rows = []

        for name, col_leaky, col_clean, role in contrast_defs:
            s_leaky = piv[col_leaky].dropna()
            s_clean = piv[col_clean].dropna()
            common = s_leaky.index.intersection(s_clean.index)

            a = s_leaky.loc[common].values
            b = s_clean.loc[common].values
            d = (a - b) * 100.0  # percentage points
            n = len(d)

            row: Dict[str, Any] = {
                "decoder": decoder,
                "contrast": name,
                "role": role,
                "design_leaky": col_leaky,
                "design_clean": col_clean,
                "n_subjects": n,
                "mean_diff_pp": float(d.mean()) if n else np.nan,
                "median_diff_pp": float(np.median(d)) if n else np.nan,
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

                # Wilcoxon signed-rank test with Pratt correction for zero differences
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

        # Apply Holm adjustment within the two primary contrasts for each decoder
        # Primary family = D1s_vs_D3 and P1_vs_D3
        primary_indices = [i for i, c in enumerate(contrast_defs) if c[0] in ("D1s_vs_D3", "P1_vs_D3", "T1_ts_reference_vs_D3")]
        if len(primary_indices) == 2 and not any(np.isnan(raw_pvals[i]) for i in primary_indices):
            prim_pvals = [raw_pvals[i] for i in primary_indices]
            adj_pvals = holm(prim_pvals)
            for idx, adj in zip(primary_indices, adj_pvals):
                contrast_rows[idx]["wilcoxon_p_holm"] = float(adj)

        # For secondary sensitivity (D1m_vs_D3), m=1
        for i, c in enumerate(contrast_defs):
            if c[0] == "D1m_vs_D3" and not np.isnan(raw_pvals[i]):
                contrast_rows[i]["wilcoxon_p_holm"] = float(raw_pvals[i])

        results.extend(contrast_rows)

    return pd.DataFrame(results)


# ----------------------------------------------------------------------
# Main Runner Orchestrator
# ----------------------------------------------------------------------

def run_openbmi_benchmark(
    subjects: List[int],
    designs: List[str],
    decoders: List[str],
    output_dir: Path,
    data_dir: Path,
    target_fs: float = 250.0,
    tmin: float = -0.5,
    tmax: float = 4.0,
    bandpass: Optional[Tuple[float, float]] = (8.0, 30.0),
    baseline: Optional[Tuple[float, float]] = (-0.5, 0.0),
    reject_ptp_uv: float = 150.0,
    seed: int = 0,
    n_repeats_d1s: int = 20,
    n_repeats_d1m: int = 5,
    n_csp: int = 6,
) -> Dict[str, Any]:
    """Execute complete OpenBMI validation benchmark."""
    t_start = time.time()
    output_dir.mkdir(parents=True, exist_ok=True)
    splits_dir = output_dir / "fold_indices"
    splits_dir.mkdir(parents=True, exist_ok=True)

    log.info("Starting OpenBMI benchmark on %d subjects: %s", len(subjects), subjects)
    log.info("Designs: %s | Decoders: %s", designs, decoders)
    log.info("Preprocessing: %s Hz, bandpass=%s, baseline=%s, reject_ptp=%s uV",
             target_fs, bandpass, baseline, reject_ptp_uv)

    eligibility_rows: List[Dict[str, Any]] = []
    all_fold_rows: List[Dict[str, Any]] = []
    eligible_subjects: List[int] = []

    # 1. Eligibility audit
    for sub in subjects:
        is_ok, row, data = verify_subject_eligibility(
            subject=sub,
            data_dir=data_dir,
            target_fs=target_fs,
            tmin=tmin,
            tmax=tmax,
            bandpass=bandpass,
            baseline=baseline,
            reject_ptp_uv=reject_ptp_uv,
        )
        eligibility_rows.append(row)
        if not is_ok:
            log.warning("Subject %d excluded: %s", sub, row["rejection_reason"])
            continue

        eligible_subjects.append(sub)
        log.info("Subject %d ELIGIBLE (200 trials, 62 channels, %d flagged artifacts)",
                 sub, row["n_artifacts_flagged"])

        # Execute selected designs for eligible subject
        sub_splits: Dict[str, Any] = {"subject": sub}

        # D3 Leave-One-Run-Out
        if "D3_loro" in designs:
            f_rows, sp = run_d3_loro_for_subject(sub, data, decoders, n_csp=n_csp)
            all_fold_rows.extend(f_rows)
            sub_splits["D3_loro"] = sp

        # D1s Size-Matched Pooled Random Partition
        if "D1s_size_matched" in designs:
            f_rows, sp = run_d1s_size_matched_for_subject(
                sub, data, decoders, n_csp=n_csp, n_repeats=n_repeats_d1s, base_seed=seed
            )
            all_fold_rows.extend(f_rows)
            sub_splits["D1s_size_matched"] = sp

        # P1 Supervised Spatial Contamination
        if "P1_csp_on_all" in designs:
            f_rows, sp = run_p1_csp_on_all_for_subject(sub, data, decoders, n_csp=n_csp)
            all_fold_rows.extend(f_rows)
            sub_splits["P1_csp_on_all"] = sp

        # D1m Secondary Sensitivity
        if "D1m_stratified" in designs:
            f_rows, sp = run_d1m_stratified_for_subject(
                sub, data, decoders, n_csp=n_csp, n_repeats=n_repeats_d1m, base_seed=seed
            )
            all_fold_rows.extend(f_rows)
            sub_splits["D1m_stratified"] = sp

        # Save deterministic split indices
        split_path = splits_dir / f"sub-{sub:02d}_splits.json"
        with open(split_path, "w", encoding="utf-8") as f:
            json.dump(sub_splits, f, indent=2)

    # Convert to DataFrames
    eligibility_df = pd.DataFrame(eligibility_rows)
    eligibility_csv = output_dir / "participant_eligibility.csv"
    eligibility_df.to_csv(eligibility_csv, index=False)

    if not all_fold_rows:
        log.error("No fold results generated. Check subject eligibility.")
        return {"status": "NO_ELIGIBLE_SUBJECTS"}

    fold_df = pd.DataFrame(all_fold_rows)
    fold_csv = output_dir / "fold_metrics.csv"
    fold_df.to_csv(fold_csv, index=False)

    # 2. Participant-Level Aggregation
    # Invariant: Each repeat is averaged across its folds first, then averaged across repeats
    part_rows = []
    for (sub, dec, des), g in fold_df.groupby(["subject", "decoder", "design"]):
        rep_means = g.groupby("repeat")["accuracy"].mean()
        tr_rep_means = g.groupby("repeat")["train_acc"].mean()
        part_rows.append({
            "subject": sub,
            "decoder": dec,
            "design": des,
            "accuracy": float(rep_means.mean()),
            "train_accuracy": float(tr_rep_means.mean()),
            "n_trials": 200,
            "n_repeats": int(len(rep_means)),
        })
    participant_df = pd.DataFrame(part_rows)
    participant_csv = output_dir / "participant_metrics.csv"
    participant_df.to_csv(participant_csv, index=False)

    # 3. Statistical Contrasts
    contrasts_df = compute_design_contrasts(participant_df, seed=seed)
    contrasts_csv = output_dir / "design_comparisons.csv"
    contrasts_df.to_csv(contrasts_csv, index=False)

    elapsed_s = time.time() - t_start

    # 4. Provenance Manifest
    manifest = {
        "benchmark": "OpenBMI_Replication_V2",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": round(elapsed_s, 2),
        "host_platform": platform.platform(),
        "python_version": sys.version,
        "packages": {
            "emi": getattr(emi, "__version__", "1.1.0"),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "mne": mne.__version__,
            "sklearn": sklearn.__version__,
            "pandas": pd.__version__,
        },
        "arguments": {
            "subjects": subjects,
            "eligible_subjects": eligible_subjects,
            "n_eligible": len(eligible_subjects),
            "designs": designs,
            "decoders": decoders,
            "target_fs": target_fs,
            "tmin": tmin,
            "tmax": tmax,
            "bandpass": bandpass,
            "baseline": baseline,
            "reject_ptp_uv": reject_ptp_uv,
            "seed": seed,
            "n_repeats_d1s": n_repeats_d1s,
            "n_repeats_d1m": n_repeats_d1m,
            "n_csp": n_csp,
        },
        "output_files": {
            "participant_eligibility.csv": {
                "sha256": sha256_file(eligibility_csv),
                "rows": len(eligibility_df),
            },
            "fold_metrics.csv": {
                "sha256": sha256_file(fold_csv),
                "rows": len(fold_df),
            },
            "participant_metrics.csv": {
                "sha256": sha256_file(participant_csv),
                "rows": len(participant_df),
            },
            "design_comparisons.csv": {
                "sha256": sha256_file(contrasts_csv),
                "rows": len(contrasts_df),
            },
        },
    }

    manifest_json = output_dir / "benchmark_manifest.json"
    with open(manifest_json, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    log.info("Benchmark complete in %.2f seconds. Outputs written to %s", elapsed_s, output_dir)
    return manifest


def main():
    parser = argparse.ArgumentParser(
        description="Run LeakCheck V2 OpenBMI Replication Benchmark"
    )
    parser.add_argument(
        "--subjects",
        type=str,
        default="2,3",
        help="Comma-separated subject IDs, ranges (e.g. 2,3,10,12-39), or 'intact'",
    )
    parser.add_argument(
        "--designs",
        type=str,
        default="D3_loro,D1s_size_matched,P1_csp_on_all",
        help="Comma-separated designs: D3_loro,D1s_size_matched,P1_csp_on_all,D1m_stratified",
    )
    parser.add_argument(
        "--decoders",
        type=str,
        default="csp_lda,ts_lr",
        help="Comma-separated decoders: csp_lda,ts_lr",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("benchmark_results/openbmi_v2"),
        help="Destination directory for benchmark tables and manifest",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(r"D:\my lab\LeakCheck\data\OpenBMI"),
        help="Root path to OpenBMI dataset",
    )
    parser.add_argument("--target-fs", type=float, default=250.0, help="Downsampled sfreq in Hz")
    parser.add_argument("--tmin", type=float, default=-0.5, help="Epoch start in seconds")
    parser.add_argument("--tmax", type=float, default=4.0, help="Epoch end in seconds")
    parser.add_argument("--bandpass", type=str, default="8.0,30.0", help="l_freq,h_freq or 'none'")
    parser.add_argument("--baseline", type=str, default="-0.5,0.0", help="bmin,bmax or 'none'")
    parser.add_argument("--reject-ptp-uv", type=float, default=150.0, help="Artifact threshold in uV")
    parser.add_argument("--seed", type=int, default=0, help="Base random seed")
    parser.add_argument("--n-repeats-d1s", type=int, default=20, help="Number of D1s repeats")
    parser.add_argument("--n-repeats-d1m", type=int, default=5, help="Number of D1m repeats")
    parser.add_argument("--n-csp", type=int, default=6, help="Number of CSP components")

    args = parser.parse_args()

    # Parse parameters
    subjects = parse_subjects(args.subjects)
    designs = [d.strip() for d in args.designs.split(",") if d.strip()]
    decoders = [dec.strip() for dec in args.decoders.split(",") if dec.strip()]

    bandpass = None
    if args.bandpass.lower() != "none":
        bp_parts = [float(x.strip()) for x in args.bandpass.split(",")]
        bandpass = (bp_parts[0], bp_parts[1])

    baseline = None
    if args.baseline.lower() != "none":
        bl_parts = [float(x.strip()) for x in args.baseline.split(",")]
        baseline = (bl_parts[0], bl_parts[1])

    manifest = run_openbmi_benchmark(
        subjects=subjects,
        designs=designs,
        decoders=decoders,
        output_dir=args.output_dir,
        data_dir=args.data_dir,
        target_fs=args.target_fs,
        tmin=args.tmin,
        tmax=args.tmax,
        bandpass=bandpass,
        baseline=baseline,
        reject_ptp_uv=args.reject_ptp_uv,
        seed=args.seed,
        n_repeats_d1s=args.n_repeats_d1s,
        n_repeats_d1m=args.n_repeats_d1m,
        n_csp=args.n_csp,
    )

    print("\n================== BENCHMARK EXECUTION SUMMARY ==================")
    print(f"Status: SUCCESS")
    print(f"Elapsed Time: {manifest['elapsed_seconds']} s")
    print(f"Eligible Subjects: {manifest['arguments']['n_eligible']} / {len(subjects)}")
    print(f"Outputs written to: {args.output_dir.resolve()}")
    for fname, meta in manifest["output_files"].items():
        print(f"  - {fname}: {meta['rows']} rows, sha256={meta['sha256'][:12]}...")
    print("=================================================================\n")


if __name__ == "__main__":
    main()
