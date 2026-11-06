"""Metrics and the fold-evaluation loop (numpy and scikit-learn only)."""
import numpy as np
from sklearn.metrics import balanced_accuracy_score, cohen_kappa_score, roc_auc_score

METRIC_KEYS = ("acc_pooled", "acc_fold_mean", "bal_acc", "auc", "kappa",
               "recall_left", "recall_right", "n_folds", "n_test_mean")


def _scores(model, X):
    """Positive-class score for AUC, or None if the model has none."""
    if hasattr(model, "predict_proba"):
        p = model.predict_proba(X)
        return p[:, 1] if p.shape[1] == 2 else None
    if hasattr(model, "decision_function"):
        return np.ravel(model.decision_function(X))
    return None


def metrics_from_predictions(y_true, y_pred, y_score=None, fold_accs=None, n_folds=None, n_test_mean=None):
    """Pooled metrics over all test trials of one repeat."""
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    out = {k: np.nan for k in METRIC_KEYS}
    out["acc_pooled"] = float(np.mean(y_true == y_pred))
    out["acc_fold_mean"] = float(np.mean(fold_accs)) if fold_accs is not None and len(fold_accs) else np.nan
    if len(np.unique(y_true)) == 2:
        out["bal_acc"] = float(balanced_accuracy_score(y_true, y_pred))
        out["recall_left"] = float(np.mean(y_pred[y_true == 0] == 0))
        out["recall_right"] = float(np.mean(y_pred[y_true == 1] == 1))
        if y_score is not None:
            out["auc"] = float(roc_auc_score(y_true, y_score))
    try:
        out["kappa"] = float(cohen_kappa_score(y_true, y_pred))
    except ValueError:
        pass
    out["n_folds"] = n_folds if n_folds is not None else np.nan
    out["n_test_mean"] = n_test_mean if n_test_mean is not None else np.nan
    return out


def evaluate_repeats(build_model, X, y, repeats, train_transform=None):
    """Fit a fresh model in every fold; return metrics averaged over repeats.

    build_model: callable returning an unfitted estimator (so nothing is shared between folds).
    train_transform: optional callable (X_train, y_train) -> (X_train, y_train), applied to
                     TRAINING data only (used for augmentation done the correct way).
    """
    X, y = np.asarray(X), np.asarray(y)
    per_repeat = []
    for folds in repeats:
        yt, yp, ys, fa, sizes = [], [], [], [], []
        for tr, te in folds:
            Xtr, ytr = X[tr], y[tr]
            if train_transform is not None:
                Xtr, ytr = train_transform(Xtr, ytr)
            model = build_model()  # a fresh, unfitted estimator for every fold
            model.fit(Xtr, ytr)
            pred = model.predict(X[te])
            yt.append(y[te])
            yp.append(pred)
            s = _scores(model, X[te])
            ys.append(s if s is not None else np.full(len(te), np.nan))
            fa.append(float(np.mean(pred == y[te])))
            sizes.append(len(te))
        yt, yp, ys = np.concatenate(yt), np.concatenate(yp), np.concatenate(ys)
        per_repeat.append(metrics_from_predictions(
            yt, yp, None if np.isnan(ys).any() else ys, fa, len(folds), float(np.mean(sizes))))
    return {k: float(np.nanmean([m[k] for m in per_repeat])) if not all(np.isnan(m[k]) for m in per_repeat)
            else np.nan for k in METRIC_KEYS}
