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
  Level 1: Fold-level trial metrics (accuracy, balanced_accuracy, auroc, f1, train_time_s, test_time_s, split_hash)
  Level 2: Participant-level repeat-first aggregate metrics and eligibility
  Level 3: Dataset-level Hodges-Lehmann differences, BCa 95% CIs, Wilcoxon p-values, Holm correction, Cohen's dz, rank-biserial
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
from sklearn.decomposition import FastICA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, f1_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

import emi
from emi.datasets_base import get_adapter, list_registered_adapters
import emi.datasets_adapters  # Ensure adapters are registered
from emi.decoders import (
    DECODERS,
    DEFAULT_FILTER_BANKS,
    ChannelScaler,
    ChannelSelector,
    CovarianceTransformer,
    FilterBankCSP,
    TangentSpaceTransformer,
    build_decoder_pipeline,
    get_csp_factory,
)
from emi.leakstats import bca_ci, cohens_dz, hodges_lehmann, holm, rank_biserial
from emi.splitters import kfold_repeats, loro_splits, size_matched_random_repeats

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("unified_benchmark")


def compute_split_hash(train_idx: np.ndarray, test_idx: np.ndarray) -> str:
    """Compute SHA-256 digest of train/test indices."""
    payload = f"train:{list(np.sort(train_idx))}|test:{list(np.sort(test_idx))}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def evaluate_fold(
    pipe: Pipeline,
    X_tr: np.ndarray,
    y_tr: np.ndarray,
    X_te: np.ndarray,
    y_te: np.ndarray,
) -> Tuple[float, float, float, float, float, float, float]:
    """Fit pipeline on X_tr/y_tr, evaluate on X_te/y_te.

    Returns:
      (acc, bal_acc, auroc, f1, tr_acc, train_time_s, test_time_s)
    """
    t0 = time.perf_counter()
    pipe.fit(X_tr, y_tr)
    train_time_s = time.perf_counter() - t0

    t1 = time.perf_counter()
    y_pred = pipe.predict(X_te)
    test_time_s = time.perf_counter() - t1

    tr_acc = float(pipe.score(X_tr, y_tr))
    acc = float(np.mean(y_pred == y_te))

    bal_acc = float(balanced_accuracy_score(y_te, y_pred)) if len(np.unique(y_te)) == 2 else np.nan
    f1 = float(f1_score(y_te, y_pred, average="binary", zero_division=0)) if len(np.unique(y_te)) == 2 else np.nan

    auroc = np.nan
    if len(np.unique(y_te)) == 2:
        score_vec = None
        if hasattr(pipe, "predict_proba"):
            try:
                proba = pipe.predict_proba(X_te)
                if proba.shape[1] == 2:
                    score_vec = proba[:, 1]
            except Exception:
                pass
        if score_vec is None and hasattr(pipe, "decision_function"):
            try:
                df = pipe.decision_function(X_te)
                score_vec = np.ravel(df)
            except Exception:
                pass
        if score_vec is not None:
            try:
                auroc = float(roc_auc_score(y_te, score_vec))
            except Exception:
                auroc = np.nan

    return acc, bal_acc, auroc, f1, tr_acc, train_time_s, test_time_s


def get_loro_folds(runs: np.ndarray, y: Optional[np.ndarray] = None) -> List[Tuple[str, np.ndarray, np.ndarray]]:
    """Generate Leave-One-Run-Out folds for arbitrary K >= 2 runs."""
    unique_runs = np.unique(runs)
    if len(unique_runs) < 2:
        raise ValueError(
            "Leave-One-Run-Out (D3 LORO) requires at least 2 distinct acquisition runs; "
            "single-run cohorts cannot be evaluated under D3 without manufacturing artificial run boundaries."
        )

    loro_reps = loro_splits(runs)
    folds = []
    for tr_idx, te_idx in loro_reps[0]:
        held_out_run = int(runs[te_idx[0]])
        fold_label = f"leave_out_run_{held_out_run}"
        folds.append((fold_label, tr_idx, te_idx))
    return folds


