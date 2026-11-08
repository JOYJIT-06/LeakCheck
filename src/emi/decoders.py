"""Decoders as small specifications, so every audit design can use any decoder.

csp_lda   CSP + LDA (solver lsqr, automatic shrinkage)          default
csp_lr    CSP + L2 logistic regression
ts_lr     Riemannian tangent space + logistic regression         needs the optional `pyriemann` package

Not implemented here (see docs/REQUIREMENTS_STATUS.md): filter-bank CSP with feature
selection and a compact CNN.
"""
from dataclasses import dataclass, field

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from scipy import stats

N_KEEP_CHANNELS = 16


def mne_csp_factory(reg=None):
    """Factory for MNE's CSP (imported lazily, so the package works without MNE)."""
    def make(n_components):
        import mne
        from mne.decoding import CSP
        mne.set_log_level("ERROR")
        return CSP(n_components=n_components, reg=reg, log=True, norm_trace=False)
    return make


default_csp_factory = mne_csp_factory()


def get_csp_factory(name="rank_safe", reg=None):
    """'rank_safe' (alias 'numpy') = built-in numpy CSP that whitens inside the data subspace;
    'mne' = mne.decoding.CSP. Single subjects can differ by 10-30 points between the two on real data,
    so always report which one produced a number."""
    if name == "mne":
        return mne_csp_factory(reg)
    if name in ("rank_safe", "numpy"):
        from .simple_csp import numpy_csp_factory
        return numpy_csp_factory
    raise ValueError(f"Unknown CSP implementation {name!r}")


class ChannelSelector(BaseEstimator, TransformerMixin):
    """Keep the `n_keep` channels whose log-variance differs most between the classes.

    Uses the labels. Inside a Pipeline it is re-fitted on training trials only (correct).
    Fitted once on all trials before cross-validation it leaks (wrong).
    """

    def __init__(self, n_keep: int = N_KEEP_CHANNELS):
        self.n_keep = n_keep

    def fit(self, X, y):
        y = np.asarray(y)
        logvar = np.log(X.var(axis=2) + 1e-30)
        t, _ = stats.ttest_ind(logvar[y == 0], logvar[y == 1], axis=0, equal_var=False)
        score = np.abs(np.nan_to_num(t))
        self.idx_ = np.sort(np.argsort(score)[::-1][: self.n_keep])
        return self

    def transform(self, X):
        return X[:, self.idx_, :]


class ChannelScaler(BaseEstimator, TransformerMixin):
    """Divide every channel by its standard deviation (pooled over trials and time).

    Uses no labels. Fitted on training trials it is correct; fitted on all trials
    (including test trials) it is a mild, label-free leak.
    """

    def fit(self, X, y=None):
        self.scale_ = X.std(axis=(0, 2)) + 1e-30
        return self

    def transform(self, X):
        return X / self.scale_[None, :, None]


class CovarianceTransformer(BaseEstimator, TransformerMixin):
    """Compute normalized sample covariance matrices per trial for Riemannian geometry decoding."""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        covs = []
        for trial in X:
            t_centered = trial - trial.mean(axis=1, keepdims=True)
            c = np.cov(t_centered)
            tr = np.trace(c)
            if tr > 0:
                c = c / tr
            c += 1e-5 * np.eye(c.shape[0])
            covs.append(c)
        return np.stack(covs, axis=0)


class TangentSpaceTransformer(BaseEstimator, TransformerMixin):
    """Project SPD covariance matrices onto the tangent space of their log-Euclidean Frechet mean."""

    def fit(self, X, y=None):
        eigvals, eigvecs = np.linalg.eigh(X)
        eigvals = np.maximum(eigvals, 1e-7)
        log_covs = [v @ np.diag(np.log(val)) @ v.T for v, val in zip(eigvecs, eigvals)]
        mean_log = np.mean(log_covs, axis=0)
        evals_m, evecs_m = np.linalg.eigh(mean_log)
        self.ref_ = evecs_m @ np.diag(np.exp(evals_m)) @ evecs_m.T
        evals_r, evecs_r = np.linalg.eigh(self.ref_)
        evals_r = np.maximum(evals_r, 1e-7)
        self.ref_inv_sqrt_ = evecs_r @ np.diag(1.0 / np.sqrt(evals_r)) @ evecs_r.T
        return self

    def transform(self, X):
        n_trials, n_ch, _ = X.shape
        idx = np.triu_indices(n_ch)
        sqrt2 = np.sqrt(2.0)
        features = []
        for C in X:
            S = self.ref_inv_sqrt_ @ C @ self.ref_inv_sqrt_
            evals, evecs = np.linalg.eigh(S)
            evals = np.maximum(evals, 1e-7)
            log_S = evecs @ np.diag(np.log(evals)) @ evecs.T
            diag_mask = np.eye(n_ch, dtype=bool)
            vec = log_S[idx].copy()
            off_mask = ~diag_mask[idx]
            vec[off_mask] *= sqrt2
            features.append(vec)
        return np.stack(features, axis=0)


def add_noise_channels(X, n_noise, seed=0):
    """Append `n_noise` pure-noise channels (same typical amplitude). Used to magnify selection leaks."""
    if n_noise <= 0:
        return X
    rng = np.random.default_rng(seed)
    sd = float(np.median(X.std(axis=2)))
    noise = rng.standard_normal((X.shape[0], int(n_noise), X.shape[2])) * sd
    return np.concatenate([X, noise], axis=1)


@dataclass(frozen=True)
class DecoderSpec:
    name: str
    uses_csp: bool
    base: dict = field(default_factory=dict)       # fixed primary settings
    grid: tuple = ()                               # settings tuned in the P5 designs

    def _features(self, csp_factory, p):
        if self.name in ("csp_lda", "csp_lr"):
            return [("csp", csp_factory(p["n_csp"]))]
        if self.name == "ts_lr":
            try:
                from pyriemann.estimation import Covariances
                from pyriemann.tangentspace import TangentSpace
                return [("cov", Covariances(estimator="oas")), ("ts", TangentSpace(metric="riemann"))]
            except ImportError:
                return [("cov", CovarianceTransformer()), ("ts", TangentSpaceTransformer())]
        raise ValueError(f"Unknown decoder {self.name}")

    def head(self, **params):
        """The classifier alone (used when features were computed outside the pipeline)."""
        p = {**self.base, **params}
        if self.name == "csp_lda":
            return LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")
        return LogisticRegression(C=p["C"], max_iter=1000)

    def build(self, csp_factory, n_keep=None, scale=False, **params):
        """Full pipeline. Every data-dependent step sits inside it, so it is re-fitted per fold."""
        p = {**self.base, **params}
        steps = []
        if scale:
            steps.append(("scale", ChannelScaler()))
        if n_keep:
            steps.append(("sel", ChannelSelector(n_keep)))
        steps += self._features(csp_factory, p)
        steps.append(("clf", self.head(**params)))
        return Pipeline(steps)


DECODERS = {
    "csp_lda": DecoderSpec("csp_lda", True, {"n_csp": 4}, tuple({"n_csp": k} for k in (2, 4, 6, 8))),
    "csp_lr": DecoderSpec("csp_lr", True, {"n_csp": 4, "C": 1.0}, tuple({"C": c} for c in (0.01, 0.1, 1.0, 10.0))),
    "ts_lr": DecoderSpec("ts_lr", False, {"C": 1.0}, tuple({"C": c} for c in (0.01, 0.1, 1.0, 10.0))),
}
