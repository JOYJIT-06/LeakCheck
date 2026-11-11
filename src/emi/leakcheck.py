"""LeakCheck: how much do validation choices inflate within-subject EEG decoding accuracy?

Two kinds of design are compared. All of them use the same data and the same decoder.

A) VALIDATION designs (everything fitted inside the training folds):
   D1_shuffled_kfold, D2_stratified_kfold, D1m_matched_k, D1s_size_matched,
   D3_loro, D4_chrono, D4b_forward_chain, D5_gap2, D5_gap4, D6_loso_session
B) INJECTED LEAKS, each paired with a correctly done comparator:
   P1_csp_on_all            vs D3_loro
   P3_scale_on_all          vs P3_scale_inside
   P4_select_on_all@N       vs P4_select_inside@N     (N = extra noise channels)
   P5_tune_on_test          vs P5_tune_nested
   P6_overlap_random@step   vs P6_overlap_loro@step   (1 s windows, step in seconds)
   P7_aug_all_random@n      vs P7_aug_train_only@n    (n augmented copies per trial)
   (P2, ICA fitted on all data, needs the raw recordings and is not part of this module.)

Every design is run on the real labels and on null labels (within-run permutation "perm" and
circular shift "shift"). A clean pipeline under null labels is the negative control N0: it must
return chance. Inflation is Delta = accuracy(leaky) - accuracy(reference), in percentage points.

Needs numpy, scipy, pandas and scikit-learn. MNE is imported only by the default CSP factory.
"""
import hashlib
import logging
import time
import warnings

import numpy as np
import pandas as pd

from . import splitters as sp
from .decoders import (
    DECODERS,
    DEFAULT_FILTER_BANKS,
    ChannelScaler,
    ChannelSelector,
    FilterBankCSP,
    N_KEEP_CHANNELS,
    add_noise_channels,
)
from .leakstats import holm, paired_summary
from .metrics import METRIC_KEYS, evaluate_repeats, metrics_from_predictions, _scores
from .nulls import NULL_GENERATORS, empirical_p, label_agreement
from .summary import binomial_threshold
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.pipeline import Pipeline

_log = logging.getLogger(__name__)

from .config import Config as _Config  # noqa: E402

_CFG = _Config()
BASE_WINDOW = (_CFG.decode_tmin, _CFG.decode_tmax)   # one source of truth: emi.config (fixed in advance)
WINDOWS = ((0.5, 2.5), (1.0, 3.0), (1.5, 3.5), (0.5, 3.5), (0.0, 4.0))
AUG_NOISE_FRACTION = 0.3

DEFAULT_DOSE = {
    "P2_ica_on_all": "16", "P2_ica_inside": "16",
    "P4_select_on_all": "64", "P4_select_inside": "64",
    "P7_select_on_all": "64", "P7_select_inside": "64",
    "P6_overlap_random": "0.5", "P6_overlap_loro": "0.5",
    "P7_aug_all_random": "4", "P7_aug_train_only": "4",
}

PRESETS = {
    "quick": ["D3_loro", "D1m_matched_k", "P1_csp_on_all"],
    "core": ["D1_shuffled_kfold", "D2_stratified_kfold", "D1m_matched_k", "D1s_size_matched", "D3_loro",
             "D4_chrono", "D5_gap2", "D5_gap4", "P1_csp_on_all", "P3_scale_on_all", "P3_scale_inside",
             "P4_select_on_all@64", "P4_select_inside@64", "P5_tune_on_test", "P5_tune_nested"],
    "full": ["D1_shuffled_kfold", "D2_stratified_kfold", "D1m_matched_k", "D1s_size_matched", "D3_loro",
             "D4_chrono", "D4b_forward_chain", "D5_gap2", "D5_gap4", "D6_loso_session",
             "P1_csp_on_all", "P2_ica_on_all", "P2_ica_inside",
             "P3_scale_on_all", "P3_scale_inside", "P5_scale_on_all", "P5_scale_inside",
             "P4_select_on_all@0", "P4_select_inside@0", "P4_select_on_all@64", "P4_select_inside@64",
             "P4_select_on_all@256", "P4_select_inside@256",
             "P7_select_on_all@0", "P7_select_inside@0", "P7_select_on_all@64", "P7_select_inside@64",
             "P5_tune_on_test", "P5_tune_nested",
             "P6_overlap_random@1.0", "P6_overlap_loro@1.0", "P6_overlap_random@0.5", "P6_overlap_loro@0.5",
             "P6_overlap_random@0.25", "P6_overlap_loro@0.25",
             "P7_aug_all_random@4", "P7_aug_train_only@4"],
}

