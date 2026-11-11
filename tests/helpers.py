"""Test helpers that need no MNE: a small numpy CSP and a synthetic EEG-like dataset."""
import numpy as np


from emi.simple_csp import SimpleCSP, numpy_csp_factory  # noqa: E402,F401


def csp_factory(n_components):
    return SimpleCSP(n_components)


def make_data(n_runs=3, per_run=16, n_ch=16, n_times=320, informative=True, seed=0, gain=2.5):
    """Balanced trials in n_runs runs. If informative, channel 0 / 1 variance depends on the class."""
    rng = np.random.default_rng(seed)
    y, runs = [], []
    for r in range(n_runs):
        yy = np.array([0, 1] * (per_run // 2))
        rng.shuffle(yy)
        y.extend(yy)
        runs.extend([r] * per_run)
    y, runs = np.array(y), np.array(runs)
    X = rng.standard_normal((len(y), n_ch, n_times))
    if informative:
        X[y == 0, 0, :] *= gain
        X[y == 1, 1, :] *= gain
    times = np.linspace(0.0, 4.0, n_times, endpoint=False)
    return X, y, runs, times
