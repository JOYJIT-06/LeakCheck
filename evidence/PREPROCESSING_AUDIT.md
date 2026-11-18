# PREPROCESSING, FILTERING & LEAKAGE AUDIT

**Audit Date**: November 18, 2026 (Stage 2 / Day 2)  
**Lead Auditor**: AGENT 3 (EEG Preprocessing & Leakage Specialist)  
**Reviewer**: LEAD (Scientific Project Director)  
**Target Codebase**: `src/emi/preprocess.py`, `src/emi/config.py`  

---

## 1. Preprocessing Sequence & Operation Taxonomy

The LeakCheck preprocessing pipeline applies eight sequential operations to continuous PhysioNet recordings. The audit categorizes each operation according to its statistical and temporal dependency:

| Step | Operation | Parameters | Category | Temporal Dependency | Cross-Partition Leakage Risk |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **1** | Raw Load & Standardize | 64 channels, standard 10–05 | Fixed Signal I/O | Instantaneous | None |
| **2** | 1.0–40.0 Hz FIR Filtering | $N=529$ taps, Hamming | Fixed Linear Filter | $T_{\mathrm{half}} = 1.650\text{ s}$ | Bleed if concatenated across runs |
| **3** | Common Average Reference (CAR) | $P = I - \frac{1}{M}\mathbf{1}\mathbf{1}^T$ | Instantaneous Spatial Projection | Strictly Instantaneous ($0$ memory) | **Zero** (no fitted parameters) |
| **4** | Bad-Channel Detection | Correlation $<0.40$, Var outlier $|z|>4$ | Data-Adaptive Statistical Fit | Whole Input Time Series | **Yes** if test run included in fit |
| **5** | Spherical Spline Interpolation | MNE spherical splines | Linear Spatial Interpolation | Spatial Only | Dependent on Step 4 bad-channel set |
| **6** | FastICA Blink Removal | Negentropy, max 2 components | Non-Convex Statistical Optimization | Whole Input Time Series | **Yes** if test run included in fit |
| **7** | 8.0–30.0 Hz Decoding Filter | $N=265$ taps, Hamming | Fixed Linear Filter | $T_{\mathrm{half}} = 0.825\text{ s}$ | Bleed if concatenated across runs |
| **8** | Adaptive Artifact Rejection | Median + 6 MAD, $[200, 800]\,\mu\text{V}$ | Empirical Distribution Fit | All Trials in Input | **Yes** if test trials included in fit |

---

## 2. FIR Filter Temporal Support & Boundary Overlap Audit

### 2.1 Exact Support Formulations
- **Decoding Filter (8–30 Hz)**: $N = 265$ taps, $f_s = 160\text{ Hz}$.
  - $T_{\mathrm{half}} = \frac{264}{320} = 0.825000\text{ s}$ ($132$ samples). Total support: $2 T_{\mathrm{half}} = 1.650000\text{ s}$ ($264$ samples).
- **Broadband Filter (1–40 Hz)**: $N = 529$ taps, $f_s = 160\text{ Hz}$.
  - $T_{\mathrm{half}} = \frac{528}{320} = 1.650000\text{ s}$ ($264$ samples). Total support: $2 T_{\mathrm{half}} = 3.300000\text{ s}$ ($528$ samples).

### 2.2 Boundary Separation Across Consecutive MI Trials ($N = 4,591$ Pairs)
- In PhysioNet, consecutive motor imagery trials are separated by an intervening rest period (`T0`), producing a median inter-cue interval of $\Delta t = 8.200\text{ s}$ and a minimum of $\Delta t = 6.500\text{ s}$.
- For the $[1.0, 3.0]\text{ s}$ decoding window:
  $$S_{\mathrm{dec}} = \Delta t - 2.0 - 1.6500 = \Delta t - 3.6500\text{ s}$$
  - Minimum separation: $6.500 - 3.6500 = \mathbf{+2.8500\text{ s}}$ ($456$ samples).
  - Median separation: $8.200 - 3.6500 = \mathbf{+4.5500\text{ s}}$ ($728$ samples).
  - **Empirical Overlap Count**: **0 out of 4,591 pairs overlap (0.00%)**.

---

## 3. Run-Independent Filtering Requirement

### 3.1 Defect in Legacy Pipeline
In the legacy pipeline, runs were concatenated prior to filtering, causing FIR filter impulse response tails to convolve samples across run boundaries. In $D_3$ (Leave-One-Run-Out), this introduced subtle filter bleed between the test run (Run 12) and training runs (Runs 4 and 8).

### 3.2 Required Correction (`filter_run_independent`)
Filter each continuous run ($R_4, R_8, R_{12}$) independently in its own memory buffer with reflection padding at the start and end of each run. In $D_3$, this ensures that cross-run temporal filter bleed is strictly **zero**.

---

## 4. Fold-Isolated Preprocessing Architecture

To eliminate training-transformation contamination, `FoldIsolatedPreprocessor` must be implemented in Day 4:
1. **Bad Channels**: Flagged strictly on concatenated training runs $R_{\mathrm{train}}$ and interpolated across all runs using the training-derived bad set $\mathcal{B}_{\mathrm{train}}$.
2. **FastICA Unmixing**: Unmixing matrix $W_{\mathrm{train}}$ and excluded components $\mathcal{E}_{\mathrm{train}}$ estimated strictly on $R_{\mathrm{train}}$. Applied linearly to test runs $R_{\mathrm{test}}$ without re-estimation.
3. **Artifact Thresholds**: Distribution statistics (median and MAD) computed strictly on training epochs; the resulting scalar threshold $\tau_{\mathrm{train}}$ is applied to test epochs.

---

## 5. Audit Summary & Classification

| Item | Component | Legacy State | Expected State | Classification |
| :--- | :--- | :--- | :--- | :--- |
| **PREP-01** | Cross-Run FIR Filtering | Concatenated filtering across runs | Run-independent filtering | **VERIFIED DEFECT** |
| **PREP-02** | Common Average Reference | Treated as data-dependent | Instantaneous linear projection ($P$) | **VERIFIED CORRECT** |
| **PREP-03** | FastICA Fitting Scope | Fitted on whole continuous recording | Fitted strictly on training runs | **VERIFIED DEFECT** |
| **PREP-04** | Artifact Rejection Threshold | Whole-recording adaptive threshold | Estimated strictly on training epochs | **VERIFIED DEFECT** |
| **PREP-05** | Decoding Window Support | Nominal gap $\ge 4.50\text{ s}$ | $S_{\mathrm{dec}} \ge 2.85\text{ s}$ (0% overlap) | **VERIFIED CORRECT** |
