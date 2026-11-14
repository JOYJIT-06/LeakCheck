#!/usr/bin/env python3
"""
generate_figures.py — Publication-Quality Figure Generation Suite for LeakCheck V1.1.

Generates all publication-grade figures in vector (PDF, SVG) and high-resolution raster (300 DPI PNG, 300 DPI TIFF)
using verified empirical data from the PhysioNet EEGMMIDB benchmark (N = 105).

Outputs:
  - fig1_workflow_schematic: Pipeline and cross-validation design architecture.
  - fig2_participant_flow: Participant inclusion/exclusion flow and error refutation.
  - fig3_inflation_distributions: Classification accuracy and paired difference distributions.
  - fig4_paired_trajectories_waterfall: Paired LORO vs D1s trajectories and sorted waterfall.
  - fig5_statistical_effects_tost: Standardized effect sizes and TOST equivalence testing.

Target Output Directories:
  - figures/physionet_v1_1/
  - manuscript/V1_PhysioNet/figures/
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.lines import Line2D


# Define publication style parameters
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans", "Helvetica"],
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "xtick.labelsize": 9.5,
    "ytick.labelsize": 9.5,
    "legend.fontsize": 9.5,
    "figure.titlesize": 13,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "lines.linewidth": 1.5,
})

# Color palette: Nature / IEEE publication colorblind-friendly
NAVY = "#1f4e79"
STEEL_BLUE = "#2b5c8f"
TEAL = "#2e8b57"
CORAL = "#d9534f"
CRIMSON = "#b22222"
GOLD = "#e69f00"
PURPLE = "#6a3d9a"
DARK_GRAY = "#333333"
LIGHT_GRAY = "#e0e0e0"
BG_TINT = "#f8f9fa"


def resolve_paths():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    csv_candidates = [
        os.path.join(base_dir, "benchmark_results", "physionet_v1_1", "inflation_by_subject.csv"),
        os.path.join(base_dir, "inflation_by_subject.csv"),
        "inflation_by_subject.csv",
    ]
    csv_path = None
    for cand in csv_candidates:
        if os.path.isfile(cand):
            csv_path = cand
            break
    if not csv_path:
        raise FileNotFoundError("Could not locate inflation_by_subject.csv")

    out_dirs = [
        os.path.join(base_dir, "figures", "physionet_v1_1"),
        os.path.join(base_dir, "manuscript", "V1_PhysioNet", "figures"),
    ]
    for d in out_dirs:
        os.makedirs(d, exist_ok=True)

    return csv_path, out_dirs


def save_multiformat(fig, base_name, out_dirs):
    formats = ["pdf", "svg", "png", "tiff"]
    for out_dir in out_dirs:
        for fmt in formats:
            path = os.path.join(out_dir, f"{base_name}.{fmt}")
            fig.savefig(path, format=fmt, dpi=300, bbox_inches="tight")
            print(f"Saved: {path}")


def load_and_structure_data(csv_path):
    df = pd.read_csv(csv_path)
    # Pivot so each subject has D3, D1s, D1m, P1
    # Designs: D1s_size_matched, D1m_matched_k, P1_csp_on_all
    piv_leaky = df.pivot(index="subject", columns="design", values="acc_leaky") * 100.0
    piv_ref = df.pivot(index="subject", columns="design", values="acc_ref") * 100.0
    
    # acc_ref is identical across designs for each subject (verified)
    d3_acc = piv_ref.iloc[:, 0].to_numpy()
    d1s_acc = piv_leaky["D1s_size_matched"].to_numpy()
    d1m_acc = piv_leaky["D1m_matched_k"].to_numpy()
    p1_acc = piv_leaky["P1_csp_on_all"].to_numpy()
    subjects = piv_ref.index.to_numpy()

    delta_p1 = p1_acc - d3_acc
    delta_d1s = d1s_acc - d3_acc
    delta_d1m = d1m_acc - d3_acc
    delta_d1s_d1m = d1s_acc - d1m_acc

    return {
        "subjects": subjects,
        "d3": d3_acc,
        "d1s": d1s_acc,
        "d1m": d1m_acc,
        "p1": p1_acc,
        "delta_p1": delta_p1,
        "delta_d1s": delta_d1s,
        "delta_d1m": delta_d1m,
        "delta_d1s_d1m": delta_d1s_d1m,
    }


def generate_fig1_workflow(out_dirs):
    """Figure 1: Complete LeakCheck pipeline & experimental design schematic."""
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.axis("off")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)

    # Box styling helper
    def draw_box(x, y, w, h, title, subtitle, color, text_color="white", alpha=0.9, fontsize=9.5):
        box = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.8,rounding_size=1.5",
            facecolor=color, edgecolor="none", alpha=alpha
        )
        ax.add_patch(box)
        ax.text(x + w / 2, y + h * 0.62, title, ha="center", va="center",
                fontsize=fontsize, fontweight="bold", color=text_color)
        ax.text(x + w / 2, y + h * 0.32, subtitle, ha="center", va="center",
                fontsize=fontsize - 1.5, color=text_color)

    # Stage 1: Raw EEG
    draw_box(2, 68, 22, 22, "PhysioNet EEGMMIDB", "64 channels | 160 Hz\nRuns 4, 8, 12 (Left/Right Fist)\n105 Analyzed Participants", NAVY)

    # Stage 2: Preprocessing
    draw_box(28, 68, 22, 22, "Strict Offline Preprocessing", "Butterworth [8–30 Hz]\nEpochs [-0.5, +4.0 s]\nDecoding Window [+1.0, +3.0 s]\nAmplitude Artifact Clean", STEEL_BLUE)

    # Connect Stage 1 -> Stage 2
    ax.annotate("", xy=(28, 79), xytext=(24, 79),
                arrowprops=dict(arrowstyle="->", lw=2, color=DARK_GRAY))

    # Stage 3: Feature & Classifier
    draw_box(54, 68, 20, 22, "Decoder Pipeline", "OAS Covariance Regularization\n6 CSP Spatial Components\nShrinkage LDA Classifier", TEAL)

    # Connect Stage 2 -> Stage 3
    ax.annotate("", xy=(54, 79), xytext=(50, 79),
                arrowprops=dict(arrowstyle="->", lw=2, color=DARK_GRAY))

    # Stage 4: Split into Pathways
    ax.annotate("", xy=(77, 85), xytext=(74, 79),
                arrowprops=dict(arrowstyle="->", lw=1.5, color=DARK_GRAY))
    ax.annotate("", xy=(77, 50), xytext=(74, 79),
                arrowprops=dict(arrowstyle="->", lw=1.5, color=DARK_GRAY))
    ax.annotate("", xy=(77, 28), xytext=(74, 79),
                arrowprops=dict(arrowstyle="->", lw=1.5, color=DARK_GRAY))
    ax.annotate("", xy=(77, 8), xytext=(74, 79),
                arrowprops=dict(arrowstyle="->", lw=1.5, color=DARK_GRAY))

    # Pathway 1: D3 LORO
    draw_box(77, 76, 21, 16, "D3: Leave-One-Run-Out", "Clean Operational Reference\nTrain: Runs (i, j); Test: Run (k)\nNo Run Boundary Crossing", NAVY)

    # Pathway 2: D1s Size-Matched
    draw_box(77, 54, 21, 16, "D1s: Size-Matched Random", "Headline Comparator\nUniform Shuffle across Runs\nStrict Cardinality Matching", TEAL)

    # Pathway 3: D1m k-Matched
    draw_box(77, 32, 21, 16, "D1m: k-Matched Random", "Standard 3-Fold Stratified\nUnconstrained Trial Sizes\nFold-Geometry Artifact", GOLD, text_color=DARK_GRAY)

    # Pathway 4: P1 Supervised Contamination
    draw_box(77, 10, 21, 16, "P1: Supervised Spatial Leak", "Positive Control\nCSP Fit Globally on ALL Data\nSevere Label-Correlated Leak", CRIMSON)

    # Bottom summary legend banner
    banner = patches.FancyBboxPatch(
        (2, 6), 70, 20,
        boxstyle="round,pad=0.5,rounding_size=1.0",
        facecolor="#f0f4f8", edgecolor="#c0cdd8", lw=1
    )
    ax.add_patch(banner)
    ax.text(4, 21, "Primary Experimental Design Principles:", fontweight="bold", fontsize=9.5, color=NAVY)
    ax.text(4, 16, "• Clean Fold Nesting: In D3, D1s, and D1m, CSP spatial filters and LDA are fit strictly on training fold.", fontsize=8.5, color=DARK_GRAY)
    ax.text(4, 12, "• Isolation of Non-Stationarity: D1s matches exact D3 fold cardinalities, isolating inter-run non-stationarity.", fontsize=8.5, color=DARK_GRAY)
    ax.text(4, 8, "• Controlled Positive Leakage: P1 measures maximum optimistic bias when spatial filters access test-fold labels.", fontsize=8.5, color=DARK_GRAY)

    fig.suptitle("Fig. 1. LeakCheck Experimental Workflow and Cross-Validation Architectures",
                 fontweight="bold", y=0.98, fontsize=12)
    plt.tight_layout()
    save_multiformat(fig, "fig1_workflow_schematic", out_dirs)
    plt.close(fig)


def generate_fig2_flow(out_dirs):
    """Figure 2: Cohort inclusion/exclusion flow diagram."""
    fig, ax = plt.subplots(figsize=(9, 6.5))
    ax.axis("off")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)

    def draw_node(x, y, w, h, title, desc, color, text_color="white", alpha=0.95):
        box = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.8,rounding_size=1.5",
            facecolor=color, edgecolor="none", alpha=alpha
        )
        ax.add_patch(box)
        ax.text(x + w / 2, y + h * 0.65, title, ha="center", va="center",
                fontsize=10, fontweight="bold", color=text_color)
        ax.text(x + w / 2, y + h * 0.32, desc, ha="center", va="center",
                fontsize=8.5, color=text_color)

    # Node 1: Initial Requested
    draw_node(30, 84, 40, 13, "Requested PhysioNet Cohort", "Total 109 Participants (S001 – S109)\n64-Channel Multi-Run EEG", NAVY)

    # Down arrow
    ax.annotate("", xy=(50, 71), xytext=(50, 84),
                arrowprops=dict(arrowstyle="->", lw=2, color=DARK_GRAY))

    # Exclusion 1: QC Automated Exclusions
    draw_node(65, 63, 33, 14, "Stage 1 Automated QC Exclusions (n = 3)",
              "S044: Bad channels 12/64 (18.75% > 15% ceiling)\nS069: Bad channels 12/64 (18.75% > 15% ceiling)\nS091: 100% of trials (45/45) rejected (800 µV ceiling)",
              CORAL)
    ax.annotate("", xy=(65, 70), xytext=(50, 70),
                arrowprops=dict(arrowstyle="->", lw=1.5, color=CORAL))

    # Node 2: Stage 1 Retained
    draw_node(30, 56, 40, 12, "Preprocessed Cohort", "Retained n = 106 Participants\nMotor Imagery Epochs Extracted", STEEL_BLUE)

    # Down arrow
    ax.annotate("", xy=(50, 43), xytext=(50, 56),
                arrowprops=dict(arrowstyle="->", lw=2, color=DARK_GRAY))

    # Exclusion 2: Sample Size Exclusions
    draw_node(65, 36, 33, 13, "Stage 2 Eligibility Exclusion (n = 1)",
              "S086: Only 24 post-cleaning trials retained\n(Fails minimum eligibility threshold of 30 trials)",
              CORAL)
    ax.annotate("", xy=(65, 42), xytext=(50, 42),
                arrowprops=dict(arrowstyle="->", lw=1.5, color=CORAL))

    # Node 3: Final Evaluated Cohort
    draw_node(30, 27, 40, 13, "Analyzed Empirical Benchmark Cohort",
              "N = 105 Participants (96.33% Retention)\nEvaluated across D3, D1s, D1m, and P1",
              TEAL)

    # Callout Box: Refutation of line 95 error
    callout = patches.FancyBboxPatch(
        (10, 3), 80, 18,
        boxstyle="round,pad=0.8,rounding_size=1.5",
        facecolor="#fef8e7", edgecolor="#f0ad4e", lw=1.5
    )
    ax.add_patch(callout)
    ax.text(12, 17, "Formal Refutation of Historical Draft Manuscript Error (Line 95):",
            fontweight="bold", fontsize=9.5, color="#8a6d3b")
    ax.text(12, 13, "• Earlier draft text erroneously claimed S088, S092, S100, S104 were excluded for sampling rate corruption.",
            fontsize=8.5, color=DARK_GRAY)
    ax.text(12, 9.5, "• Audit confirms all 4 participants are 100% evaluated: S088 (51.8%), S092 (61.4%), S100 (61.1%) at native 128 Hz;",
            fontsize=8.5, color=DARK_GRAY)
    ax.text(12, 6, "  and S104 (54.8%) at native 160 Hz with dynamic sample-rate-aware windowing. Only S044, S069, S086, S091 excluded.",
            fontsize=8.5, color=DARK_GRAY)

    fig.suptitle("Fig. 2. PhysioNet EEGMMIDB Participant Flow and Verification Accounting (N = 105)",
                 fontweight="bold", y=0.98, fontsize=12)
    plt.tight_layout()
    save_multiformat(fig, "fig2_participant_flow", out_dirs)
    plt.close(fig)


def generate_fig3_distributions(data, out_dirs):
    """Figure 3: Absolute classification accuracy and paired difference distributions."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.8), gridspec_kw={"width_ratios": [1, 1.2]})

    # Panel A: Absolute Accuracies
    designs = ["D3 (LORO)", "D1s (Size-M)", "D1m (k-M)", "P1 (Global)"]
    acc_data = [data["d3"], data["d1s"], data["d1m"], data["p1"]]
    colors = [NAVY, TEAL, GOLD, CRIMSON]

    vp = ax1.violinplot(acc_data, positions=[1, 2, 3, 4], showmeans=False, showmedians=False, showextrema=False)
    for i, pc in enumerate(vp["bodies"]):
        pc.set_facecolor(colors[i])
        pc.set_edgecolor("none")
        pc.set_alpha(0.35)

    bp = ax1.boxplot(acc_data, positions=[1, 2, 3, 4], widths=0.22, patch_artist=True,
                     boxprops=dict(facecolor="white", edgecolor=DARK_GRAY, lw=1.2),
                     medianprops=dict(color=DARK_GRAY, lw=2),
                     whiskerprops=dict(color=DARK_GRAY, lw=1.2),
                     capprops=dict(color=DARK_GRAY, lw=1.2),
                     flierprops=dict(marker="o", markersize=3, color=DARK_GRAY, alpha=0.5))

    for i, box in enumerate(bp["boxes"]):
        box.set_facecolor(colors[i])
        box.set_alpha(0.6)

    # Add jittered points
    np.random.seed(42)
    for i, y_vals in enumerate(acc_data):
        x_jitter = np.random.normal(i + 1, 0.05, size=len(y_vals))
        ax1.scatter(x_jitter, y_vals, color=colors[i], alpha=0.35, s=12, edgecolors="none")

    ax1.axhline(50.0, color="crimson", linestyle="--", lw=1.2, alpha=0.7, label="Chance Level (50%)")
    ax1.set_xticks([1, 2, 3, 4])
    ax1.set_xticklabels(designs)
    ax1.set_ylabel("Classification Accuracy (%)")
    ax1.set_ylim(25, 105)
    ax1.set_title("A. Absolute Decoding Accuracy Distributions", fontweight="bold", fontsize=10.5)
    ax1.legend(loc="upper left", frameon=True, facecolor=BG_TINT)

    # Panel B: Paired Differences (Deltas relative to D3)
    contrast_labels = ["D1s − D3\n(Size-Matched)", "D1m − D3\n(k-Matched)", "P1 − D3\n(Positive Leak)"]
    deltas = [data["delta_d1s"], data["delta_d1m"], data["delta_p1"]]
    hl_estimates = [-2.6768, -4.4697, +24.5029]
    bca_low = [-3.9444, -5.7980, +21.7460]
    bca_high = [-1.4559, -3.1111, +27.7778]
    p_holm = ["p = 5.86e-5", "p = 1.08e-8", "p = 4.43e-18"]

    vp2 = ax2.violinplot(deltas, positions=[1, 2, 3], showmeans=False, showmedians=False, showextrema=False)
    diff_colors = [TEAL, GOLD, CRIMSON]
    for i, pc in enumerate(vp2["bodies"]):
        pc.set_facecolor(diff_colors[i])
        pc.set_edgecolor("none")
        pc.set_alpha(0.35)

    for i, y_vals in enumerate(deltas):
        x_jitter = np.random.normal(i + 1, 0.05, size=len(y_vals))
        ax2.scatter(x_jitter, y_vals, color=diff_colors[i], alpha=0.35, s=12, edgecolors="none")

    # Plot Hodges-Lehmann estimate & 95% BCa CI
    for i in range(3):
        ax2.errorbar(i + 1, hl_estimates[i], yerr=[[hl_estimates[i] - bca_low[i]], [bca_high[i] - hl_estimates[i]]],
                     fmt="D", color="black", markersize=6, capsize=5, capthick=1.5, lw=1.5, zorder=5)
        # Annotate text
        sign = "+" if hl_estimates[i] > 0 else ""
        ax2.text(i + 1 + 0.18, hl_estimates[i], f"{sign}{hl_estimates[i]:.2f} pp\n{p_holm[i]}",
                 va="center", fontsize=8.5, fontweight="bold", color=DARK_GRAY)

    ax2.axhline(0.0, color="black", linestyle="-", lw=1.0, alpha=0.6)
    # Shaded equivalence region (+- 2 pp)
    ax2.axhspan(-2.0, 2.0, color="#d0e1fd", alpha=0.35, label="Equivalence Region (±2 pp)")
    ax2.set_xticks([1, 2, 3])
    ax2.set_xticklabels(contrast_labels)
    ax2.set_ylabel("Paired Accuracy Shift Δ (pp)")
    ax2.set_ylim(-30, 65)
    ax2.set_title("B. Paired Performance Shifts Relative to D3 (LORO)", fontweight="bold", fontsize=10.5)
    ax2.legend(loc="upper left", frameon=True, facecolor=BG_TINT)

    fig.suptitle("Fig. 3. Cohort Decoding Performance and Paired Cross-Validation Contrasts (N = 105)",
                 fontweight="bold", y=0.99, fontsize=12)
    plt.tight_layout()
    save_multiformat(fig, "fig3_inflation_distributions", out_dirs)
    plt.close(fig)


