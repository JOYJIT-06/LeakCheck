# LeakCheck V1.1 Scope Compliance and Single-Dataset Isolation Report

**Document ID**: `docs/AUDIT/V1_1_SCOPE_COMPLIANCE_REPORT.md`  
**Milestone**: M1/M5 Audit Reconciliation  
**Directive**: User Directive 2026-11-15 (Critical Scope Correction — Strictly PhysioNet EEGMMIDB Only)  
**Author**: Reviewer & Adversarial Critic M1-1  
**Repository**: `D:\my lab\LeakCheck_remote`  
**Active Working Branch**: `research/v1.1-final-audit`  
**Target Release**: LeakCheck V1.1 (`emi-1.1.0`)  
**Date**: November 15, 2026  
**Final Compliance Status**: **100% VERIFIED — STRICTLY PHYSIONET-ONLY**  

---

## 1. Executive Summary & Purpose

This audit report formalizes the execution of the **Critical Scope Correction Directive** issued by the Project Owner on November 15, 2026:
> *"I noticed that OpenBMI appears in the final V1.1 audit. This is incorrect if it is being treated as part of the V1.1 experimental study. Our final V1.1 scope is STRICTLY PHYSIONET EEGMMIDB ONLY. Please revise the complete V1.1 audit and all related documents accordingly... Verify that every V1.1 result comes exclusively from PhysioNet EEGMMIDB... Create a scope-compliance report listing every file checked and any OpenBMI references retained or removed... Do not delete historical OpenBMI work or modify V2 files. Do not modify or overwrite historical benchmark results."*

### Key Actions Executed:
1. **Complete V1.1 Audit Purge**:
   - `docs/AUDIT/FINAL_COMPLETION_REPORT.md`: Completely removed the OpenBMI replication benchmark subsection (Section 11.2) and all OpenBMI numerical results from the dataset, leakage, and decoder matrices.
   - `docs/AUDIT/claim_evidence_matrix.csv`: Purged all 6 OpenBMI claim rows, leaving strictly PhysioNet scientific claims.
   - `docs/AUDIT/V1_1_PROVENANCE_RECONCILIATION.md`: Corrected Section 4 to explicitly state that Paper 1 (V1.1) reports strictly and exclusively PhysioNet EEGMMIDB ($N=105$), with OpenBMI deferred to V2.
   - `docs/AUDIT/V1_1_RELEASE_READINESS_REPORT.md`: Updated release capability summaries to reflect pure PhysioNet single-dataset isolation.
2. **Strict Single-Dataset Provenance**:
   - Verified that 100% of V1.1 statistical findings ($\Delta_{\text{HL}} = +24.50\text{ pp}$ for $P_1$, $-2.68\text{ pp}$ for $D_{1s}$, $-4.47\text{ pp}$ for $D_{1m}$) originate strictly from the 105 PhysioNet participants in `benchmark_results/physionet_v1_1/inflation_by_subject.csv`.
   - Verified that zero OpenBMI data or participants are combined with PhysioNet.
3. **Quarantine of Historical V2 Assets**:
   - In accordance with the explicit constraint (*"Do not delete historical OpenBMI work or modify V2 files. Do not modify or overwrite historical benchmark results"*), historical OpenBMI artifacts (`benchmark_results/openbmi_v2/`, `docs/V2/*`, `src/emi/datasets_openbmi.py`, `tests/test_openbmi.py`) remain preserved in Git history as part of the quarantined V2 research track, but are 100% decoupled from V1.1.

---

## 2. Inviolable Single-Dataset Scope Invariant

| Attribute | LeakCheck V1.1 Benchmark Standard | LeakCheck V2 Development Track (Separate) |
|---|---|---|
| **Primary Dataset** | **PhysioNet EEGMMIDB only** | Multi-dataset (OpenBMI, BNCI, Cho, etc.) |
| **Cohort Size** | Exactly $N = 105$ eligible participants (from 109 requested) | Pilot $N = 34$ on OpenBMI Session 1 |
| **Excluded Subjects** | $4$ total: S044, S069, S091 (missing cache); S086 (24 trials) | $5$ truncated subjects ({1, 4, 11, 40, 45}) |
| **Experimental Task** | Two-class motor imagery: Left Fist vs Right Fist | Calibration (Run 0) vs Online Feedback (Run 1) |
| **EEG Recording** | 64 channels, 160 Hz, Runs 4, 8, 12 | 62 channels, 1000 Hz $\to$ 250/160 Hz |
| **Evaluated Decoders** | OAS-regularized CSP-LDA, CSP-LR | CSP-LDA, Riemannian TS-LR, TS-LDA |
| **Evaluated Protocols** | $D_3$ (LORO), $D_{1s}$ (size-matched), $D_{1m}$ ($k$-matched), $P_1$ (global CSP) | Arbitrary-$K$ LORO, cross-session transfer |
| **Publication Scope** | Standalone PhysioNet research paper (Figs. 1–5) | Dedicated multi-dataset replication paper |

