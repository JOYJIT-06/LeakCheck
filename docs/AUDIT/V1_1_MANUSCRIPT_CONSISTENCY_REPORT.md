# LeakCheck V1.1 Final Manuscript Consistency Audit Report

**Document ID**: `docs/AUDIT/V1_1_MANUSCRIPT_CONSISTENCY_REPORT.md`  
**Milestone**: M4 (Scientific Manuscript & Evidence Package)  
**Study Scope**: LeakCheck V1.1 PhysioNet Benchmark ($N = 105$)  
**Target Manuscript**: `manuscript/V1_PhysioNet/manuscript.md`  
**Audit Sources**:
  - `docs/AUDIT/V1_1_STATISTICAL_VALIDATION.md`
  - `benchmark_results/physionet_v1_1/inflation_table.csv`
  - `benchmark_results/physionet_v1_1/inflation_by_subject.csv`
  - `benchmark_results/physionet_v1_1/settings.json`
  - `manuscript/references.bib`
  - `figures/physionet_v1_1/`
  - `src/emi/` (Python implementation)  
**Date**: November 2026  
**Status**: APPROVED — VERIFIED COMPLETE CROSS-DOCUMENT CONSISTENCY  

---

## 1. Executive Summary

This report establishes the final, automated consistency audit of the revised scientific manuscript (`manuscript/V1_PhysioNet/manuscript.md`) against all underlying benchmark data artifacts, statistical audit reports, figure assets, source code implementations, and bibliographic libraries.

