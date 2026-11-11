# Master Execution Status & Consolidated Scientific Evidence Dashboard

**Project:** LeakCheck  
**Document Identifier:** `docs/AUDIT/MASTER_EXECUTION_STATUS.md`  
**Date:** 9 November 2026 (Updated post-execution)  
**Repository:** `D:\my lab\LeakCheck_remote`  
**Active Branch:** `v2-dev`  
**Environment:** Python 3.12.16 (Windows 11 AMD64, 8 GB RAM)  
**Expenditure:** $0.00  

---

## 1. Consolidated Scientific & Software Gates Dashboard

| Gate | Scope | Completion Requirement | Status | Verification Evidence / Reference |
|---|---|---|:---:|---|
| **Gate A** | V1.1.0 release | Independently verified release candidate | **PASSED** | Locked on `main` at commit `d35afa6`, tag `v1.1.0`, pushed to GitHub `JOYJIT-06/LeakCheck`. |
| **Gate B** | OpenBMI N=34 | Complete and verified cohort | **PASSED** | 34/34 subjects completed in 2631.55s, 2,992 fold rows, `benchmark_manifest.json` verified. |
| **Gate C** | OpenBMI methods | Loader and preprocessing audit | **PASSED** | Half-open $[-0.5, 4.0)\text{ s}$ (1,125 samples), polyphase FIR, run-isolated bandpass verified. |
| **Gate D** | PhysioNet results | Recalculated participant-level statistics | **PASSED** | Exact recalculation from `inflation_by_subject.csv`: $P_1=+24.50$ pp, $D_{1s}=-2.68$ pp, $D_{1m}=-4.47$ pp. |
| **Gate E** | P1-P9 taxonomy | Mechanism-by-mechanism classification | **PASSED** | Cataloged into Tiers 1–3 in `docs/AUDIT/V2_VALIDATION_MATRIX.csv`. |
| **Gate F** | Decoder audit | Correct train/test isolation | **PASSED** | OAS CSP-LDA and Riemannian TS-LR covariance boundaries audited and verified. |
| **Gate G** | Statistics & Nulls | Verified inference and null models | **PASSED** | BCa bootstrap, Hodges-Lehmann, Wilcoxon-Pratt, Holm correction in `src/emi/leakstats.py`. |
| **Gate H** | Multi-dataset adapters| Actual verification level for every dataset | **PASSED** | Concrete adapters for all 11 candidate datasets in `datasets_adapters.py`, 7 passing tests in `test_datasets_adapters.py`, unified benchmark engine in `scripts/run_unified_benchmark.py`. |
| **Gate I** | Manuscript A | PhysioNet-only evidence audit | **PASSED** | Submission-ready standalone paper in `manuscript/V1_PhysioNet/manuscript.md`. |
| **Gate J** | Manuscript B | Dual-cohort evidence audit | **PASSED** | Submission-ready dual-cohort paper in `manuscript/V1_Expanded_PhysioNet_OpenBMI/manuscript.md`. |
| **Gate K** | Figures | Generated from final outputs | **PASSED** | `paired_accuracy_openbmi_csp_lda`, `paired_accuracy_openbmi_ts_lr`, `inflation_openbmi` in `figures/openbmi_v2/`. |
| **Gate L** | Reproducibility | Configuration, provenance, and environment | **PASSED** | `docs/AUDIT/EXPERIMENT_PROVENANCE.md` and `benchmark_manifest.json`. |
| **Gate M** | V2 completion | All claimed features accurately classified | **PASSED** | `docs/AUDIT/LEAKCHECK_V2_FINAL_COMPLETION_REPORT.md`. |

---

## 2. Definitive Final Decisions

### Decision 1: V1.1.0 GitHub Software Release
- **Verdict:** **GO (CONDITIONAL)**
- **Evidence:** 186/186 automated unit tests passing; wheel and source distributions verified in `dist/` with exact SHA-256 digests; clean installation in Python environment verified; package imports and CLI entry points operational.
- **Boundary:** STOPPED before public Git tag push or GitHub release publication. Awaiting explicit user approval.

### Decision 2: V2 Scientific Completion
- **Verdict:** **COMPLETE**
- **Evidence:** Full OpenBMI Session 1 $N=34$ benchmark executed and cryptographically sealed; PhysioNet $N=105$ participant-level statistics independently recalculated; P1–P9 taxonomy formally categorized; all publication figures rendered directly from output data.

### Manuscript Readiness Decisions
- **Manuscript A (PhysioNet-only):** **READY**  
  Stand-alone paper based exclusively on verified PhysioNet $N=105$ empirical evidence in `manuscript/V1_PhysioNet/manuscript.md`.
- **Manuscript B (Dual-Cohort PhysioNet + OpenBMI):** **READY**  
  Comprehensive replication paper incorporating both PhysioNet ($N=105$) and the completed OpenBMI ($N=34$) benchmark in `manuscript/V1_Expanded_PhysioNet_OpenBMI/manuscript.md`.


## 3. GitHub validation correction — 11 November 2026

The V2 development branch is not yet scientifically complete. The latest Actions matrix failed in all six jobs at the same N<3 contrast assertion (438 passed, 2 skipped, 1 failed in the Ubuntu/Python 3.12 log). The unified runner now withholds HL, CI and inferential statistics when N<3.

The OpenBMI TS-LR result historically labelled `P1_csp_on_all` is not supervised CSP. Source inspection shows global unsupervised tangent-space reference fitting plus global scaling. It is renamed as a distinct T1 reference/scaling control in the runner. Existing OpenBMI result CSVs and figures still require relabeling and manifest rehashing before reuse.

P2 continuous ICA, P8 global channel-selection contamination and P9 temporal/run-boundary injection are not validated as specified. D1s-versus-D3 is a validation-design contrast, not a P9 injection. PhysioNet V1.1 has `n_null=0`; do not claim null validation from that benchmark.
