#!/usr/bin/env python3
"""
rebuild_and_verify_raw_edf.py — Non-Destructive Raw PhysioNet EDF+ Cache Rebuild,
Cache Array Comparison, 4-Protocol Benchmark Rerun, and Historical CSV Diff Utility.

Usage (from the LeakCheck repository root on a machine with raw EDFs or internet):
    python3 rebuild_and_verify_raw_edf.py \
        --edf-dir ./physionet_edf \
        --cache-dir ./cache/physionet_rebuilt \
        --historical-cache-dir ./cache/physionet \
        --historical-csv ./benchmark_results/physionet_v1_1/inflation_by_subject.csv \
        --out-dir ./benchmark_results/physionet_rebuilt
"""
import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import traceback
import numpy as np
import pandas as pd


EXPECTED_RUNS = (4, 8, 12)
EXPECTED_SFREQS = (160.0, 128.0)
EXPECTED_N_CHANNELS = 64


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def get_git_commit() -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "unknown_git_commit"


def verify_edf_run_mapping(subj: int, run_id: int, fpath: str) -> None:
    bname = os.path.basename(fpath)
    expected_prefix = f"S{subj:03d}R{run_id:02d}"
    if not re.match(rf"^{expected_prefix}\.edf$", bname, flags=re.IGNORECASE):
        raise ValueError(
            f"Run-to-file mapping mismatch for subject S{subj:03d}, run {run_id}: "
            f"expected '{expected_prefix}.edf', got '{bname}'"
        )


def compare_npz_caches(rebuilt_path: str, hist_path: str) -> dict:
    if not os.path.isfile(hist_path):
        return {"historical_cache_present": False}

    with np.load(rebuilt_path, allow_pickle=False) as reb, np.load(hist_path, allow_pickle=False) as hist:
        reb_keys = sorted(reb.files)
        hist_keys = sorted(hist.files)
        common_arrays = [k for k in ["X", "y", "runs"] if k in reb and k in hist]
        comp = {
            "historical_cache_present": True,
            "rebuilt_keys": reb_keys,
            "historical_keys": hist_keys,
            "sha256_equal": sha256_file(rebuilt_path) == sha256_file(hist_path),
        }
        for k in common_arrays:
            a_reb = reb[k]
            a_hist = hist[k]
            comp[f"{k}_shape_reb"] = list(a_reb.shape)
            comp[f"{k}_shape_hist"] = list(a_hist.shape)
            comp[f"{k}_dtype_reb"] = str(a_reb.dtype)
            comp[f"{k}_dtype_hist"] = str(a_hist.dtype)
            if a_reb.shape == a_hist.shape:
                max_diff = float(np.max(np.abs(a_reb.astype(np.float64) - a_hist.astype(np.float64))))
                comp[f"{k}_max_abs_diff"] = max_diff
                comp[f"{k}_exact_equal"] = bool(np.array_equal(a_reb, a_hist))
            else:
                comp[f"{k}_max_abs_diff"] = None
                comp[f"{k}_exact_equal"] = False
        return comp


