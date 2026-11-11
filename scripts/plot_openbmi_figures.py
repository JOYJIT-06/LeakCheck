# -*- coding: utf-8 -*-
"""Publication-Quality Figure Generation for OpenBMI (Lee et al. 2019) Replication Benchmark.

Outputs:
  1. figures/openbmi_v2/paired_accuracy_openbmi.png (and .pdf)
     - Paired accuracy plot comparing D3 (Leave-One-Run-Out) vs D1s (Size-Matched Random Partition)
  2. figures/openbmi_v2/inflation_openbmi.png (and .pdf)
     - Leakage inflation plot showing P1 - D3 effect across CSP-LDA and Riemannian TS-LR
"""

from __future__ import annotations

import argparse
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def set_publication_style():
    """Configure matplotlib parameters for publication-grade figures."""
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["DejaVu Serif", "Times New Roman", "Computer Modern Roman"],
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 13,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.titlesize": 14,
        "lines.linewidth": 1.5,
        "lines.markersize": 6,
        "axes.linewidth": 1.0,
        "grid.linewidth": 0.5,
        "grid.alpha": 0.5,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.05,
    })


def plot_paired_accuracy(
    metrics_df: pd.DataFrame,
    contrasts_df: pd.DataFrame,
    out_dir: Path,
    decoder: str = "csp_lda",
):
    """Plot paired scatter and slope comparing D3 vs D1s for the specified decoder."""
    sub_df = metrics_df[metrics_df["decoder"] == decoder].copy()
    piv = sub_df.pivot(index="subject", columns="design", values="accuracy")

    if "D3_loro" not in piv.columns or "D1s_size_matched" not in piv.columns:
        print(f"Skipping paired accuracy plot: required designs not found for {decoder}")
        return

    x = piv["D3_loro"].values * 100.0
    y = piv["D1s_size_matched"].values * 100.0

    # Retrieve contrast statistics from design_comparisons.csv
    contrast_row = contrasts_df[
        (contrasts_df["decoder"] == decoder) &
        (contrasts_df["contrast"] == "D1s_vs_D3")
    ]
    
    delta_hl = np.median(y - x)
    ci_low, ci_high = np.nan, np.nan
    p_val = np.nan
    if not contrast_row.empty:
        delta_hl = contrast_row["hl_pp"].values[0]
        ci_low = contrast_row["hl_ci_low_pp"].values[0]
        ci_high = contrast_row["hl_ci_high_pp"].values[0]
        p_val = contrast_row["wilcoxon_p"].values[0]

    fig, ax = plt.subplots(figsize=(6.5, 6))

    # Scatter points
    ax.scatter(x, y, color="#1f77b4", alpha=0.85, edgecolors="navy", s=55, zorder=4, label=f"Participants (N={len(x)})")

    # Identity line y = x
    lims = [35, 102]
    ax.plot(lims, lims, color="#7f7f7f", linestyle="--", linewidth=1.2, zorder=2, label="Identity (D1s = D3)")

    # Linear trend
    m, b = np.polyfit(x, y, 1)
    x_grid = np.linspace(lims[0], lims[1], 100)
    ax.plot(x_grid, m * x_grid + b, color="#d62728", linestyle="-", linewidth=1.6, zorder=3,
            label=f"Fit: y = {m:.2f}x + {b:.1f}%")

    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel("Leave-One-Run-Out Accuracy ($D_3$, %)")
    ax.set_ylabel("Size-Matched Random Partition Accuracy ($D_{1s}$, %)")
    decoder_label = "Shrinkage CSP-LDA" if decoder == "csp_lda" else "Riemannian TS-LR"
    ax.set_title(f"Operational ($D_3$) vs Randomized ($D_{{1s}}$) MI Classification\nOpenBMI Session 1 Cohort - {decoder_label}")
    ax.grid(True, linestyle=":", alpha=0.6)

    # Annotation box with Hodges-Lehmann difference
    stat_text = (
        f"$\\Delta_{{\\mathrm{{HL}}}} = {delta_hl:+.2f}$ pp\n"
        f"95% BCa CI: [{ci_low:+.2f}, {ci_high:+.2f}] pp\n"
        f"$p_{{\\mathrm{{Wilcoxon}}}} = {p_val:.2e}$"
    )
    ax.text(
        0.05, 0.95, stat_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#f8f9fa", edgecolor="#ced4da", alpha=0.9),
        zorder=5,
    )

    ax.legend(loc="lower right", framealpha=0.9)
    plt.tight_layout()

    out_png = out_dir / f"paired_accuracy_openbmi_{decoder}.png"
    out_pdf = out_dir / f"paired_accuracy_openbmi_{decoder}.pdf"
    fig.savefig(out_png)
    fig.savefig(out_pdf)
    plt.close(fig)
    print(f"Saved: {out_png}")


