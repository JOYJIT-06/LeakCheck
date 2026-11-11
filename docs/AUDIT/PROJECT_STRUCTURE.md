# LeakCheck Project Structure & Directory Audit Report

**Date of Audit:** November 8, 2026  
**Auditor:** Google Antigravity Research Engineering & Scientific Software Audit  
**Status:** Complete & Verified on Disk  
**Repository Working Copy:** `D:\my lab\LeakCheck_remote` (Git clone of `https://github.com/JOYJIT-06/LeakCheck.git`)  
**Historical Working Copy:** `D:\my lab\LeakCheck` (Directory Junction to local checkout)

---

## 1. Executive Summary of Workspace Topography

The workspace on `D:\my lab` contains 10 distinct top-level directories and 2 root files, totaling 727 cataloged files:

| Directory / Entity | File Count | Size (MB) | Primary Content Classification | Preservation Priority | Role in V1.1 / V2 |
|---|---|---|---|---|---|
| `LeakCheck_remote` | 269 | 34.99 | Active Git repository (`fix/v1.1-stabilization`) | **CRITICAL** | Core V1.1 Release Target |
| `LeakCheck` | 173 | 21,040.90 | Directory Junction + Raw OpenBMI dataset (20.55 GB) | **CRITICAL** | Source of OpenBMI raw data |
| `LeakCheck_Cache` | 106 npz | 681.24 | Cleaned PhysioNet EEG epochs (legacy schema v1) | **CRITICAL** | Precomputed PhysioNet cache (106 subjects) |
| `LeakCheck_Cache_Test` | 1 npz | 6.53 | Single-subject test cache (`sub-001_epochs.npz`) | PRESERVE | Test fixture for cache validation |
| `LeakCheck_Data` | 3 edf | 7.43 | PhysioNet Raw EDFs (`S001R04`, `S001R08`, `S001R12`) | PRESERVE | Real data smoke tests |
| `LeakCheck_FullResults` | 224 | 56.70 | Per-subject CSV & JSON runs for `091e47dc` | **HISTORICAL EVIDENCE** | Complete benchmark evidence (105 subjects) |
| `LeakCheck_Pilot` | 23 | 0.36 | Pilot benchmark outputs for `80e72224` | **HISTORICAL EVIDENCE** | Pilot run records |
| `LeakCheck_Test` | 30 | 0.16 | Test runs `1590c90e` and `25afcada` | TEMPORARY / DIAGNOSTIC | Verification outputs |
| `LeakCheck_tmp` | 3 | 0.05 | Wheel builds, logs, and temp redirected MNE home | SCRATCH | Workspace runtime temporary directory |
| `.ipynb_checkpoints` | 1 | 0.00 | Historical notebook checkpoint | ARCHIVAL | Archived checkpoint |
| `LeakCheck.zip` | 1 | 0.10 | Source zip excluding large arrays and git | ARCHIVAL | Distribution backup |
| `make_zip.py` | 1 | 0.00 | Packaging script for generating `LeakCheck.zip` | TOOLING | Helper utility |

---

## 2. Comprehensive Directory Inspection

### 2.1 `.github/`
- **Location:** `LeakCheck_remote/.github/` and `LeakCheck/.github/`
- **Purpose:** Continuous Integration, automated pytest execution, code linting, and GitHub workflow configuration.
- **Files Contained:** `workflows/test.yml` (CI workflow testing Python matrix and pytest execution).
- **Application Dependencies:** Invoked by GitHub Actions on pull requests and pushes to `main` and `fix/*` branches.
- **Content Classification:** Configuration and automation code.
- **Status:** Current in `LeakCheck_remote`.
- **Preservation Requirement:** YES.
- **Release Target:** Part of V1.1 and V2 release packages.

