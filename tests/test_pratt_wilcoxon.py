"""Unit tests for Pratt Wilcoxon signed-rank test and statistical edge cases."""
import numpy as np
import pytest
import scipy.stats as stats
from emi.leakstats import wilcoxon_pratt, hodges_lehmann


def test_pratt_no_zeros_no_ties():
    """Case 1: Standard sample without zeros or ties."""
    d = [1.2, 2.5, -0.8, 3.1, -1.5, 4.0, 0.5]
    w, z, p = wilcoxon_pratt(d)
    res_sp = stats.wilcoxon(d, zero_method="pratt", correction=True, method="approx")
    assert np.isclose(w, res_sp.statistic)
    assert np.isclose(p, res_sp.pvalue)
    assert z > 0


def test_pratt_single_zero():
    """Case 2: Single zero difference ranked among absolute values."""
    d = [1.2, 0.0, -0.8, 3.1, -1.5, 4.0, 0.5]
    w, z, p = wilcoxon_pratt(d)
    res_sp = stats.wilcoxon(d, zero_method="pratt", correction=True, method="approx")
    assert np.isclose(w, res_sp.statistic)
    assert np.isclose(p, res_sp.pvalue)


def test_pratt_multiple_zeros():
    """Case 3: Multiple zeros verifying non-zero tie correction isolation."""
    d = [1.2, 0.0, 0.0, 3.1, -1.5, 4.0, 0.0]
    w, z, p = wilcoxon_pratt(d)
    res_sp = stats.wilcoxon(d, zero_method="pratt", correction=True, method="approx")
    assert np.isclose(w, res_sp.statistic)
    assert np.isclose(p, res_sp.pvalue)


def test_pratt_tied_nonzero():
    """Case 4: Tied nonzero differences in positive and negative values."""
    d = [1.2, 1.2, -1.2, 3.1, -1.5, 3.1, 0.5]
    w, z, p = wilcoxon_pratt(d)
    res_sp = stats.wilcoxon(d, zero_method="pratt", correction=True, method="approx")
    assert np.isclose(w, res_sp.statistic)
    assert np.isclose(p, res_sp.pvalue)


def test_pratt_symmetric_tied_pairs():
    """Case 5: Perfectly symmetric tied pairs centered at zero."""
    d = [0.0, 2.0, 2.0, -2.0, -2.0, 0.0, 5.0, -5.0]
    w, z, p = wilcoxon_pratt(d)
    res_sp = stats.wilcoxon(d, zero_method="pratt", correction=True, method="approx")
    assert np.isclose(w, res_sp.statistic)
    assert np.isclose(z, 0.0)
    assert np.isclose(p, 1.0)


def test_pratt_float_tolerance():
    """Case 6: Differences smaller than tolerance threshold 1e-9 classified as zero."""
    d = [1.2, 1e-10, -0.8, 3.1, -1e-11, 4.0, 0.5]
    d_clean = [1.2, 0.0, -0.8, 3.1, 0.0, 4.0, 0.5]
    w, z, p = wilcoxon_pratt(d, zero_tol=1e-9)
    res_sp = stats.wilcoxon(d_clean, zero_method="pratt", correction=True, method="approx")
    assert np.isclose(w, res_sp.statistic)
    assert np.isclose(p, res_sp.pvalue)


def test_pratt_all_zeros():
    """Case 7: All differences exactly zero."""
    d = [0.0, 0.0, 0.0, 0.0, 0.0]
    w, z, p = wilcoxon_pratt(d)
    assert w == 0.0
    assert z == 0.0
    assert p == 1.0


def test_pratt_empty_and_nan():
    """Case 8: Handling of empty arrays and NaNs."""
    w, z, p = wilcoxon_pratt([])
    assert np.isnan(w) and np.isnan(p)
    d = [1.0, np.nan, -2.0, 3.0]
    w, z, p = wilcoxon_pratt(d)
    assert not np.isnan(w) and not np.isnan(p)


def test_hodges_lehmann_walsh():
    """Case 9: Exact Hodges-Lehmann pseudomedian calculation."""
    d = np.array([1.0, 2.0, 3.0, 4.0])
    # Walsh averages:
    # (1+1)/2=1, (1+2)/2=1.5, (1+3)/2=2, (1+4)/2=2.5
    # (2+2)/2=2, (2+3)/2=2.5, (2+4)/2=3
    # (3+3)/2=3, (3+4)/2=3.5
    # (4+4)/2=4
    # Sorted: [1.0, 1.5, 2.0, 2.0, 2.5, 2.5, 3.0, 3.0, 3.5, 4.0] -> median is 2.5
    assert np.isclose(hodges_lehmann(d), 2.5)


def test_continuity_correction_direction():
    """Case 10: Continuity correction properly shrinks z towards zero."""
    d = [5.0, 4.0, 3.0, 2.0, 1.0, 0.5]
    w, z, p = wilcoxon_pratt(d)
    # W+ is maximum (21), mu is 21/2 = 10.5. diff = 10.5, cc reduces diff by 0.5 to 10.0
    n = 6
    mu = n * (n + 1) / 4.0
    sd = np.sqrt(n * (n + 1) * (2 * n + 1) / 24.0)
    z_expected = (21 - mu - 0.5) / sd
    assert np.isclose(z, z_expected)