# leaky design -> (reference design, kind). The dose suffix is carried over automatically.
REFERENCE = {
    "D1_shuffled_kfold": ("D3_loro", "raw difference"),
    "D2_stratified_kfold": ("D3_loro", "raw difference"),
    "D1m_matched_k": ("D3_loro", "k-matched"),
    "D1s_size_matched": ("D3_loro", "size-matched (headline)"),
    "D4_chrono": ("D5_gap4", "effect of a 4-trial gap"),
    "P1_csp_on_all": ("D3_loro", "P1 CSP on all data"),
    "P2_ica_on_all": ("P2_ica_inside", "P2 global ICA unmixing contamination"),
    "P3_scale_on_all": ("P3_scale_inside", "P3 scaling on all data"),
    "P5_scale_on_all": ("P5_scale_inside", "P5 scaling on all data"),
    "P4_select_on_all": ("P4_select_inside", "P4 selection on all data"),
    "P7_select_on_all": ("P7_select_inside", "P7 selection on all data"),
    "P5_tune_on_test": ("P5_tune_nested", "P5 tuning on test folds"),
    "P6_overlap_random": ("P6_overlap_loro", "P6 overlapping windows"),
    "P7_aug_all_random": ("P7_aug_train_only", "P7 augmentation before split"),
}


class NotApplicable(Exception):
    """The design cannot run for this decoder or dataset (for example P1 for a decoder without CSP)."""


def default_csp_factory(n_components: int):
    """MNE's CSP with the same settings as emi.decode (imported lazily)."""
    from mne.decoding import CSP
    return CSP(n_components=n_components, reg=None, log=True, norm_trace=False)


class Ctx:
    """Everything a design needs about one subject, one decoder and one set of labels."""

    def __init__(self, X, y, runs, sessions, order, times, spec, csp_factory, seed, n_repeats, n_repeats_matched,
                 base_window=BASE_WINDOW):
        self.X, self.y, self.runs = X, y, runs
        self.sessions, self.order, self.times = sessions, order, times
        self.spec, self.csp_factory, self.seed = spec, csp_factory, seed
        self.n_repeats, self.n_repeats_matched = n_repeats, n_repeats_matched
        self.dt = float(times[1] - times[0])
        try:
            self.base_window = tuple(base_window)
            self.Xb = self.window(self.base_window)
        except NotApplicable as exc:
            raise ValueError(f"The base window {tuple(base_window)} s must fit the recording: {exc}")

    def window(self, w, X=None):
        X = self.X if X is None else X
        mask = (self.times >= w[0] - 1e-9) & (self.times < w[1] - 1e-9)
        if mask.sum() < 10:
            raise NotApplicable(f"window {w} not available in this recording")
        return X[:, :, mask]

    def valid_windows(self):
        t0, t1 = self.times[0], self.times[-1] + self.dt
        return [w for w in WINDOWS if w[0] >= t0 - 1e-9 and w[1] <= t1 + 1e-9]

    def build(self, **kw):
        return self.spec.build(self.csp_factory, **kw)


def _clean(ctx, repeats, X=None, y=None, train_transform=None, **build_kw):
    X = ctx.Xb if X is None else X
    y = ctx.y if y is None else y

    sp.validate_splits(repeats, y)

    return evaluate_repeats(
        lambda: ctx.build(**build_kw),
        X, y, repeats, train_transform
    )# ------------------------------------------------------------------ A) validation designs
def d1_shuffled_kfold(c, dose):
    return _clean(c, sp.kfold_repeats(c.y, 5, False, c.n_repeats, c.seed))


def d2_stratified_kfold(c, dose):
    return _clean(c, sp.kfold_repeats(c.y, 5, True, c.n_repeats, c.seed))


def d1m_matched_k(c, dose):
    k = len(np.unique(c.runs))
    return _clean(c, sp.kfold_repeats(c.y, k, True, c.n_repeats, c.seed))


def d1s_size_matched(c, dose):
    return _clean(c, sp.size_matched_random_repeats(c.y, c.runs, c.n_repeats_matched, c.seed))


def d3_loro(c, dose):
    repeats = sp.loro_splits(c.runs)
    sp.validate_splits(repeats, c.y, groups=c.runs)
    return _clean(c, repeats)