def run_four_protocols_on_subject(X: np.ndarray, y: np.ndarray, runs: np.ndarray, seed: int = 0) -> dict:
    """
    Executes the four LeakCheck protocols (D3_loro, D1m_matched_k, D1s_size_matched, P1_csp_on_all)
    using the repository's splitter and decoder definitions if available, or identical MNE/sklearn calls.
    """
    from mne.decoding import CSP
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    from sklearn.model_selection import LeaveOneGroupOut, StratifiedKFold
    from sklearn.pipeline import Pipeline

    def make_clf():
        csp = CSP(n_components=4, reg="oas", log=True, norm_trace=False)
        lda = LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")
        return Pipeline([("csp", csp), ("lda", lda)])

    # 1. D3_loro (Run-held-out reference across runs 4, 8, 12)
    logo = LeaveOneGroupOut()
    d3_fold_accs = []
    d3_fold_specs = []
    for train_idx, test_idx in logo.split(X, y, groups=runs):
        clf = make_clf()
        clf.fit(X[train_idx], y[train_idx])
        preds = clf.predict(X[test_idx])
        d3_fold_accs.append(float(np.mean(preds == y[test_idx])))
        d3_fold_specs.append({
            "n_train_0": int(np.sum(y[train_idx] == 0)),
            "n_train_1": int(np.sum(y[train_idx] == 1)),
            "n_test_0": int(np.sum(y[test_idx] == 0)),
            "n_test_1": int(np.sum(y[test_idx] == 1)),
        })
    acc_d3 = float(np.mean(d3_fold_accs))

    # 2. D1m_matched_k (5 repeats of 3-fold StratifiedKFold)
    d1m_rep_accs = []
    for rep in range(5):
        skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=seed + rep)
        f_accs = []
        for train_idx, test_idx in skf.split(X, y):
            clf = make_clf()
            clf.fit(X[train_idx], y[train_idx])
            preds = clf.predict(X[test_idx])
            f_accs.append(float(np.mean(preds == y[test_idx])))
        d1m_rep_accs.append(float(np.mean(f_accs)))
    acc_d1m = float(np.mean(d1m_rep_accs))

    # 3. D1s_size_matched (20 repeats matching D3 fold train/test class counts)
    idx_c0 = np.where(y == 0)[0]
    idx_c1 = np.where(y == 1)[0]
    d1s_rep_accs = []
    for rep in range(20):
        f_accs = []
        for fold_i, spec in enumerate(d3_fold_specs):
            rng = np.random.default_rng(123 + rep * 1000 + fold_i)
            perm0 = rng.permutation(idx_c0)
            perm1 = rng.permutation(idx_c1)
            test_0 = perm0[: spec["n_test_0"]]
            train_0 = perm0[spec["n_test_0"] : spec["n_test_0"] + spec["n_train_0"]]
            test_1 = perm1[: spec["n_test_1"]]
            train_1 = perm1[spec["n_test_1"] : spec["n_test_1"] + spec["n_train_1"]]
            train_idx = np.concatenate([train_0, train_1])
            test_idx = np.concatenate([test_0, test_1])
            clf = make_clf()
            clf.fit(X[train_idx], y[train_idx])
            preds = clf.predict(X[test_idx])
            f_accs.append(float(np.mean(preds == y[test_idx])))
        d1s_rep_accs.append(float(np.mean(f_accs)))
    acc_d1s = float(np.mean(d1s_rep_accs))

    # 4. P1_csp_on_all (Global supervised CSP on all trials/labels before LORO LDA)
    csp_global = CSP(n_components=4, reg="oas", log=True, norm_trace=False)
    X_csp_all = csp_global.fit_transform(X, y)
    p1_fold_accs = []
    for train_idx, test_idx in logo.split(X_csp_all, y, groups=runs):
        lda = LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")
        lda.fit(X_csp_all[train_idx], y[train_idx])
        preds = lda.predict(X_csp_all[test_idx])
        p1_fold_accs.append(float(np.mean(preds == y[test_idx])))
    acc_p1 = float(np.mean(p1_fold_accs))

    return {
        "D3_loro": acc_d3,
        "D1m_matched_k": acc_d1m,
        "D1s_size_matched": acc_d1s,
        "P1_csp_on_all": acc_p1,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Non-destructively rebuild PhysioNet .npz caches, compare with historical caches, rerun protocols, and diff CSV outputs."
    )
    parser.add_argument("--edf-dir", default="./physionet_edf", help="Directory containing or downloading raw PhysioNet EDF+ files")
    parser.add_argument("--cache-dir", default="./cache/physionet_rebuilt", help="New directory for rebuilt .npz caches (never overwrites historical)")
    parser.add_argument("--historical-cache-dir", default="./cache/physionet", help="Historical cache directory for array-level comparison")
    parser.add_argument("--historical-csv", default="./benchmark_results/physionet_v1_1/inflation_by_subject.csv", help="Historical participant CSV for diffing")
    parser.add_argument("--out-dir", default="./benchmark_results/physionet_rebuilt", help="Output directory for rebuilt protocol CSV and comparison report")
    parser.add_argument("--skip-protocols", action="store_true", help="Only rebuild and compare caches without rerunning the 4 decoding protocols")
    args = parser.parse_args()

    if os.path.abspath(args.cache_dir) == os.path.abspath(args.historical_cache_dir):
        raise ValueError(
            "Refusing to overwrite historical cache directory! "
            "Pass a distinct --cache-dir (e.g., ./cache/physionet_rebuilt)."
        )

    os.makedirs(args.edf_dir, exist_ok=True)
    os.makedirs(args.cache_dir, exist_ok=True)
    os.makedirs(args.out_dir, exist_ok=True)

    try:
        import mne
        from mne.datasets import eegbci
        import scipy
        import sklearn
    except ImportError as exc:
        raise SystemExit(f"Missing required scientific packages (mne, scipy, scikit-learn): {exc}")

    manifest = {
        "git_commit": get_git_commit(),
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
        "sklearn_version": sklearn.__version__,
        "mne_version": mne.__version__,
        "preprocessing_contract": {
            "runs": list(EXPECTED_RUNS),
            "sfreq_hz": list(EXPECTED_SFREQS),
            "n_channels": EXPECTED_N_CHANNELS,
            "bandpass_hz": [8.0, 30.0],
            "fir_design": "firwin",
            "epoch_tmin_tmax_s": [-1.0, 4.0],
            "baseline": None,
            "crop_window_s": [1.0, 3.0],
            "include_tmax": False,
            "expected_n_times": {"160Hz": 320, "128Hz": 256},
            "label_mapping": {"T1_left_fist": 0, "T2_right_fist": 1},
        },
        "subjects": {},
    }

    eligible_subjects = []
    excluded_subjects = []
    error_subjects = []
    rebuilt_rows = []

    for subj in range(1, 110):
        sid = f"S{subj:03d}"
        try:
            raw_fnames = eegbci.load_data(
                subj,
                runs=list(EXPECTED_RUNS),
                path=args.edf_dir,
                update_path=False,
                verbose=False,
            )
            if len(raw_fnames) != len(EXPECTED_RUNS):
                raise RuntimeError(f"Expected {len(EXPECTED_RUNS)} EDF files for {sid}, got {len(raw_fnames)}")

            for r_id, fpath in zip(EXPECTED_RUNS, raw_fnames):
                verify_edf_run_mapping(subj, r_id, fpath)

            edf_hashes = {os.path.basename(p): sha256_file(p) for p in raw_fnames}
            X_list, y_list, run_list = [], [], []
            ch_names_ref = None
            per_run_counts = {}

            for r_id, fpath in zip(EXPECTED_RUNS, raw_fnames):
                raw = mne.io.read_raw_edf(fpath, preload=True, verbose=False)
                eegbci.standardize(raw)
                raw.pick_types(eeg=True, exclude="bads")
                sfreq = float(raw.info["sfreq"])
                if not any(abs(sfreq - s) < 1e-3 for s in EXPECTED_SFREQS):
                    raise ValueError(f"{sid} R{r_id:02d} sfreq={sfreq} Hz not in {EXPECTED_SFREQS}")
                expected_n_times = int(round(2.0 * sfreq))
                if len(raw.ch_names) != EXPECTED_N_CHANNELS:
                    raise ValueError(f"{sid} R{r_id:02d} n_channels={len(raw.ch_names)} != {EXPECTED_N_CHANNELS}")
                if ch_names_ref is None:
                    ch_names_ref = list(raw.ch_names)
                elif list(raw.ch_names) != ch_names_ref:
                    raise ValueError(f"{sid} channel order mismatch across runs")

                raw.filter(8.0, 30.0, fir_design="firwin", skip_by_annotation="edge", verbose=False)
                events, event_id = mne.events_from_annotations(raw, event_id={"T1": 1, "T2": 2}, verbose=False)
                epochs = mne.Epochs(
                    raw,
                    events,
                    event_id=event_id,
                    tmin=-1.0,
                    tmax=4.0,
                    baseline=None,
                    preload=True,
                    reject=None,
                    verbose=False,
                )
                ep_dec = epochs.copy().crop(1.0, 3.0, include_tmax=False)
                data = ep_dec.get_data(copy=True).astype(np.float64)
                if data.shape[2] != expected_n_times:
                    raise ValueError(f"{sid} R{r_id:02d} cropped time samples={data.shape[2]} != {expected_n_times}")
                labels = (ep_dec.events[:, 2] == 2).astype(np.int64)
                per_run_counts[f"R{r_id:02d}"] = {
                    "n_total": int(len(labels)),
                    "n_class0_T1": int(np.sum(labels == 0)),
                    "n_class1_T2": int(np.sum(labels == 1)),
                }
                X_list.append(data)
                y_list.append(labels)
                run_list.append(np.full(len(labels), r_id, dtype=np.int64))

            X = np.concatenate(X_list, axis=0)
            y = np.concatenate(y_list, axis=0)
            runs = np.concatenate(run_list, axis=0)

            npz_name = f"sub-{subj:03d}_epochs.npz"
            rebuilt_npz = os.path.join(args.cache_dir, npz_name)
            np.savez_compressed(
                rebuilt_npz,
                X=X,
                y=y,
                runs=runs,
                sfreq=np.float64(sfreq),
                ch_names=np.asarray(ch_names_ref),
            )
            npz_hash = sha256_file(rebuilt_npz)

            n_total = int(len(y))
            n_c0 = int(np.sum(y == 0))
            n_c1 = int(np.sum(y == 1))
            min_run = int(min(np.sum(runs == r) for r in EXPECTED_RUNS))
            eligible = (n_total >= 30) and (n_c0 >= 10) and (n_c1 >= 10) and (min_run >= 8)

            hist_npz = os.path.join(args.historical_cache_dir, npz_name)
            cache_diff = compare_npz_caches(rebuilt_npz, hist_npz)

            subj_entry = {
                "status": "ELIGIBLE" if eligible else "EXCLUDED_GATE",
                "n_trials": n_total,
                "n_class0": n_c0,
                "n_class1": n_c1,
                "min_per_run": min_run,
                "per_run_counts": per_run_counts,
                "shape": list(X.shape),
                "dtype_X": str(X.dtype),
                "ch_names": ch_names_ref,
                "edf_sha256": edf_hashes,
                "npz_sha256": npz_hash,
                "historical_cache_comparison": cache_diff,
            }

            if eligible:
                eligible_subjects.append(sid)
                if not args.skip_protocols:
                    accs = run_four_protocols_on_subject(X, y, runs, seed=0)
                    subj_entry["protocol_accuracies"] = accs
                    for design_name in ["D1m_matched_k", "D1s_size_matched", "P1_csp_on_all"]:
                        rebuilt_rows.append({
                            "subject": subj,
                            "design": design_name,
                            "acc_ref": accs["D3_loro"],
                            "acc_leaky": accs[design_name],
                            "delta_pp": (accs[design_name] - accs["D3_loro"]) * 100.0,
                        })
            else:
                excluded_subjects.append(sid)

            manifest["subjects"][sid] = subj_entry
            print(f"[{sid}] status={subj_entry['status']} | trials={n_total} (c0={n_c0}, c1={n_c1}, min_run={min_run}) | sha256={npz_hash[:12]}...")

        except Exception as exc:
            error_subjects.append(sid)
            manifest["subjects"][sid] = {
                "status": "ERROR",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "traceback": traceback.format_exc(),
            }
            print(f"[{sid}] ERROR ({type(exc).__name__}): {exc}", file=sys.stderr)

    manifest["summary"] = {
        "n_requested": 109,
        "n_eligible": len(eligible_subjects),
        "n_excluded_gate": len(excluded_subjects),
        "n_errors": len(error_subjects),
        "eligible_subject_ids": eligible_subjects,
        "excluded_subject_ids": excluded_subjects,
        "error_subject_ids": error_subjects,
    }

    manifest_path = os.path.join(args.out_dir, "cache_manifest_sha256.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print("\n" + "=" * 80)
    print("RAW-EDF CACHE REBUILD SUMMARY")
    print("=" * 80)
    print(f"Eligible Subjects ({len(eligible_subjects)}) : {eligible_subjects}")
    print(f"Excluded by Gate  ({len(excluded_subjects)}) : {excluded_subjects}")
    print(f"Errors            ({len(error_subjects)}) : {error_subjects}")
    print(f"Manifest Saved To : {os.path.abspath(manifest_path)}")

    # Save rebuilt CSV and compare against historical CSV if protocols ran
    if not args.skip_protocols and rebuilt_rows:
        rebuilt_df = pd.DataFrame(rebuilt_rows).sort_values(["design", "subject"]).reset_index(drop=True)
        rebuilt_csv_path = os.path.join(args.out_dir, "inflation_by_subject_rebuilt.csv")
        rebuilt_df.to_csv(rebuilt_csv_path, index=False)
        print(f"Rebuilt CSV Saved : {os.path.abspath(rebuilt_csv_path)} (N={rebuilt_df['subject'].nunique()} subjects)")

        if os.path.isfile(args.historical_csv):
            hist_df = pd.read_csv(args.historical_csv)
            hist_subs = set(hist_df["subject"].unique())
            reb_subs = set(rebuilt_df["subject"].unique())
            only_in_hist = sorted(hist_subs - reb_subs)
            only_in_reb = sorted(reb_subs - hist_subs)
            print("-" * 80)
            print("HISTORICAL VS. REBUILT CSV COMPARISON:")
            print(f"   - Historical N={len(hist_subs)} vs. Rebuilt N={len(reb_subs)}")
            print(f"   - Subjects only in historical CSV : {[f'S{i:03d}' for i in only_in_hist]}")
            print(f"   - Subjects only in rebuilt CSV    : {[f'S{i:03d}' for i in only_in_reb]}")
            merged = pd.merge(
                hist_df,
                rebuilt_df,
                on=["subject", "design"],
                how="inner",
                suffixes=("_hist", "_reb"),
                validate="one_to_one",
            )
            for dname in ["D1s_size_matched", "D1m_matched_k", "P1_csp_on_all"]:
                sub_m = merged[merged["design"] == dname]
                max_ref_diff = float(np.max(np.abs(sub_m["acc_ref_hist"] - sub_m["acc_ref_reb"])) * 100.0)
                max_lky_diff = float(np.max(np.abs(sub_m["acc_leaky_hist"] - sub_m["acc_leaky_reb"])) * 100.0)
                max_del_diff = float(np.max(np.abs(sub_m["delta_pp_hist"] - sub_m["delta_pp_reb"])))
                print(
                    f"   - {dname:18s} (overlap N={len(sub_m)}): "
                    f"max |acc_ref diff|={max_ref_diff:.4e} pp | "
                    f"max |acc_leaky diff|={max_lky_diff:.4e} pp | "
                    f"max |delta_pp diff|={max_del_diff:.4e} pp"
                )
    print("=" * 80)

    if error_subjects:
        sys.exit(1)


if __name__ == "__main__":
    main()
