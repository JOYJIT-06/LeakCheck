# REPOSITORY PROVENANCE & PRESERVATION AUDIT

**Repository Path**: `D:\my lab\LeakCheck_remote`  
**Audit Date**: November 18, 2026 (Stage 1 / Day 1)  
**Auditor**: AGENT 1 (Repository, Git and Provenance Auditor) & LEAD (Project Director)  
**Status**: VERIFIED & PRESERVED  

---

## 1. Git State and Branch Hierarchy

- **Current Working Branch**: `research/v1.1-final-audit`
- **Current HEAD Commit**: `2774aa9c9461d96546d401a4ab8c490b8eb12790`
- **Commit Subject**: `docs(audit): add independent scientific validation audit report (18 sections, 60 KB)`
- **Tracking**: Ahead of `origin/research/v1.1-final-audit` by 1 commit (`2774aa9`).
- **Protected Baseline Branch**: `main` locked at `d35afa6fe8e86dfdf532ee4f26e4abc1482c3155` (Tag: `v1.1.0` at `026e280`).
- **Development Branch (V2)**: `v2-dev` at `eb279d698e6ad71424c58cf39885c3db08f309a4`.
- **Working Tree**: Completely clean on all tracked files. Zero uncommitted changes to existing code.

---

## 2. Backup Integrity Verification

- **Primary Cold Backup**: `D:\my lab\LeakCheck_V1_1_BACKUP_20261118`
  - Status: VERIFIED.
  - Subdirectories verified: `.github`, `.gitignore`, `analysis`, `archive`, `benchmark_results`, `docs`, `notebooks`, `scripts`, `src`, `tests`.
- **Secondary Recovery Snapshots**: `D:\my lab\LeakCheck_backups/`
  - `LeakCheck_code_backup_20261114`
  - `LeakCheck_recovery_20261115_011109`
  - `LeakCheck_remote_backup_20261114`
  - `manuscript_local_20261115`

---

## 3. Historical Benchmark & Archive Invariants

1. **`benchmark_results/physionet_v1_1_final/`**:
   - Status: **100% READ-ONLY & FROZEN**.
   - Contains 16 critical artifacts (including `participant_accuracy.csv`, `participant_flow_manifest.json`, `settings.json`, and summary logs).
   - Checksum Manifest: All files hashed and recorded in `progress/FILE_HASH_MANIFEST.csv`.
2. **`archive/v2/`**:
   - Status: **100% READ-ONLY & PRESERVED**.
   - Contains historical V2 multi-dataset benchmark results, registry definitions, and cross-dataset evaluation assets.
   - Quarantined permanently from V1.1 single-dataset PhysioNet scope.

---

## 4. Active Python Execution Environment

- **Interpreter**: `D:\anaconda\envs\leakcheck\python.exe`
- **Python Version**: `3.12.16` (64-bit AMD64 Windows)
- **Verified Package Manifest**:
  - `mne`: `1.8.0`
  - `scipy`: `1.14.1`
  - `scikit-learn`: `1.5.2`
  - `numpy`: `2.1.3`
  - `pandas`: `2.2.3`
  - `pytest`: `9.2.0`
  - `pyedflib`: `0.1.38`

---
*Signed: AGENT 1 & LEAD — Verified November 18, 2026*