def d4_chrono(c, dose):
    return _clean(c, sp.chrono_holdout(len(c.y), 1 / 3, 0, c.order))


def d4b_forward_chain(c, dose):
    return _clean(c, sp.forward_chain(len(c.y), 3, 0, c.order))


def _gap(g):
    return lambda c, dose: _clean(c, sp.chrono_holdout(len(c.y), 1 / 3, g, c.order))


def d6_loso_session(c, dose):
    try:
        return _clean(c, sp.session_splits(c.sessions))
    except ValueError as exc:
        raise NotApplicable(str(exc))


# ------------------------------------------------------------------ B) injected leaks
def p1_csp_on_all(c, dose):
    if not c.spec.uses_csp:
        raise NotApplicable("P1 needs a decoder with CSP")
    if c.spec.name == "fbcsp":
        fbcsp_step = FilterBankCSP(
            sfreq=c.spec.base.get("sfreq", 250.0),
            bands=c.spec.base.get("bands", DEFAULT_FILTER_BANKS),
            n_components=c.spec.base.get("n_csp", 4),
            csp_factory=c.csp_factory,
        )
        sel = SelectKBest(score_func=f_classif, k=c.spec.base.get("k_features", 8))
        pipe = Pipeline([("fbcsp", fbcsp_step), ("select", sel)])
        feats = pipe.fit_transform(c.Xb, c.y)
    else:
        feats = c.csp_factory(c.spec.base["n_csp"]).fit_transform(c.Xb, c.y)
    repeats = sp.loro_splits(c.runs)
    sp.validate_splits(repeats, c.y, groups=c.runs)
    return evaluate_repeats(lambda: c.spec.head(), feats, c.y, repeats)


def p2_ica_on_all(c, dose):
    """P2: Global ICA unmixing matrix fitted across all trials before split."""
    from sklearn.decomposition import FastICA
    n_trials, n_ch, n_times = c.Xb.shape
    n_comp = min(int(float(dose)) if dose else 16, n_ch - 1)
    if n_comp < 2:
        n_comp = min(4, n_ch)
    X_2d = c.Xb.transpose(1, 0, 2).reshape(n_ch, -1).T
    ica = FastICA(n_components=n_comp, random_state=c.seed, max_iter=200, tol=1e-3)
    S = ica.fit_transform(X_2d)
    X_clean_2d = ica.inverse_transform(S)
    X_leaky = X_clean_2d.T.reshape(n_ch, n_trials, n_times).transpose(1, 0, 2)
    return _clean(c, sp.loro_splits(c.runs), X=X_leaky)


def p2_ica_inside(c, dose):
    """P2 clean reference: fold-nested ICA unmixing matrix fitted strictly on training trials."""
    from sklearn.decomposition import FastICA
    n_trials, n_ch, n_times = c.Xb.shape
    n_comp = min(int(float(dose)) if dose else 16, n_ch - 1)
    if n_comp < 2:
        n_comp = min(4, n_ch)
    repeats = sp.loro_splits(c.runs)
    sp.validate_splits(repeats, c.y, groups=c.runs)

    fold_accs = []
    yt_all, yp_all, ys_all = [], [], []
    n_test = []
    for tr, te in repeats[0]:
        Xtr, ytr = c.Xb[tr], c.y[tr]
        Xte, yte = c.Xb[te], c.y[te]
        n_tr_trials = len(tr)
        n_te_trials = len(te)

        Xtr_2d = Xtr.transpose(1, 0, 2).reshape(n_ch, -1).T
        ica = FastICA(n_components=n_comp, random_state=c.seed, max_iter=200, tol=1e-3)
        S_tr = ica.fit_transform(Xtr_2d)
        Xtr_clean = ica.inverse_transform(S_tr).T.reshape(n_ch, n_tr_trials, n_times).transpose(1, 0, 2)

        Xte_2d = Xte.transpose(1, 0, 2).reshape(n_ch, -1).T
        S_te = ica.transform(Xte_2d)
        Xte_clean = ica.inverse_transform(S_te).T.reshape(n_ch, n_te_trials, n_times).transpose(1, 0, 2)

        model = c.build().fit(Xtr_clean, ytr)
        pred = model.predict(Xte_clean)
        yt_all.append(yte)
        yp_all.append(pred)
        score = _scores(model, Xte_clean)
        if score is not None:
            ys_all.append(score)
        fold_accs.append(float(np.mean(pred == yte)))
        n_test.append(n_te_trials)

    y_true = np.concatenate(yt_all)
    y_pred = np.concatenate(yp_all)
    y_score = np.concatenate(ys_all) if len(ys_all) == len(yt_all) else None
    return metrics_from_predictions(
        y_true, y_pred, y_score=y_score, fold_accs=fold_accs,
        n_folds=len(fold_accs), n_test_mean=float(np.mean(n_test))
    )


