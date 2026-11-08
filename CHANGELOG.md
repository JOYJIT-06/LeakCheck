# Changelog

All notable changes to the LeakCheck package (`emi`) are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0-dev] — 2026-11-09 (V2 Development Milestone)

### Added
- **Full OpenBMI Multi-Dataset Empirical Benchmark ($N = 34$)**:
  - Evaluated 34 intact participants across 62 channels comparing Shrinkage CSP-LDA and Riemannian Tangent Space Logistic Regression (`ts_lr`).
  - Cryptographically sealed results in `benchmark_results/openbmi_v2/` (`participant_eligibility.csv`, `fold_metrics.csv`, `participant_metrics.csv`, `design_comparisons.csv`, `benchmark_manifest.json`).
  - Generated publication figures in `figures/openbmi_v2/` (`paired_accuracy_openbmi_csp_lda.png`, `paired_accuracy_openbmi_ts_lr.png`, `inflation_openbmi.png`).
- **Comprehensive Documentation Suite**:
  - Overhauled main `README.md` across 27 structured sections for public GitHub release.
  - Added 10 modular user guides under `docs/` (`installation.md`, `quickstart.md`, `user_guide.md`, `datasets.md`, `benchmark_protocols.md`, `leakage_mechanisms.md`, `statistical_methods.md`, `reproducibility.md`, `troubleshooting.md`, `architecture.md`).
- **Quick-Start Self-Contained Demo**:
  - `scripts/quickstart_demo.py` provides an instant ($<2\text{ s}$), zero-download audit on synthetic 3-run motor imagery data.
- **Dataset Adapters**:
  - Added `BNCI2014001DatasetAdapter` (BCI IV-2a) and `Cho2017DatasetAdapter` in `src/emi/datasets_adapters.py`.

---

## [1.1.0] — 2026-11-08 (Target Release: 2026-11-12)

### Added
- **Size-Matched Random Split Benchmark (`D1s_size_matched`)**:
  - Full evaluation across $N=105$ participants of the PhysioNet EEG Motor Movement/Imagery dataset.
  - Paired comparison against clean leave-one-run-out (`D3_loro`), establishing that trial shuffling deflates performance by $-2.68$ pp (Hodges-Lehmann median diff, $95\%$ BCa CI: $[-3.94, -1.46]$ pp, $p = 5.86 \times 10^{-5}$) rather than inflating it, resolving the key open question from V1.0.
  - Dedicated artifact generation: `paired_csp_lda_size_matched.png`, `inflation_table.csv`, and `inflation_by_subject.csv` in `benchmark_results/physionet_v1_1/`.
- **OpenBMI Dataset Adapter (`src/emi/datasets_openbmi.py`)**:
  - Multi-dataset ingestion supporting Lee et al. 2019 (GigaScience) 62-channel motor imagery recordings.
  - Automated detection of corrupted downloads and extraction of intact session-1 data.
  - Downsampling from 1000 Hz to arbitrary target frequencies (e.g. 160 Hz) and epoch slicing.
- **Standalone Riemannian Tangent Space Decoders (`src/emi/decoders.py`)**:
  - Pure NumPy/SciPy implementations of `CovarianceTransformer` and `TangentSpaceTransformer`.
  - Enables `ts_lr` (Riemannian tangent space logistic regression) without requiring external C-extensions, with automatic fallback if `pyriemann` is absent.
- **Dedicated Preprocessing Test Suite (`tests/test_preprocess.py`)**:
  - Direct unit tests for `clean_raw`, `_reject`, `build_epochs_full`, bad-channel detection, and label-blind artifact rejection.
- **OpenBMI Test Suite (`tests/test_openbmi.py`)**:
  - Verified loading of real session-1 participant recordings.
- **EEG Benchmark Registry JSON Schemas (`registry/schemas/`)**:
  - Formal schemas for datasets, preprocessing pipelines, decoding algorithms, leakage mechanisms, and reproducibility records.

### Fixed
- **Preprocessing Indentation Blocker (`src/emi/preprocess.py`)**:
  - Fixed syntax error in `_reject()` where unindented conditional statements caused `IndentationError` during raw epoching.
- **Console Log Spam in MNE CSP**:
  - Suppressed verbose OAS covariance estimation prints in `mne_csp_factory()` to prevent terminal I/O latency during multi-core execution.
- **Empty Null Table Handling**:
  - Fixed `KeyError: 'decoder'` in `scripts/run_leakcheck.py` when evaluating benchmarks without null permutations (`--n-null 0`).

### Changed
- Bumped package version to `1.1.0`.
- Expanded test suite from 87 to 186 passing tests.