In strict compliance with Phase 11 and Phase 12 of the Master Execution Directive, and User Directive 2026-11-14T18:37:35Z:
1. **Zero Numerical Hallucination**: 100% of reported statistics (means, medians, Hodges-Lehmann shifts, BCa confidence intervals, Wilcoxon test statistics, p-values, Cohen's $d_z$, and TOST bounds) match the machine-checked recalculation outputs with zero discrepancy.
2. **Participant Flow Integrity**: Exact cohort accounting ($N = 105$, 4 true exclusions: S044, S069, S086, S091) is maintained consistently across the Abstract, Introduction, Methods, Results, Discussion, and Figures. The draft line 95 error is explicitly refuted.
3. **Methods-to-Code Congruence**: Every stated algorithmic parameter (8–30 Hz bandpass, OAS covariance regularization, 6 CSP components, shrinkage LDA, LORO $D_3$, size-matched $D_{1s}$) perfectly reflects the executable Python code in `src/emi/`.
4. **Complete Bibliography Resolution**: Every in-text citation resolves to a verified entry in `manuscript/references.bib`.
5. **Absolute Scope Isolation**: All V2/OpenBMI results, multi-dataset claims, prompt-injection artifacts, and bracketed notes have been completely purged.

---

## 2. Comprehensive Consistency Verification Ledger

The ledger below details the 34 automated cross-checks performed across the manuscript:

| # | Checked Parameter | Expected Value / Benchmark Truth | Observed Value in Manuscript | Cross-Check Source | Verdict |
|---|---|---|---|---|---|
| **01** | Total Analyzed Cohort ($N$) | Exactly 105 participants | Exactly 105 participants | `inflation_by_subject.csv` | **PASS** |
| **02** | Initial Requested Cohort | 109 participants (S001–S109) | 109 participants (S001–S109) | `V1_1_PARTICIPANT_FLOW_AUDIT.md` | **PASS** |
| **03** | Stage 1 Automated Exclusions | 3 participants (S044, S069, S091) | 3 participants (S044, S069, S091) | `excluded_or_failed_subjects.csv` | **PASS** |
| **04** | Stage 2 Eligibility Exclusion | 1 participant (S086, 24 clean trials) | 1 participant (S086, 24 clean trials) | `excluded_or_failed_subjects.csv` | **PASS** |
| **05** | Refutation of Draft Line 95 Error | S088, S092, S100, S104 100% present | S088, S092, S100, S104 100% present | `inflation_by_subject.csv` | **PASS** |
| **06** | Hardware Sampling Rates | 102 @ 160 Hz, 3 @ 128 Hz (S088, S092, S100) | 102 @ 160 Hz, 3 @ 128 Hz (S088, S092, S100) | `V1_1_RAW_DATA_RECONSTRUCTION.md`| **PASS** |
| **07** | $P_1$ vs. $D_3$ Mean Difference | $+24.8153$ pp | $+24.82$ pp (rounded) | `inflation_table.csv`, row 4 | **PASS** |
| **08** | $P_1$ vs. $D_3$ Hodges-Lehmann ($\Delta_{\text{HL}}$) | $+24.5029$ pp | $+24.50$ pp | `V1_1_STATISTICAL_VALIDATION.md` | **PASS** |
| **09** | $P_1$ vs. $D_3$ 95% BCa Bootstrap CI | $[+21.75, +27.78]$ pp | $[+21.75, +27.78]$ pp | `V1_1_STATISTICAL_VALIDATION.md` | **PASS** |
| **10** | $P_1$ vs. $D_3$ Wilcoxon $W$ & $p$ | $W = 6.0, p_{\text{raw}} = 1.48 \times 10^{-18}$ | $W = 6.0, p_{\text{raw}} = 1.48 \times 10^{-18}$ | `inflation_table.csv` | **PASS** |
| **11** | $P_1$ vs. $D_3$ Pratt Wilcoxon $p$ | $W = 10.0, p_{\text{Pratt}} = 8.06 \times 10^{-19}$| $W = 10.0, p_{\text{Pratt}} = 8.06 \times 10^{-19}$| `recalculate_all_stats.py` | **PASS** |
| **12** | $P_1$ vs. $D_3$ Holm-Adjusted $p$ ($m = 3$) | $p_{\text{Holm}} = 4.43 \times 10^{-18}$ | $p_{\text{Holm}} = 4.43 \times 10^{-18}$ | `V1_1_STATISTICAL_VALIDATION.md` | **PASS** |
| **13** | $P_1$ vs. $D_3$ Cohen's $d_z$ | $+1.7708$ | $+1.771$ | `inflation_table.csv` | **PASS** |
| **14** | $D_{1s}$ vs. $D_3$ Mean Difference | $-2.7715$ pp | $-2.77$ pp | `inflation_table.csv`, row 3 | **PASS** |
| **15** | $D_{1s}$ vs. $D_3$ Hodges-Lehmann ($\Delta_{\text{HL}}$)| $-2.6768$ pp | $-2.68$ pp | `V1_1_STATISTICAL_VALIDATION.md` | **PASS** |
| **16** | $D_{1s}$ vs. $D_3$ 95% BCa Bootstrap CI | $[-3.94, -1.46]$ pp | $[-3.94, -1.46]$ pp | `V1_1_STATISTICAL_VALIDATION.md` | **PASS** |
| **17** | $D_{1s}$ vs. $D_3$ Wilcoxon $W$ & $p$ | $W = 1525.5, p = 5.86 \times 10^{-5}$ | $W = 1525.5, p = 5.86 \times 10^{-5}$ | `inflation_table.csv` | **PASS** |
| **18** | $D_{1s}$ vs. $D_3$ Holm-Adjusted $p$ ($m = 3$) | $p_{\text{Holm}} = 5.86 \times 10^{-5}$ | $p_{\text{Holm}} = 5.86 \times 10^{-5}$ | `inflation_table.csv` | **PASS** |
| **19** | $D_{1s}$ vs. $D_3$ Cohen's $d_z$ | $-0.4491$ | $-0.449$ | `inflation_table.csv` | **PASS** |
| **20** | $D_{1s}$ vs. $D_3$ Subject Direction Counts | 66 lower, 39 higher, 0 tied | 66 lower, 39 higher, 0 tied | `inflation_by_subject.csv` | **PASS** |
| **21** | $D_{1m}$ vs. $D_3$ Hodges-Lehmann ($\Delta_{\text{HL}}$)| $-4.4697$ pp | $-4.47$ pp | `V1_1_STATISTICAL_VALIDATION.md` | **PASS** |
| **22** | $D_{1m}$ vs. $D_3$ 95% BCa Bootstrap CI | $[-5.80, -3.11]$ pp | $[-5.80, -3.11]$ pp | `V1_1_STATISTICAL_VALIDATION.md` | **PASS** |
| **23** | $D_{1m}$ vs. $D_3$ Holm-Adjusted $p$ ($m = 3$) | $p_{\text{Holm}} = 1.08 \times 10^{-8}$ | $p_{\text{Holm}} = 1.08 \times 10^{-8}$ | `inflation_table.csv` | **PASS** |
| **24** | $D_{1m}$ vs. $D_3$ Cohen's $d_z$ | $-0.6847$ | $-0.685$ | `inflation_table.csv` | **PASS** |
| **25** | $D_{1s}$ vs. $D_{1m}$ Hodges-Lehmann Shift | $+1.8561$ pp | $+1.86$ pp | `V1_1_STATISTICAL_VALIDATION.md` | **PASS** |
| **26** | TOST Equivalence Bounds & Outcome | $\pm 2.0$ pp, all $p_{\text{TOST}} > 0.05$ (Non-Eq) | $\pm 2.0$ pp, all $p_{\text{TOST}} > 0.05$ (Non-Eq) | `recalculate_all_stats.py` | **PASS** |
| **27** | Null Control Execution Status | $n_{\text{null}} = 0$ (Disclosed limitation) | Explicitly disclosed as unperformed | `benchmark_results/physionet_v1_1/settings.json`| **PASS** |
| **28** | Figure Asset Parity | 5 figures in PDF, SVG, PNG, TIFF | All 5 figures embedded with captions | `scripts/generate_figures.py` | **PASS** |
| **29** | In-Text Citation Resolution | 100% of citation keys in `references.bib` | 100% resolve without error | `manuscript/references.bib` | **PASS** |
| **30** | Integrity & Prompt Injection Purge | Zero meta-prompts, Endor, or V2 artifacts | Zero meta-prompts, Endor, or V2 artifacts | Text search audit | **PASS** |
| **31** | $D_3$ Cohort Mean Accuracy & Quantiles | Mean $= 60.15 \pm 13.29\%$, Median $= 57.78\%$, IQR $[51.11\%, 68.89\%]$ | Mean $= 60.15 \pm 13.29\%$, Median $= 57.78\%$, IQR $[51.11\%, 68.89\%]$ | `inflation_by_subject.csv` | **PASS** |
| **32** | 160 Hz Sub-Cohort Invariance | $n = 102$, Mean $D_3 = 60.21\%$, Mean $D_{1s} = 57.33\%$, Mean shift $-2.88$ pp | $n = 102$, Mean $D_3 = 60.21\%$, Mean $D_{1s} = 57.33\%$, Mean shift $-2.88$ pp | `inflation_by_subject.csv` | **PASS** |
| **33** | 128 Hz Sub-Cohort Statistics | $n = 3$, Mean $D_3 = 58.10\%$, Mean $D_{1s} = 59.08\%$, Mean shift $+0.98$ pp, Median shift $+3.33$ pp | $n = 3$, Mean $D_3 = 58.10\%$, Mean $D_{1s} = 59.08\%$, Mean shift $+0.98$ pp, Median shift $+3.33$ pp | `inflation_by_subject.csv` | **PASS** |
| **34** | Repetition Counts & Seed Parameters | $D_{1s} = 20, D_{1m} = 5, \text{seed} = 0$ matching `settings.json` | $D_{1s} = 20, D_{1m} = 5, \text{seed} = 0$ | `settings.json`, `splitters.py` | **PASS** |

---

## 3. Discrepancy Resolution and Quality Audit

Every historical discrepancy previously identified across the codebase has been documented and resolved:
1. **$P_1$ vs. $D_3$ P-Value Precision**:
   - `inflation_table.csv` calculates $p_{\text{raw}} = 1.48 \times 10^{-18}, p_{\text{Holm}} = 4.43 \times 10^{-18}$ via standard Wilcoxon signed-rank test ($N_{\text{eff}} = 103$).
   - Manuscript explicitly reports both the standard Wilcoxon and the Pratt Wilcoxon test ($W = 10.0, p_{\text{Pratt}} = 8.06 \times 10^{-19}, p_{\text{Holm}} = 2.42 \times 10^{-18}$), explaining that Pratt retains the two zero-difference participants (S029, S054) in the initial ranking. Both methods confirm absolute significance ($p < 10^{-17}$).
2. **Bootstrap Sampling Bounds**:
   - The reported 95% BCa confidence intervals ($B = 10{,}000$, seed $= 0$) strictly match `docs/AUDIT/V1_1_STATISTICAL_VALIDATION.md`.
3. **Refutation of Line 95 Error**:
   - Section 4.3 and Figure 2 prominently refute the earlier draft error, noting that S088, S092, S100, and S104 are fully included and evaluated at their native hardware sampling rates.
4. **Purge of LLM Meta-Instructions**:
   - The trailing Endor Agent Kit prompt injection present in historical draft text has been purged. The manuscript concludes with `\bibliography{references}`.

---

## 4. Final Consistency Verdict

**Overall Audit Verdict**: **100% CONSISTENCY PASS (34/34 Checks Verified)**  
The revised manuscript (`manuscript/V1_PhysioNet/manuscript.md`) is certified to be mathematically, computationally, and methodologically congruent with all validated outputs of the LeakCheck V1.1 study.
