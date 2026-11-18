"""Unit tests for dimension-aware numerical SVD rank analysis."""
import numpy as np
import pytest
from emi.diagnostics import numerical_rank_svd


def test_svd_rank_full_rank():
    """Verify that a random full-rank matrix achieves full rank under dimension-aware tolerance."""
    rng = np.random.default_rng(42)
    # 64 channels x 1000 timepoints
    X = rng.standard_normal((64, 1000))
    rank, tol, s = numerical_rank_svd(X)
    assert rank == 64
    assert tol > 0
    assert len(s) == 64


def test_svd_rank_car_projection():
    """Common average reference reduces spatial rank from 64 to 63."""
    rng = np.random.default_rng(42)
    X = rng.standard_normal((64, 1000))
    # Apply CAR
    car_proj = np.eye(64) - (1.0 / 64.0) * np.ones((64, 64))
    X_car = car_proj @ X
    rank, tol, s = numerical_rank_svd(X_car)
    assert rank == 63
    # The smallest singular value should be below tol
    assert s[-1] < tol


def test_svd_rank_interpolated_channels():
    """Interpolating 2 bad channels as linear combinations before CAR reduces rank to 61."""
    rng = np.random.default_rng(42)
    X = rng.standard_normal((64, 1000))
    # Two channels are exact linear combinations of neighbors
    X[0] = (X[1] + X[2]) / 2.0
    X[3] = (X[4] + X[5]) / 2.0
    
    # CAR projection applied to interpolated data
    car_proj = np.eye(64) - (1.0 / 64.0) * np.ones((64, 64))
    X_car = car_proj @ X
    rank, tol, s = numerical_rank_svd(X_car)
    assert rank == 61
    assert s[-1] < tol
    assert s[-2] < tol
    assert s[-3] < tol
