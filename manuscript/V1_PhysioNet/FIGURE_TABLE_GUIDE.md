# LeakCheck V1.1 Figure and Table Writing Package Guide

**Document ID**: `manuscript/V1_PhysioNet/FIGURE_TABLE_GUIDE.md`  
**Milestone**: M4 (Scientific Manuscript & Evidence Package)  
**Study Scope**: PhysioNet EEGMMIDB Benchmark ($N = 105$)  
**Target Manuscript Section**: Section 4, Section 6, Section 7, Section 8  
**Generating Scripts**: `scripts/generate_figures.py`, `recalculate_all_stats.py`  
**Date**: November 2026  
**Status**: APPROVED — VERIFIED COMPLETE FIGURE & TABLE WRITING GUIDE  

---

## 1. Overview

This guide catalogs every final figure and table included in the LeakCheck V1.1 manuscript. For each visual and tabular asset, it specifies:
- Table/Figure Number and Canonical Filename
- Output formats and resolutions (PDF, SVG, 300 DPI PNG, 300 DPI TIFF)
- Source data artifacts and generating script functions
- Publication-ready manuscript caption
- Plotted quantities, axes, annotations, and measurement units
- Target manuscript subsection reference

---

## 2. Comprehensive Tables

### Table I: Comprehensive Statistical Revalidation of Cross-Validation Contrasts ($N = 105$)
- **Location in Manuscript**: Section 7 (Empirical Results), immediately following Section 7.1.
- **Source Data**: `benchmark_results/physionet_v1_1/inflation_table.csv`, `inflation_by_subject.csv`
- **Generating Script**: `recalculate_all_stats.py`, lines 180–350; verified via `analysis/R_validation/reproduce_statistics.R`.
- **Target Subsection**: Section 7.1 to 7.4.
- **Description & Content**:
  Presents full parametric, non-parametric, robust Hodges-Lehmann, BCa bootstrap ($B = 10{,}000$), Wilcoxon (standard and Pratt), Holm-adjusted p-values ($m = 3$ and $m = 4$), standardized effect sizes (Cohen's $d_z$, $r_{\text{rb}}$), and Two One-Sided Tests (TOST, $\pm 2.0$ pp margin) across all four contrasts:
  1. Contrast 1 ($P_1$ vs. $D_3$): Supervised Spatial Leakage (Positive Control)
  2. Contrast 2 ($D_{1s}$ vs. $D_3$): Size- and Class-Matched Random Trial Partitioning (Headline)
  3. Contrast 3 ($D_{1m}$ vs. $D_3$): $k$-Matched Stratified Random Partitioning
  4. Contrast 4 ($D_{1s}$ vs. $D_{1m}$): Fold-Geometry Artifact (Exploratory)
- **Units**:
  - Point estimates, medians, means, SE, and Hodges-Lehmann shifts in **percentage points (pp)**.
  - Confidence intervals in **percentage points (pp)**.
  - Standardized effect sizes in **dimensionless units ($d_z$)**.
  - P-values as exact scientific notation.

---

## 3. Publication Figures Manifest

### Figure 1: Pipeline and Cross-Validation Architectures
- **Figure Number**: Figure 1
- **Canonical Filename**: `fig1_workflow_schematic`
- **File Paths**:
  - Vector: `figures/physionet_v1_1/fig1_workflow_schematic.pdf`, `.svg`
  - High-Res Print: `figures/physionet_v1_1/fig1_workflow_schematic.tiff` (300 DPI)
  - Web Preview: `figures/physionet_v1_1/fig1_workflow_schematic.png` (300 DPI, $3000 \times 1650$ px)
- **Source Data**: Architectural specification (`src/emi/splitters.py`, `src/emi/decoders.py`).
- **Generating Function**: `generate_fig1_workflow()` in `scripts/generate_figures.py`.
- **Target Manuscript Section**: Section 3 (Mathematical Formulation of Validation Framework).
- **Plotted Elements & Layout**:
  - Stage 1: PhysioNet EEGMMIDB (64 channels, 160 Hz, Runs 4, 8, 12, $N = 105$).
  - Stage 2: Offline Preprocessing (Butterworth 8–30 Hz bandpass, $[-0.5, +4.0]\,\text{s}$ epoching, $[+1.0, +3.0]\,\text{s}$ active slice, amplitude cleaning).
  - Stage 3: Decoder Pipeline (OAS covariance regularization, 6 CSP components, shrinkage LDA).
  - Stage 4: Four parallel cross-validation routing pathways ($D_3$ LORO, $D_{1s}$ size-matched, $D_{1m}$ $k$-matched, $P_1$ supervised spatial leakage).
- **Manuscript Caption**:
  > *Fig. 1. Schematic diagram of the LeakCheck evaluation architecture. Continuous 64-channel EEG recordings from PhysioNet Runs 4, 8, and 12 undergo zero-phase bandpass filtering (8–30 Hz) and active window extraction (1.0–3.0 s). The preprocessed epochs are routed into four distinct evaluation pipelines: clean operational Leave-One-Run-Out (D3), cardinality-matched random partitioning (D1s), standard k-fold random partitioning (D1m), and supervised spatial filter contamination (P1).*

---

### Figure 2: Participant Accounting and Verification Flow
- **Figure Number**: Figure 2
- **Canonical Filename**: `fig2_participant_flow`
- **File Paths**:
  - Vector: `figures/physionet_v1_1/fig2_participant_flow.pdf`, `.svg`
  - High-Res Print: `figures/physionet_v1_1/fig2_participant_flow.tiff` (300 DPI)
  - Web Preview: `figures/physionet_v1_1/fig2_participant_flow.png` (300 DPI, $2700 \times 1950$ px)
- **Source Data**: `benchmark_results/physionet_v1_1/excluded_or_failed_subjects.csv` and `docs/AUDIT/V1_1_PARTICIPANT_FLOW_AUDIT.md`.
- **Generating Function**: `generate_fig2_flow()` in `scripts/generate_figures.py`.
- **Target Manuscript Section**: Section 4 (Dataset and Participant Selection).
- **Plotted Elements & Annotations**:
  - Top Node: Requested Cohort ($109$ subjects, S001–S109).
  - Branch 1: Automated Preprocessing Exclusions ($n = 3$: S044 bad channels $18.75\%$, S069 bad channels $18.75\%$, S091 $100\%$ amplitude threshold rejections).
  - Intermediate Node: Preprocessed Cohort ($n = 106$).
  - Branch 2: Minimum Trial Threshold Exclusion ($n = 1$: S086 retaining only 24 clean trials $< 30$).
  - Bottom Node: Evaluated Benchmark Cohort ($N = 105$, $96.33\%$ retention).
  - Prominent Callout Box: Formal refutation of preliminary draft line 95 error, proving S088, S092, S100 (128 Hz native) and S104 (160 Hz native) are fully evaluated.
- **Manuscript Caption**:
  > *Fig. 2. Participant inclusion and exclusion flow diagram for the PhysioNet EEGMMIDB cohort. From 109 requested participant recordings, exactly 3 failed automated quality control (S044, S069, S091) and 1 failed minimum trial criteria (S086). The remaining N = 105 participants were fully evaluated across all validation designs. The draft manuscript line 95 error regarding S088, S092, S100, and S104 is formally refuted.*

---

### Figure 3: Absolute Accuracies and Paired Contrast Distributions
- **Figure Number**: Figure 3
- **Canonical Filename**: `fig3_inflation_distributions`
- **File Paths**:
  - Vector: `figures/physionet_v1_1/fig3_inflation_distributions.pdf`, `.svg`
  - High-Res Print: `figures/physionet_v1_1/fig3_inflation_distributions.tiff` (300 DPI)
  - Web Preview: `figures/physionet_v1_1/fig3_inflation_distributions.png` (300 DPI, $3300 \times 1440$ px)
- **Source Data**: `inflation_by_subject.csv` ($N = 105$).
- **Generating Function**: `generate_fig3_distributions()` in `scripts/generate_figures.py`.
- **Target Manuscript Section**: Section 7.1, Section 7.2.
- **Plotted Elements & Units**:
  - **Panel A (Absolute Accuracy)**: Four violin/box plots with jittered subject points for $D_3$, $D_{1s}$, $D_{1m}$, and $P_1$. Dashed crimson line marks chance level ($50.0\%$). Units: Classification Accuracy (%).
  - **Panel B (Paired Performance Shifts $\Delta$)**: Three violin plots with jittered subject points showing $\Delta$ relative to $D_3$ for $D_{1s} - D_3$, $D_{1m} - D_3$, and $P_1 - D_3$. Diamonds with error bars denote Hodges-Lehmann pseudo-median shifts and 95% BCa bootstrap confidence intervals. Shaded blue horizontal region denotes $\pm 2.0$ pp equivalence margin. Units: Percentage Points (pp).
- **Manuscript Caption**:
  > *Fig. 3. Cohort decoding performance and paired cross-validation contrasts across N = 105 participants. (A) Absolute decoding accuracy distributions for clean operational LORO (D3), size-matched random partitioning (D1s), standard k-fold random partitioning (D1m), and global spatial filter contamination (P1). Crimson dashed line marks theoretical chance performance (50%). (B) Paired accuracy shifts relative to D3. Error diamonds and vertical bars depict the Hodges-Lehmann pseudo-median shifts and 95% BCa confidence intervals. Shaded blue band denotes the pre-specified equivalence region (±2.0 pp).*

---

### Figure 4: Paired Trajectories and Individual Shift Waterfall
- **Figure Number**: Figure 4
- **Canonical Filename**: `fig4_paired_trajectories_waterfall`
- **File Paths**:
  - Vector: `figures/physionet_v1_1/fig4_paired_trajectories_waterfall.pdf`, `.svg`
  - High-Res Print: `figures/physionet_v1_1/fig4_paired_trajectories_waterfall.tiff` (300 DPI)
  - Web Preview: `figures/physionet_v1_1/fig4_paired_trajectories_waterfall.png` (300 DPI, $3300 \times 1440$ px)
- **Source Data**: `inflation_by_subject.csv` (pairs of $D_3$ and $D_{1s}$ per subject).
- **Generating Function**: `generate_fig4_trajectories_waterfall()` in `scripts/generate_figures.py`.
- **Target Manuscript Section**: Section 7.2 (Contrast 2 Headline).
- **Plotted Elements & Units**:
  - **Panel A (Paired Trajectories)**: 105 individual grey/colored lines connecting $D_3 \to D_{1s}$. Bold black line marks median trajectory ($57.78\% \to 52.89\%$). Dashed crimson line marks chance ($50.0\%$). Units: Decoding Accuracy (%).
  - **Panel B (Waterfall Plot)**: 105 ranked vertical bars of individual subject $\Delta = D_{1s} - D_3$. Deflated participants ($\Delta < 0$, coral/red): $66/105$ ($62.9\%$). Inflated participants ($\Delta > 0$, teal/green): $39/105$ ($37.1\%$). Dashed line denotes median shift ($-2.61$ pp). Shaded region denotes $\pm 2.0$ pp equivalence. Units: Accuracy Shift $\Delta$ (pp).
- **Manuscript Caption**:
  > *Fig. 4. Empirical demonstration refuting the universal inflation assumption (N = 105). (A) Paired subject-by-subject trajectories between clean operational LORO (D3) and size-matched random partitioning (D1s). The bold black line denotes the cohort median trajectory (57.78% → 52.89%). (B) Sorted waterfall plot of individual participant performance shifts (D1s − D3). Sixty-six participants (62.9%) exhibit performance deflation (coral bars), while thirty-nine exhibit inflation (teal bars).*

---

### Figure 5: Standardized Effect Sizes and TOST Equivalence Testing
- **Figure Number**: Figure 5
- **Canonical Filename**: `fig5_statistical_effects_tost`
- **File Paths**:
  - Vector: `figures/physionet_v1_1/fig5_statistical_effects_tost.pdf`, `.svg`
  - High-Res Print: `figures/physionet_v1_1/fig5_statistical_effects_tost.tiff` (300 DPI)
  - Web Preview: `figures/physionet_v1_1/fig5_statistical_effects_tost.png` (300 DPI, $3300 \times 1380$ px)
- **Source Data**: `recalculate_all_stats.py`, Table I.
- **Generating Function**: `generate_fig5_effects_tost()` in `scripts/generate_figures.py`.
- **Target Manuscript Section**: Section 7 (Summary), Section 8 (Sensitivity).
- **Plotted Elements & Units**:
  - **Panel A (Effect Sizes)**: Bar chart of within-subject Cohen's $d_z$ for all four contrasts: $P_1$ vs $D_3$ ($+1.771$), $D_{1s}$ vs $D_3$ ($-0.449$), $D_{1m}$ vs $D_3$ ($-0.685$), $D_{1s}$ vs $D_{1m}$ ($+0.552$). Horizontal guidelines mark standard thresholds for small ($0.2$), medium ($0.5$), and large ($0.8$) effects. Units: Dimensionless ($d_z$).
  - **Panel B (TOST Equivalence Testing)**: Forest plot displaying mean differences and 90% confidence intervals against vertical equivalence bounds $[-2.0, +2.0]$ pp. Demonstrates that 90% CIs for all four contrasts fall outside or breach the equivalence region ($p_{\text{TOST}} > 0.05$). Units: Percentage Points (pp).
- **Manuscript Caption**:
  > *Fig. 5. Effect size and equivalence audit across all four evaluated contrasts (N = 105). (A) Standardized within-subject Cohen's dz effect sizes. Horizontal dashed lines denote conventional thresholds for small (|d| = 0.2), medium (|d| = 0.5), and large (|d| = 0.8) effects. (B) Two One-Sided Tests (TOST) equivalence analysis against an equivalence margin of ±2.0 pp (shaded blue band). Error bars represent 90% confidence intervals around the mean difference. All comparisons demonstrate statistical non-equivalence (p > 0.05).*
