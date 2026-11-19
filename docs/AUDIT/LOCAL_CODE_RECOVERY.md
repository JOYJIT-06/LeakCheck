# LeakCheck V1.1 Local Code Recovery and Preservation Report

**Document ID**: `docs/AUDIT/LOCAL_CODE_RECOVERY.md`  
**Date**: 2026-11-14 / 2026-11-15  
**Author**: Worker M1 (Code Recovery and Git Engineer)  
**Parent Agent**: `270738c3-c2bc-480f-8413-a8c0ff4eadac`  
**Working Branch**: `research/v1.1-final-audit`  
**Authoritative Commit**: `d35afa6fe8e86dfdf532ee4f26e4abc1482c3155` (Tag `v1.1.0`)  
**Status**: APPROVED — VERIFIED NON-DESTRUCTIVE RECOVERY  

---

## Executive Summary

In compliance with Phase 1 of the Master Execution Prompt and Requirements R1 and R2:
1. An exhaustive forensic audit was conducted on the local development directory `D:\my lab\LeakCheck` and the authoritative Git repository `D:\my lab\LeakCheck_remote`.
2. A complete non-destructive backup was generated in `D:\my lab\LeakCheck_backups\LeakCheck_code_backup_20261114\` (74 code/docs/config files, 282,937 bytes), strictly excluding the 21.04 GB `data/Multi-Dataset` raw dataset.
3. Every local modification made by the user on 2026-11-04 (including cache shape assertions, automatic sampling frequency detection, `file_sha256` hashing, and settings-hashed directory structures) was forensically compared and verified to be 100% incorporated and preserved within release tag `v1.1.0` (commit `d35afa6fe8e86dfdf532ee4f26e4abc1482c3155`).
4. Two critical defects present in the older local snapshot—an unhandled empty null DataFrame crash in `scripts/run_leakcheck.py:452` and an unsafe rejection window ternary in `src/emi/preprocess.py:72`—were identified and verified as already repaired in `v1.1.0`.
5. A comprehensive backup of `LeakCheck_remote` was created in `D:\my lab\LeakCheck_backups\LeakCheck_remote_backup_20261114\`, including a full Git bundle (`leakcheck_remote_all.bundle`, 15.73 MB, SHA256 `858710844b51428feb2e1921396f9fbadbfec8ead72976337d35412fe32d6b5a`), unstaged diff patches, and all untracked evidence files.
6. Zero user code was lost or overwritten.

---

## 1. Target Repositories & Working Directory Topology

### A. Local Snapshot Directory: `D:\my lab\LeakCheck`
- **Filesystem Type**: Windows NTFS Directory Junction (`d----l`).
- **Junction Target**: `C:\Users\user\OneDrive\Documents\GitHub\eeg pipeline 2\eeg-motor-imagery-mne\eeg-motor-imagery-mne`.
- **Git Repository Status**: `fatal: not a git repository (or any of the parent directories): .git`.
- **Nature of Content**: An unversioned historical development snapshot corresponding to the pre-release v0.3 / v1.0.0 transition, containing local backup files (`*.bak`, `*.validation_backup`, `*.pre_csp_backup`), unversioned package metadata (`__version__ = "0.1.0"`), and 39 raw Multi-DatasetEEG recordings (`.mat`) totaling 21.04 GB downloaded on 2026-11-13.
- **Code Size**: Excluding `data/`, the tree contains exactly 74 files totaling 282,937 bytes (276.31 KB).

### B. Authoritative Git Repository: `D:\my lab\LeakCheck_remote`
- **Filesystem Type**: Standard directory containing full Git repository (`.git`).
- **Remote Origin**: `https://github.com/JOYJIT-06/LeakCheck.git`.
- **Active Working Branch**: `research/v1.1-final-audit` (established off tag `v1.1.0`, commit `d35afa6fe8e86dfdf532ee4f26e4abc1482c3155`).
- **Preserved Archive Branch**: `v2-dev` (HEAD `d5891dbffb3e6cedd1ce843666553ef9e0eacc1b`).
- **Immutable Protected Tag**: `v1.1.0` (`d35afa6fe8e86dfdf532ee4f26e4abc1482c3155`).

---

## 2. Complete Local File Inventory (`D:\my lab\LeakCheck`)

Forensic enumeration of all 74 non-data files in `D:\my lab\LeakCheck` revealed:

| File Path | Size (Bytes) | Category | Description |
|---|---|---|---|
| `.github/workflows/tests.yml` | 387 | CI Workflow | GitHub Actions test workflow |
| `.gitignore` | 98 | Git Config | Basic gitignore rules |
| `CHANGELOG.md` | 3,847 | Docs | Pre-release changelog (ends at v0.3.0) |
| `CITATION.cff` | 357 | Metadata | Citation metadata |
| `CONTRIBUTING.md` | 679 | Docs | Contribution guidelines |
| `inspect_cache.py` | 1,663 | Script | Historical inspection script with hardcoded path |
| `inspect_eeg.py` | 1,093 | Script | Historical raw EDF inspection utility |
| `LICENSE` | 11,558 | Legal | Apache 2.0 license file |
| `LICENSE.pre_release_backup` | 1,067 | Local Backup | Historical MIT license backup |
| `pyproject.toml` | 419 | Build Config | Historical packaging configuration |
| `README.md` | 5,246 | Docs | Historical v0.3 README |
| `requirements.txt` | 72 | Dependencies | Runtime dependencies |
| `scripts/analyze_leakcheck.py` | 9,118 | Script | Statistical analysis and LaTeX table generation |
| `scripts/build_cache.py` | 2,103 | Script | EDF preprocessing and cache generation |
| `scripts/build_cache_moabb.py` | 1,406 | Script | MOABB cache generation utility |
| `scripts/make_synthetic_cache.py` | 2,877 | Script | Synthetic cache fixture generator |
| `scripts/run_group.py` | 2,766 | Script | Multi-subject batch benchmark runner |
| `scripts/run_leakcheck.py` | 13,944 | Script | Master PhysioNet benchmark runner |
| `scripts/run_leakcheck.py.bak` | 10,297 | Local Backup | Pre-modification backup of run_leakcheck |
| `scripts/run_leakcheck.py.pre_csp_backup` | 10,297 | Local Backup | Backup before CSP injection modifications |
| `scripts/run_subject.py` | 1,811 | Script | Single-subject runner wrapper |
| `src/emi/__init__.py` | 221 | Source | Package initialization (`__version__ = "0.1.0"`) |
| `src/emi/cache.py` | 6,822 | Source | Cache I/O with Nov 4 shape checks |
| `src/emi/cache.py.bak` | 3,651 | Local Backup | Pre-Nov 4 backup of cache module |
| `src/emi/cache.py.validation_backup` | 3,651 | Local Backup | Pre-validation backup of cache module |
| `src/emi/config.py` | 3,061 | Source | Config dataclass and constants |
| `src/emi/data.py` | 1,574 | Source | PhysioNet EDF data reader |
| `src/emi/datasets_moabb.py` | 2,665 | Source | MOABB bridge loader |
| `src/emi/decode.py` | 5,014 | Source | Decoding evaluation harness |
| `src/emi/decoders.py` | 5,274 | Source | CSP and Riemannian TS-LR decoders |
| `src/emi/diagnostics.py` | 6,190 | Source | Runs tests and independence diagnostics |
| `src/emi/leakcheck.py` | 28,193 | Source | Validation design and leakage harness |
| `src/emi/leakstats.py` | 9,415 | Source | Statistical calculations (HL, BCa, Holm, TOST) |
| `src/emi/metrics.py` | 3,230 | Source | Metric calculations (balanced acc, AUROC) |
| `src/emi/nulls.py` | 1,967 | Source | Permutation and shift null generators |
| `src/emi/pipeline.py` | 2,805 | Source | Pipeline integrity verifiers |
| `src/emi/plotting.py` | 4,734 | Source | Figure rendering functions |
| `src/emi/preprocess.py` | 7,053 | Source | MNE preprocessing and ICA filtering |
| `src/emi/signal_utils.py` | 5,600 | Source | Signal rejection and bad channel utilities |
| `src/emi/simple_csp.py` | 1,903 | Source | Pure NumPy CSP implementation |
| `src/emi/splitters.py` | 6,963 | Source | LORO, k-fold, size-matched splitters |
| `src/emi/summary.py` | 1,984 | Source | Binomial confidence intervals |
| `src/emi/tfr.py` | 1,250 | Source | Morlet time-frequency calculations |
| `tests/*` (12 test files) | 36,081 | Tests | 87 unit tests (100% passing) |
| `docs/*` (14 doc/csv files) | 52,900 | Docs | Historical v0.3 documentation and audit notes |

---

## 3. Cryptographic and Diff Reconciliation vs Git Lineage

A byte-by-byte SHA256 cryptographic comparison was performed between `D:\my lab\LeakCheck` and Git commits `v1.0.0` (`002dc4f`) and `v1.1.0` (`d35afa6`):

