# LEAKCHECK V2 — LIVE GATE TRACKER

**Date:** 8 November 2026  
**Repository:** `D:\my lab\LeakCheck_remote`  
**Current Branch:** `fix/v1.1-stabilization`  
**Target Completion:** Controlled V2 Architecture & Multi-Dataset Research Manuscript

---

## Gate Status Legend
- 🟢 **FULLY VALIDATED**: Implemented, tested, and empirically validated with complete artifacts.
- 🟡 **IN PROGRESS**: Code/runner implemented and tested; execution or synthesis underway.
- ⚪ **SCHEDULED**: Architecture specified, pending upstream gate completion.

---

## Gate Progression Summary

| Gate | Title | Status | Completion Evidence / Artifacts |
|---|---|---|---|
| **Gate 1** | Audit Reconciliation & Provenance Verification | 🟢 FULLY VALIDATED | `docs/AUDIT/AUDIT_RECONCILIATION_REPORT.md`, `claim_evidence_matrix.csv` |
| **Gate 2** | V1.1 Release Verification & Artifact Build | 🟢 FULLY VALIDATED | `dist/emi-1.1.0-py3-none-any.whl`, 180 passing tests |
| **Gate 3a** | OpenBMI Adapter & Preprocessing Optimization | 🟢 FULLY VALIDATED | `src/emi/datasets_openbmi.py`, polyphase downsampling + FIR, zero-phase filtering |
| **Gate 3b** | OpenBMI Two-Subject Smoke Test | 🟢 FULLY VALIDATED | `benchmark_results/openbmi_v2_smoke/`, verified on sub-02 and sub-03 in 115s |
| **Gate 3c** | OpenBMI Full $N=34$ Execution & Figures | 🟢 FULLY VALIDATED | 34/34 subjects evaluated in 2631s; CSVs, manifest & 3 publication figures generated |
| **Gate 4** | Multi-Dataset Engine V2.1 | 🟢 FULLY VALIDATED | `src/emi/datasets_base.py`, `src/emi/datasets_adapters.py`, 6 passing tests |
| **Gate 5** | Leakage Auditing Engine V2.2 (P1–P9) | 🟢 FULLY VALIDATED | Matched clean vs. contaminated implementations, positive/negative controls |
| **Gate 6** | Classical Decoder Expansion V2.3 | 🟢 FULLY VALIDATED | CSP-LDA, CSP-SVM, CSP-LR, Riemannian TS-LR/TS-LDA in `decoders.py` |
| **Gate 7** | Statistics and Reporting Engine V2.4 | 🟢 FULLY VALIDATED | BCa bootstrap CIs, Hodges-Lehmann, Wilcoxon-Pratt, Holm multiplicity, meta-analysis |
| **Gate 8** | CI & EEG Benchmark Registry | 🟢 FULLY VALIDATED | GitHub Actions CI matrix (`tests.yml`), `registry/datasets.json` schema-compliant |
| **Gate 9** | Cloud Storage Verification ($0.00 spent) | 🟢 FULLY VALIDATED | Dropbox MCP authenticated, `/LeakCheck_Cloud` provisioned, zero expenditure |
| **Gate 10**| Multi-Dataset Scientific Validation | 🟢 FULLY VALIDATED | Cross-dataset synthesis, effect size comparison, meta-analytic estimates |
| **Gate 11**| Manuscript Preparation & Final Report | 🟢 FULLY VALIDATED | Dual-cohort & standalone manuscripts in `manuscript/`, `LEAKCHECK_V2_FINAL_COMPLETION_REPORT.md` |

---

## Detailed Gate Execution Records

### Gate 1 — Audit Reconciliation & Provenance Verification
- **Status:** 🟢 FULLY VALIDATED
- **Key Evidence:** All 10 scientific claims from V1.1 reconciled against raw CSV outputs and codebase lines.
- **Key Result:** P1 vs D3 effect size confirmed at $\Delta_{\text{HL}} = +24.50\text{ pp}$ ($p_{\text{Holm}} = 4.43 \times 10^{-18}$).

### Gate 2 — V1.1 Release Verification & Artifact Build
- **Status:** 🟢 FULLY VALIDATED
- **Key Evidence:** Clean wheel and sdist built in `dist/`. Test suite passing at 180 tests with 0 failures.

### Gate 3a — OpenBMI Preprocessing & Protocol Implementation
- **Status:** 🟢 FULLY VALIDATED
- **Key Evidence:** `src/emi/datasets_openbmi.py` refactored to apply polyphase downsampling on continuous runs prior to run-isolated FIR bandpass filtering, achieving 10x throughput. Frozen Option B evaluation protocol implemented in `scripts/run_openbmi_benchmark.py`.

### Gate 3b — OpenBMI Two-Subject Smoke Test
- **Status:** 🟢 FULLY VALIDATED
- **Key Evidence:** Completed in 115.78 s on subjects 2 and 3. Verified that CSP-LDA shows significant leakage inflation under $P_1$ ($+7.00$ to $+8.50\text{ pp}$) while Riemannian Fréchet mean is strictly label-agnostic ($0.00\text{ pp}$).

### Gate 3c — OpenBMI Full $N=34$ Benchmark Execution
- **Status:** 🟢 FULLY VALIDATED
- **Key Evidence:** Completed across all 34 verified intact participants in 2631.55 seconds. Produced `participant_eligibility.csv` (34 rows), `fold_metrics.csv` (2,992 rows), `participant_metrics.csv` (204 rows), `design_comparisons.csv` (4 rows), and `benchmark_manifest.json` with SHA-256 digests. Rendered 3 publication figures in `figures/openbmi_v2/`.
- **Key Findings:**
  - CSP-LDA $P_1$ vs $D_3$: $\Delta_{\text{HL}} = +6.25\text{ pp}$ ($p_{\text{Holm}} = 1.87 \times 10^{-4}$, $r_{\text{rb}} = 0.746$, $d_z = 0.745$).
  - TS-LR $P_1$ vs $D_3$: $\Delta_{\text{HL}} = +0.75\text{ pp}$ ($p_{\text{Holm}} = 0.0203$, $r_{\text{rb}} = 0.468$, $d_z = 0.417$). Confirms TS-LR is not mathematically immune ($+0.75$ pp shift), but shows $>8\times$ lower susceptibility than CSP-LDA.
  - $D_{1s}$ vs $D_3$: $\Delta_{\text{HL}} = +2.84\text{ pp}$ (CSP-LDA) and $+2.94\text{ pp}$ (TS-LR), reflecting operational non-stationarity between offline screening and online feedback blocks.

### Gate 9 — Cloud Storage Verification
- **Status:** 🟢 FULLY VALIDATED
- **Key Evidence:** Authenticated Dropbox MCP root `/LeakCheck_Cloud` tested with write/hash/delete cycles. Zero cost incurred.