def p3_scale_on_all(c, dose):
    Xs = ChannelScaler().fit(c.Xb).transform(c.Xb)                              # statistics from ALL trials
    return _clean(c, sp.loro_splits(c.runs), X=Xs)


def p3_scale_inside(c, dose):
    return _clean(c, sp.loro_splits(c.runs), scale=True)


p5_scale_on_all = p3_scale_on_all
p5_scale_inside = p3_scale_inside


def _noisy(c, dose):
    return add_noise_channels(c.Xb, int(float(dose)), seed=c.seed)


def p4_select_on_all(c, dose):
    Xn = _noisy(c, dose)
    Xs = ChannelSelector(N_KEEP_CHANNELS).fit(Xn, c.y).transform(Xn)           # selection saw ALL labels
    return _clean(c, sp.loro_splits(c.runs), X=Xs)


def p4_select_inside(c, dose):
    return _clean(c, sp.loro_splits(c.runs), X=_noisy(c, dose), n_keep=N_KEEP_CHANNELS)


p7_select_on_all = p4_select_on_all
p7_select_inside = p4_select_inside


def _grid(c):
    grid = [(w, p) for w in c.valid_windows() for p in c.spec.grid]
    if not grid:
        raise NotApplicable("no tuning windows fit this recording")
    return grid


def _pred(c, params, Xtr, ytr, Xte):
    return c.build(**params).fit(Xtr, ytr).predict(Xte)


def p5_tune_on_test(c, dose):
    """Choose window and settings by the score on the held-out run itself, then report that score."""
    grid, yt, yp = _grid(c), [], []
    wins = {w: c.window(w) for w, _ in grid}
    for tr, te in sp.loro_splits(c.runs)[0]:
        best = None
        for w, params in grid:
            pred = _pred(c, params, wins[w][tr], c.y[tr], wins[w][te])
            acc = float(np.mean(pred == c.y[te]))
            if best is None or acc > best[0]:
                best = (acc, pred)
        yt.append(c.y[te])
        yp.append(best[1])
    return metrics_from_predictions(np.concatenate(yt), np.concatenate(yp), n_folds=len(yt))


def p5_tune_nested(c, dose):
    """The same tuning done properly: choose using the training runs only (inner leave-one-run-out)."""
    grid, yt, yp = _grid(c), [], []
    wins = {w: c.window(w) for w, _ in grid}
    for tr, te in sp.loro_splits(c.runs)[0]:
        inner = sp.loro_splits(c.runs[tr])
        best = None
        for w, params in grid:
            m = evaluate_repeats(lambda: c.build(**params), wins[w][tr], c.y[tr], inner)["acc_pooled"]
            if best is None or m > best[0]:
                best = (m, w, params)
        _, w, params = best
        yt.append(c.y[te])
        yp.append(_pred(c, params, wins[w][tr], c.y[tr], wins[w][te]))
    return metrics_from_predictions(np.concatenate(yt), np.concatenate(yp), n_folds=len(yt))


def _sliding(c, step, length=1.0):
    """1 s windows from every trial. Returns windowed data and the label, run and trial of each window."""
    n_samp = int(round(length / c.dt))
    t0, t1 = c.times[0], c.times[-1] + c.dt
    starts = np.arange(t0, t1 - length + 1e-9, step)
    idx = [int(round((s - t0) / c.dt)) for s in starts]
    Xw = np.concatenate([c.X[:, :, i:i + n_samp] for i in idx], axis=0)
    rep = len(idx)
    return Xw, np.tile(c.y, rep), np.tile(c.runs, rep)


def p6_overlap_random(c, dose):
    Xw, yw, _ = _sliding(c, float(dose))
    return _clean(c, sp.kfold_repeats(yw, 5, True, c.n_repeats, c.seed), X=Xw, y=yw)


def p6_overlap_loro(c, dose):
    Xw, yw, rw = _sliding(c, float(dose))
    return _clean(c, sp.loro_splits(rw), X=Xw, y=yw)




