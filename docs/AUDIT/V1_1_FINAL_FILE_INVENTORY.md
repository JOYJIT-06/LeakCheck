# LeakCheck V1.1 Final Repository File Inventory

**Document ID**: `docs/AUDIT/V1_1_FINAL_FILE_INVENTORY.md`  
**Date**: 2026-11-14 / 2026-11-15  
**Author**: Worker M1 (Code Recovery and Git Engineer)  
**Parent Agent**: `270738c3-c2bc-480f-8413-a8c0ff4eadac`  
**Working Branch**: `research/v1.1-final-audit`  
**Base Commit**: `d35afa6fe8e86dfdf532ee4f26e4abc1482c3155` (Tag `v1.1.0`)  
**Status**: VERIFIED REPOSITORY INVENTORY  

---

## Executive Summary

In accordance with Phase 3 of the Master Execution Prompt and Requirements R1, R2, and R5:
This inventory classifies all files within the LeakCheck research project into four discrete architectural tiers:
1. **Historical V1 Baseline** (v0.1–v1.0.0 initial exploratory release)
2. **V1.1 PhysioNet Study** (authoritative core codebase, benchmark runner, 171 tests, results, and manuscript)
3. **V2 Development Archive** (preserved on branch `v2-dev`; multi-dataset adapters, unified runner, Multi-Datasetpipeline)
4. **General Documentation and Project Governance**

On working branch `research/v1.1-final-audit`, exactly 145 files are tracked by Git. All V2 development modules, scripts, and test suites reside exclusively on branch `v2-dev`, ensuring 100% clean isolation of the V1.1 PhysioNet release.

---

## 1. Tier Breakdown and Category Summary

| Tier | Category / Path | File Count | Primary Function |
|---|---|---|---|
| **Tier 1: Historical V1** | `benchmark_results/physionet_v1/` | 14 files | Initial exploratory benchmark results ($N=105$) |
| **Tier 2: V1.1 PhysioNet Core** | `src/emi/` | 20 modules | Core signal processing, caching, cross-validation, decoders, and stats |
| **Tier 2: V1.1 PhysioNet Scripts**| `scripts/` | 8 scripts | PhysioNet benchmark runners, cache builders, and CLI tools |
| **Tier 2: V1.1 PhysioNet Tests**  | `tests/` | 14 modules | 171 unit and integration tests (100% passing) |
| **Tier 2: V1.1 PhysioNet Results**| `benchmark_results/physionet_v1_1/` | 13 files | Verified empirical benchmark outputs and summary tables |
| **Tier 2: V1.1 PhysioNet Paper**  | `manuscript/V1_PhysioNet/` | 2 files | Standalone manuscript (`manuscript.md`) and BibTeX references |
| **Tier 3: Preserved V2 Archive**  | On `v2-dev` branch | ~300 files | 11 dataset adapters, unified runner, challenger probe test suites |
| **Tier 4: Governance & Docs**      | `docs/`, `pyproject.toml`, etc. | 74 files | Architectural specs, audit reports, configuration, CI workflows |

---

## 2. Detailed File Enumeration on `research/v1.1-final-audit`

### A. Core Python Modules (`src/emi/` — 20 Files)

