# MASTER V2 EXECUTION BASELINE — LEAKCHECK

**Date:** 8 November 2026  
**Project:** LeakCheck — EEG Leakage Auditing and Benchmarking Framework  
**Repository:** `D:\my lab\LeakCheck_remote`  
**Active Branch:** `fix/v1.1-stabilization`  
**Python Environment:** `D:\anaconda\envs\leakcheck\python.exe` (Python 3.12.16, pytest-9.2.0)  
**Package:** `emi` v1.1.0  
**Current Test Status:** 180 passed, 0 failed (42.78s)

---

## 1. Executive Summary

This baseline establishes the exact scientific, software, and data environment before launching full execution of the LeakCheck V2 multi-dataset benchmark and manuscript generation. All 180 unit and regression tests pass deterministically. The historical PhysioNet V1 and V1.1 caches are strictly preserved and immutable. The OpenBMI dataset has been reconciled to 34 intact Session 1 participants (20.60 GB), and its processing pipeline and runner have been verified via a successful two-subject smoke test (Subjects 2 and 3). Cloud storage integration (Dropbox MCP and Google Drive CLI) has been audited and validated with zero financial expenditure.

---

## 2. Environment & System Configuration

- **Host OS:** Windows 11 AMD64
- **CPU:** Multi-core x86_64 CPU (CPU-only execution, no NVIDIA CUDA/GPU)
- **RAM:** 8 GB physical memory (strict sequential processing required, `--n-jobs 1`)
- **Python:** `D:\anaconda\envs\leakcheck\python.exe` (3.12.16)
- **Primary Dependencies:**
  - `numpy`, `scipy`, `mne` (v1.9.0), `scikit-learn` (v1.6.1), `pandas` (v2.2.3)
  - Zero proprietary or C-compiler build dependencies; native Riemannian geometry transformers implemented in `src/emi/decoders.py`.
- **Git State:**
  - Branch: `fix/v1.1-stabilization`
  - Uncommitted staging: Documented in `V11_current_working.patch` and working directory.
  - Release artifacts in `dist/`: `emi-1.1.0-py3-none-any.whl` (51.8 KB), `emi-1.1.0.tar.gz` (53.3 KB).

---

## 3. Preserved Empirical Baselines

### 3.1 PhysioNet EEGMMIDB ($N=105$ complete participants)
- **Location:** `benchmark_results/physionet_v1/` and `benchmark_results/physionet_v1_1/`
- **Integrity Invariant:** Read-only / Immutable. Never modified or overwritten.
- **Audited Ground Truth Contrast Effects:**
  - $P_1$ vs $D_3$ (Supervised preprocessing leakage):  
    $\Delta_{\text{HL}} = +24.50\text{ pp}$ ($95\%\text{ BCa CI}: [22.40, 26.50]\text{ pp}$), $p_{\text{raw}} = 1.48 \times 10^{-18}$, $p_{\text{Holm}} = 4.43 \times 10^{-18}$ ($m=3$).
  - $D_{1s}$ vs $D_3$ (Trial randomization leakage, size-matched):  
    $\Delta_{\text{HL}} = -2.68\text{ pp}$ ($95\%\text{ BCa CI}: [-3.97, -1.38]\text{ pp}$), $p_{\text{raw}} = 5.86 \times 10^{-5}$, $p_{\text{Holm}} = 5.86 \times 10^{-5}$ ($m=3$).
  - $D_{1m}$ vs $D_3$ (Trial randomization leakage, max-power):  
    $\Delta_{\text{HL}} = -4.47\text{ pp}$ ($95\%\text{ BCa CI}: [-5.84, -3.10]\text{ pp}$), $p_{\text{raw}} = 5.41 \times 10^{-9}$, $p_{\text{Holm}} = 1.08 \times 10^{-8}$ ($m=3$).

---

## 4. OpenBMI Dataset Inventory Baseline

- **Location:** `D:\my lab\LeakCheck\data\OpenBMI`
- **Reconciliation Status:** Full physical audit completed (see `docs/AUDIT/OPENBMI_INVENTORY_RECONCILIATION.md`).
- **Participant Breakdown (Session 1):**
  - **Intact Participants ($N=34$):** Complete runs 1–4, 400 trials, 62 EEG channels, valid header and data blocks. Total volume: 20.60 GB.
    - Eligible Subject IDs: `02, 03, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 42, 43, 44`
  - **Truncated / Corrupted ($N=5$):** `01, 04, 11, 40, 45` (premature EOF or partial download; excluded from analysis).
  - **Missing ($N=15$):** `05, 06, 07, 08, 09, 41, 46, 47, 48, 49, 50, 51, 52, 53, 54`.
- **Pre-download Requirement:** ZERO local downloads required. The local $N=34$ intact cohort is sufficient for an authoritative, fully powered replication benchmark.

---

## 5. Software Architecture & Verification Baseline

### 5.1 Test Suite Status (180 Tests)
- `tests/test_cache.py`: 31 tests passed
- `tests/test_decode.py`: 3 tests passed
- `tests/test_decode_loro.py`: 6 tests passed
- `tests/test_diagnostics.py`: 11 tests passed
- `tests/test_leakcheck.py`: 17 tests passed
- `tests/test_leakstats.py`: 21 tests passed
- `tests/test_openbmi.py`: 3 tests passed
- `tests/test_openbmi_benchmark.py`: 6 tests passed
- `tests/test_preprocess.py`: 5 tests passed
- `tests/test_real_checks.py`: 2 tests passed
- `tests/test_signal_utils.py`: 59 tests passed
- `tests/test_splitters.py`: 12 tests passed
- `tests/test_summary.py`: 4 tests passed
- **Total:** 180 passed in 42.78 seconds.

### 5.2 Gate 3b Smoke Test Verification
- Ran on `sub-02` and `sub-03` in 115.78 s.
- Produced all required CSVs and fold indices matching the frozen schema.
- Confirmed that CSP-LDA exhibits severe positive inflation ($+7.00$ to $+8.50\text{ pp}$) under $P_1$ contamination.
- Confirmed that Riemannian TS-LR Fréchet mean is strictly label-unsupervised, producing $0.00\text{ pp}$ $P_1$ inflation.

---

## 6. Cloud Storage & Zero-Cost Architecture

- **Dropbox MCP:** Authenticated as `Joyjit Das` (`dasjoyjit84@gmail.com`). Verified read/write/hash/delete cycles. Root `/LeakCheck_Cloud` provisioned.
- **Google Drive CLI (`gdrive`):** Provisioned binary `gdrive-1015343799.exe` in plugin data path.
- **Financial Commitment:** Exactly $\$0.00$ expended. No paid compute, no billable cloud egress.

---

## 7. Scope Boundaries & Immediate Action Plan

1. **Step 1:** Gate 3c execution across all 34 intact OpenBMI participants.
2. **Step 2:** Publication figure rendering for OpenBMI benchmark.
3. **Step 3:** 14-point criteria evaluation for manuscript architecture (Part 5).
4. **Step 4:** Implementation of Gate 4 (Multi-dataset adapter engine), Gate 5 (P1–P9 leakage mechanisms), Gate 6 (Decoders), Gate 7 (Statistics & reporting), Gate 8 (CI & registry), Gate 10 & 11 (Manuscript & final completion report).