def _augment_from_sources(X_sources, y_sources, target_y, rng):
    """Create noisy augmented samples from class-matched source trials."""
    X_sources = np.asarray(X_sources, dtype=float)
    y_sources = np.asarray(y_sources).astype(int)
    target_y = np.asarray(target_y).astype(int)

    if len(X_sources) == 0 or len(target_y) == 0:
        raise ValueError("Cannot augment an empty source or target set.")

    source_indices = []

    for label in target_y:
        candidates = np.flatnonzero(y_sources == label)

        if len(candidates) == 0:
            raise ValueError(
                f"No source trials available for class {label}."
            )

        source_indices.append(rng.choice(candidates))

    source_indices = np.asarray(source_indices, dtype=int)
    selected = X_sources[source_indices]

    sd = selected.std(axis=2, keepdims=True)
    noise = rng.standard_normal(selected.shape)

    X_aug = selected + AUG_NOISE_FRACTION * sd * noise

    return X_aug, target_y.copy()


def _p7_loro(c, dose, leaky):
    """Matched leave-one-run-out comparison of augmentation leakage.

    Both conditions use identical held-out original trials and LORO folds.
    The original held-out trials remain untouched as the test set.

    Leaky condition: augmentation sources come from the held-out run.
    Clean condition: augmentation sources come only from training runs.
    """
    n_aug = int(float(dose))

    if n_aug < 0:
        raise ValueError("P7 augmentation dose must be non-negative.")

    repeats = sp.loro_splits(c.runs)
    sp.validate_splits(repeats, c.y)

    y_true_all = []
    y_pred_all = []
    y_score_all = []
    fold_accs = []
    scores_available = True
    n_test = []

    for fold_idx, (tr, te) in enumerate(repeats[0]):
        Xtr, ytr = c.Xb[tr], c.y[tr]
        Xte, yte = c.Xb[te], c.y[te]

        # Augmentation labels are sampled from training labels only.
        target_rng = np.random.default_rng(
            c.seed + 7000 + fold_idx
        )

        target_y = target_rng.choice(
            ytr,
            size=len(te) * n_aug,
            replace=True
        )

        if leaky:
            X_sources, y_sources = Xte, yte
        else:
            X_sources, y_sources = Xtr, ytr

        aug_rng = np.random.default_rng(
            c.seed + 8000 + fold_idx
        )

        if n_aug == 0:
            X_aug = np.empty(
                (0,) + Xtr.shape[1:],
                dtype=Xtr.dtype
            )
            y_aug = np.empty(0, dtype=c.y.dtype)
        else:
            X_aug, y_aug = _augment_from_sources(
                X_sources,
                y_sources,
                target_y,
                aug_rng
            )

        X_train = np.concatenate([Xtr, X_aug], axis=0)
        y_train = np.concatenate([ytr, y_aug], axis=0)

        model = c.build().fit(X_train, y_train)

        y_pred = model.predict(Xte)
        y_score = _scores(model, Xte)

        y_true_all.append(yte)
        y_pred_all.append(y_pred)
        fold_accs.append(float(np.mean(y_pred == yte)))
        n_test.append(len(te))

        if y_score is None:
            scores_available = False
        else:
            y_score_all.append(y_score)

    y_true = np.concatenate(y_true_all)
    y_pred = np.concatenate(y_pred_all)

    y_score = (
        np.concatenate(y_score_all)
        if scores_available and y_score_all
        else None
    )

    return metrics_from_predictions(
        y_true,
        y_pred,
        y_score=y_score,
        fold_accs=fold_accs,
        n_folds=len(fold_accs),
        n_test_mean=float(np.mean(n_test))
    )


def p7_aug_all_random(c, dose):
    """P7 leakage: held-out-run trials contribute augmented training samples."""
    return _p7_loro(c, dose, leaky=True)


def p7_aug_train_only(c, dose):
    """P7 clean comparator: only training-run trials contribute augmentation."""
    return _p7_loro(c, dose, leaky=False)


