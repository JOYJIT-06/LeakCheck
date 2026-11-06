"""Needs MNE. Skipped automatically when MNE is not installed."""
import numpy as np
import pytest

pytest.importorskip("mne")

from emi.config import Config  # noqa: E402
from emi.decode import evaluate  # noqa: E402


def _synthetic(n_trials=60, n_ch=8, n_times=160, informative=True, seed=0):
    rng = np.random.default_rng(seed)
    y = np.tile([0, 1], n_trials // 2)
    X = rng.standard_normal((n_trials, n_ch, n_times))
    if informative:
        X[y == 0, 0, :] *= 3.0   # class 0: more variance in channel 0
        X[y == 1, 1, :] *= 3.0   # class 1: more variance in channel 1
    return X, y


def test_informative_data_is_decoded():
    X, y = _synthetic(informative=True)
    res = evaluate(X, y, Config(n_perm=20))
    assert res["mean_acc"] > 0.8
    assert res["perm_p"] < 0.1


def test_noise_is_not_decoded():
    X, y = _synthetic(informative=False, seed=1)
    res = evaluate(X, y, Config(n_perm=20))
    assert 0.3 < res["mean_acc"] < 0.7
