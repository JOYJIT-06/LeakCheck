"""Statistics for the audit (numpy and scipy only). Unit of analysis = SUBJECT.

Everything here works on paired per-subject differences. Repeated cross-validation
runs are averaged inside a subject first; they are never treated as extra subjects.
"""
import numpy as np
from scipy import stats


def hodges_lehmann(d):
    """Hodges-Lehmann estimate: median of all pairwise (Walsh) averages."""
    d = np.asarray(d, float)
    i, j = np.triu_indices(len(d))
    return float(np.median((d[i] + d[j]) / 2.0))


def bca_ci(d, stat=hodges_lehmann, n_resamples=10000, confidence=0.95, seed=0, return_method=False):
    """BCa bootstrap interval over subjects. Falls back to a percentile interval if BCa fails.

    With return_method=True the result is (low, high, method) with method in
    {"BCa", "percentile", "degenerate", "too_few"}, so the fallback is never silent.
    """
    d = np.asarray(d, float)
    _ret = (lambda lo, hi, m: (lo, hi, m)) if return_method else (lambda lo, hi, m: (lo, hi))
    if len(d) < 3:
        return _ret(np.nan, np.nan, "too_few")
    if np.allclose(d, d[0]):
        return _ret(float(d[0]), float(d[0]), "degenerate")
    try:
        res = stats.bootstrap((d,), lambda x: stat(x), vectorized=False, n_resamples=n_resamples,
                              confidence_level=confidence, method="BCa", random_state=seed)
        lo, hi = res.confidence_interval.low, res.confidence_interval.high
        if np.isfinite(lo) and np.isfinite(hi):
            return _ret(float(lo), float(hi), "BCa")
    except Exception:
        pass
    rng = np.random.default_rng(seed)
    boots = np.array([stat(rng.choice(d, len(d), replace=True)) for _ in range(min(n_resamples, 2000))])
    a = (1 - confidence) / 2
    return _ret(float(np.quantile(boots, a)), float(np.quantile(boots, 1 - a)), "percentile")


def rank_biserial(d):
    """Matched-pairs rank-biserial correlation from the Wilcoxon signed ranks (range -1 to 1)."""
    d = np.asarray(d, float)
    d = d[d != 0]
    if len(d) == 0:
        return 0.0
    ranks = stats.rankdata(np.abs(d))
    wp, wm = ranks[d > 0].sum(), ranks[d < 0].sum()
    return float((wp - wm) / (wp + wm))


def cohens_dz(d):
    d = np.asarray(d, float)
    sd = d.std(ddof=1) if len(d) > 1 else np.nan
    return float(d.mean() / sd) if sd and np.isfinite(sd) and sd > 0 else np.nan


def holm(pvals):
    """Holm step-down adjusted p-values (same order as the input)."""
    p = np.asarray(pvals, float)
    order = np.argsort(p)
    adj = np.empty_like(p)
    running = 0.0
    m = len(p)
    for rank, idx in enumerate(order):
        running = max(running, (m - rank) * p[idx])
        adj[idx] = min(1.0, running)
    return adj


def tost_paired(d, margin, alpha=0.05):
    """Two one-sided t tests for equivalence of the mean paired difference to zero within +-margin."""
    d = np.asarray(d, float)
    n = len(d)
    if n < 3 or d.std(ddof=1) == 0:
        return {"tost_p": np.nan, "equivalent": False}
    se = d.std(ddof=1) / np.sqrt(n)
    p_lower = 1 - stats.t.cdf((d.mean() + margin) / se, n - 1)   # H0: mean <= -margin
    p_upper = stats.t.cdf((d.mean() - margin) / se, n - 1)       # H0: mean >= +margin
    p = float(max(p_lower, p_upper))
    return {"tost_p": p, "equivalent": bool(p < alpha)}


def _logit(a, eps):
    a = np.clip(np.asarray(a, float), eps, 1 - eps)
    return np.log(a / (1 - a))


def paired_summary(acc_leaky, acc_ref, n_test=None, margin_pp=2.0, n_boot=10000, seed=0):
    """Everything the requirements ask for on one paired contrast (inputs are accuracies in 0-1)."""
    a, b = np.asarray(acc_leaky, float), np.asarray(acc_ref, float)
    ok = np.isfinite(a) & np.isfinite(b)
    a, b = a[ok], b[ok]
    d = (a - b) * 100.0                                    # percentage points
    n = len(d)
    out = {"n_subjects": n, "mean_diff_pp": float(d.mean()) if n else np.nan,
           "median_diff_pp": float(np.median(d)) if n else np.nan}
    if n < 3:
        return out
    out["hl_pp"] = hodges_lehmann(d)
    out["hl_ci_low_pp"], out["hl_ci_high_pp"], out["hl_ci_method"] = bca_ci(d, n_resamples=n_boot, seed=seed, return_method=True)
    out["wilcoxon_p"] = 1.0 if np.allclose(d, 0) else float(stats.wilcoxon(d).pvalue)
    eps = 0.5 / max(float(n_test) if n_test else 45.0, 2.0)
    la, lb = _logit(a, eps), _logit(b, eps)
    out["t_logit_p"] = 1.0 if np.allclose(la, lb) else float(stats.ttest_rel(la, lb).pvalue)
    out["rank_biserial"] = rank_biserial(d)
    out["cohens_dz"] = cohens_dz(d)
    out.update(tost_paired(d, margin_pp))
    out["tost_margin_pp"] = margin_pp
    return out