DESIGN_FUNCS = {
    "D1_shuffled_kfold": d1_shuffled_kfold, "D2_stratified_kfold": d2_stratified_kfold,
    "D1m_matched_k": d1m_matched_k, "D1s_size_matched": d1s_size_matched, "D3_loro": d3_loro,
    "D4_chrono": d4_chrono, "D4b_forward_chain": d4b_forward_chain,
    "D5_gap2": _gap(2), "D5_gap4": _gap(4), "D6_loso_session": d6_loso_session,
    "P1_csp_on_all": p1_csp_on_all,
    "P2_ica_on_all": p2_ica_on_all, "P2_ica_inside": p2_ica_inside,
    "P3_scale_on_all": p3_scale_on_all, "P3_scale_inside": p3_scale_inside,
    "P5_scale_on_all": p5_scale_on_all, "P5_scale_inside": p5_scale_inside,
    "P4_select_on_all": p4_select_on_all, "P4_select_inside": p4_select_inside,
    "P7_select_on_all": p7_select_on_all, "P7_select_inside": p7_select_inside,
    "P5_tune_on_test": p5_tune_on_test, "P5_tune_nested": p5_tune_nested,
    "P6_overlap_random": p6_overlap_random, "P6_overlap_loro": p6_overlap_loro,
    "P7_aug_all_random": p7_aug_all_random, "P7_aug_train_only": p7_aug_train_only,
}


def resolve_designs(spec):
    """'core' / 'quick' / 'full' / comma-separated list -> list of design ids."""
    if isinstance(spec, str):
        spec = PRESETS[spec] if spec in PRESETS else [s for s in spec.split(",") if s]
    for d in spec:
        if d.split("@")[0] not in DESIGN_FUNCS:
            raise ValueError(f"Unknown design {d}. Known: {sorted(DESIGN_FUNCS)}")
    return list(spec)


def run_design(design, ctx):
    base, _, dose = design.partition("@")
    return DESIGN_FUNCS[base](ctx, dose or DEFAULT_DOSE.get(base, ""))


# ------------------------------------------------------------------ one subject
def audit_subject(X, y, runs, times, subject, csp_factory=None, dataset="physionet", sessions=None,
                  order=None, decoders=("csp_lda",), designs="core", n_null=20, null_types=("perm", "shift"),
                  n_repeats=5, n_repeats_matched=20, seed=0, csp_name="unspecified", base_window=None):
    """Run every design on the real labels and on `n_null` null label sets per null type.

    X: (trials, channels, time points), band-passed (8-30 Hz). Returns a tidy DataFrame with one row
    per dataset x subject x decoder x design x label set, with all metrics and the run time.
    """
    csp_factory = csp_factory or default_csp_factory
    X = np.asarray(X, float)
    y = np.asarray(y).astype(int)
    runs = np.asarray(runs).astype(int)
    times = np.asarray(times, float)
    sessions = np.zeros(len(y), int) if sessions is None else np.asarray(sessions).astype(int)
    order = np.arange(len(y)) if order is None else np.asarray(order)
    designs = resolve_designs(designs)
    if len(np.unique(runs)) < 3:
        raise ValueError("LeakCheck needs at least 3 runs (nested tuning needs 2 runs for training).")
    for r in np.unique(runs):
        if len(np.unique(y[runs == r])) < 2:
            raise ValueError(f"Run {r} contains only one class.")

    rng = np.random.default_rng(seed + 1000 * int(subject))
    label_sets = [("real", 0, y)]
    for nt in null_types:
        for k in range(1, n_null + 1):
            label_sets.append((nt, k, NULL_GENERATORS[nt](y, runs, rng)))

    rows = []
    for dec in decoders:
        spec = DECODERS[dec]
        for label_type, k, yk in label_sets:
            # the SAME fold seed for real and null labels: folds differ only through the labels, so null and real are paired
            ctx = Ctx(X, yk, runs, sessions, order, times, spec, csp_factory, seed, n_repeats, n_repeats_matched,
                      base_window or BASE_WINDOW)
            agree = label_agreement(y, yk)
            lhash = hashlib.md5(np.asarray(yk).astype(np.int8).tobytes()).hexdigest()[:8]
            for d in designs:
                t0 = time.time()
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        m = run_design(d, ctx)
                except NotApplicable:
                    continue
                except ValueError as exc:                     # e.g. a fold without both classes
                    m = {key: np.nan for key in METRIC_KEYS}
                    m["error"] = str(exc)[:80]
                rows.append({"dataset": dataset, "subject": int(subject), "decoder": dec, "design": d,
                             "label_type": label_type, "perm": k, "n_trials": int(len(y)),
                             "n_channels": int(X.shape[1]), "csp_impl": csp_name if spec.uses_csp else "n/a",
                             "base_window": f"{ctx.base_window[0]:g}-{ctx.base_window[1]:g}",
                             "label_agreement": agree, "label_hash": lhash,
                             **{key: m.get(key, np.nan) for key in METRIC_KEYS},
                             "seconds": round(time.time() - t0, 3), "error": m.get("error", "")})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ tables