---

## 3. Comprehensive File Audit and Remediation Ledger

Every file in the repository containing references to OpenBMI was audited and classified:

| File Path | Original Context | Action Taken | Current Scope Status |
|---|---|---|---|
| `docs/AUDIT/FINAL_COMPLETION_REPORT.md` | Reported OpenBMI benchmark results alongside PhysioNet (Sec 8, 9, 10, 11.2, 12) | **REVISED**: Removed Sec 11.2 entirely; removed OpenBMI effect sizes from matrices; declared V1.1 strictly PhysioNet-only | **100% PhysioNet Compliant** |
| `docs/AUDIT/claim_evidence_matrix.csv` | Contained 6 rows of OpenBMI empirical claims and benchmark metrics | **REVISED**: Purged all 6 OpenBMI rows; verified remaining 8 rows are 100% PhysioNet claims | **100% PhysioNet Compliant** |
| `docs/AUDIT/V1_1_PROVENANCE_RECONCILIATION.md` | Line 111 stated Paper 1 would report PhysioNet alongside OpenBMI replication | **REVISED**: Corrected to state Paper 1 is strictly PhysioNet $N=105$, with OpenBMI deferred to V2 | **100% PhysioNet Compliant** |
| `docs/AUDIT/V1_1_RELEASE_READINESS_REPORT.md` | Listed OpenBMI adapter in V1.1 verified release capabilities (Sec 1, 4) | **REVISED**: Clarified OpenBMI adapter is quarantined to V2 track; V1.1 is strictly single-dataset | **100% PhysioNet Compliant** |
| `docs/AUDIT/V1_1_REFERENCE_AUDIT.md` | Included Lee et al. (2019) citation | **AUDITED & RETAINED**: Formally annotated as historical literature context for future V2 validation only; no V1.1 results derive from it | **Compliant with Rule 5** |
| `docs/AUDIT/V1_1_STATISTICAL_VALIDATION.md` | Line 21: Declared strict single-dataset invariant | **AUDITED & CONFIRMED**: Already explicitly enforces single PhysioNet corpus ($N=105$) | **100% PhysioNet Compliant** |
| `docs/AUDIT/V1_1_FINAL_SCIENTIFIC_VALIDATION.md` | Line 23: Declared strict PhysioNet scope | **AUDITED & CONFIRMED**: Already explicitly excludes all V2/OpenBMI results | **100% PhysioNet Compliant** |
| `docs/AUDIT/V1_1_MANUSCRIPT_CONSISTENCY_REPORT.md`| Line 29: Scope isolation confirmation | **AUDITED & CONFIRMED**: Affirms complete purge of OpenBMI results from manuscript | **100% PhysioNet Compliant** |
| `docs/AUDIT/V1_1_FINAL_QUALITY_GATES.md` | Gate 17 and pre-backup descriptions | **AUDITED & CONFIRMED**: Confirms zero V2/OpenBMI contamination in release package | **100% PhysioNet Compliant** |
| `docs/AUDIT/V1_1_FINAL_REPORT.md` | Line 29, 56: Documented raw filesystem state (21.04 GB OpenBMI data on disk) | **AUDITED & CONFIRMED**: Historical record of disk footprint; confirms OpenBMI was excluded from code backups | **100% PhysioNet Compliant** |
| `docs/AUDIT/V1_1_FINAL_FILE_INVENTORY.md` | Line 19, 147: Categorized OpenBMI under Tier 3 (Preserved V2 Archive) | **AUDITED & CONFIRMED**: Correctly partitions OpenBMI as separate V2 archive | **100% PhysioNet Compliant** |
| `figures/physionet_v1_1/` (Figs. 1–5) | Vector/raster figures for V1.1 paper | **AUDITED & CONFIRMED**: 100% of figures (Figs. 1–5) represent exclusively PhysioNet $N=105$ | **100% PhysioNet Compliant** |
| `figures/openbmi_v2/` | OpenBMI pilot figures (`inflation_openbmi.pdf`, etc.) | **QUARANTINED**: Preserved strictly in V2 development archive; 0 references in V1.1 paper | **Quarantined to V2** |
| `benchmark_results/physionet_v1_1/` | Primary empirical benchmark tables and JSON outputs | **AUDITED & CONFIRMED**: Contains strictly PhysioNet $N=105$ empirical outputs | **100% PhysioNet Compliant** |
| `benchmark_results/physionet_v1_1_final/` | Reproducibility benchmark replication outputs | **AUDITED & CONFIRMED**: Contains strictly PhysioNet $N=105$ empirical outputs | **100% PhysioNet Compliant** |
| `benchmark_results/openbmi_v2/` | Historical V2 OpenBMI benchmark outputs ($N=34$) | **PRESERVED UNCHANGED**: In strict accordance with directive: "Do not delete historical OpenBMI work or modify V2 files" | **Quarantined to V2** |
| `docs/V2/*` (10 files) | Architectural specs and execution plans for V2 | **PRESERVED UNCHANGED**: In strict accordance with directive: "Do not modify V2 files" | **Quarantined to V2** |
| `src/emi/datasets_openbmi.py` | OpenBMI parser module | **PRESERVED ON V2 TRACK**: Excluded from V1.1 release package manifest | **Quarantined to V2** |
| `tests/test_openbmi*.py` | OpenBMI unit and benchmark tests | **PRESERVED ON V2 TRACK**: Marked with `@pytest.mark.v2`; excluded from stable V1.1 test suite | **Quarantined to V2** |
| `dist/emi-1.1.0-py3-none-any.whl` | Release distribution wheel | **AUDITED & CONFIRMED**: Contains only core `emi` package; 0 OpenBMI results or figures included | **100% PhysioNet Compliant** |