### 2.2 `.ipynb_checkpoints/`
- **Location:** `D:\my lab\.ipynb_checkpoints/` and `LeakCheck/docs/real_eeg_checks/.ipynb_checkpoints/`
- **Purpose:** Jupyter notebook automated recovery checkpoints.
- **Files Contained:** `make_zip-checkpoint.py`, `README-checkpoint.md`, `code_review_leakcheck_v0_2-checkpoint.md`, `csp_implementation_loro_accuracy_real-checkpoint.csv`, `label_runs_test_real-checkpoint.csv`, `reviewer_fix_status-checkpoint.md`.
- **Application Dependencies:** None (historical checkpoint artifacts).
- **Content Classification:** Historical scratch and checkpoint files.
- **Status:** Historical.
- **Preservation Requirement:** YES (preserve in place; do not package into clean distributions).
- **Release Target:** Excluded from source distributions (`.gitignore`).

### 2.3 `.pytest_cache/`
- **Location:** `LeakCheck_remote/.pytest_cache/` and `LeakCheck/.pytest_cache/`
- **Purpose:** Pytest execution cache (`.cache/v/cache/stepwise`, `nodeids`).
- **Files Contained:** Ephemeral test metadata.
- **Application Dependencies:** Internal to `pytest`.
- **Content Classification:** Generated runtime cache.
- **Status:** Ephemeral.
- **Preservation Requirement:** NO (can be cleared and regenerated).
- **Release Target:** Excluded from git repository and distributions.

### 2.4 `data/`
- **Location:** `LeakCheck/data/OpenBMI/`
- **Purpose:** Local raw and BIDS-structured dataset storage.
- **Files Contained:**
  - Metadata: `dataset_description.json`, `participants.json`, `participants.tsv`, `manifest.json`, `urls.txt`, `README.md`, `failed_downloads.txt`.
  - Raw session data: `sourcedata/session1/` containing 39 `.mat` files across 40 subject folders (`s1` through `s54`), totaling **20.55 GB (21,039.20 MB)**.
- **Application Dependencies:** Consumed by dataset loaders and cache creation scripts (`scripts/build_cache.py`, `src/emi/data.py`).
- **Content Classification:** Raw empirical research data.
- **Status:** Partially downloaded (39 of 54 session-1 subjects present; 5 failed downloads explicitly logged).
- **Preservation Requirement:** **CRITICAL — NEVER DELETE OR OVERWRITE**.
- **Release Target:** Kept in local research storage; excluded from Git and releases.

### 2.5 `docs/`
- **Location:** `LeakCheck_remote/docs/`
- **Purpose:** Scientific methodology documentation, preregistration template, review records, data dictionaries, and architectural specifications.
- **Files Contained:**
  - `CHECKLIST.md` (EEG decoding reporting checklist).
  - `DATA_DICTIONARY.md` (schema definition for `leakcheck_raw.csv` and summary files).
  - `LEAKCHECK.md` (definitions of validation designs D1–D6 and leakage mechanisms P1–P9).
  - `METHODS.md` (methods writeup of PhysioNet V1 benchmark).
  - `PREREGISTRATION.md` (preregistration template; contains unpopulated fields).
  - `PROVENANCE.md` (provenance records of datasets and subjects).
  - `REQUIREMENTS_STATUS.md` (matrix of V1 requirements).
  - `REVIEW_RESPONSE.md` (consolidated response to code review v0.2 items 1–37).
  - `real_eeg_checks/` (historical review documents and real EEG inspection scripts).
- **Application Dependencies:** Documentation for human researchers and benchmark consumers.
- **Content Classification:** Scientific documentation and research records.
- **Status:** Partially updated in `LeakCheck_remote`; requires audit synchronization.
- **Preservation Requirement:** YES.
- **Release Target:** Part of V1.1 and V2 releases.

