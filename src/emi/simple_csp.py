"""A plain two-class CSP in numpy/scipy.

Used (a) by the tests, and (b) by `--csp numpy` in the scripts, so the audit can run without MNE.
It follows the standard definition (trace-normalised class covariances, generalised eigenvectors,
log band power of the projected signals). It is NOT guaranteed to give identical numbers to
mne.decoding.CSP; use the MNE version for the results you report.

v0.3: the generalised eigenproblem is solved inside the subspace the data actually occupy.
Average-referenced EEG (and data with removed ICA components) is rank-deficient; the old code
ranked the empty directions (eigenvalue about 0) as the most discriminative components.
"""
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin


class SimpleCSP(BaseEstimator, TransformerMixin):
    def __init__(self, n_components=4, rank_tol=1e-6):
        self.n_components = n_components
        self.rank_tol = rank_tol

    def fit(self, X, y):
        y = np.asarray(y)
        covs = [np.mean([x @ x.T / np.trace(x @ x.T) for x in X[y == c]], axis=0) for c in (0, 1)]
        w, V = np.linalg.eigh(covs[0] + covs[1])
        keep = w > self.rank_tol * w.max()
        self.rank_ = int(keep.sum())
        P = V[:, keep] / np.sqrt(w[keep])                 # whitening restricted to the data subspace
        ev, U = np.linalg.eigh(P.T @ covs[0] @ P)
        k = min(self.n_components, len(ev))
        order = np.argsort(np.abs(ev - 0.5))[::-1][:k]    # most discriminative = furthest from 0.5
        self.filters_ = (P @ U[:, order]).T
        self.eigenvalues_ = ev
        return self

    def transform(self, X):
        Z = np.einsum("kc,ncs->nks", self.filters_, X)
        return np.log((Z ** 2).mean(axis=2) + 1e-30)


def numpy_csp_factory(n_components):
    return SimpleCSP(n_components)


rank_safe_csp_factory = numpy_csp_factory   # the name used in the scripts and the docs