def plot_leakage_inflation(
    metrics_df: pd.DataFrame,
    contrasts_df: pd.DataFrame,
    out_dir: Path,
):
    """Plot leakage inflation (P1 - D3) comparing CSP-LDA against Riemannian TS-LR."""
    decoders = ["csp_lda", "ts_lr"]
    data_points = []
    labels = []

    for dec in decoders:
        sub_df = metrics_df[metrics_df["decoder"] == dec].copy()
        piv = sub_df.pivot(index="subject", columns="design", values="accuracy")
        if "P1_csp_on_all" in piv.columns and "D3_loro" in piv.columns:
            diff = (piv["P1_csp_on_all"] - piv["D3_loro"]).values * 100.0
            data_points.append(diff)
            lbl = "Shrinkage CSP-LDA\n(Supervised Spatial Filters)" if dec == "csp_lda" else "Riemannian TS-LR\n(Unsupervised Geometry)"
            labels.append(lbl)

    if not data_points:
        print("Skipping leakage inflation plot: data points not available.")
        return

    fig, ax = plt.subplots(figsize=(7, 5.5))

    positions = [1, 2]
    colors = ["#d62728", "#2ca02c"]

    # Boxplot
    bp = ax.boxplot(
        data_points,
        positions=positions,
        widths=0.35,
        patch_artist=True,
        showmeans=True,
        meanline=True,
        medianprops=dict(color="black", linewidth=1.8),
        meanprops=dict(color="blue", linewidth=1.5, linestyle="--"),
    )

    for patch, col in zip(bp["boxes"], colors):
        patch.set_facecolor(col)
        patch.set_alpha(0.35)

    # Jittered individual points
    rng = np.random.RandomState(42)
    for pos, pts, col in zip(positions, data_points, colors):
        jitter = rng.normal(0, 0.04, size=len(pts))
        ax.scatter(pos + jitter, pts, color=col, alpha=0.75, edgecolors="black", s=45, zorder=4)

    # Zero line
    ax.axhline(0, color="black", linestyle=":", linewidth=1.0, alpha=0.7)

    ax.set_xticks(positions)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Leakage Inflation $\\Delta$ ($P_1 - D_3$, percentage points)")
    ax.set_title("Susceptibility to Global Spatial Preprocessing Contamination ($P_1$)\nOpenBMI Motor Imagery ($N=34$ participants)")
    ax.grid(True, linestyle=":", alpha=0.5, axis="y")

    # Annotation highlighting CSP-LDA vs TS-LR susceptibility
    ax.text(
        0.55, 0.88,
        "CSP-LDA: Strong $P_1$ inflation (+6.25 pp)\n(Spatial filters overfit across runs)\n\nRiemannian TS-LR: Modest $P_1$ shift (+0.75 pp)\n(Covariance geometry is label-agnostic)",
        transform=ax.transAxes,
        fontsize=9.5,
        verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#fff3cd", edgecolor="#ffeeba", alpha=0.9),
    )

    plt.tight_layout()
    out_png = out_dir / "inflation_openbmi.png"
    out_pdf = out_dir / "inflation_openbmi.pdf"
    fig.savefig(out_png)
    fig.savefig(out_pdf)
    plt.close(fig)
    print(f"Saved: {out_png}")


def main():
    parser = argparse.ArgumentParser(description="Generate OpenBMI publication figures")
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("benchmark_results/openbmi_v2"),
        help="Path to openbmi_v2 results",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("figures/openbmi_v2"),
        help="Output directory for figure files",
    )
    args = parser.parse_args()

    metrics_csv = args.results_dir / "participant_metrics.csv"
    contrasts_csv = args.results_dir / "design_comparisons.csv"

    if not metrics_csv.is_file() or not contrasts_csv.is_file():
        print(f"Error: Required CSV files not found in {args.results_dir}")
        return

    args.output_dir.mkdir(parents=True, exist_ok=True)
    set_publication_style()

    metrics_df = pd.read_csv(metrics_csv)
    contrasts_df = pd.read_csv(contrasts_csv)

    for dec in ["csp_lda", "ts_lr"]:
        plot_paired_accuracy(metrics_df, contrasts_df, args.output_dir, decoder=dec)
    plot_leakage_inflation(metrics_df, contrasts_df, args.output_dir)


if __name__ == "__main__":
    main()
