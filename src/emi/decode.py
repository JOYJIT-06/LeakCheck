"""Decoding for the basic pipeline: CSP + LDA, with leave-one-run-out as the PRIMARY design.

The decoder is the same specification the audit uses (emi.decoders.DECODERS['csp_lda']: LDA with lsqr solver and
automatic shrinkage), so the basic pipeline and LeakCheck cannot disagree about what 'CSP + LDA' means.

Random-split accuracy (`evaluate`, shuffled stratified k-fold) is kept as a LABELLED comparison: with trials of one
run in both training and test data it is the design the audit studies as possibly inflated.
"""
import numpy as np
from sklearn.model_selection import StratifiedKFold, permutation_test_score

from . import splitters as sp
from .config import Config
from .decoders import DECODERS, default_csp_factory
from .metrics import evaluate_repeats
from .nulls import NULL_GENERATORS, empirical_p


def build_pipeline(n_components: int = 4, csp_factory=None):
    """CSP is inside the pipeline, so it is re-fitted on training trials only in every fold."""
    return DECODERS["csp_lda"].build(csp_factory or default_csp_factory, n_csp=n_components)


def evaluate_loro(X, y, runs, cfg: Config, csp_factory=None, seed=None) -> dict:
    """Leave-one-run-out accuracy with a label-null p-value (null type from cfg.null_type). PRIMARY result."""
    X, y, runs = np.asarray(X), np.asarray(y).astype(int), np.asarray(runs).astype(int)
    if len(np.unique(runs)) < 2:
        raise ValueError("Leave-one-run-out needs at least 2 runs.")
    factory = csp_factory or default_csp_factory
    repeats = sp.loro_splits(runs)
    sp.validate_splits(repeats, y)

    def run(labels):
        return evaluate_repeats(lambda: build_pipeline(cfg.n_csp, factory), X, labels, repeats)

    m = run(y)
    out = {"validation": "leave-one-run-out (run-aware)", "n_trials": int(len(y)),
           "n_left": int((y == 0).sum()), "n_right": int((y == 1).sum()), "mean_acc": m["acc_pooled"],
           "acc_fold_mean": m["acc_fold_mean"], "bal_acc": m["bal_acc"], "auc": m["auc"], "n_folds": m["n_folds"],
           "majority_class_acc": float(max((y == 0).mean(), (y == 1).mean())), "null_type": cfg.null_type}
    if cfg.n_perm > 0:
        kinds = ("perm", "shift") if cfg.null_type == "both" else (cfg.null_type,)
        ps, means = {}, {}
        for kind in kinds:
            rng = np.random.default_rng((cfg.seed if seed is None else seed) + (0 if kind == "perm" else 1))
            null = [run(NULL_GENERATORS[kind](y, runs, rng))["acc_pooled"] for _ in range(cfg.n_perm)]
            ps[kind], means[kind] = empirical_p(m["acc_pooled"], null), float(np.mean(null))
        # Neither null is perfect: permutation ignores the label order, a shift keeps it but can reproduce the real
        # labels when they nearly alternate. The reported p is the more cautious (larger) of the two.
        out["perm_p"] = float(max(ps.values()))
        out.update({f"p_{k}": v for k, v in ps.items()})
        out.update({f"null_mean_acc_{k}": v for k, v in means.items()})
        out["min_possible_p"] = 1 / (1 + cfg.n_perm)
    else:
        out["perm_p"] = out["min_possible_p"] = float("nan")
    return out


def evaluate(X: np.ndarray, y: np.ndarray, cfg: Config, csp_factory=None) -> dict:
    """RANDOM-SPLIT accuracy (stratified shuffled k-fold) plus a label-permutation p-value.

    Not run-aware (audit design D2). Report it only as 'random-split accuracy', next to the leave-one-run-out
    number from `evaluate_loro`; do not use it alone for single-subject claims.
    """
    counts = np.bincount(y)
    if len(counts) != 2 or counts.min() < cfg.n_splits:
        raise ValueError(f"Not enough trials per class for {cfg.n_splits}-fold CV: {counts.tolist()}")
    cv = StratifiedKFold(n_splits=cfg.n_splits, shuffle=True, random_state=cfg.seed)
    clf = build_pipeline(cfg.n_csp, csp_factory)
    repeats = [[(tr, te) for tr, te in cv.split(np.zeros(len(y)), y)]]
    m = evaluate_repeats(lambda: build_pipeline(cfg.n_csp, csp_factory), X, y, repeats)
    out = {"n_trials": int(len(y)), "n_left": int(counts[0]), "n_right": int(counts[1]),
           "mean_acc": m["acc_pooled"], "acc_fold_mean": m["acc_fold_mean"],
           "majority_class_acc": float(counts.max() / counts.sum()),
           "validation": "stratified shuffled k-fold (not run-aware; audit design D2)"}
    if cfg.n_perm > 0:
        _, _, p = permutation_test_score(clf, X, y, cv=cv, n_permutations=cfg.n_perm, scoring="accuracy",
                                         random_state=cfg.seed, n_jobs=1)
        out["perm_p"] = float(p)
    else:
        out["perm_p"] = float("nan")
    return out


def csp_patterns_figure(epochs, X: np.ndarray, y: np.ndarray, cfg: Config):
    """CSP spatial patterns fitted on ALL trials with MNE's CSP. For visualisation only, never for accuracy."""
    from mne.decoding import CSP
    csp = CSP(n_components=cfg.n_csp, reg=cfg.csp_reg, log=True, norm_trace=False)
    csp.fit(X, y)
    return csp.plot_patterns(epochs.info, ch_type="eeg", units="Patterns (AU)", size=1.5, show=False)