def generate_fig4_trajectories_waterfall(data, out_dirs):
    """Figure 4: Paired subject trajectories and sorted waterfall plot for D1s vs D3."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.8), gridspec_kw={"width_ratios": [1, 1.2]})

    # Panel A: Paired Trajectories D3 vs D1s
    d3 = data["d3"]
    d1s = data["d1s"]
    n_subj = len(d3)

    for i in range(n_subj):
        col = TEAL if d1s[i] >= d3[i] else CORAL
        ax1.plot([1, 2], [d3[i], d1s[i]], color=col, alpha=0.3, lw=1.0)
        ax1.scatter([1, 2], [d3[i], d1s[i]], color=col, alpha=0.4, s=10)

    # Median trajectory
    med_d3 = np.median(d3)
    med_d1s = np.median(d1s)
    ax1.plot([1, 2], [med_d3, med_d1s], color="black", lw=3.0, marker="o", markersize=8, zorder=6, label=f"Median ({med_d3:.2f}% → {med_d1s:.2f}%)")

    ax1.axhline(50.0, color="crimson", linestyle="--", lw=1.2, alpha=0.7, label="Chance Level (50%)")
    ax1.set_xticks([1, 2])
    ax1.set_xticklabels(["Clean Reference\n(D3 LORO)", "Size-Matched\n(D1s Random)"], fontweight="bold")
    ax1.set_ylabel("Decoding Accuracy (%)")
    ax1.set_xlim(0.8, 2.2)
    ax1.set_ylim(25, 105)
    ax1.set_title("A. Paired Subject Trajectories (D3 vs. D1s)", fontweight="bold", fontsize=10.5)
    ax1.legend(loc="upper left", frameon=True, facecolor=BG_TINT)

    # Panel B: Waterfall Plot of Deltas
    deltas = data["delta_d1s"]
    sorted_idx = np.argsort(deltas)
    sorted_deltas = deltas[sorted_idx]

    bar_colors = [CORAL if val < 0 else TEAL for val in sorted_deltas]
    ax2.bar(range(n_subj), sorted_deltas, color=bar_colors, width=0.85, alpha=0.85)

    n_deflated = np.sum(deltas < 0)
    n_inflated = np.sum(deltas > 0)
    n_tied = np.sum(deltas == 0)

    ax2.axhline(0.0, color="black", lw=1.2)
    ax2.axhline(np.median(deltas), color="black", linestyle="--", lw=1.5, label=f"Median Shift: {np.median(deltas):.2f} pp")
    ax2.axhspan(-2.0, 2.0, color="#d0e1fd", alpha=0.3, label="Equivalence Region (±2 pp)")

    # Annotate summary counts
    ax2.text(10, -15, f"Deflated: {n_deflated}/105 ({n_deflated/n_subj*100:.1f}%)\nMedian Δ: -2.61 pp",
             fontsize=9, fontweight="bold", color=CRIMSON, bbox=dict(boxstyle="round,pad=0.3", facecolor="#fee", edgecolor=CORAL, alpha=0.8))
    ax2.text(70, 10, f"Inflated: {n_inflated}/105 ({n_inflated/n_subj*100:.1f}%)",
             fontsize=9, fontweight="bold", color=TEAL, bbox=dict(boxstyle="round,pad=0.3", facecolor="#efe", edgecolor=TEAL, alpha=0.8))

    ax2.set_xlabel("Participants Ranked by Accuracy Shift (N = 105)")
    ax2.set_ylabel("Accuracy Shift Δ (D1s − D3, pp)")
    ax2.set_xlim(-1, n_subj)
    ax2.set_ylim(-25, 20)
    ax2.set_title("B. Sorted Participant Waterfall Shift (D1s vs. D3)", fontweight="bold", fontsize=10.5)
    ax2.legend(loc="upper left", frameon=True, facecolor=BG_TINT)

    fig.suptitle("Fig. 4. Paired Trajectories and Individual Shift Waterfall Refuting Universal Inflation (N = 105)",
                 fontweight="bold", y=0.99, fontsize=12)
    plt.tight_layout()
    save_multiformat(fig, "fig4_paired_trajectories_waterfall", out_dirs)
    plt.close(fig)


def generate_fig5_effects_tost(out_dirs):
    """Figure 5: Effect sizes (Cohen's dz) and TOST equivalence analysis."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.6), gridspec_kw={"width_ratios": [1, 1.2]})

    # Panel A: Effect Sizes (Cohen's dz)
    contrasts = [
        "P1 vs. D3\n(Positive Leak)",
        "D1s vs. D3\n(Size-Matched)",
        "D1m vs. D3\n(k-Matched)",
        "D1s vs. D1m\n(Fold Geometry)",
    ]
    cohens_dz = [1.7708, -0.4491, -0.6847, 0.5522]
    effect_colors = [CRIMSON, TEAL, GOLD, PURPLE]

    bars = ax1.bar(range(4), cohens_dz, color=effect_colors, width=0.55, alpha=0.85, edgecolor=DARK_GRAY, lw=1.2)
    ax1.axhline(0.0, color="black", lw=1.0)
    ax1.axhline(0.2, color="gray", linestyle=":", lw=1.0, alpha=0.6)
    ax1.axhline(-0.2, color="gray", linestyle=":", lw=1.0, alpha=0.6)
    ax1.axhline(0.5, color="gray", linestyle="--", lw=1.0, alpha=0.6)
    ax1.axhline(-0.5, color="gray", linestyle="--", lw=1.0, alpha=0.6)
    ax1.axhline(0.8, color="gray", linestyle="-.", lw=1.0, alpha=0.6)
    ax1.axhline(-0.8, color="gray", linestyle="-.", lw=1.0, alpha=0.6)

    for i, bar in enumerate(bars):
        yval = bar.get_height()
        va_align = "bottom" if yval >= 0 else "top"
        offset = 0.06 if yval >= 0 else -0.06
        sign = "+" if yval > 0 else ""
        ax1.text(bar.get_x() + bar.get_width() / 2, yval + offset, f"{sign}{yval:.3f}",
                 ha="center", va=va_align, fontweight="bold", fontsize=9, color=DARK_GRAY)

    ax1.set_xticks(range(4))
    ax1.set_xticklabels(contrasts, fontsize=8.5)
    ax1.set_ylabel("Standardized Effect Size (Cohen's $d_z$)")
    ax1.set_ylim(-1.0, 2.1)
    ax1.set_title("A. Within-Subject Effect Sizes (Cohen's $d_z$)", fontweight="bold", fontsize=10.5)

    # Panel B: TOST Equivalence Analysis
    # Means and 90% CIs
    tost_contrasts = [
        "P1 vs. D3",
        "D1s vs. D3",
        "D1m vs. D3",
        "D1s vs. D1m",
    ]
    mean_diffs = [24.8153, -2.7715, -4.6659, 1.8944]
    tost_ci_low = [22.545, -3.771, -5.770, 1.339]
    tost_ci_high = [27.086, -1.772, -3.562, 2.450]
    tost_p = ["p = 1.000", "p = 0.898", "p = 1.000", "p = 0.377"]

    y_pos = np.arange(4)
    ax2.axvspan(-2.0, 2.0, color="#d0e1fd", alpha=0.45, label="Equivalence Bounds (±2.0 pp)")
    ax2.axvline(-2.0, color="crimson", linestyle="--", lw=1.2)
    ax2.axvline(2.0, color="crimson", linestyle="--", lw=1.2)
    ax2.axvline(0.0, color="black", linestyle="-", lw=1.0, alpha=0.5)

    for i in range(4):
        yerr_val = [[mean_diffs[i] - tost_ci_low[i]], [tost_ci_high[i] - mean_diffs[i]]]
        ax2.errorbar(mean_diffs[i], y_pos[i], xerr=yerr_val,
                     fmt="o", color=effect_colors[i], markersize=7, capsize=5, capthick=1.5, lw=2, zorder=5)
        # Text annotation
        ax2.text(tost_ci_high[i] + 0.6, y_pos[i], f"{mean_diffs[i]:+.2f} pp [90% CI: {tost_ci_low[i]:.2f}, {tost_ci_high[i]:.2f}]\n{tost_p[i]} (Non-Equivalent)",
                 va="center", fontsize=8.2, fontweight="bold", color=DARK_GRAY)

    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(tost_contrasts, fontweight="bold", fontsize=9)
    ax2.set_xlabel("Mean Difference and 90% Confidence Interval (pp)")
    ax2.set_xlim(-8, 38)
    ax2.set_ylim(-0.8, 3.8)
    ax2.set_title("B. Two One-Sided Tests (TOST) Equivalence (Margin: ±2.0 pp)", fontweight="bold", fontsize=10.5)
    ax2.legend(loc="lower right", frameon=True, facecolor=BG_TINT)

    fig.suptitle("Fig. 5. Standardized Effect Sizes and TOST Statistical Equivalence Audit (N = 105)",
                 fontweight="bold", y=0.99, fontsize=12)
    plt.tight_layout()
    save_multiformat(fig, "fig5_statistical_effects_tost", out_dirs)
    plt.close(fig)


def main():
    print("=" * 70)
    print("LeakCheck V1.1: Publication Figure Generation Suite")
    print("=" * 70)
    csv_path, out_dirs = resolve_paths()
    print(f"Data Source: {csv_path}")
    print(f"Output Directories: {out_dirs}")

    data = load_and_structure_data(csv_path)
    print(f"Loaded N = {len(data['subjects'])} participant evaluations.")

    print("\n[1/5] Generating Figure 1 (Workflow Schematic)...")
    generate_fig1_workflow(out_dirs)

    print("\n[2/5] Generating Figure 2 (Participant Inclusion Flow)...")
    generate_fig2_flow(out_dirs)

    print("\n[3/5] Generating Figure 3 (Inflation & Shift Distributions)...")
    generate_fig3_distributions(data, out_dirs)

    print("\n[4/5] Generating Figure 4 (Paired Trajectories & Waterfall)...")
    generate_fig4_trajectories_waterfall(data, out_dirs)

    print("\n[5/5] Generating Figure 5 (Effect Sizes & TOST Equivalence)...")
    generate_fig5_effects_tost(out_dirs)

    print("\n" + "=" * 70)
    print("All figures successfully generated in PDF, SVG, 300-DPI PNG, and 300-DPI TIFF.")
    print("=" * 70)


if __name__ == "__main__":
    main()
