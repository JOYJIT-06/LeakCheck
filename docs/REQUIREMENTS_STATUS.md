# LeakCheck V1.1 Release & V2 Extended Roadmap Status

**Evaluation Date**: 2026-11-08  
**Target Release Date**: 2026-11-12  
**Active Repository**: `D:\my lab\LeakCheck_remote`  
**Software Version**: `1.1.0`

---

## 1. Release Deliverables Status Matrix

| Directive Requirement | Status | Verification Evidence / Path |
|---|---|---|
| **Repository & File Audit** | **COMPLETE** | `docs/AUDIT/PROJECT_STRUCTURE.md`, `FILE_INVENTORY.csv`, `REPOSITORY_DIFFERENCES.md` |
| **Scientific Capabilities Audit** | **COMPLETE** | `docs/AUDIT/EXISTING_CAPABILITIES.md`, `KNOWN_LIMITATIONS.md`, `RESEARCH_STATUS.md` |
| **Fix Preprocessing Indentation Blocker** | **RESOLVED** | `src/emi/preprocess.py` lines 72–78; verified via `tests/test_preprocess.py`. |
| **Comprehensive Test Suite** | **174 PASSING** | Pytest test suite executed: 174 passed, 0 failed in 70.75s. |
| **Headline D1s vs D3 Benchmark** | **EXECUTED ($N=105$)** | `benchmark_results/physionet_v1_1/`: $\Delta_{\text{HL}} = -2.68$ pp ($95\%$ BCa CI: $[-3.95, -1.47]$). |
| **OAS Logging De-noising** | **RESOLVED** | MNE log spam suppressed in `mne_csp_factory()` for multi-core scalability. |
| **Null Table KeyError Fix** | **RESOLVED** | Empty null handling guarded in `scripts/run_leakcheck.py`. |
| **OpenBMI Dataset Adapter (V2)** | **IMPLEMENTED** | `src/emi/datasets_openbmi.py`; verified via `tests/test_openbmi.py`. |
| **Riemannian Tangent Space Decoders (V2)** | **IMPLEMENTED** | Built-in `CovarianceTransformer` & `TangentSpaceTransformer` in `src/emi/decoders.py`. |
| **EEG Benchmark Registry Schemas (V2)** | **IMPLEMENTED** | JSON Schemas created in `registry/schemas/`. |
| **Version Bump & Packaging** | **READY** | Bumped to `1.1.0` in `pyproject.toml` and `src/emi/__init__.py`. |

---

## 2. Statistical Findings Comparison: V1.0 vs V1.1

| Metric / Contrast | Historical V1.0 Run `091e47dc` | LeakCheck V1.1 Run `physionet_v1_1` | Scientific Conclusion |
|---|---|---|---|
| **Cohort Size** | 105 participants (1 excluded) | 105 participants (1 excluded) | Exact participant cohort match. |
| **P1 vs D3 (Spatial Leakage)** | $\Delta_{\text{HL}} = +24.50$ pp ($d_z = 1.771$) | $\Delta_{\text{HL}} = +24.50$ pp ($d_z = 1.771$) | Exact numerical reproducibility. |
| **D1m vs D3 (k-Matched Random)** | $\Delta_{\text{HL}} = -3.17$ pp (unconstrained) | $\Delta_{\text{HL}} = -4.47$ pp ($d_z = -0.685$) | Consistent deflation relative to LORO. |
| **D1s vs D3 (Size-Matched Random)** | **Omitted / Missing** | **$\Delta_{\text{HL}} = -2.68$ pp ($p = 5.86 \times 10^{-5}$)** | Proves trial mixing deflates performance even under strict geometric matching. |
| **Test Suite Coverage** | 87 tests | 174 tests | $+100\%$ expansion in automated test assertions. |