def generate_synthetic_subject_epochs(
    adapter_name: str,
    subject: int,
    n_trials: int = 100,
    n_channels: int = 64,
    n_times: int = 750,
    sfreq: float = 250.0,
    n_runs: int = 2,
    seed: int = 42,
) -> Dict[str, Any]:
    """Generate reproducible synthetic EEG trials matching adapter montage for testing."""
    rng = np.random.RandomState(seed + subject)
    # Balanced classes
    y = np.array([0] * (n_trials // 2) + [1] * (n_trials // 2))
    # Runs distribution
    trials_per_run = n_trials // n_runs
    runs_list = []
    for r in range(n_runs):
        runs_list.extend([r] * trials_per_run)
    while len(runs_list) < n_trials:
        runs_list.append(0)
    runs = np.array(runs_list[:n_trials])
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
    dataset_name: str,
    subject: int,
    data: Dict[str, Any],
    decoders: List[str],
    n_csp: int = 6,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Run D3: Operational Leave-One-Run-Out partition for arbitrary K >= 2 runs."""
    X, y, runs = data["X"], data["y"], data["runs"]
    try:
        folds = get_loro_folds(runs, y)
    except ValueError as exc:
        log.warning("Subject %s ineligible for D3 (LORO): %s", subject, exc)
        return [], {}

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
            pipe = build_decoder_pipeline(dec, n_csp=n_csp, sfreq=data.get("sfreq", 250.0))
            acc, bal_acc, auroc, f1, tr_acc, tr_time, te_time = evaluate_fold(pipe, X_tr, y_tr, X_te, y_te)

            records.append({
                "dataset": dataset_name,
                "subject_id": subject,
                "subject": subject,
                "decoder": dec,
                "design": "D3_loro",
                "repeat": 0,
                "fold": fold_idx,
                "fold_id": f"fold_{fold_idx}",
                "fold_label": fold_label,
                "n_train": len(y_tr),
                "n_test": len(y_te),
                "accuracy": acc,
                "balanced_accuracy": bal_acc,
                "auroc": auroc,
                "f1": f1,
                "train_acc": tr_acc,
                "train_time_s": round(tr_time, 5),
                "test_time_s": round(te_time, 5),
                "split_hash": shash,
            })

    return records, splits_manifest


def run_d1s_size_matched(
    dataset_name: str,
    subject: int,
    data: Dict[str, Any],
    decoders: List[str],
    n_csp: int = 6,
    n_repeats: int = 20,
    base_seed: int = 0,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Run D1s: Size- and class-matched pooled random partition using splitters.py."""
    X, y, runs = data["X"], data["y"], data["runs"]
    unique_runs = np.unique(runs)
    if len(unique_runs) < 2:
        repeats_list = []
        c0_idx = np.where(y == 0)[0]
        c1_idx = np.where(y == 1)[0]
        for rep in range(n_repeats):
            rng = np.random.RandomState(base_seed + rep)
            s0, s1 = rng.permutation(c0_idx), rng.permutation(c1_idx)
            h0 = np.sort(np.concatenate([s0[: len(s0) // 2], s1[: len(s1) // 2]]))
            h1 = np.sort(np.concatenate([s0[len(s0) // 2 :], s1[len(s1) // 2 :]]))
            repeats_list.append([(h1, h0), (h0, h1)])
    else:
        repeats_list = size_matched_random_repeats(y, runs, repeats=n_repeats, seed=base_seed)

    records: List[Dict[str, Any]] = []
    splits_manifest: Dict[str, Any] = {}

    for rep, folds_list in enumerate(repeats_list):
        for f_idx, (tr_idx, te_idx) in enumerate(folds_list):
            shash = compute_split_hash(tr_idx, te_idx)
            splits_manifest[f"rep_{rep}_fold_{f_idx}"] = {
                "train_idx": tr_idx.tolist(),
                "test_idx": te_idx.tolist(),
                "split_hash": shash,
            }

            X_tr, y_tr = X[tr_idx], y[tr_idx]
            X_te, y_te = X[te_idx], y[te_idx]

            for dec in decoders:
                pipe = build_decoder_pipeline(dec, n_csp=n_csp, sfreq=data.get("sfreq", 250.0))
                acc, bal_acc, auroc, f1, tr_acc, tr_time, te_time = evaluate_fold(pipe, X_tr, y_tr, X_te, y_te)

                records.append({
                    "dataset": dataset_name,
                    "subject_id": subject,
                    "subject": subject,
                    "decoder": dec,
                    "design": "D1s_size_matched",
                    "repeat": rep,
                    "fold": f_idx,
                    "fold_id": f"rep{rep}_fold{f_idx}",
                    "fold_label": f"rep{rep}_fold{f_idx}",
                    "n_train": len(y_tr),
                    "n_test": len(y_te),
                    "accuracy": acc,
                    "balanced_accuracy": bal_acc,
                    "auroc": auroc,
                    "f1": f1,
                    "train_acc": tr_acc,
                    "train_time_s": round(tr_time, 5),
                    "test_time_s": round(te_time, 5),
                    "split_hash": shash,
                })

    return records, splits_manifest


def run_d1m_matched_k(
    dataset_name: str,
    subject: int,
    data: Dict[str, Any],
    decoders: List[str],
    n_csp: int = 6,
    n_repeats: int = 10,
    base_seed: int = 0,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Run D1m: Stratified K-fold cross-validation with K = number of runs."""
    X, y, runs = data["X"], data["y"], data["runs"]
    k = max(2, len(np.unique(runs)))
    repeats_list = kfold_repeats(y, k=k, stratified=True, repeats=n_repeats, seed=base_seed)

    records: List[Dict[str, Any]] = []
    splits_manifest: Dict[str, Any] = {}

    for rep, folds_list in enumerate(repeats_list):
        for f_idx, (tr_idx, te_idx) in enumerate(folds_list):
            shash = compute_split_hash(tr_idx, te_idx)
            splits_manifest[f"rep_{rep}_fold_{f_idx}"] = {
                "train_idx": tr_idx.tolist(),
                "test_idx": te_idx.tolist(),
                "split_hash": shash,
            }

            X_tr, y_tr = X[tr_idx], y[tr_idx]
            X_te, y_te = X[te_idx], y[te_idx]

            for dec in decoders:
                pipe = build_decoder_pipeline(dec, n_csp=n_csp, sfreq=data.get("sfreq", 250.0))
                acc, bal_acc, auroc, f1, tr_acc, tr_time, te_time = evaluate_fold(pipe, X_tr, y_tr, X_te, y_te)

                records.append({
                    "dataset": dataset_name,
                    "subject_id": subject,
                    "subject": subject,
                    "decoder": dec,
                    "design": "D1m_matched_k",
                    "repeat": rep,
                    "fold": f_idx,
                    "fold_id": f"rep{rep}_fold{f_idx}",
                    "fold_label": f"rep{rep}_fold{f_idx}",
                    "n_train": len(y_tr),
                    "n_test": len(y_te),
                    "accuracy": acc,
                    "balanced_accuracy": bal_acc,
                    "auroc": auroc,
                    "f1": f1,
                    "train_acc": tr_acc,
                    "train_time_s": round(tr_time, 5),
                    "test_time_s": round(te_time, 5),
                    "split_hash": shash,
                })

    return records, splits_manifest


def run_p1_csp_on_all(
    dataset_name: str,
    subject: int,
    data: Dict[str, Any],
    decoders: List[str],
    n_csp: int = 6,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Run P1: Supervised Spatial Filter Contamination under LORO partition across all decoders."""
    X, y, runs = data["X"], data["y"], data["runs"]
    try:
        folds = get_loro_folds(runs, y)
    except ValueError as exc:
        log.warning("Subject %s ineligible for P1 (LORO): %s", subject, exc)
        return [], {}

    records: List[Dict[str, Any]] = []
    splits_manifest: Dict[str, Any] = {}

    for fold_idx, (fold_label, train_idx, test_idx) in enumerate(folds):
        splits_manifest[f"fold_{fold_idx}"] = {
            "label": fold_label,
            "train_idx": train_idx.tolist(),
            "test_idx": test_idx.tolist(),
            "split_hash": compute_split_hash(train_idx, test_idx),
        }

    for dec in decoders:
        # Determine design label and contaminated feature pipeline
        if dec in ("csp_lda", "csp_svm", "csp_lr"):
            design_name = "P1_csp_on_all"
            global_csp = get_csp_factory("rank_safe")(n_csp)
            global_csp.fit(X, y)
            Z_all = global_csp.transform(X)
            clf_factory = lambda: DECODERS[dec].head()
        elif dec == "ts_lr":
            design_name = "P1_ts_on_all"
            cov_trans = CovarianceTransformer()
            cov_all = cov_trans.transform(X)
            global_ts = TangentSpaceTransformer()
            global_ts.fit(cov_all)
            T_all = global_ts.transform(cov_all)
            scaler = StandardScaler()
            Z_all = scaler.fit_transform(T_all)
            clf_factory = lambda: DECODERS["ts_lr"].head()
        elif dec == "fbcsp":
            design_name = "P1_csp_on_all"
            fbcsp_step = FilterBankCSP(
                sfreq=data.get("sfreq", 250.0),
                bands=DEFAULT_FILTER_BANKS,
                n_components=n_csp,
            )
            sel = SelectKBest(score_func=f_classif, k=8)
            pipe_prep = Pipeline([("fbcsp", fbcsp_step), ("select", sel)])
            Z_all = pipe_prep.fit_transform(X, y)
            clf_factory = lambda: DECODERS["fbcsp"].head()
        else:
            continue

        for fold_idx, (fold_label, train_idx, test_idx) in enumerate(folds):
            shash = splits_manifest[f"fold_{fold_idx}"]["split_hash"]
            Z_tr, y_tr = Z_all[train_idx], y[train_idx]
            Z_te, y_te = Z_all[test_idx], y[test_idx]

            clf = clf_factory()
            t0 = time.perf_counter()
            clf.fit(Z_tr, y_tr)
            tr_time = time.perf_counter() - t0

            t1 = time.perf_counter()
            y_pred = clf.predict(Z_te)
            te_time = time.perf_counter() - t1

            tr_acc = float(clf.score(Z_tr, y_tr))
            acc = float(np.mean(y_pred == y_te))
            bal_acc = float(balanced_accuracy_score(y_te, y_pred)) if len(np.unique(y_te)) == 2 else np.nan
            f1 = float(f1_score(y_te, y_pred, average="binary", zero_division=0)) if len(np.unique(y_te)) == 2 else np.nan

            auroc = np.nan
            if len(np.unique(y_te)) == 2:
                score_vec = None
                if hasattr(clf, "predict_proba"):
                    try:
                        p = clf.predict_proba(Z_te)
                        if p.shape[1] == 2:
                            score_vec = p[:, 1]
                    except Exception:
                        pass
                if score_vec is None and hasattr(clf, "decision_function"):
                    try:
                        score_vec = np.ravel(clf.decision_function(Z_te))
                    except Exception:
                        pass
                if score_vec is not None:
                    try:
                        auroc = float(roc_auc_score(y_te, score_vec))
                    except Exception:
                        auroc = np.nan

            records.append({
                "dataset": dataset_name,
                "subject_id": subject,
                "subject": subject,
                "decoder": dec,
                "design": design_name,
                "repeat": 0,
                "fold": fold_idx,
                "fold_id": f"fold_{fold_idx}",
                "fold_label": fold_label,
                "n_train": len(y_tr),
                "n_test": len(y_te),
                "accuracy": acc,
                "balanced_accuracy": bal_acc,
                "auroc": auroc,
                "f1": f1,
                "train_acc": tr_acc,
                "train_time_s": round(tr_time, 5),
                "test_time_s": round(te_time, 5),
                "split_hash": shash,
            })

    return records, splits_manifest


def run_p2_ica_on_all(
    dataset_name: str,
    subject: int,
    data: Dict[str, Any],
    decoders: List[str],
    n_csp: int = 6,
    n_components: int = 16,
    random_state: int = 42,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Run P2: Global ICA unmixing contamination under LORO partition."""
    X, y, runs = data["X"], data["y"], data["runs"]
    try:
        folds = get_loro_folds(runs, y)
    except ValueError as exc:
        log.warning("Subject %s ineligible for P2 (LORO): %s", subject, exc)
        return [], {}

    n_trials, n_ch, n_times = X.shape
    n_comp = min(n_components, n_ch - 1)
    if n_comp < 2:
        n_comp = min(4, n_ch)

    # Fit FastICA on all trials before split
    X_2d = X.transpose(1, 0, 2).reshape(n_ch, -1).T
    ica = FastICA(n_components=n_comp, random_state=random_state, max_iter=200, tol=1e-3)
    S = ica.fit_transform(X_2d)
    X_clean_2d = ica.inverse_transform(S)
    X_leaky = X_clean_2d.T.reshape(n_ch, n_trials, n_times).transpose(1, 0, 2)

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
        X_tr, y_tr = X_leaky[train_idx], y[train_idx]
        X_te, y_te = X_leaky[test_idx], y[test_idx]

        for dec in decoders:
            pipe = build_decoder_pipeline(dec, n_csp=n_csp, sfreq=data.get("sfreq", 250.0))
            acc, bal_acc, auroc, f1, tr_acc, tr_time, te_time = evaluate_fold(pipe, X_tr, y_tr, X_te, y_te)

            records.append({
                "dataset": dataset_name,
                "subject_id": subject,
                "subject": subject,
                "decoder": dec,
                "design": "P2_ica_on_all",
                "repeat": 0,
                "fold": fold_idx,
                "fold_id": f"fold_{fold_idx}",
                "fold_label": fold_label,
                "n_train": len(y_tr),
                "n_test": len(y_te),
                "accuracy": acc,
                "balanced_accuracy": bal_acc,
                "auroc": auroc,
                "f1": f1,
                "train_acc": tr_acc,
                "train_time_s": round(tr_time, 5),
                "test_time_s": round(te_time, 5),
                "split_hash": shash,
            })

    return records, splits_manifest


def run_p5_scale_on_all(
    dataset_name: str,
    subject: int,
    data: Dict[str, Any],
    decoders: List[str],
    n_csp: int = 6,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Run P5: Global Feature Normalization / Scaling across all trials."""
    X, y, runs = data["X"], data["y"], data["runs"]
    try:
        folds = get_loro_folds(runs, y)
    except ValueError as exc:
        log.warning("Subject %s ineligible for P5 (LORO): %s", subject, exc)
        return [], {}

    scaler = ChannelScaler()
    X_scaled = scaler.fit(X).transform(X)

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
        X_tr, y_tr = X_scaled[train_idx], y[train_idx]
        X_te, y_te = X_scaled[test_idx], y[test_idx]

        for dec in decoders:
            pipe = build_decoder_pipeline(dec, n_csp=n_csp, sfreq=data.get("sfreq", 250.0))
            acc, bal_acc, auroc, f1, tr_acc, tr_time, te_time = evaluate_fold(pipe, X_tr, y_tr, X_te, y_te)

            records.append({
                "dataset": dataset_name,
                "subject_id": subject,
                "subject": subject,
                "decoder": dec,
                "design": "P5_scale_on_all",
                "repeat": 0,
                "fold": fold_idx,
                "fold_id": f"fold_{fold_idx}",
                "fold_label": fold_label,
                "n_train": len(y_tr),
                "n_test": len(y_te),
                "accuracy": acc,
                "balanced_accuracy": bal_acc,
                "auroc": auroc,
                "f1": f1,
                "train_acc": tr_acc,
                "train_time_s": round(tr_time, 5),
                "test_time_s": round(te_time, 5),
                "split_hash": shash,
            })

    return records, splits_manifest


def run_p7_select_on_all(
    dataset_name: str,
    subject: int,
    data: Dict[str, Any],
    decoders: List[str],
    n_csp: int = 6,
    n_keep: int = 16,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Run P7: Global Channel / Feature Selection across all trials."""
    X, y, runs = data["X"], data["y"], data["runs"]
    try:
        folds = get_loro_folds(runs, y)
    except ValueError as exc:
        log.warning("Subject %s ineligible for P7 (LORO): %s", subject, exc)
        return [], {}

    n_ch = X.shape[1]
    keep = min(n_keep, max(4, n_ch // 2))
    selector = ChannelSelector(n_keep=keep)
    X_selected = selector.fit(X, y).transform(X)

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
        X_tr, y_tr = X_selected[train_idx], y[train_idx]
        X_te, y_te = X_selected[test_idx], y[test_idx]

        for dec in decoders:
            pipe = build_decoder_pipeline(dec, n_csp=min(n_csp, max(2, keep // 2)), sfreq=data.get("sfreq", 250.0))
            acc, bal_acc, auroc, f1, tr_acc, tr_time, te_time = evaluate_fold(pipe, X_tr, y_tr, X_te, y_te)

            records.append({
                "dataset": dataset_name,
                "subject_id": subject,
                "subject": subject,
                "decoder": dec,
                "design": "P7_select_on_all",
                "repeat": 0,
                "fold": fold_idx,
                "fold_id": f"fold_{fold_idx}",
                "fold_label": fold_label,
                "n_train": len(y_tr),
                "n_test": len(y_te),
                "accuracy": acc,
                "balanced_accuracy": bal_acc,
                "auroc": auroc,
                "f1": f1,
                "train_acc": tr_acc,
                "train_time_s": round(tr_time, 5),
                "test_time_s": round(te_time, 5),
                "split_hash": shash,
            })

    return records, splits_manifest


def compute_design_contrasts(
    participant_df: pd.DataFrame,
    dataset_name: str = "dataset",
    seed: int = 42,
) -> pd.DataFrame:
    """Compute Level 3 dataset contrasts: Hodges-Lehmann difference, BCa CI, Wilcoxon p, Holm correction."""
    results: List[Dict[str, Any]] = []

    candidate_contrasts = [
        ("D1s_vs_D3", "D1s_size_matched", "D3_loro", "Pooled Size-Matched Partitioning Effect"),
        ("D1m_vs_D3", "D1m_matched_k", "D3_loro", "Pooled K-Matched Partitioning Effect"),
        ("P1_vs_D3", "P1_csp_on_all", "D3_loro", "Supervised Spatial Filter Contamination"),
        ("P2_vs_D3", "P2_ica_on_all", "D3_loro", "Global ICA Unmixing Contamination Effect"),
        ("P5_vs_D3", "P5_scale_on_all", "D3_loro", "Global Feature Normalization Effect"),
        ("P7_vs_D3", "P7_select_on_all", "D3_loro", "Global Channel Selection Contamination"),
    ]

    for dec in participant_df["decoder"].unique():
        sub_df = participant_df[participant_df["decoder"] == dec]
        available_designs = set(sub_df["design"].unique())

        contrast_rows: List[Dict[str, Any]] = []
        raw_pvals: List[float] = []

        for contrast_name, cond_b, cond_a, desc in candidate_contrasts:
            actual_cond_b = cond_b
            actual_desc = desc
            if contrast_name == "P1_vs_D3":
                if "P1_ts_on_all" in available_designs:
                    actual_cond_b = "P1_ts_on_all"
                    actual_desc = "Global Riemannian Tangent Space Reference Contamination"

            if actual_cond_b not in available_designs or cond_a not in available_designs:
                continue

            df_b = sub_df[sub_df["design"] == actual_cond_b].set_index("subject_id")["mean_accuracy"]
            df_a = sub_df[sub_df["design"] == cond_a].set_index("subject_id")["mean_accuracy"]
            common = df_b.index.intersection(df_a.index)
            if len(common) == 0:
                continue

            d = (df_b.loc[common] - df_a.loc[common]).values * 100.0  # in percentage points
            n = len(d)

            row: Dict[str, Any] = {
                "dataset": dataset_name,
                "contrast": contrast_name,
                "estimator": "hodges_lehmann",
                "decoder": dec,
                "description": actual_desc,
                "condition_a": cond_a,
                "condition_b": actual_cond_b,
                "n_subjects": n,
                "mean_diff_pp": float(np.mean(d)) if n > 0 else np.nan,
                "std_diff_pp": float(np.std(d, ddof=1)) if n > 1 else np.nan,
                "median_diff_pp": float(np.median(d)) if n > 0 else np.nan,
                "hodges_lehmann_delta": np.nan,
                "bca_ci_lower": np.nan,
                "bca_ci_upper": np.nan,
                "hl_ci_method": "none",
                "wilcoxon_w": np.nan,
                "raw_p_value": np.nan,
                "holm_p_value": np.nan,
                "cohens_dz": np.nan,
                "rank_biserial": np.nan,
            }

            if n >= 3:
                row["hodges_lehmann_delta"] = float(hodges_lehmann(d))
                ci_lo, ci_hi, ci_meth = bca_ci(d, n_resamples=2000, seed=seed, return_method=True)
                row["bca_ci_lower"] = float(ci_lo) if np.isfinite(ci_lo) else np.nan
                row["bca_ci_upper"] = float(ci_hi) if np.isfinite(ci_hi) else np.nan
                row["hl_ci_method"] = ci_meth

                if np.allclose(d, 0):
                    p_val = 1.0
                    w_stat = 0.0
                else:
                    try:
                        res = stats.wilcoxon(d, zero_method="pratt")
                        p_val = float(res.pvalue)
                        w_stat = float(res.statistic)
                    except Exception:
                        p_val = 1.0
                        w_stat = 0.0
                row["wilcoxon_w"] = w_stat
                row["raw_p_value"] = p_val
                raw_pvals.append(p_val)
                row["rank_biserial"] = float(rank_biserial(d))
                row["cohens_dz"] = float(cohens_dz(d))
            else:
                raw_pvals.append(np.nan)

            contrast_rows.append(row)

        # Holm adjustment across evaluated contrasts for this decoder
        valid_indices = [i for i, p in enumerate(raw_pvals) if np.isfinite(p)]
        if valid_indices:
            sub_pvals = [raw_pvals[i] for i in valid_indices]
            adj = holm(sub_pvals)
            for idx, adj_p in zip(valid_indices, adj):
                contrast_rows[idx]["holm_p_value"] = float(adj_p)

        results.extend(contrast_rows)

    cols = [
        "dataset", "contrast", "estimator", "decoder",
        "hodges_lehmann_delta", "bca_ci_lower", "bca_ci_upper",
        "wilcoxon_w", "raw_p_value", "holm_p_value",
        "cohens_dz", "rank_biserial",
        "description", "condition_a", "condition_b",
        "n_subjects", "mean_diff_pp", "std_diff_pp", "median_diff_pp",
        "hl_ci_method",
    ]
    if not results:
        return pd.DataFrame(columns=cols)
    return pd.DataFrame(results)[cols]


def main():
    parser = argparse.ArgumentParser(description="Unified Multi-Dataset LeakCheck V2 Benchmark Runner")
    parser.add_argument("--dataset", required=True, help="Registered dataset name (e.g. physionet, openbmi, cho2017, bnci2014_001, etc.)")
    parser.add_argument("--data-dir", default="data", help="Directory where dataset recordings are stored")
    parser.add_argument("--outdir", required=True, help="Directory to save benchmark metrics and manifests")
    parser.add_argument("--subjects", default="all", help="Subjects list, e.g. '1-10' or '1,2,3' or 'all'")
    parser.add_argument("--decoders", default="csp_lda,ts_lr", help="Comma-separated decoders (csp_lda, csp_svm, csp_lr, ts_lr, fbcsp)")
    parser.add_argument("--designs", default="D3,D1s,P1", help="Comma-separated designs (D3, D1s, D1m, P1, P2, P5, P7)")
    parser.add_argument("--synthetic", action="store_true", help="Generate synthetic test data matching adapter montage")
    parser.add_argument("--smoke", action="store_true", help="Smoke mode: run minimal repeats (1 repeat) for fast test execution")
    parser.add_argument("--n-csp", type=int, default=6, help="Number of CSP filters")
    parser.add_argument("--n-repeats-d1s", type=int, default=20, help="Number of repeats for D1s")
    parser.add_argument("--n-repeats-d1m", type=int, default=10, help="Number of repeats for D1m")
    parser.add_argument("--n-jobs", "--n_jobs", type=int, default=4, help="Number of worker jobs (for concurrency compatibility)")
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

    n_repeats_d1s = 1 if args.smoke else args.n_repeats_d1s
    n_repeats_d1m = 1 if args.smoke else args.n_repeats_d1m

    log.info("Running benchmark on %d subjects: %s", len(subjects), subjects)
    log.info("Decoders: %s | Designs: %s | Synthetic: %s | Smoke: %s", decoders, designs, args.synthetic, args.smoke)

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

        n_runs = len(np.unique(data["runs"]))
        row["n_runs"] = n_runs
        row["d3_eligible"] = bool(n_runs >= 2)
        if n_runs < 2:
            row["d3_ineligibility_reason"] = (
                f"Subject {sub} has {n_runs} acquisition run(s); D3 LORO requires K >= 2 distinct runs."
            )
            log.warning("Subject %d has %d run(s) (< 2); ineligible for D3 LORO partitions.", sub, n_runs)
        else:
            row["d3_ineligibility_reason"] = ""

        # 1. D3
        if "D3" in designs:
            d3_records, d3_splits = run_d3_loro(adapter.name, sub, data, decoders=decoders, n_csp=args.n_csp)
            all_fold_rows.extend(d3_records)
            sub_manifest["D3_loro"] = d3_splits

        # 2. D1s
        if "D1s" in designs:
            d1s_records, d1s_splits = run_d1s_size_matched(
                adapter.name, sub, data, decoders=decoders, n_csp=args.n_csp, n_repeats=n_repeats_d1s, base_seed=args.seed
            )
            all_fold_rows.extend(d1s_records)
            sub_manifest["D1s_size_matched"] = d1s_splits

        # 3. D1m
        if "D1m" in designs:
            d1m_records, d1m_splits = run_d1m_matched_k(
                adapter.name, sub, data, decoders=decoders, n_csp=args.n_csp, n_repeats=n_repeats_d1m, base_seed=args.seed
            )
            all_fold_rows.extend(d1m_records)
            sub_manifest["D1m_matched_k"] = d1m_splits

        # 4. P1
        if "P1" in designs:
            p1_records, p1_splits = run_p1_csp_on_all(adapter.name, sub, data, decoders=decoders, n_csp=args.n_csp)
            all_fold_rows.extend(p1_records)
            sub_manifest["P1_csp_on_all"] = p1_splits

        # 5. P2
        if "P2" in designs:
            p2_records, p2_splits = run_p2_ica_on_all(adapter.name, sub, data, decoders=decoders, n_csp=args.n_csp, random_state=args.seed)
            all_fold_rows.extend(p2_records)
            sub_manifest["P2_ica_on_all"] = p2_splits

        # 6. P5
        if "P5" in designs:
            p5_records, p5_splits = run_p5_scale_on_all(adapter.name, sub, data, decoders=decoders, n_csp=args.n_csp)
            all_fold_rows.extend(p5_records)
            sub_manifest["P5_scale_on_all"] = p5_splits

        # 7. P7
        if "P7" in designs:
            p7_records, p7_splits = run_p7_select_on_all(adapter.name, sub, data, decoders=decoders, n_csp=args.n_csp)
            all_fold_rows.extend(p7_records)
            sub_manifest["P7_select_on_all"] = p7_splits

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

    # Participant-level aggregation (repeat-first)
    rep_df = (
        fold_df.groupby(["dataset", "subject_id", "subject", "decoder", "design", "repeat"])
        .agg(
            rep_accuracy=("accuracy", "mean"),
            rep_balanced_accuracy=("balanced_accuracy", "mean"),
            rep_auroc=("auroc", "mean"),
            rep_f1=("f1", "mean"),
            rep_train_acc=("train_acc", "mean"),
        )
        .reset_index()
    )

    part_df = (
        rep_df.groupby(["dataset", "subject_id", "subject", "decoder", "design"])
        .agg(
            mean_accuracy=("rep_accuracy", "mean"),
            std_accuracy=("rep_accuracy", lambda x: float(np.std(x, ddof=1)) if len(x) > 1 else 0.0),
            sem_accuracy=("rep_accuracy", lambda x: float(stats.sem(x)) if len(x) > 1 else 0.0),
            median_accuracy=("rep_accuracy", "median"),
            mean_balanced_accuracy=("rep_balanced_accuracy", "mean"),
            mean_auroc=("rep_auroc", "mean"),
            mean_f1=("rep_f1", "mean"),
            mean_train_accuracy=("rep_train_acc", "mean"),
            n_repeats=("rep_accuracy", "count"),
        )
        .reset_index()
    )
    n_evals = fold_df.groupby(["dataset", "subject_id", "decoder", "design"]).size().reset_index(name="n_evaluations")
    part_df = part_df.merge(n_evals, on=["dataset", "subject_id", "decoder", "design"])
    part_df.to_csv(outdir / "participant_metrics.csv", index=False)

    # Design comparisons
    comp_df = compute_design_contrasts(part_df, dataset_name=adapter.name, seed=args.seed)
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
        "smoke": args.smoke,
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