def random_effects_meta(effects, variances, hksj=False):
    """DerSimonian-Laird random-effects pooling across datasets (each dataset = one study).

    effects: per-dataset mean inflation; variances: squared standard error of each mean.
    Returns pooled effect, CI, tau^2, I^2 and a prediction interval for a new dataset.
    With hksj=True the result also carries Hartung-Knapp-Sidik-Jonkman CI fields (suffix _hksj).
    """
    y, v = np.asarray(effects, float), np.asarray(variances, float)
    k = len(y)
    if k < 2 or np.any(v <= 0):
        raise ValueError("Need at least 2 datasets with positive variances.")
    w = 1 / v
    fixed = (w * y).sum() / w.sum()
    q = (w * (y - fixed) ** 2).sum()
    c = w.sum() - (w ** 2).sum() / w.sum()
    tau2 = max(0.0, (q - (k - 1)) / c)
    ws = 1 / (v + tau2)
    mu = (ws * y).sum() / ws.sum()
    se = np.sqrt(1 / ws.sum())
    out = {"k": k, "pooled": float(mu), "se": float(se),
           "ci_low": float(mu - 1.96 * se), "ci_high": float(mu + 1.96 * se),
           "tau2": float(tau2), "I2": float(max(0.0, (q - (k - 1)) / q)) if q > 0 else 0.0, "Q": float(q)}
    if hksj:
        # Hartung-Knapp-Sidik-Jonkman: t-based interval, variance scaled by the weighted residual
        # spread (never narrower than the DL interval). Recommended with fewer than about 10 datasets.
        qh = max(1.0, float((ws * (y - mu) ** 2).sum() / (k - 1)))
        se_h = float(np.sqrt(qh / ws.sum()))
        tq = stats.t.ppf(0.975, k - 1)
        out.update({"se_hksj": se_h, "ci_low_hksj": float(mu - tq * se_h), "ci_high_hksj": float(mu + tq * se_h)})
    if k > 2:
        half = stats.t.ppf(0.975, k - 2) * np.sqrt(tau2 + se ** 2)
        out["pred_low"], out["pred_high"] = float(mu - half), float(mu + half)
    return out


def required_subjects(sd, effect, alpha=0.05, power=0.80, n_max=5000):
    """Subjects needed for a two-sided paired t test to detect `effect` given the SD of paired differences.

    Estimate `sd` from a pilot; do not guess it.
    """
    for n in range(3, n_max):
        df = n - 1
        nc = effect / sd * np.sqrt(n)
        tcrit = stats.t.ppf(1 - alpha / 2, df)
        pw = 1 - stats.nct.cdf(tcrit, df, nc) + stats.nct.cdf(-tcrit, df, nc)
        if pw >= power:
            return n
    return None


def ranking_reversal(acc_leaky: dict, acc_clean: dict):
    """Compare decoder rankings under a leaky and a clean design (inputs: decoder -> mean accuracy)."""
    names = sorted(set(acc_leaky) & set(acc_clean))
    if len(names) < 2:
        raise ValueError("Need at least 2 decoders in both designs.")
    a = np.array([acc_leaky[n] for n in names])
    b = np.array([acc_clean[n] for n in names])
    tau = stats.kendalltau(a, b).statistic
    reversals = sum(1 for i in range(len(names)) for j in range(i + 1, len(names))
                    if (a[i] - a[j]) * (b[i] - b[j]) < 0)
    return {"kendall_tau": float(tau), "n_pairs_reversed": int(reversals),
            "best_leaky": names[int(np.argmax(a))], "best_clean": names[int(np.argmax(b))],
            "best_changed": bool(np.argmax(a) != np.argmax(b))}


def ranking_reversal_bootstrap(acc_leaky_by_decoder, acc_clean_by_decoder, n_boot=2000, seed=0):
    """Does the ranking of decoders change between a leaky and a clean design? With uncertainty.

    Inputs: dict decoder -> per-subject accuracy array (same subject order in both dicts). Subjects are resampled.
    Returns the observed Kendall tau and the bootstrap probability that the best decoder differs between designs.
    With only 2 decoders tau can only be +1 or -1, so the probability is the informative number.
    """
    names = sorted(set(acc_leaky_by_decoder) & set(acc_clean_by_decoder))
    if len(names) < 2:
        raise ValueError("Need at least 2 decoders in both designs.")
    A = np.array([np.asarray(acc_leaky_by_decoder[n], float) for n in names])
    B = np.array([np.asarray(acc_clean_by_decoder[n], float) for n in names])
    ok = np.isfinite(A).all(axis=0) & np.isfinite(B).all(axis=0)
    A, B = A[:, ok], B[:, ok]
    n = A.shape[1]
    rng = np.random.default_rng(seed)
    changed, taus = 0, []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        a, b = A[:, idx].mean(axis=1), B[:, idx].mean(axis=1)
        changed += int(np.argmax(a) != np.argmax(b))
        taus.append(stats.kendalltau(a, b).statistic)
    obs_a, obs_b = A.mean(axis=1), B.mean(axis=1)
    return {"n_subjects": int(n), "kendall_tau_observed": float(stats.kendalltau(obs_a, obs_b).statistic),
            "p_best_decoder_changes": changed / n_boot,
            "tau_ci_low": float(np.nanpercentile(taus, 2.5)), "tau_ci_high": float(np.nanpercentile(taus, 97.5)),
            "best_leaky": names[int(np.argmax(obs_a))], "best_clean": names[int(np.argmax(obs_b))]}
