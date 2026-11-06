"""Group-level summaries and chance-level helpers (numpy/scipy/pandas only)."""
import numpy as np
import pandas as pd
from scipy import stats


def binomial_threshold(n_trials: int, p: float = 0.5, alpha: float = 0.05) -> float:
    """Smallest accuracy that beats chance at one-sided level `alpha`.

    Uses the binomial distribution. With few trials this threshold is far
    above 50 percent, which is why single-subject accuracy needs care.
    CAUTION: it assumes independent test trials. Trials within a run are not independent (alternating labels,
    slow drift), so this threshold is only a rough guide. For per-subject claims use the label-null p-values
    (permutation and circular shift) from emi.decode / emi.leakcheck.
    """
    k = int(stats.binom.isf(alpha, n_trials, p)) + 1  # smallest k with P(X >= k) <= alpha
    return k / n_trials


def summarize_group(df: pd.DataFrame, n_boot: int = 2000, seed: int = 0) -> dict:
    """Summarise per-subject results.

    Expects columns: mean_acc (0-1) and perm_p (permutation p-value).
    """
    acc = df["mean_acc"].to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    boots = np.array([rng.choice(acc, size=len(acc), replace=True).mean() for _ in range(n_boot)])
    n_sig = int((df["perm_p"] < 0.05).sum())
    diffs = acc - 0.5
    if np.allclose(diffs, 0):
        wilcoxon_p = 1.0
    else:
        wilcoxon_p = float(stats.wilcoxon(diffs).pvalue)
    return {
        "n_subjects": int(len(acc)),
        "mean_acc": float(acc.mean()),
        "median_acc": float(np.median(acc)),
        "sd_acc": float(acc.std(ddof=1)) if len(acc) > 1 else float("nan"),
        "ci95_mean_acc": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
        "n_subjects_perm_p_below_0.05": n_sig,
        "fraction_perm_p_below_0.05": n_sig / len(acc),
        "wilcoxon_p_vs_chance": wilcoxon_p,
        "note": "About 5 percent of subjects are expected to pass p<0.05 by chance alone.",
    }