def _ref_of(design):
    base, _, dose = design.partition("@")
    if base not in REFERENCE:
        return None
    ref_base, kind = REFERENCE[base]
    return ref_base + (f"@{dose}" if dose else ""), kind


def inflation_by_subject(df, metric="acc_pooled"):
    """Per subject: metric(leaky) - metric(reference) in percentage points, real labels only."""
    real = df[df["label_type"] == "real"]
    parts, dropped = [], []
    for (dataset, decoder), g in real.groupby(["dataset", "decoder"]):
        piv = g.pivot_table(index="subject", columns="design", values=metric)
        for leaky in piv.columns:
            pair = _ref_of(leaky)
            if pair is None or pair[0] not in piv.columns:
                continue
            ref, kind = pair
            full = ((piv[leaky] - piv[ref]) * 100).rename("delta_pp")
            d = full.dropna().reset_index()
            n_lost = int(full.isna().sum())
            if n_lost:
                _log.warning("inflation_by_subject: %d subject(s) dropped for %s/%s/%s (missing accuracy under %s or %s): %s",
                             n_lost, dataset, decoder, leaky, leaky, ref, sorted(full[full.isna()].index.tolist()))
                dropped.append({"dataset": dataset, "decoder": decoder, "design": leaky, "subjects": sorted(full[full.isna()].index.tolist())})
            d["acc_leaky"], d["acc_ref"] = piv[leaky].reindex(d["subject"]).values, piv[ref].reindex(d["subject"]).values
            d["dataset"], d["decoder"], d["design"], d["reference"], d["kind"] = dataset, decoder, leaky, ref, kind
            parts.append(d)
    cols = ["dataset", "decoder", "design", "reference", "kind", "subject", "delta_pp", "acc_leaky", "acc_ref"]
    out = pd.concat(parts, ignore_index=True)[cols] if parts else pd.DataFrame(columns=cols)
    out.attrs["dropped_subjects"] = dropped          # subjects lost to missing accuracies, per contrast
    return out


def inflation_table(by_subject, margin_pp=2.0, n_boot=2000, seed=0):
    """Paired statistics per dataset x decoder x contrast, with Holm correction inside each decoder family."""
    rows = []
    for (dataset, decoder, design, ref, kind), g in by_subject.groupby(
            ["dataset", "decoder", "design", "reference", "kind"], sort=False):
        s = paired_summary(g["acc_leaky"], g["acc_ref"], n_test=None, margin_pp=margin_pp, n_boot=n_boot, seed=seed)
        rows.append({"dataset": dataset, "decoder": decoder, "design": design, "reference": ref, "kind": kind, **s})
    tab = pd.DataFrame(rows)
    if len(tab) and "wilcoxon_p" in tab:
        tab["wilcoxon_p_holm"] = np.nan
        for _, idx in tab.groupby(["dataset", "decoder"]).groups.items():
            p = tab.loc[idx, "wilcoxon_p"].to_numpy(float)
            if np.isfinite(p).all():
                tab.loc[idx, "wilcoxon_p_holm"] = holm(p)
    return tab


def null_table(df, alpha=0.05, n_boot=2000, seed=0):
    """Under null labels: mean accuracy, optimism over 0.5 and false-positive rate for each design.

    A null dataset is a false positive when its pooled accuracy reaches the binomial threshold for
    its number of trials (the check a researcher would normally use). Intervals resample subjects.
    """
    nul = df[df["label_type"] != "real"].dropna(subset=["acc_pooled"]).copy()
    if nul.empty:
        return pd.DataFrame()
    nul["thr"] = nul["n_trials"].map(lambda n: binomial_threshold(int(n), alpha=alpha))
    nul["fp"] = (nul["acc_pooled"] >= nul["thr"]).astype(float)
    per = (nul.groupby(["dataset", "decoder", "label_type", "design", "subject"])
           .agg(mean_acc=("acc_pooled", "mean"), fpr=("fp", "mean")).reset_index())
    rng = np.random.default_rng(seed)
    rows = []
    for keys, g in per.groupby(["dataset", "decoder", "label_type", "design"], sort=False):
        fp, acc = g["fpr"].to_numpy(), g["mean_acc"].to_numpy()
        idx = [rng.integers(0, len(g), len(g)) for _ in range(n_boot)]
        fb = np.array([fp[i].mean() for i in idx])
        ab = np.array([acc[i].mean() for i in idx])
        rows.append(dict(zip(["dataset", "decoder", "null_type", "design"], keys),
                         n_subjects=len(g), null_mean_acc=float(acc.mean()),
                         optimism_pp=float((acc.mean() - 0.5) * 100),
                         optimism_ci_low_pp=float((np.percentile(ab, 2.5) - 0.5) * 100),
                         optimism_ci_high_pp=float((np.percentile(ab, 97.5) - 0.5) * 100),
                         false_positive_rate=float(fp.mean()),
                         fpr_ci_low=float(np.percentile(fb, 2.5)), fpr_ci_high=float(np.percentile(fb, 97.5)),
                         nominal_alpha=alpha))
    tab = pd.DataFrame(rows)
    if len(tab):
        leaky = tab["design"].map(lambda d: _ref_of(d) is not None)
        tab["design_type"] = np.where(leaky, "leaky", "clean")
        # clean design: should stay near nominal_alpha (a false-positive rate).
        # leaky design: a high value means the leak was DETECTED as inflated accuracy under null labels.
        tab["rate_meaning"] = np.where(leaky, "detection_of_leak", "false_positive_rate")
    return tab


