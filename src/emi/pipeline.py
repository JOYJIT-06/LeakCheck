"""One-subject pipeline used by the command-line scripts."""
import json
import logging
from pathlib import Path

import numpy as np
import sklearn

from . import __version__, data, decode, plotting, preprocess, tfr
from .config import EVENT_ID, Config
from .decoders import get_csp_factory

log = logging.getLogger(__name__)


def run_subject(subject: int, cfg: Config, outdir, make_figures: bool = True, csp: str = "rank_safe") -> dict:
    """Load, clean, analyse and save results for one subject. Returns the result dict.

    Primary accuracy = leave-one-run-out (`mean_acc`, `perm_p`, the larger p of the permutation and the circular-shift
    null). Random-split accuracy is added as a labelled comparison. `csp` names the CSP implementation and is written
    into the result; the report also lists trials lost, bad channels and removed ICA components for this subject.
    """
    import mne

    sub_dir = Path(outdir) / f"sub-{subject:03d}"
    sub_dir.mkdir(parents=True, exist_ok=True)
    factory = get_csp_factory(csp, cfg.csp_reg)

    raw = data.load_raw(subject, cfg)
    raw_clean, prep_info = preprocess.clean_raw(raw, cfg)
    ep_bb, ep_dec, runs, qc = preprocess.build_epochs_full(raw_clean, cfg)

    X = ep_dec.get_data()
    y = (ep_dec.events[:, 2] == EVENT_ID["right"]).astype(int)
    loro = decode.evaluate_loro(X, y, runs, cfg, factory)
    rand = decode.evaluate(X, y, cfg_no_perm(cfg), factory)
    result = {"subject": int(subject), "csp_impl": csp, **prep_info, **qc, **loro,
              "random_split_acc": rand["mean_acc"], "random_split_note": rand["validation"]}
    result["versions"] = {"emi": __version__, "mne": mne.__version__,
                          "scikit-learn": sklearn.__version__, "numpy": np.__version__}
    result["config"] = cfg.to_dict()

    if make_figures and len(ep_bb) >= 10:
        erd, times, freqs, ch_names = tfr.compute_erd(ep_bb, cfg)
        for name, band in (("mu", cfg.mu_band), ("beta", cfg.beta_band)):
            plotting.plot_erd_timecourses(erd, times, freqs, ch_names, band, sub_dir / f"erd_{name}.png",
                                          title=f"Subject {subject}: {name} band ({len(ep_bb)} trials)")
        try:
            fig = decode.csp_patterns_figure(ep_dec, X, y, cfg)
            fig.savefig(sub_dir / "csp_patterns.png", dpi=150)
        except Exception as exc:  # plotting must not stop the analysis
            log.warning("CSP pattern plot failed: %s", exc)

    with open(sub_dir / "result.json", "w") as f:
        json.dump(result, f, indent=2, default=str)
    return result


def cfg_no_perm(cfg: Config) -> Config:
    """Same settings without the (slow) permutation test; used for the labelled random-split comparison."""
    from dataclasses import replace
    return replace(cfg, n_perm=0)


def evaluate_loro_fold_isolated(subject, cfg: Config, factory=None) -> dict:
    """True fold-isolated LORO: fit preprocessor strictly on train runs, transform test run.

    Parameters
    ----------
    subject : int or list of mne.io.BaseRaw
        Either subject ID (loaded via data.load_raw_runs) or pre-loaded list of run BaseRaws.
    cfg : Config
        Configuration options.
    factory : callable, optional
        CSP factory function (defaults to rank_safe CSP factory).

    Returns
    -------
    dict
        Evaluation results with fold_details and pooled accuracy.
    """
    if isinstance(subject, (list, tuple)):
        raw_runs = list(subject)
    else:
        raw_runs = data.load_raw_runs(int(subject), cfg)

    n_runs = len(raw_runs)
    if n_runs < 2:
        raise ValueError("Leave-one-run-out requires at least 2 runs.")

    csp_factory = factory or get_csp_factory(getattr(cfg, "csp_impl", "rank_safe"), cfg.csp_reg)
    fold_accs = []
    fold_details = []
    y_true_all, y_pred_all = [], []
    X_test_all, y_test_all, runs_test_all = [], [], []
    fold_specs = []

    for k in range(n_runs):
        train_runs = [raw_runs[i] for i in range(n_runs) if i != k]
        test_runs = [raw_runs[k]]

        prep = preprocess.FoldIsolatedPreprocessor(cfg)
        X_tr, y_tr = prep.fit_transform(train_runs)
        X_te, y_te = prep.transform(test_runs)

        if len(np.unique(y_tr)) < 2:
            raise ValueError(f"Fold {k} training set has only one class.")
        if len(y_te) == 0:
            raise ValueError(f"Fold {k} test set has 0 kept trials.")

        clf = decode.build_pipeline(cfg.n_csp, csp_factory)
        clf.fit(X_tr, y_tr)
        y_pred = clf.predict(X_te)

        fold_acc = float(np.mean(y_pred == y_te))
        fold_accs.append(fold_acc)
        y_true_all.extend(y_te.tolist())
        y_pred_all.extend(y_pred.tolist())
        X_test_all.append(X_te)
        y_test_all.append(y_te)
        runs_test_all.append(np.full(len(y_te), k))
        fold_specs.append({
            "n_train_0": int(np.sum(y_tr == 0)),
            "n_train_1": int(np.sum(y_tr == 1)),
            "n_test_0": int(np.sum(y_te == 0)),
            "n_test_1": int(np.sum(y_te == 1)),
        })
        fold_details.append({
            "fold": k,
            "test_run": k,
            "acc": fold_acc,
            "n_train": len(y_tr),
            "n_test": len(y_te),
            "threshold_uv": prep.reject_threshold_uv_,
            "bad_channels": list(prep.bad_channels_),
            "ica_excluded": list(prep.ica_excluded_),
        })

    pooled_acc = float(np.mean(np.array(y_pred_all) == np.array(y_true_all)))
    return {
        "validation": "leave-one-run-out (fold-isolated)",
        "mean_acc": pooled_acc,
        "acc_fold_mean": float(np.mean(fold_accs)),
        "n_trials": len(y_true_all),
        "n_folds": n_runs,
        "fold_details": fold_details,
        "y_true": np.array(y_true_all),
        "y_pred": np.array(y_pred_all),
        "X": np.concatenate(X_test_all, axis=0) if X_test_all else np.empty(0),
        "y": np.concatenate(y_test_all, axis=0) if y_test_all else np.empty(0),
        "runs": np.concatenate(runs_test_all, axis=0) if runs_test_all else np.empty(0),
        "fold_specs": fold_specs,
    }