### 2.6 `scripts/`
- **Location:** `LeakCheck_remote/scripts/` and `LeakCheck/scripts/`
- **Purpose:** Executable CLI workflows for cache generation, benchmark execution, and statistical analysis.
- **Files Contained:**
  - `run_leakcheck.py` (Main benchmark orchestrator CLI; 13,944 bytes).
  - `analyze_leakcheck.py` (Statistical aggregation and figure generation; 9,118 bytes).
  - `build_cache.py` (PhysioNet raw-to-cache epoch extractor; 2,103 bytes).
  - `build_cache_moabb.py` (MOABB dataset adapter runner; 1,406 bytes).
  - `make_synthetic_cache.py` (Synthetic dataset generator for testing; 2,877 bytes).
  - `run_group.py` (Batch execution across multiple subjects; 2,766 bytes).
  - `run_subject.py` (Single-subject execution; 1,811 bytes).
  - Historical backups in `LeakCheck/scripts/`: `run_leakcheck.py.bak`, `run_leakcheck.py.pre_csp_backup`.
- **Application Dependencies:** Driven by end users and benchmark runners; imports `src/emi`.
- **Content Classification:** Executable research software.
- **Status:** Current; 7 active scripts are bit-for-bit identical between repositories.
- **Preservation Requirement:** YES.
- **Release Target:** Packaged with V1.1 and V2.

### 2.7 `src/emi/`
- **Location:** `LeakCheck_remote/src/emi/` (and linked via `LeakCheck/src/emi/`)
- **Purpose:** The core scientific Python library.
- **Modules (20 modules):**
  - `__init__.py`: Package entrypoint, specifies package version (`1.0.0` in remote).
  - `cache.py`: Epoch caching engine, schema validation, software provenance tracking.
  - `config.py`: Central configuration dataclass (`Config`).
  - `data.py`: PhysioNet raw EEG data resolver and loader.
  - `datasets_moabb.py`: MOABB dataset adapter interface.
  - `decode.py`: Classical decoding pipeline (CSP + LDA), LORO evaluation.
  - `decoders.py`: Decoder specifications (`DecoderSpec`, `ChannelSelector`, `ChannelScaler`).
  - `diagnostics.py`: Statistical diagnostics for label autocorrelation and Wald-Wolfowitz runs test.
  - `leakcheck.py`: Validation design implementations (D1, D2, D1m, D1s, D3, D4, D4b, D5, D6) and leakage injection mechanisms (P1–P9).
  - `leakstats.py`: Participant-level non-parametric and robust statistics (Hodges-Lehmann, BCa bootstrap CI, Wilcoxon, TOST, Holm FDR).
  - `metrics.py`: Classification scoring and repetition aggregation.
  - `nulls.py`: Negative controls (within-run permutation and circular shift).
  - `pipeline.py`: Subject-level execution pipeline.
  - `plotting.py`: Scientific figure generation (inflation plots, null distributions, paired deltas).
  - `preprocess.py`: Filtering, epoch slicing, and label-blind artifact rejection.
  - `signal_utils.py`: Pure-NumPy signal processing helpers and mathematical validations.
  - `simple_csp.py`: Standalone NumPy/SciPy Common Spatial Pattern implementation.
  - `splitters.py`: Cross-validation splitters (`SizeMatchedRandomSplit`, `GappedChronologicalSplit`).
  - `summary.py`: Binomial thresholding and group-level performance summaries.
  - `tfr.py`: Time-frequency analysis and ERD/ERS power calculations.
- **Application Dependencies:** The foundation of all experiments, scripts, and tests.
- **Content Classification:** Core scientific source code.
- **Status:** 19 modules fully operational; 1 module (`preprocess.py`) contains a critical indentation syntax error in `LeakCheck_remote` on line 72.
- **Preservation Requirement:** YES.
- **Release Target:** Core of V1.1 and V2.

### 2.8 `tests/`
- **Location:** `LeakCheck_remote/tests/`
- **Purpose:** Automated test suite validating numerical algorithms, split integrity, cache compatibility, statistical estimators, and leakage detection.
- **Files Contained:** 13 files (10 test suites + 3 helpers):
  - `conftest.py`, `helpers.py`, `__init__.py`.
  - `test_cache.py` (31 tests).
  - `test_decode.py` (2 tests).
  - `test_decode_loro.py` (6 tests).
  - `test_diagnostics.py` (11 tests).
  - `test_leakcheck.py` (17 tests).
  - `test_leakstats.py` (21 tests).
  - `test_real_checks.py` (2 tests).
  - `test_signal_utils.py` (59 tests).
  - `test_splitters.py` (12 tests).
  - `test_summary.py` (4 tests).
