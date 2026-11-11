import numpy as np
import pandas as pd
from scipy import stats

from emi.summary import binomial_threshold, summarize_group


def test_binomial_threshold_is_correct_boundary():
    n, alpha = 45, 0.05
    thr = binomial_threshold(n, alpha=alpha)
    k = round(thr * n)
    assert stats.binom.sf(k - 1, n, 0.5) <= alpha        # P(X >= k) small enough
    assert stats.binom.sf(k - 2, n, 0.5) > alpha         # k-1 would not be


def test_threshold_shrinks_towards_half_with_more_trials():
    assert binomial_threshold(45) > binomial_threshold(450) > 0.5


def test_summarize_group_basic_numbers():
    df = pd.DataFrame({"mean_acc": [0.5, 0.6, 0.7, 0.8], "perm_p": [0.5, 0.2, 0.03, 0.01]})
    s = summarize_group(df, n_boot=200)
    assert s["n_subjects"] == 4
    assert abs(s["mean_acc"] - 0.65) < 1e-9
    assert s["n_subjects_perm_p_below_0.05"] == 2
    assert s["ci95_mean_acc"][0] <= s["mean_acc"] <= s["ci95_mean_acc"][1]


def test_all_chance_gives_wilcoxon_one():
    df = pd.DataFrame({"mean_acc": [0.5, 0.5, 0.5], "perm_p": [0.9, 0.8, 0.7]})
    assert summarize_group(df, n_boot=50)["wilcoxon_p_vs_chance"] == 1.0
