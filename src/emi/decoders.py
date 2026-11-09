"""Decoders as small specifications, so every audit design can use any decoder.

csp_lda   CSP + LDA (solver lsqr, automatic shrinkage)          default
csp_svm   CSP + Linear Support Vector Machine
csp_lr    CSP + L2 logistic regression
ts_lr     Riemannian tangent space + logistic regression         NumPy/SciPy fallback or pyriemann
fbcsp     Filter-Bank CSP with SelectKBest and shrinkage LDA
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
from scipy import signal, stats
from sklearn.base import BaseEstimator, ClassifierMixin, TransformerMixin
from sklearn.covariance import ledoit_wolf, oas
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

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
    """Compute normalized sample or regularized covariance matrices per trial for Riemannian geometry decoding.

    Parameters
    ----------
    estimator : str, default="oas"
        Covariance regularizer: "oas" (Oracle Approximating Shrinkage),
        "ledoit_wolf" (Ledoit-Wolf optimal shrinkage), or "empirical"
        (sample covariance with trace normalization and diagonal ridge).
    reg_eps : float, default=1e-5
        Diagonal regularizing constant added for robust positive definiteness.
    """

    def __init__(self, estimator: str = "oas", reg_eps: float = 1e-5):
        self.estimator = estimator
        self.reg_eps = reg_eps

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        covs = []
        for trial in X:
            t_centered = trial - trial.mean(axis=1, keepdims=True)
            if self.estimator == "oas":
                try:
                    c, _ = oas(t_centered.T)
                except Exception:
                    c = np.cov(t_centered)
            elif self.estimator == "ledoit_wolf":
                try:
                    c, _ = ledoit_wolf(t_centered.T)
                except Exception:
                    c = np.cov(t_centered)
            elif self.estimator == "empirical":
                c = np.cov(t_centered)
            else:
                raise ValueError(f"Unknown covariance estimator: {self.estimator}")

            tr = np.trace(c)
            if tr > 0:
                c = c / tr
            c += self.reg_eps * np.eye(c.shape[0])
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


DEFAULT_FILTER_BANKS: Tuple[Tuple[float, float], ...] = (
    (4.0, 8.0),
    (8.0, 12.0),
    (12.0, 16.0),
    (16.0, 20.0),
    (20.0, 24.0),
    (24.0, 28.0),
    (28.0, 32.0),
    (32.0, 36.0),
    (36.0, 40.0),
)


class FilterBankCSP(BaseEstimator, TransformerMixin):
    """Filter Bank Common Spatial Patterns (FBCSP) multi-band spatial filter transformer.

    Decomposes continuous EEG trials into multiple frequency sub-bands via
    Butterworth bandpass filters, extracts CSP log-variance features per band,
    and concatenates them across bands.

    Parameters
    ----------
    sfreq : float, default=250.0
        Sampling frequency in Hz.
    bands : Sequence[Tuple[float, float]], optional
        Frequency band pairs (low_hz, high_hz). Defaults to 9 bands covering 4–40 Hz.
    n_components : int, default=4
        Number of CSP spatial filters to retain per sub-band.
    csp_factory : Optional[Callable[[int], BaseEstimator]], optional
        Factory returning an unfitted CSP transformer. Defaults to rank_safe numpy CSP.
    filter_order : int, default=4
        Order of Butterworth bandpass filter.
    """

    def __init__(
        self,
        sfreq: float = 250.0,
        bands: Optional[Sequence[Tuple[float, float]]] = None,
        n_components: int = 4,
        csp_factory: Optional[Callable] = None,
        filter_order: int = 4,
    ):
        self.sfreq = sfreq
        self.bands = tuple(bands) if bands is not None else DEFAULT_FILTER_BANKS
        self.n_components = n_components
        self.csp_factory = csp_factory
        self.filter_order = filter_order

    def fit(self, X: np.ndarray, y: np.ndarray) -> "FilterBankCSP":
        factory = self.csp_factory or get_csp_factory("rank_safe")
        self.active_bands_ = []
        self.filters_ = []
        self.csps_ = []
        nyq = float(self.sfreq) / 2.0
        for low, high in self.bands:
            low = float(low)
            high = float(high)
            if low >= nyq - 1.0:
                continue
            high = min(high, nyq - 0.5)
            if high <= low:
                continue
            sos = signal.butter(self.filter_order, [low, high], btype="bandpass", fs=self.sfreq, output="sos")
            X_band = signal.sosfiltfilt(sos, X, axis=-1)
            csp = factory(self.n_components)
            csp.fit(X_band, y)
            self.active_bands_.append((low, high))
            self.filters_.append(sos)
            self.csps_.append(csp)
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        feats = []
        for sos, csp in zip(self.filters_, self.csps_):
            X_band = signal.sosfiltfilt(sos, X, axis=-1)
            f = csp.transform(X_band)
            feats.append(f)
        if not feats:
            return np.empty((len(X), 0), dtype=float)
        return np.concatenate(feats, axis=1)


class FBCSP(BaseEstimator, ClassifierMixin):
    """Filter Bank Common Spatial Patterns (FBCSP) Classifier.

    Combines multi-band filtering (FilterBankCSP), feature selection (SelectKBest),
    and classification (LDA with automatic shrinkage or Logistic Regression).
    """

    def __init__(
        self,
        sfreq: float = 250.0,
        bands: Optional[Sequence[Tuple[float, float]]] = None,
        n_components: int = 4,
        k_features: int = 8,
        score_func: Any = f_classif,
        classifier: str = "lda",
        filter_order: int = 4,
        csp_factory: Optional[Callable] = None,
    ):
        self.sfreq = sfreq
        self.bands = bands
        self.n_components = n_components
        self.k_features = k_features
        self.score_func = score_func
        self.classifier = classifier
        self.filter_order = filter_order
        self.csp_factory = csp_factory

    def fit(self, X: np.ndarray, y: np.ndarray) -> "FBCSP":
        X = np.asarray(X)
        y = np.asarray(y)
        self.classes_ = np.unique(y)
        self.fb_ = FilterBankCSP(
            sfreq=self.sfreq,
            bands=self.bands,
            n_components=self.n_components,
            csp_factory=self.csp_factory,
            filter_order=self.filter_order,
        )
        feats = self.fb_.fit_transform(X, y)
        k = min(self.k_features, feats.shape[1]) if feats.shape[1] > 0 else 1
        self.selector_ = SelectKBest(score_func=self.score_func, k=k)
        feats_sel = self.selector_.fit_transform(feats, y)
        if self.classifier == "lr":
            self.clf_ = LogisticRegression(C=1.0, max_iter=1000, solver="lbfgs")
        else:
            self.clf_ = LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")
        self.clf_.fit(feats_sel, y)
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        feats = self.fb_.transform(X)
        return self.selector_.transform(feats)

    def fit_transform(self, X: np.ndarray, y: np.ndarray) -> np.ndarray:
        return self.fit(X, y).transform(X)

    def predict(self, X: np.ndarray) -> np.ndarray:
        feats_sel = self.transform(X)
        return self.clf_.predict(feats_sel)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        feats_sel = self.transform(X)
        if hasattr(self.clf_, "predict_proba"):
            return self.clf_.predict_proba(feats_sel)
        raise AttributeError("Classifier has no predict_proba method.")

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        feats_sel = self.transform(X)
        if hasattr(self.clf_, "decision_function"):
            return self.clf_.decision_function(feats_sel)
        raise AttributeError("Classifier has no decision_function method.")

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        pred = self.predict(X)
        return float(np.mean(pred == np.asarray(y)))


@dataclass(frozen=True)
class DecoderSpec:
    name: str
    uses_csp: bool
    base: dict = field(default_factory=dict)       # fixed primary settings
    grid: tuple = ()                               # settings tuned in the P5 designs

    def _features(self, csp_factory, p):
        if self.name in ("csp_lda", "csp_lr", "csp_svm"):
            return [("csp", csp_factory(p.get("n_csp", 4)))]
        if self.name == "ts_lr":
            try:
                from pyriemann.estimation import Covariances
                from pyriemann.tangentspace import TangentSpace
                return [("cov", Covariances(estimator="oas")), ("ts", TangentSpace(metric="riemann")), ("scaler", StandardScaler())]
            except ImportError:
                return [("cov", CovarianceTransformer(estimator=p.get("cov_estimator", "oas"))), ("ts", TangentSpaceTransformer()), ("scaler", StandardScaler())]
        if self.name == "fbcsp":
            fbcsp_step = FilterBankCSP(
                sfreq=p.get("sfreq", 250.0),
                bands=p.get("bands", DEFAULT_FILTER_BANKS),
                n_components=p.get("n_csp", 4),
                csp_factory=csp_factory,
            )
            sel = SelectKBest(score_func=p.get("score_func", f_classif), k=p.get("k_features", 8))
            return [("fbcsp", fbcsp_step), ("select", sel)]
        raise ValueError(f"Unknown decoder {self.name}")

    def head(self, **params):
        """The classifier alone (used when features were computed outside the pipeline)."""
        p = {**self.base, **params}
        if self.name in ("csp_lda", "fbcsp"):
            return LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")
        if self.name == "csp_svm":
            return SVC(kernel="linear", C=p.get("C", 1.0), random_state=p.get("seed", 42))
        return LogisticRegression(C=p.get("C", 1.0), max_iter=1000, solver="lbfgs")

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
    "csp_svm": DecoderSpec("csp_svm", True, {"n_csp": 4, "C": 1.0}, tuple({"C": c} for c in (0.01, 0.1, 1.0, 10.0))),
    "csp_lr": DecoderSpec("csp_lr", True, {"n_csp": 4, "C": 1.0}, tuple({"C": c} for c in (0.01, 0.1, 1.0, 10.0))),
    "ts_lr": DecoderSpec("ts_lr", False, {"C": 1.0, "cov_estimator": "oas"}, tuple({"C": c} for c in (0.01, 0.1, 1.0, 10.0))),
    "fbcsp": DecoderSpec("fbcsp", True, {"n_csp": 4, "k_features": 8, "sfreq": 250.0}, tuple({"k_features": k} for k in (4, 6, 8, 12, 16))),
}


def build_decoder_pipeline(
    decoder_name: str,
    n_csp: int = 6,
    csp_factory: Optional[Callable] = None,
    sfreq: float = 250.0,
    **kwargs,
) -> Pipeline:
    """Build a standard decoder pipeline.

    Supported decoders:
      - 'csp_lda': CSP + Linear Discriminant Analysis with automatic shrinkage
      - 'csp_svm': CSP + Linear Support Vector Classifier (SVC with linear kernel)
      - 'csp_lr':  CSP + L2-regularized Logistic Regression
      - 'ts_lr':   Covariance + Riemannian Tangent Space + StandardScaler + Logistic Regression
      - 'fbcsp':   Filter Bank CSP + SelectKBest + Shrinkage LDA
    """
    if decoder_name not in DECODERS:
        raise ValueError(f"Unknown decoder: {decoder_name}. Supported: {sorted(DECODERS.keys())}")
    factory = csp_factory or get_csp_factory("rank_safe")
    params = {"n_csp": n_csp, "sfreq": sfreq, **kwargs}
    return DECODERS[decoder_name].build(factory, **params)