---

## 4. Empirical Result Ground Truth Verification

We verified that every empirical finding, figure, table, and claim for LeakCheck V1.1 originates strictly from PhysioNet EEGMMIDB ($N=105$):

### 4.1 Statistical Effects Ground Truth
- **Dataset**: PhysioNet EEGMMIDB (Runs 4, 8, 12, Left Fist vs. Right Fist).
- **Participants**: Exactly 105 analyzed participants (S001–S109, excluding S044, S069, S086, S091).
- **Hodges-Lehmann Estimator & BCa 95% CIs**:
  - $P_1$ vs $D_3$: $\Delta_{\text{HL}} = \mathbf{+24.50\text{ pp}}$ ($95\%\text{ BCa CI}: [+21.81, +27.78]\text{ pp}$, $p_{\text{Holm}} = 2.42 \times 10^{-18}$, $d_z = +1.771$).
  - $D_{1s}$ vs $D_3$: $\Delta_{\text{HL}} = \mathbf{-2.68\text{ pp}}$ ($95\%\text{ BCa CI}: [-3.89, -1.46]\text{ pp}$, $p_{\text{Holm}} = 5.86 \times 10^{-5}$, $d_z = -0.449$).
  - $D_{1m}$ vs $D_3$: $\Delta_{\text{HL}} = \mathbf{-4.47\text{ pp}}$ ($95\%\text{ BCa CI}: [-5.80, -3.11]\text{ pp}$, $p_{\text{Holm}} = 1.10 \times 10^{-8}$, $d_z = -0.685$).
- **Single-Dataset Integrity**: Zero pooling, zero cross-dataset averaging, zero OpenBMI data used in calculation.

### 4.2 Figure Verification
All 5 publication figures in `figures/physionet_v1_1/`:
- `fig1_workflow_schematic`: Illustrates PhysioNet 64-channel 160 Hz preprocessing and validation designs ($D_3, D_{1s}, D_{1m}, P_1$).
- `fig2_participant_flow`: Details PhysioNet cohort ($109 \to 105$) and exact exclusion rationale.
- `fig3_inflation_distributions`: Displays empirical distributions across 105 PhysioNet subjects.
- `fig4_paired_trajectories_waterfall`: Displays within-subject paired trajectories across 105 PhysioNet subjects.
- `fig5_statistical_effects_tost`: Displays Cohen's $d_z$ effect sizes and TOST equivalence for PhysioNet comparisons.

---

## 5. Formal Verdict

The LeakCheck V1.1 audit, evidence ledgers, claims matrices, and release artifacts are now **COMPLETELY PHYSIONET-ONLY**:
1. Zero OpenBMI results are used to support any V1.1 scientific claim.
2. Zero OpenBMI data are pooled or combined with PhysioNet results.
3. Zero OpenBMI entries exist in V1.1 reproducibility manifests or claim evidence matrices.
4. Historical OpenBMI benchmark results and V2 development files remain safely preserved in their designated V2 archive locations without modification.
5. LeakCheck V1.1 stands as a rigorous, defensible, and 100% standalone PhysioNet research benchmark.

**Final Certification**: **SCOPE COMPLIANCE VERIFIED — 100% PHYSIONET-ONLY**
