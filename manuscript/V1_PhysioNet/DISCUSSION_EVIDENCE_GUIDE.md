# LeakCheck V1.1 Discussion and Limitations Evidence Guide

**Document ID**: `manuscript/V1_PhysioNet/DISCUSSION_EVIDENCE_GUIDE.md`  
**Milestone**: M4 (Scientific Manuscript & Evidence Package)  
**Study Scope**: PhysioNet EEGMMIDB Benchmark ($N = 105$)  
**Target Manuscript Section**: Section 9 (Discussion) & Section 10 (Limitations)  
**Date**: November 2026  
**Status**: APPROVED — VERIFIED COMPLETE DISCUSSION & LIMITATIONS GUIDE  

---

## 1. Overview and Core Philosophy

The purpose of this guide is to establish strict epistemological boundaries for the Discussion and Limitations sections of the LeakCheck V1.1 manuscript. It enforces a rigorous distinction between:
1. **Directly Demonstrated Empirical Findings**: Claims conclusively proven by our data ($N = 105$) and statistical tests.
2. **Methodological Hypotheses & Explanations**: Plausible scientific mechanisms that explain the observed data but are not directly isolated by independent experimental manipulation.
3. **Findings Consistent with Previous Literature**: Empirical agreements and divergences with published BCI benchmarks.
4. **Findings That Cannot Be Generalized**: Specific boundary conditions where findings must not be extrapolated without further testing.
5. **Explicit Methodological Limitations**: Transparent disclosures regarding unperformed controls, recording constraints, and design boundaries.

---

## 2. Five-Pillar Epistemological Categorization

### Pillar 1: Directly Demonstrated Empirical Findings (Rock-Solid Facts)
These claims are mathematically proven and supported by 100% reproducible computational evidence:
1. **Spatial Filter Contamination Produces Massive Optimistic Bias**: Fitting Common Spatial Pattern (CSP) filters globally across all recording runs prior to fold partitioning ($P_1$) causes an extreme $+24.50$ pp pseudo-median performance inflation ($d_z = +1.771, p_{\text{Holm}} = 4.43 \times 10^{-18}$). Over $96\%$ of participants exhibit substantial inflation.
2. **Cardinality-Matched Trial Shuffling Refutes Universal Inflation**: When fold sample size and per-class trial counts strictly match Leave-One-Run-Out cross-validation ($D_{1s}$), random trial shuffling produces a statistically significant performance *deflation* ($-2.68$ pp, $p_{\text{Holm}} = 5.86 \times 10^{-5}$, $d_z = -0.449$). Across the cohort, 66 of 105 participants ($62.9\%$) experience lower accuracy under random shuffling.
3. **Unconstrained $k$-Fold Cross-Validation Exacerbates Deflation**: Standard $k$-fold cross-validation ($D_{1m}$) compounds performance deflation to $-4.47$ pp ($d_z = -0.685, p_{\text{Holm}} = 1.08 \times 10^{-8}$) due to fluctuating fold sizes.
4. **Cardinality Matching Recovers Hidden Accuracy**: Matching fold cardinalities ($D_{1s}$ vs. $D_{1m}$) recovers $+1.86$ pp of classification performance ($p_{\text{Holm}} = 5.29 \times 10^{-7}, d_z = +0.552$).
5. **Cross-Validation Schemes Are Statistically Non-Equivalent**: Two One-Sided Tests (TOST) confirm that none of the evaluated cross-validation schemes are equivalent to the clean operational reference $D_3$ within a clinically relevant $\pm 2.0$ pp equivalence margin (all $p_{\text{TOST}} > 0.05$).

---

### Pillar 2: Methodological Hypotheses & Neurophysiological Explanations
These are interpretations that explain *why* the findings occur. They must be clearly phrased as hypotheses, not proven facts:
1. **Inter-Run Non-Stationarity Mechanism**:
   - *Hypothesis*: In clean LORO ($D_3$), classifiers are trained on contiguous runs where sensor contact and cognitive states are relatively stable within the block. When trials are randomly shuffled across runs ($D_{1s}$), each training fold contains a heterogeneous mixture of trials from different sessions. This forces the linear classifier to fit a compromise decision boundary that bridges shifting baseline noise, degrading test-fold accuracy.
   - *Manuscript Guidance*: Use hedged phrasing ("our findings suggest," "this pattern is consistent with inter-run non-stationarity"). Do not assert that impedance drift was directly measured.