| File | Size (Bytes) | Role / Architectural Scope |
|---|---|---|
| `src/emi/__init__.py` | 232 | Package exports and version string (`1.1.0`) |
| `src/emi/cache.py` | 15,612 | Epoch caching, Schema Version 2, tensor shape validation, SHA256 checksums |
| `src/emi/config.py` | 3,061 | Preprocessing dataclass, event codes, frequency passbands, window parameters |
| `src/emi/data.py` | 2,286 | PhysioNet raw EDF reader, channel normalization, run concatenation |
| `src/emi/datasets_moabb.py` | 2,665 | Optional MOABB data bridge for PhysioNet comparison |
| `src/emi/decode.py` | 5,014 | Cross-validation decoding wrapper, accuracy, AUROC, score aggregation |
| `src/emi/decoders.py` | 16,770 | CSP-LDA, CSP-LR, and Riemannian TS-LR decoders; OAS covariance regularization |
| `src/emi/diagnostics.py` | 6,190 | Wald-Wolfowitz runs test PMF, label autocorrelation, trial dependence |
| `src/emi/leakcheck.py` | 32,211 | Master benchmark harness (D3 LORO, D1m matched-k, D1s size-matched, P1 global CSP) |
| `src/emi/leakstats.py` | 9,415 | Hodges-Lehmann pseudomedian, BCa bootstrap CIs, Wilcoxon signed-rank, Holm, TOST |
| `src/emi/metrics.py` | 3,230 | Balanced accuracy, Cohen's kappa, AUROC scoring functions |
| `src/emi/nulls.py` | 1,967 | Within-run label permutation and circular-shift null distribution generators |
| `src/emi/pipeline.py` | 2,805 | Pipeline verification assertions (fold isolation, absence of label leakage) |
| `src/emi/plotting.py` | 4,734 | Inflation distribution and null model visualization renderers |
| `src/emi/preprocess.py` | 7,337 | MNE FIR bandpass (1–45 Hz), bad channel interpolation, CAR, ICA ocular artifact removal |
| `src/emi/signal_utils.py` | 14,279 | PTP rejection, variance/correlation bad channel detection, run length parsing |
| `src/emi/simple_csp.py` | 1,903 | Pure NumPy generalized eigenvalue CSP implementation |
| `src/emi/splitters.py` | 6,963 | LORO, stratified k-fold, size-matched random partition generators; disjointness validation |
| `src/emi/summary.py` | 1,984 | Exact Clopper-Pearson binomial confidence intervals and threshold calculations |
| `src/emi/tfr.py` | 1,250 | Morlet wavelet time-frequency calculations for ERD/ERS validation |

### B. Execution Scripts (`scripts/` — 8 Files)

| File | Size (Bytes) | Category | Description |
|---|---|---|---|
| `scripts/analyze_leakcheck.py` | 9,118 | Analysis | Computes paired contrast statistics and exports LaTeX summary tables |
| `scripts/build_cache.py` | 2,103 | Preprocessing | Batch reads raw PhysioNet EDFs, applies preprocessing, writes `.npz` caches |
| `scripts/build_cache_moabb.py` | 1,406 | Utility | Alternative cache builder using MOABB wrapper |
| `scripts/make_synthetic_cache.py` | 2,877 | Testing | Generates synthetic `.npz` cache fixtures for testing and CI pipelines |
| `scripts/quickstart_demo.py` | 5,600 | Tutorial | Demonstrates basic pipeline execution on synthetic or cached data |
| `scripts/run_group.py` | 2,766 | Coordinator | Executes multi-subject batch benchmarks across participant cohorts |
| `scripts/run_leakcheck.py` | 14,700 | Master CLI | Master CLI runner for PhysioNet V1.1 study (D1–D6, P1–P7, settings hashing) |
| `scripts/run_subject.py` | 1,811 | Single Runner | Single-subject runner wrapper for HPC cluster array jobs |

### C. Test Suite Modules (`tests/` — 14 Files, 171 Tests)

| File | Test Count | Domain / Target Functionality |
|---|---|---|
| `tests/__init__.py` | 0 | Package initializer |
| `tests/conftest.py` | 0 | Pytest configuration and shared fixtures |
| `tests/helpers.py` | 0 | Test data synthesis utilities |
| `tests/test_cache.py` | 31 | Cache Schema V2, tensor shape validation, array types, provenance round-trip |
| `tests/test_decode.py` | 3 | Decoding accuracy, noise floor, Riemannian TS-LR decoding |
| `tests/test_decode_loro.py` | 6 | LORO cross-validation, null distribution generation, degenerate shift detection |
| `tests/test_diagnostics.py` | 11 | Exact runs test PMF, label autocorrelation, SimpleCSP whitening |
| `tests/test_leakcheck.py` | 17 | Core benchmark harness, D1–D6 designs, P1 positive control, negative controls |
| `tests/test_leakstats.py` | 21 | Hodges-Lehmann delta, BCa bootstrap CIs, Holm correction, TOST equivalence |
| `tests/test_preprocess.py` | 11 | FIR filtering, spherical spline interpolation, FastICA, PTP rejection |
| `tests/test_real_checks.py` | 2 | Permutation null on real EEG structures, reviewer check replication |
| `tests/test_signal_utils.py` | 53 | Bad channel detection, adaptive rejection masks, run length parsing |
| `tests/test_splitters.py` | 12 | Disjoint partition assertions, size-matched partitioning, chronological splits |
| `tests/test_summary.py` | 4 | Clopper-Pearson binomial thresholds, chance level Wilcoxon verification |
| **Total** | **171** | **100% Pass Rate in 37.16s** |

