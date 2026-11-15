# OpenBMI (Lee et al. 2019) Dataset Download Audit & File Manifest Report

**Dataset Identifier**: NEMAR nm000338 / OpenBMI GigaScience 2019  
**Local Storage Path**: `D:\my lab\LeakCheck\data\OpenBMI`  
**Authoritative Manifest**: `D:\my lab\LeakCheck\data\OpenBMI\manifest.json` (1,955 items)  
**Audit Date**: 2026-11-08

---

## 1. Executive Summary & File Inventory

The local OpenBMI directory was exhaustively audited against the official NEMAR `manifest.json` (v1.0.5).

| Category | Expected in Manifest | Present Locally | Exact Size Match | Truncated / Incomplete | Missing | Local Coverage (%) |
|---|---:|---:|---:|---:|---:|---:|
| **Root Metadata** | 6 | 6 | 6 | 0 | 0 | 100.0% |
| **Toolbox & NEMAR Code** | 3 | 3 | 3 | 0 | 0 | 100.0% |
| **Sourcedata Session 1 (`.mat`)** | 54 | 39 | 34 | 5 | 15 | 63.0% (Intact) |
| **Sourcedata Session 2 (`.mat`)** | 54 | 0 | 0 | 0 | 54 | 0.0% |
| **BIDS Derivatives (`sub-1`..`54`)** | 1,836 | 0 | 0 | 0 | 1,836 | 0.0% |
| **Sourcedata Documentation** | 2 | 1 | 1 | 0 | 1 | 50.0% |
| **TOTAL** | **1,955** | **49** | **44** | **5** | **1,906** | **2.25%** |

---

## 2. Session-1 Detailed Status & Truncated Files

Local `sourcedata/session1/` contains subdirectories for subjects `s1` through `s45`:
- **34 Subjects Verified Intact**: Subjects 2, 3, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 42, 43, 44.
  *Note*: All 34 match their exact expected byte sizes from `manifest.json` and load cleanly via SciPy/MNE.
- **5 Truncated Files (Interrupted Historical Downloads)**:
  1. `s1/sess01_subj01_EEG_MI.mat`: 22,194,601 bytes present vs. 609,007,751 bytes expected (3.6% complete).
  2. `s4/sess01_subj04_EEG_MI.mat`: 314,294,220 bytes present vs. 588,517,366 bytes expected (53.4% complete).
  3. `s11/sess01_subj11_EEG_MI.mat`: 453,564,536 bytes present vs. 619,133,876 bytes expected (73.3% complete).
  4. `s40/sess01_subj40_EEG_MI.mat`: 173,647,902 bytes present vs. 608,097,253 bytes expected (28.6% complete).
  5. `s45/sess01_subj45_EEG_MI.mat`: 488,937,278 bytes present vs. 641,370,581 bytes expected (76.2% complete).
- **1 Empty Directory**:
  - `s41/`: Subdirectory exists on disk, but contains 0 files.
- **9 Subjects Not Started in Session 1**:
  - `s46` through `s54` are not present locally.

---

## 3. Storage Estimates and Recovery Roadmap

### Phase 1: Zero-Download Pilot (Current State)
- **Available Immediately**: 34 intact participants in Session 1 ($N = 34$).
- **Storage Needed**: 0 GB (already on disk).
- **Feasibility**: High. Can benchmark `D3_loro`, `D1m_matched_k`, `D1s_size_matched`, and `P1_csp_on_all` across 34 subjects without any network downloads.

### Phase 2: Targeted Session-1 Recovery (Recommended)
- **Target**: Recover the 5 truncated files (`s1`, `s4`, `s11`, `s40`, `s45`) and download `s41` through `s54`.
- **Files to Acquire**: 15 files.
- **Download Footprint**: $\approx 8.4$ GB.
- **Result**: Complete 54-participant Session-1 cohort for multi-dataset validation.

### Phase 3: Complete Two-Session Acquisition (Future Registry)
- **Target**: Download Session 2 (54 MAT files) for cross-session validation (`D6_loso_session`).
- **Download Footprint**: $\approx 32.5$ GB.

---

## 4. Generated Artifacts
- Full manifest: `data/manifests/openbmi_download_manifest.csv` (1,955 rows).
- Missing/truncated list: `data/manifests/openbmi_missing_files.csv` (1,911 rows).