2. **Cognitive Fatigue and SMR Desynchronization Dynamics**:
   - *Hypothesis*: Motor imagery mastery, attention, and sensory feedback fluctuate across recording runs (Run 4 vs. 8 vs. 12), introducing non-stationary class distributions.
   - *Manuscript Guidance*: State as a plausible contributing factor supported by clinical BCI literature.

---

### Pillar 3: Consistency and Divergence with Published Literature

| Literature Theme | Landmark Citations | Agreement / Divergence in LeakCheck V1.1 |
|---|---|---|
| **Data Leakage Severity** | Kapoor & Narayanan (2023), Kaufman et al. (2012), Lemm et al. (2011) | **Complete Agreement**: Confirms that supervised feature extraction prior to partitioning severely inflates accuracy ($+24.50$ pp), completely distorting scientific claims. |
| **Universal Random CV Inflation Dogma** | Saeb et al. (2017), Farquhar & Hill (2013) | **Direct Divergence / Refutation**: While prior literature asserted that random cross-validation always inflates performance in neuroimaging, we prove that in multi-run SMR-EEG, random cross-validation deflates performance ($-2.68$ pp) due to run-level non-stationarity. |
| **Cross-Validation Sample Size Confounds** | Varoquaux et al. (2017), Varma & Simon (2006) | **Complete Agreement**: Demonstrates that mismatched fold cardinalities introduce an artificial $-1.86$ pp penalty, highlighting the necessity of cardinality matching ($D_{1s}$). |
| **Inter-Run Non-Stationarity & Covariate Shift** | Shenoy et al. (2006), Raza et al. (2019), Perdikis et al. (2018) | **Complete Agreement**: Supports the observation that EEG statistics drift across physical recording blocks. |

---

### Pillar 4: Non-Generalizable Findings (Boundary Conditions)
The author and readers must not generalize the findings beyond these boundaries:
1. **Do Not Generalize Magnitude Across Paradigms**: The $+24.50$ pp leakage inflation and $-2.68$ pp deflation were measured in two-class SMR motor imagery (Left vs. Right fist, 64 channels, OAS-CSP and shrinkage LDA). In P300 spellers, SSVEP, or passive workload monitoring, the magnitude of leakage and non-stationarity will differ substantially due to different feature spaces and SNR characteristics.
2. **Do Not Generalize to Single-Continuous-Run Paradigms**: In paradigms recorded within a single unbroken continuous session with zero run breaks, inter-run impedance drift is absent; temporal autocorrelation may dominate, potentially producing positive inflation rather than deflation under random splitting.
3. **Do Not Generalize to Deep Learning Architectures**: Decoders utilizing end-to-end convolutional neural networks (e.g. EEGNet) or Riemannian tangent-space classifiers may exhibit different sensitivities to inter-run covariance shifts.

---

### Pillar 5: Explicit Disclosures and Methodological Limitations

The manuscript must preserve the following transparent disclosures:
1. **Unperformed Null Controls ($n_{\text{null}} = 0$)**:
   - The historical benchmark run explicitly logged `"n_null": 0` in `settings.json`. Permutation and circular-shift null models were not executed in the historical run. The manuscript must never claim empirical null distribution p-values were computed; all inferential statistics are strictly within-subject paired differences against operational reference $D_3$.
2. **Single Public Corpus**:
   - All empirical analyses evaluate the PhysioNet EEGMMIDB dataset ($N = 105$). While this is a large, high-quality public cohort, it represents a single laboratory acquisition environment (Wadsworth Center, BCI2000).
3. **Lack of Direct Continuous Impedance Telemetry**:
   - While the physical block protocol of PhysioNet (Runs 4, 8, 12 separated by resting pauses) provides strong structural evidence for inter-run drift, continuous scalp-electrode impedance values were not recorded in the EDF files. The impedance drift explanation remains an inference.
4. **Operational vs. Absolute Ground Truth**:
   - Leave-One-Run-Out ($D_3$) cross-validation is an operational engineering reference that simulates deploying a calibrated system on a subsequent block; it is not an absolute mathematical ground truth.