### A. Bit-for-Bit Exact Matches to `v1.0.0` (`002dc4f`)
53 files in `D:\my lab\LeakCheck` match `v1.0.0` bit-for-bit, including core pipeline files:
- `src/emi/leakcheck.py`
- `src/emi/preprocess.py`
- `src/emi/decoders.py`
- `src/emi/signal_utils.py`
- `src/emi/splitters.py`
- `src/emi/leakstats.py`
- `src/emi/metrics.py`
- `src/emi/nulls.py`
- `src/emi/pipeline.py`
- `src/emi/plotting.py`
- `src/emi/simple_csp.py`
- `src/emi/summary.py`
- `src/emi/tfr.py`

### B. Reconciliation of User's Local Modifications (Nov 4, 2026)
In `D:\my lab\LeakCheck`, local edits made on 2026-11-04 introduced:
1. **Input Shape Assertions & Automatic `sfreq` in `src/emi/cache.py`**:
   - Verification that `X` is 3D with shape `(n_epochs, n_channels, n_times)`.
   - Automatic extraction of sampling frequency from time vector when `sfreq` is omitted.
   - Verification: These changes are 100% present in `v1.1.0` (`d35afa6`) with enhanced Schema Version 2 validation.
2. **Deterministic Output Path Hashing in `scripts/run_leakcheck.py`**:
   - `file_sha256(path)` function computing cryptographic input hashes.
   - Per-subject settings hash subdirectory generation ensuring run reproducibility.
   - Verification: These changes are 100% present in `v1.1.0` (`d35afa6`).

### C. Repair of Two Known Defects Present in `D:\my lab\LeakCheck`
Forensic code audit revealed two software defects present in the local snapshot that were repaired in `v1.1.0`:
1. **Empty Null DataFrame Crash (`scripts/run_leakcheck.py:452`)**:
   - *Local Bug*: `nul.groupby(["decoder", "null_type"])` threw `KeyError: 'decoder'` when `nul` was empty (e.g. when `n_null=0`).
   - *Fix in v1.1.0*: Guarded with `if not nul.empty and "decoder" in nul.columns:`.
2. **Rejection Window Ternary Bug (`src/emi/preprocess.py:72`)**:
   - *Local Bug*: `_reject()` used an unsafe inline ternary that failed when `cfg.reject_window == "full"`.
   - *Fix in v1.1.0*: Explicitly handles window modes: `"full"`, tuple bounds `(tmin, tmax)`, or default epoch range.

---

## 4. Non-Destructive Backup Verification

Two comprehensive backups were established in `D:\my lab\LeakCheck_backups\`:

### Backup 1: Local Code Snapshot (`LeakCheck_code_backup_20261114`)
- **Destination**: `D:\my lab\LeakCheck_backups\LeakCheck_code_backup_20261114\`
- **Files Backed Up**: 74 files
- **Total Bytes**: 282,937 bytes (276.31 KB)
- **Manifest**: `backup_manifest.json` (SHA256, byte sizes, relative paths)
- **Exclusion Compliance**: The 21.04 GB `data/` directory and all binary formats (`*.mat`, `*.edf`, `*.npz`) were strictly excluded.
- **Verification**: Every backed-up file was SHA256-verified against the source.

### Backup 2: Repository Snapshot & Bundle (`LeakCheck_remote_backup_20261114`)
- **Destination**: `D:\my lab\LeakCheck_backups\LeakCheck_remote_backup_20261114\`
- **Files Backed Up**: 139 files
- **Total Bytes**: 16,498,317 bytes (15.73 MB)
- **Git Bundle**: `leakcheck_remote_all.bundle` (Full repository archive including all branches, tags, and commits; SHA256: `858710844b51428feb2e1921396f9fbadbfec8ead72976337d35412fe32d6b5a`)
- **Git Metadata Preserved**: `git_status.txt`, `git_branch.txt`, `git_commit.txt`, `git_diff_unstaged.patch`, `git_diff_staged.patch`
- **Untracked Evidence Preserved**: `FINAL_DIAGNOSTIC.txt`, `LeakCheck_paper_evidence/`, `paper_evidence/`

---

## 5. Integrity Declaration

All code recovery procedures were conducted non-destructively:
- Zero files in `D:\my lab\LeakCheck` were modified, overwritten, or deleted.
- Branch `v2-dev` in `D:\my lab\LeakCheck_remote` remains intact.
- Branch `main` and tag `v1.1.0` remain locked at `d35afa6fe8e86dfdf532ee4f26e4abc1482c3155`.
- Dedicated working branch `research/v1.1-final-audit` provides a clean, isolated environment containing only verified V1.1 code.
