# Scientific Issues and Methodological Clarifications

**Project:** LeakCheck  
**Document Identifier:** `docs/AUDIT/SCIENTIFIC_ISSUES.md`  
**Date:** 8 November 2026  
**Auditor:** Senior Computational Neuroscientist & Scientific Software Architect  

---

## 1. Executive Summary

This document records the independent investigation into critical scientific, statistical, and methodological issues raised during the LeakCheck V1.1.0 release and V2 multi-dataset audit. In accordance with core principles of intellectual honesty and anti-sycophancy, all overgeneralized or provisional claims have been scrutinized and corrected against empirical evidence.

---

## 2. Issue Log & Scientific Resolutions

### Issue 1: Epoch Endpoint Convention & Sample Count (OpenBMI)
- **Problem Statement:** The previous report ambiguously stated 1,125 time points for an interval from $-0.5$ to $+4.0$ seconds at 250 Hz. If endpoints were inclusive, $4.5 \times 250 + 1 = 1,126$ samples would be expected.
- **Code Inspection:** In `src/emi/datasets_openbmi.py`:
  ```python
  s_min_proc = int(round(tmin * actual_fs))  # -125
  s_max_proc = int(round(tmax * actual_fs))  # 1000
  start = onset + s_min_proc
  end = onset + s_max_proc
  epoch = cx_proc[start:end, :].T            # Python slice: end - start = 1125
  times = np.linspace(tmin, tmax, X.shape[2], endpoint=False)
  ```
- **Resolution:** The implementation strictly uses a **half-open interval $[-0.5, 4.0)\text{ s}$** with `endpoint=False`. The sample count of **1,125 samples** at 250 Hz is mathematically exact ($1000 - (-125) = 1125$). Documentation and manuscript methods sections have been updated to explicitly specify the half-open interval.

---

### Issue 2: Refutation of Riemannian "Mathematical Immunity" Claim
- **Problem Statement:** Earlier drafts asserted that Riemannian Tangent Space Logistic Regression (TS-LR) is "mathematically immune" to $P_1$ leakage based on an observed $0.00$ pp difference in a 2-subject smoke test.
- **Empirical Evidence ($N=34$ Full OpenBMI Cohort):**
  - CSP-LDA under $P_1$: $\Delta_{\text{HL}} = +6.25\text{ pp}$ ($95\%\text{ BCa CI}: [3.25, 8.23]\text{ pp}$, $p = 1.47 \times 10^{-4}$).
  - TS-LR under $P_1$: $\Delta_{\text{HL}} = +0.75\text{ pp}$ ($95\%\text{ BCa CI}: [0.25, 1.50]\text{ pp}$, $p = 0.0203$).
- **Resolution:** TS-LR is **NOT mathematically immune** to global contamination. A statistically significant, albeit small, positive shift ($+0.75$ pp) occurs because global covariance centering slightly alters the Riemannian Fréchet mean. However, TS-LR is **substantially less susceptible** ($>8\times$ smaller inflation than CSP-LDA) because covariance estimation does not utilize supervised class labels. All manuscript claims asserting "mathematical immunity" have been excised and replaced with:  
  *"No large P1-associated inflation was observed for TS-LR under the tested configuration ($\Delta_{\text{HL}} = +0.75\text{ pp}$ vs. $+6.25\text{ pp}$ for CSP-LDA)."*

---

### Issue 3: Rejection of Universal Claims Regarding Random Cross-Validation
- **Problem Statement:** Earlier literature assumed that random trial-level splitting always inflates BCI performance due to autocorrelation leakage.
- **Empirical Findings Across Cohorts:**
  1. **PhysioNet ($N=105$, 3 stationary MI runs):** Size-matched random splitting ($D_{1s}$) produces a statistically significant **deflation** of $-2.68$ pp ($p = 5.86 \times 10^{-5}$) relative to LORO ($D_3$). Inter-run electrode drift and baseline shifts create heterogeneous multi-modal distributions in mixed training folds, impairing linear classification boundaries.
  2. **OpenBMI ($N=34$, Run 0 offline calibration vs Run 1 online feedback):** Size-matched random splitting ($D_{1s}$) produces a statistically significant **optimistic bias** of $+2.84$ pp ($p = 9.4 \times 10^{-5}$) on CSP-LDA and $+2.94$ pp on TS-LR. In OpenBMI, Run 0 and Run 1 represent distinct operational states; pooling trials across runs allows models to interpolate within states rather than extrapolate across them.
- **Resolution:** The effect of random cross-validation is **paradigm- and dataset-dependent**. It cannot be characterized as universally inflating or deflating. The manuscript has been revised to frame this as an operational divergence reflecting whether recording blocks share stationary experimental conditions.

---

### Issue 4: Precise Characterization of $P_1$ Contamination Pathway
- **Problem Statement:** Previous drafts informally described $P_1$ as injecting "label noise."
- **Resolution:** This description is technically incorrect. $P_1$ does not corrupt labels; rather, it performs **supervised test-label information leakage through the feature-space projection**. Common Spatial Patterns optimizes spatial variance ratios using true test-set class labels, allowing spatial filters to encode test-set noise into the discriminative subspace.

---

### Issue 5: Rigorous Evidence Hierarchy for Leakage Mechanisms (P1–P9)
- **Problem Statement:** Stating that P1–P9 are "validated" when only a subset have been run on real human EEG cohorts.
- **Resolution:** Each mechanism is formally categorized in `docs/AUDIT/V2_VALIDATION_MATRIX.csv` into:
  - *Tier 1: Validated on Real Human EEG Cohorts* ($P_1, D_3, D_{1s}, D_{1m}$).
  - *Tier 2: Validated on Synthetic Benchmarks with Negative Controls* ($P_3, P_4, P_5, P_6, P_7$).
  - *Tier 3: Implemented Architectural Specifications* ($P_2$ ICA, $P_8$ Channel Selection, $P_9$ Run Boundary).
