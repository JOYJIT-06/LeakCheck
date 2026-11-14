# Git Safety, Branch Architecture, and Recovery Protocol

**Document ID**: `docs/AUDIT/GIT_SAFETY_AND_RECOVERY.md`  
**Date**: 2026-11-14 / 2026-11-15  
**Author**: Worker M1 (Code Recovery and Git Engineer)  
**Parent Agent**: `270738c3-c2bc-480f-8413-a8c0ff4eadac`  
**Working Branch**: `research/v1.1-final-audit`  
**Authoritative Base Commit**: `d35afa6fe8e86dfdf532ee4f26e4abc1482c3155` (Tag `v1.1.0`)  
**Status**: ACTIVE — SAFE NON-DESTRUCTIVE BRANCH ESTABLISHED  

---

## Executive Summary

This document establishes the Git safety protocols, branching topology, non-destructive recovery procedures, and audit trail for the LeakCheck repository.

Per Phase 2 of the Master Execution Prompt and Requirements R1 and R2:
1. Exact commit hashes and branch pointers were verified prior to initiating any modifications.
2. A full pre-branching backup bundle of the repository was created in `D:\my lab\LeakCheck_backups\LeakCheck_remote_backup_20261114\`.
3. Dedicated working branch `research/v1.1-final-audit` was created and checked out originating directly from immutable tag `v1.1.0` (`d35afa6fe8e86dfdf532ee4f26e4abc1482c3155`).
4. Branches `main` and `v2-dev` remain 100% intact, unmodified, and preserved.
5. Zero destructive Git commands (`git reset --hard`, `git clean -fd`, `git push --force`) were executed.

---

## 1. Initial Git Repository State (Pre-Execution Baseline)

Prior to Milestone M1 branching, the repository state was forensically recorded:

| Parameter | State / Value |
|---|---|
| **Repository Path** | `D:\my lab\LeakCheck_remote` |
| **Configured Origin** | `https://github.com/JOYJIT-06/LeakCheck.git` |
| **Initial Active Branch** | `v2-dev` |
| **Initial HEAD Commit** | `d5891dbffb3e6cedd1ce843666553ef9e0eacc1b` |
| **Commit Message** | `fix(benchmark): robust real-data path resolution and small-cohort contrast statistics` |
| **Local Branch: `main`** | `d35afa6fe8e86dfdf532ee4f26e4abc1482c3155` (Tag `v1.1.0`) |
| **Tag: `v1.0.0`** | `002dc4f4855a2b74983bbaf62eff7614430f9c51` |
| **Tag: `v1.1.0`** | `d35afa6fe8e86dfdf532ee4f26e4abc1482c3155` |
| **Remote Tracking** | `origin/main` at `0ef76487375c9d1018a29ae69be6c3529bd65653` (ahead by 9 commits due to PR #4 merge) |
| **Remote Tracking** | `origin/v2-dev` at `6da1e583ec60308ec309a207dcb63461632bd3ed` (ahead of local `v2-dev` by 6 commits) |
| **Unstaged Working State** | 1 modified file: `scripts/run_unified_benchmark.py` (lines 765–805) |
| **Untracked Working State** | `FINAL_DIAGNOSTIC.txt`, `LeakCheck_paper_evidence/`, `paper_evidence/` |

---

## 2. Non-Destructive Git Backup Execution

Before modifying branch pointers or working tree state, a comprehensive Git backup was executed to `D:\my lab\LeakCheck_backups\LeakCheck_remote_backup_20261114\`:

1. **Full Repository Bundle**:
   - Command: `git bundle create leakcheck_remote_all.bundle --all`
   - Size: 16,498,317 bytes (15.73 MB)
   - SHA256: `858710844b51428feb2e1921396f9fbadbfec8ead72976337d35412fe32d6b5a`
   - Contains: All branches (`main`, `v2-dev`, `fix/v1.1-stabilization`), all tags (`v1.0.0`, `v1.1.0`), and all commits.
2. **Patch Preservation**:
   - `git_diff_unstaged.patch`: Verbatim diff of unstaged changes to `scripts/run_unified_benchmark.py`.
   - `git_diff_staged.patch`: Verification of empty staging area.
3. **Metadata Snapshots**:
   - `git_status.txt`: Full verbose status output.
   - `git_branch.txt`: Recorded active branch (`v2-dev`).
   - `git_commit.txt`: Recorded active commit (`d5891dbffb3e6cedd1ce843666553ef9e0eacc1b`).
4. **Untracked Artifacts Copy**:
   - `untracked_and_evidence/FINAL_DIAGNOSTIC.txt` (42.8 KB)
   - `untracked_and_evidence/LeakCheck_paper_evidence/` (66 files, 5.16 MB)
   - `untracked_and_evidence/paper_evidence/` (66 files, 5.16 MB)

---

## 3. Dedicated Working Branch Setup (`research/v1.1-final-audit`)

To isolate the PhysioNet V1.1 completion from ongoing V2 multi-dataset development, the following sequence was executed:

1. **Stash Unstaged Work on `v2-dev`**:
   ```bash
   git stash push -m "v2-dev: small cohort contrast statistics"
   ```
   - Result: Working directory cleaned without discarding changes.
   - Preserves: `v2-dev` HEAD remains exactly `d5891dbffb3e6cedd1ce843666553ef9e0eacc1b`.
2. **Branch Directly from Immutable Tag `v1.1.0`**:
   ```bash
   git checkout -b research/v1.1-final-audit v1.1.0
   ```
   - Result: Created and checked out new branch `research/v1.1-final-audit` rooted at commit `d35afa6fe8e86dfdf532ee4f26e4abc1482c3155`.
3. **Verify Branch Pointers**:
   ```python
   assert rev_parse("HEAD") == "d35afa6fe8e86dfdf532ee4f26e4abc1482c3155"
   assert rev_parse("v1.1.0^{commit}") == "d35afa6fe8e86dfdf532ee4f26e4abc1482c3155"
   assert rev_parse("main") == "d35afa6fe8e86dfdf532ee4f26e4abc1482c3155"
   assert rev_parse("v2-dev") == "d5891dbffb3e6cedd1ce843666553ef9e0eacc1b"
   ```
   - All assertions PASSED.

---

## 4. Inviolable Git Safety Rules

The following rules govern all operations on this repository:

1. **Zero Destructive Commands**:
   - `git reset --hard` is strictly PROHIBITED.
   - `git clean -fd` is strictly PROHIBITED.
   - `git push --force` and `git push --force-with-lease` are strictly PROHIBITED.
   - `git checkout -- .` is strictly PROHIBITED.
2. **Protected Branches and Tags**:
   - Branch `main` is protected. No direct commits or merges without user approval.
   - Branch `v2-dev` is protected. It represents the preserved V2 archive.
   - Tag `v1.1.0` is immutable.
3. **Commit Discipline**:
   - Use conventional commit messages (`feat:`, `fix:`, `docs:`, `test:`, `release:`).
   - Never commit sensitive data, API keys, credentials, or raw EEG data (`.mat`, `.edf`, `.npz`).
4. **Push Protocol**:
   - Push only the dedicated branch `research/v1.1-final-audit` to GitHub origin.
   - Never push directly to `main` without explicit approval.

---

## 5. Recovery Protocol in Case of Git Error

If any Git operation encounters an unexpected state or error, adhere to this deterministic recovery sequence:

1. **Halt Immediately**: Do not issue speculative commands or repeated retries.
2. **Capture Diagnostic State**:
   ```bash
   git status -vv
   git branch -vv
   git log -5 --oneline --graph
   ```
3. **Consult the Backup Manifest**:
   - Reference `D:\my lab\LeakCheck_backups\LeakCheck_remote_backup_20261114\remote_backup_manifest.json`.
4. **Restore from Bundle if Needed**:
   - The entire Git database can be verified or re-extracted from `leakcheck_remote_all.bundle`:
   ```bash
   git bundle verify leakcheck_remote_all.bundle
   ```
5. **Report and Document**: Log the exact command, error output, and remedial action in this document.

---

## 6. Current Branch Ledger

- **Initial Branch**: `v2-dev`
- **Active Working Branch**: `research/v1.1-final-audit`
- **Root Commit**: `d35afa6fe8e86dfdf532ee4f26e4abc1482c3155` (Tag `v1.1.0`)
- **Current HEAD**: `d35afa6fe8e86dfdf532ee4f26e4abc1482c3155`
- **Tracked Files in V1.1**: 145 files
- **Baseline Test Suite**: 171 passed / 0 failed / 0 skipped (37.16s)
- **Status**: Completely safe, isolated, and verified.