### D. Benchmark Results (`benchmark_results/` — 27 Files)

#### 1. V1.1 Authoritative Results (`benchmark_results/physionet_v1_1/` — 13 Files)
- `inflation_table.csv`: Primary contrast results (D3, D1m, D1s, P1 across decoders).
- `inflation_by_subject.csv`: Full participant-by-design performance matrix ($N=105$).
- `leakcheck_summary.json`: Complete machine-readable summary metrics, effect sizes, and CIs.
- `leakcheck_raw.csv`: Raw fold-level and repeat-level decoding accuracies.
- `settings.json`: Cryptographic settings manifest (seeds, frequencies, window parameters).
- `excluded_or_failed_subjects.csv`: Complete participant inclusion/exclusion ledger.
- `null_table.csv`: Empirical null model distribution summaries.
- `paired_delta_vs_null.csv`: Contrast differences compared against permutation nulls.
- `subject_empirical_p.csv`: Participant-level empirical $p$-values.
- `subject_info.csv`: Participant metadata (trial counts, run lengths, channel count).
- `inflation_csp_lda.png`: Distribution visualization for CSP-LDA inflation.
- `paired_csp_lda_size_matched.png`: Paired participant-level scatter contrast.
- `README.md`: Provenance notes for V1.1 results.

#### 2. Historical V1 Results (`benchmark_results/physionet_v1/` — 14 Files)
- Pre-stabilization benchmark results from early development (retained for historical traceability).

### E. Manuscript & Bibliography (`manuscript/` — 2 Files)
- `manuscript/V1_PhysioNet/manuscript.md`: Standalone IEEE TNSRE-style manuscript reporting the PhysioNet V1.1 study.
- `manuscript/references.bib`: Verified BibTeX citation database.

### F. Root Configuration and Project Governance (11 Files)
- `.github/workflows/tests.yml`: Automated CI workflow executing `pytest`.
- `.gitignore`: Repository hygiene rules (protecting raw data, caches, credentials).
- `pyproject.toml`: Project build configuration, dependency declarations, pytest settings.
- `requirements.txt`: Pinned runtime package dependencies.
- `README.md`: Master repository README.
- `CHANGELOG.md`: Chronological version change log.
- `CITATION.cff`: Academic citation file for the LeakCheck benchmark.
- `CONTRIBUTING.md`: Contributor guidelines and code style rules.
- `LICENSE`: Apache 2.0 open-source license.
- `inspect_cache.py`: CLI tool for inspecting Schema V2 cache files.
- `inspect_eeg.py`: CLI tool for inspecting raw PhysioNet EDF files.

---

## 3. Preserved V2 Archive (Branch `v2-dev`)

All multi-dataset and V2 expansion modules remain fully preserved on branch `v2-dev`:
- `scripts/run_unified_benchmark.py`, `run_Multi-Dataset_benchmark.py`, `generate_Multi-Dataset_manifests.py`, `plot_Multi-Dataset_figures.py`
- `tests/test_datasets_adapters.py`, `test_Multi-Dataset.py`, `test_Multi-Dataset_benchmark.py`, `test_bnci_stress.py`, `test_cho_highgamma_*.py`, `test_challenger_*.py`
- `registry/` dataset schemas and reproducibility records

Zero V2 files contaminate `research/v1.1-final-audit`.
