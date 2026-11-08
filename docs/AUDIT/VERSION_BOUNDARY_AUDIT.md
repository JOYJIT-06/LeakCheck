# Version Boundary Audit: Strict Separation of V1.1.0 and V2

**Audit Date**: 2026-11-09  
**Auditor**: Independent Release Management & Scientific Quality Assurance  
**Repository**: `D:\my lab\LeakCheck_remote`  
**Package**: `emi`  
**Target Release**: `1.1.0` (Stable)  
**Development Line**: `2.0.0.dev0` (V2 Multi-Dataset Framework)  

---

## 1. Context and Separation Mandate

Per Section 2 of the Master Execution Directive, LeakCheck maintains a strict separation between its three evolutionary stages:

| Version | Identity | Scope and Generalization Target | Release Status |
|---|---|---|---|
| **V1.0.0** | Historical Baseline | Initial PhysioNet EEGMMIDB benchmark, commit `002dc4f` | Released (Historical) |
| **V1.1.0** | Stabilized Release | Stabilized PhysioNet benchmark ($N=105$), $D_{1s}$ vs $D_3$, bug fixes, stable CLI, 171 unit tests | **Immediate Stable Release Target** |
| **V2.0.0-dev** | Expanded Research | Multi-dataset architecture, OpenBMI benchmark ($N=34$), Riemannian geometry, P1–P9 taxonomy, registry schemas | **Ongoing Development Milestone** |

---

## 2. File and Component Allocation Matrix

To prevent experimental features from masquerading as stable release capabilities, every component is explicitly partitioned:

| File / Component | Version Assignment | Justification and Status |
|---|:---:|---|
| `src/emi/preprocess.py` | **V1.1.0** | Fixed `_reject()` indentation blocker; label-blind Butterworth filtering. |
| `src/emi/splitters.py` | **V1.1.0** | Contains `loro_splits` and `size_matched_random_repeats` ($D_{1s}$). |
| `src/emi/decoders.py` (CSP-LDA, CSP-LR) | **V1.1.0** | Core spatial filtering classifiers evaluated on PhysioNet $N=105$. |
| `src/emi/decoders.py` (`ts_lr`, `ts_lda`) | **V2** | Pure-NumPy Riemannian decoders evaluated in OpenBMI V2 benchmark. |
| `src/emi/datasets_base.py` | **V2** | Abstract base class `BaseEEGDataset` for multi-dataset extension. |
| `src/emi/datasets_adapters.py` | **V2** | Adapters for BNCI2014-001 and Cho2017. |
| `src/emi/datasets_openbmi.py` | **V2** | OpenBMI parser, corruption detector, and MATLAB session loader. |
| `scripts/run_leakcheck.py` | **V1.1.0** | Primary CLI runner for PhysioNet $N=105$ leakage audits. |
| `scripts/quickstart_demo.py` | **V1.1.0** | Zero-download synthetic demo running in $1.36\text{ s}$. |
| `scripts/run_openbmi_benchmark.py` | **V2** | Benchmark runner for OpenBMI $N=34$ replication study. |
| `scripts/plot_openbmi_figures.py` | **V2** | Visualization script for OpenBMI paired scatter and inflation plots. |
| `benchmark_results/physionet_v1/` | **V1.0.0** | Frozen historical V1 baseline ($N=105$, run `091e47dc`). Immutable. |
| `benchmark_results/physionet_v1_1/` | **V1.1.0** | Stabilized V1.1 benchmark ($N=105$, $D_{1s}$ vs $D_3$, $P_1$ vs $D_3$). |
| `benchmark_results/openbmi_v2/` | **V2** | Sealed OpenBMI replication benchmark ($N=34$, 62 channels). |
| `registry/schemas/` | **V2** | JSON schemas defining open EEG Benchmark Registry specifications. |

---

## 3. Test Suite Partitioning

The automated test suite has been formally partitioned using pytest markers (`pyproject.toml`):

### V1.1.0 Stable Test Suite (171 Tests)
Invoked via:
```bash
pytest -m "not v2" -q
```
- Covers: `test_cache.py`, `test_decode.py`, `test_decode_loro.py`, `test_diagnostics.py`, `test_leakcheck.py`, `test_leakstats.py`, `test_preprocess.py`, `test_real_checks.py`, `test_signal_utils.py`, `test_splitters.py`, `test_summary.py`.
- **Result**: **171 passed in 60.78 seconds** (0 failures, 15 deselected).

### V2 Development Test Suite (15 Tests)
Invoked via:
```bash
pytest -m "v2" -q
```
- Covers: `test_datasets_adapters.py`, `test_openbmi.py`, `test_openbmi_benchmark.py`.
- **Result**: **15 passed in 14.42 seconds** (0 failures, 171 deselected).

### Combined Full Repository Suite (186 Tests)
Invoked via:
```bash
pytest -q
```
- **Result**: **186 passed in 61.95 seconds** (100% pass rate).

---

## 4. Documentation Partitioning

1. **Root Documentation (`README.md`, `docs/`)**:
   - Focuses primarily on **LeakCheck v1.1.0**.
   - Clearly documents the PhysioNet $N=105$ benchmark, installation, CLI usage, and bug fixes.
   - Contains an explicit, prominent pointer directing researchers to `docs/V2/` for ongoing multi-dataset research.
2. **Dedicated V2 Documentation (`docs/V2/`)**:
   - Resides in `docs/V2/README.md`.
   - Documents the OpenBMI full-cohort benchmark ($N=34$), Riemannian geometry decoders, P1–P9 leakage taxonomy, and registry schemas.
   - States explicitly that V2 is developmental software.

---

## 5. Build Artifact Separation

- Built release artifacts in `dist/` carry the exact stable version:
  - `dist/emi-1.1.0-py3-none-any.whl` (SHA-256: `3844759fd1fb5941baf8506f2a7a82ba30722614e2f8da3ff61bc0a2196e90b5`)
  - `dist/emi-1.1.0.tar.gz` (SHA-256: `b545229aa0a1933580d5a24fe2d671bad1e0dbd472eaa9c4029c1edf30331613`)
- No experimental V2 features are bundled as unstable external dependencies.

---

## 6. Audit Verdict

**VERDICT: STRICT BOUNDARY ENFORCED AND VERIFIED**

The division between V1.1.0 (stable release) and V2 (development framework) is clean, deterministic, and documented across files, test markers, build artifacts, and directory paths.