def subject_empirical_p(df):
    """Per subject and design: observed accuracy, null mean, null 95th percentile, empirical p."""
    real = df[df["label_type"] == "real"].set_index(["dataset", "decoder", "design", "subject"])["acc_pooled"]
    rows = []
    for (dataset, decoder, nt, design, subject), g in df[df["label_type"] != "real"].groupby(
            ["dataset", "decoder", "label_type", "design", "subject"]):
        key = (dataset, decoder, design, subject)
        if key not in real.index or np.isnan(real[key]):
            continue
        null = g["acc_pooled"].dropna().to_numpy()
        rows.append({"dataset": dataset, "decoder": decoder, "null_type": nt, "design": design,
                     "subject": subject, "observed": float(real[key]), "null_mean": float(null.mean()),
                     "null_p95": float(np.percentile(null, 95)), "n_null": len(null),
                     "min_possible_p": 1.0 / (len(null) + 1),
                     "empirical_p": empirical_p(real[key], null)})
    out = pd.DataFrame(rows)
    if len(out) and (out["min_possible_p"] >= 0.05).any():
        _log.warning("subject_empirical_p: with n_null=%d the smallest possible p is %.3f, so no subject can reach p < 0.05; "
                     "use n_null >= 20 for subject-level significance statements.",
                     int(out["n_null"].min()), float(out["min_possible_p"].max()))
    return out


def paired_delta_vs_null(df):
    """Per subject and contrast: is (leaky - reference) larger than the same difference under null labels?

    Delta_real = acc(leaky) - acc(reference) with real labels. Delta_null[k] = the same difference with null label
    set k (paired: same labels, same fold seed). Empirical p = (1 + #(Delta_null >= Delta_real)) / (1 + n_null).
    This tests the DIFFERENCE between two designs, so below-chance null artefacts of random splits cancel out.
    It needs n_null >= 19 for p < 0.05 to be reachable (column min_possible_p).
    """
    rows = []
    for (dataset, decoder), g in df.groupby(["dataset", "decoder"]):
        piv = g.pivot_table(index=["subject", "label_type", "perm"], columns="design", values="acc_pooled")
        for leaky in piv.columns:
            pair = _ref_of(leaky)
            if pair is None or pair[0] not in piv.columns:
                continue
            ref, kind = pair
            d = (piv[leaky] - piv[ref]) * 100
            for subject in sorted({i[0] for i in d.index}):
                sd = d.xs(subject, level="subject")
                if ("real", 0) not in sd.index:
                    continue
                real = sd.loc[("real", 0)]
                if np.isnan(real):
                    continue
                for nt in sorted({i[0] for i in sd.index if i[0] != "real"}):
                    null = sd.xs(nt, level="label_type").dropna().to_numpy()
                    if len(null) == 0:
                        continue
                    rows.append({"dataset": dataset, "decoder": decoder, "design": leaky, "reference": ref,
                                 "kind": kind, "null_type": nt, "subject": subject, "delta_real_pp": float(real),
                                 "delta_null_mean_pp": float(null.mean()), "n_null": len(null),
                                 "min_possible_p": 1.0 / (len(null) + 1), "empirical_p": empirical_p(real, null)})
    return pd.DataFrame(rows)
