"""Figures. Uses a non-interactive backend so scripts run on servers."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from .signal_utils import band_timecourse  # noqa: E402
from .summary import binomial_threshold  # noqa: E402


def plot_erd_timecourses(erd, times, freqs, ch_names, band, path,
                         channels=("C3", "Cz", "C4"), title=""):
    """Band-averaged ERD over motor channels, left vs right imagery."""
    chans = [c for c in channels if c in ch_names]
    fig, axes = plt.subplots(1, len(chans), figsize=(4.2 * len(chans), 3.4), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, ch in zip(axes, chans):
        i = ch_names.index(ch)
        for cond, color in (("left", "tab:blue"), ("right", "tab:red")):
            tc = band_timecourse(erd[cond][i], freqs, band)
            ax.plot(times, tc, color=color, label=f"imagine {cond}")
        ax.axvline(0, color="k", lw=0.8)
        ax.axhline(0, color="gray", lw=0.5)
        ax.set_title(ch)
        ax.set_xlabel("Time from cue (s)")
    axes[0].set_ylabel(f"Power change (%) {band[0]:g}-{band[1]:g} Hz")
    axes[0].legend(frameon=False)
    if title:
        fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_group_accuracy(df, path):
    """Per-subject accuracy against chance and the binomial significance threshold."""
    d = df.sort_values("mean_acc").reset_index(drop=True)
    sig = d["perm_p"] < 0.05
    fig, ax = plt.subplots(figsize=(max(5, 0.25 * len(d) + 2), 3.8))
    ax.scatter(d.index[~sig], d["mean_acc"][~sig], color="gray", label="p >= 0.05 (permutation)")
    ax.scatter(d.index[sig], d["mean_acc"][sig], color="tab:green", label="p < 0.05 (permutation)")
    ax.axhline(0.5, color="k", lw=0.8, label="chance (50%)")
    n = int(d["n_trials"].median())
    ax.axhline(binomial_threshold(n), color="tab:orange", ls="--", lw=0.8,
               label=f"binomial threshold, n={n}")
    ax.set_xlabel("Subjects (sorted by accuracy)")
    ax.set_ylabel("Cross-validated accuracy")
    ax.set_ylim(0.2, 1.0)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_leakcheck_null(null_tab, path, title=""):
    """False-positive rate of each design when the labels carry no signal (one decoder, one null type)."""
    t = null_tab.iloc[::-1]
    fig, ax = plt.subplots(figsize=(7, 0.45 * len(t) + 1.8))
    y = np.arange(len(t))
    err = np.vstack([t["false_positive_rate"] - t["fpr_ci_low"], t["fpr_ci_high"] - t["false_positive_rate"]])
    ax.barh(y, t["false_positive_rate"], xerr=np.clip(err, 0, None), color="#9aa5b1", ecolor="k")
    ax.axvline(float(t["nominal_alpha"].iloc[0]), color="#d55e00", ls="--", lw=1, label="nominal 5%")
    ax.set_yticks(y)
    ax.set_yticklabels(t["design"])
    ax.set_xlabel("False-positive rate with null labels")
    ax.set_title(title, fontsize=10)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_leakcheck_inflation(by_subject, path, title=""):
    """Per-subject accuracy inflation (percentage points) of each leaky design versus its reference."""
    designs = list(by_subject["design"].unique())
    fig, ax = plt.subplots(figsize=(1.5 * len(designs) + 2, 4))
    rng = np.random.default_rng(0)
    for i, d in enumerate(designs):
        v = by_subject.loc[by_subject["design"] == d, "delta_pp"].to_numpy()
        ax.scatter(i + rng.uniform(-0.15, 0.15, len(v)), v, s=14, alpha=0.6, color="#0072b2")
        ax.hlines(np.median(v), i - 0.3, i + 0.3, color="k", lw=2)
    ax.axhline(0, color="gray", lw=0.8)
    ax.set_xticks(range(len(designs)))
    ax.set_xticklabels(designs, rotation=25, ha="right", fontsize=8)
    ax.set_ylabel("Inflation (percentage points)")
    ax.set_title(title, fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_paired_accuracy(by_subject, design, path):
    """Slope plot: every subject's accuracy under the reference design and under the leaky design."""
    g = by_subject[by_subject["design"] == design]
    fig, ax = plt.subplots(figsize=(3.6, 4))
    for _, r in g.iterrows():
        ax.plot([0, 1], [r["acc_ref"], r["acc_leaky"]], color="#999999", lw=0.6, alpha=0.7)
    ax.plot([0, 1], [g["acc_ref"].median(), g["acc_leaky"].median()], color="#0072b2", lw=3)
    ax.axhline(0.5, color="k", lw=0.6, ls=":")
    ax.set_xticks([0, 1])
    ax.set_xticklabels([g["reference"].iloc[0], design], rotation=15, ha="right", fontsize=8)
    ax.set_ylabel("Accuracy")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