- **Application Dependencies:** Executed by `pytest`.
- **Content Classification:** Automated software and scientific test code.
- **Status:** Current; 165 tests collected and 100% passing (34.12s execution time).
- **Preservation Requirement:** YES.
- **Release Target:** V1.1 and V2.

### 2.9 `benchmark_results/`
- **Location:** `LeakCheck_remote/benchmark_results/physionet_v1/`
- **Purpose:** Saved experimental outputs from the historical V1 benchmark (run `091e47dc`, 105 participants completed).
- **Files Contained:** 14 files:
  - `README.md`, `settings.json`, `leakcheck_summary.json` (metadata).
  - `leakcheck_raw.csv` (29.5 MB; trial/fold level raw results).
  - `inflation_table.csv`, `inflation_by_subject.csv`, `inflation_csp_lda.png`.
  - `null_table.csv`, `null_fpr_csp_lda_perm.png`, `null_fpr_csp_lda_shift.png`.
  - `paired_delta_vs_null.csv`, `subject_empirical_p.csv`, `subject_info.csv`, `excluded_or_failed_subjects.csv`.
- **Application Dependencies:** Source of truth for historical scientific claims.
- **Content Classification:** Primary empirical research evidence.
- **Status:** Historical (computed with `emi` v0.1.0, 81,280.6 seconds / 22.5 hours compute time).
- **Preservation Requirement:** **CRITICAL — NEVER OVERWRITE**.
- **Release Target:** Preserved as immutable historical record.

### 2.10 `build/`
- **Location:** `LeakCheck_remote/build/`
- **Purpose:** Python setuptools package build output (`build/lib/emi/*`).
- **Files Contained:** Stale build snapshot.
- **Content Classification:** Generated packaging artifact.
- **Status:** Out of date relative to live `src/emi/`.
- **Preservation Requirement:** NO (can be rebuilt via `python -m build`).
- **Release Target:** Excluded from git repository.

### 2.11 `.git/`
- **Location:** `LeakCheck_remote/.git/`
- **Purpose:** Git repository tracking commits, branches, and tags.
- **State:**
  - Branch: `fix/v1.1-stabilization`
  - Commits: `461574d` (Initial commit) -> `002dc4f` (Release LeakCheck v1.0.0, tag: `v1.0.0`)
  - Remote: `https://github.com/JOYJIT-06/LeakCheck.git`
- **Content Classification:** Version control source of truth.
- **Status:** Current.
- **Preservation Requirement:** **CRITICAL**.
- **Release Target:** Preserved and extended.

### 2.12 External Cache and Results Folders
- **`LeakCheck_Cache/`**: 106 `.npz` files (681.24 MB), containing cleaned PhysioNet epochs in legacy schema v1 format. Required for running audits without reprocessing raw EDFs.
- **`LeakCheck_Cache_Test/`**: 1 `.npz` file (6.53 MB), `sub-001_epochs.npz` used for fast local testing.
- **`LeakCheck_Data/`**: 3 PhysioNet EDF files (`S001R04.edf`, `S001R08.edf`, `S001R12.edf`) for S001.
- **`LeakCheck_FullResults/`**: 224 files (56.70 MB), containing per-subject CSVs and info JSONs for the full 105-subject run `091e47dc`.
- **`LeakCheck_Pilot/`**: 23 files (0.36 MB), per-subject results from pilot run `80e72224`.
- **`LeakCheck_Test/`**: 30 files (0.16 MB), results from test runs `1590c90e` and `25afcada`.
- **`LeakCheck_tmp/`**: 3 files, contains scratch logs and `wheelhouse/emi-1.0.0-py3-none-any.whl`.
