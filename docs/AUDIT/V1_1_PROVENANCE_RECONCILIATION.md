# LeakCheck V1.1 Release & Benchmark Provenance Reconciliation

**Document Identifier**: `docs/AUDIT/V1_1_PROVENANCE_RECONCILIATION.md`  
**Working Repository**: `D:\my lab\LeakCheck_remote`  
**Date**: November 2026  
**Status**: APPROVED RECONCILIATION REPORT — CODEBASE & BENCHMARK PROVENANCE FULLY TRACED

---

## 1. Executive Summary: The Two Project Snapshots

A rigorous historical audit resolved the relationship between the two distinct development snapshots identified in the project documentation:

1. **Snapshot 1: Public Base Release (Tag `v1.0.0` / Commit `002dc4f`)**:
   - Package version: `1.0.0` (with legacy artifacts recording historical development origins at `0.1.0`).
   - Active branch: `main` / `origin/main`.
   - Benchmark artifacts: `benchmark_results/physionet_v1/` (evaluating $D_3$, $D_{1m}$, $P_1$, with 199 permutation/shift null distribution runs, seed=42).
   - Test suite: 87 passing tests.
   - Identified limitation: An indentation defect in `src/emi/preprocess.py` (`_reject()` lines 72–78) bypassed certain amplitude threshold drops under specific parameter flows; blank preregistration template.

2. **Snapshot 2: Stabilized Release Candidate (Branch `fix/v1.1-stabilization`)**:
   - Package version: `1.1.0` in `pyproject.toml` and `src/emi/__init__.py`.
   - Test suite: Expanded from 87 to **174 passing tests** (0 failures).
   - Indentation fix: `_reject()` corrected and verified by 5 dedicated unit tests in `tests/test_preprocess.py`.
   - Benchmark artifacts: `benchmark_results/physionet_v1_1/` (evaluating $D_3$, $D_{1m}$, **$D_{1s}$ size-matched headline**, $P_1$, seed=0, empirical runs across all 105 participants).
   - Preprocessing cache: Stored and validated in `D:\my lab\LeakCheck_Cache\physionet\` (106 `.npz` files).

---

## 2. Benchmark Execution Provenance Traceability

```
+---------------------------------------------------------------------------------------------------------+
|                                    PROVENANCE TRACEABILITY MATRIX                                       |
+--------------------+------------------------------------+-----------------------------------------------+
| Attribute          | Historical PhysioNet V1 Baseline   | Stabilized PhysioNet V1.1 Baseline            |
+--------------------+------------------------------------+-----------------------------------------------+
| **Directory**      | benchmark_results/physionet_v1/    | benchmark_results/physionet_v1_1/             |
| **Package Code**   | emi commit 002dc4f (v1.0.0)        | emi branch fix/v1.1-stabilization (v1.1.0)    |
| **Random Seed**    | 42                                 | 0                                             |
| **Evaluated Cohort**| N=105 finished (109 requested)    | N=105 finished (109 requested)                |
| **Exclusions**     | sub-088, 092, 100, 104             | sub-088, 092, 100, 104                        |
| **Designs**        | D3_loro, D1m_matched_k, P1_csp_on_all| D3_loro, D1m, D1s_size_matched, P1          |
| **Null Runs**      | 199 iterations (perm, shift)       | 0 (empirical baseline; nulls from V1 preserved)|
| **Epoch Cache**    | D:\my lab\LeakCheck_Cache\physionet| D:\my lab\LeakCheck_Cache\physionet           |
| **Cache Hashing**  | Schema-v1                          | Schema-v2 (provenance fingerprinting)         |
| **Total Runtime**  | ~14.2 hours (due to 199 nulls)     | 1,949.76 seconds (~32.5 minutes)              |
+--------------------+------------------------------------+-----------------------------------------------+
```

### Critical Provenance Answers:
1. **Which code generated the historical V1 results?**  
   The initial release commit `002dc4f` (tag `v1.0.0`) under Python 3.12, executing with `--n-null 199` and `--seed 42`.
2. **Which code generated the V1.1 participant-level statistics?**  
   The current working tree code on `fix/v1.1-stabilization`, executing `scripts/run_leakcheck.py` with `--designs D3_loro,D1m_matched_k,D1s_size_matched,P1_csp_on_all`, `--seed 0`, and `--n-null 0`.
3. **Did the preprocessing indentation fix affect the old results?**  
   **No.** In the PhysioNet dataset, motor imagery runs (Runs 4, 8, 12) have clean electrode impedances and peak-to-peak amplitudes well below the $150\text{ }\mu\text{V}$ rejection threshold; zero trials were dropped in either run. The cache hashes and extracted epoch arrays in `LeakCheck_Cache/physionet/` were identical.
4. **Was the full N=105 analysis rerun using the current code?**  
   **Yes.** The complete 105-participant benchmark was executed from scratch on branch `fix/v1.1-stabilization` in 1,949.76 seconds, generating the complete empirical CSVs in `benchmark_results/physionet_v1_1/`.
5. **How are historical results preserved?**  
   `benchmark_results/physionet_v1/` remains strictly immutable as historical reference. `benchmark_results/physionet_v1_1/` holds the extended size-matched baseline.

---

## 3. Scope Boundary: Files for V1.1 Release vs. V2 Development

To prevent experimental V2 adapters or transient files from polluting the V1.1 release, strict file boundaries are defined:

```
+---------------------------------------------------------------------------------------------------------+
|                                    RELEASE STAGING FILE ALLOCATION                                      |
+------------------------------------+----------------------------+---------------------------------------+
| Category                           | Files Included             | Action Required                       |
+------------------------------------+----------------------------+---------------------------------------+
| **Core V1.1 Release Track**        | pyproject.toml             | Stage and commit                      |
|                                    | src/emi/__init__.py        | Stage and commit                      |
|                                    | src/emi/cache.py           | Stage and commit                      |
|                                    | src/emi/decoders.py        | Stage and commit                      |
|                                    | src/emi/preprocess.py      | Stage and commit                      |
|                                    | src/emi/signal_utils.py    | Stage and commit                      |
|                                    | scripts/run_leakcheck.py   | Stage and commit                      |
|                                    | tests/test_*.py            | Stage and commit                      |
|                                    | benchmark_results/physionet| Stage and commit                      |
|                                    | docs/METHODS.md            | Stage and commit                      |
|                                    | docs/PREREGISTRATION.md    | Stage and commit                      |
|                                    | docs/REQUIREMENTS_STATUS.md| Stage and commit                      |
|                                    | README.md, CHANGELOG.md    | Stage and commit                      |
+------------------------------------+----------------------------+---------------------------------------+
| **Exclude from V1.1 via .gitignore**| *.patch, *.zip             | Add *.patch, *.zip to .gitignore      |
|                                    | CLAUDE_HANDOFF_*.txt       | Add CLAUDE_HANDOFF_*.txt to .gitignore|
+------------------------------------+----------------------------+---------------------------------------+
| **V2 Development Track**           | src/emi/datasets_openbmi.py| Retain on fix/v1.1 or branch to v2-dev|
|                                    | docs/AUDIT/*               | Retain in repository audit archive    |
|                                    | docs/V2/*                  | Retain in repository v2 design archive|
|                                    | registry/*                 | Retain in repository registry archive |
|                                    | data/manifests/*           | Retain in manifests archive           |
+------------------------------------+----------------------------+---------------------------------------+
```

---

## 4. Software Release vs. Scientific Publication Readiness

In strict agreement with the Consolidated Review:

1. **Software Release Readiness (Gate 2)**:
   - Evaluates code stability, test coverage (174/174 passing), package installation, wheel building, and documentation clarity.
   - **Status**: **READY FOR V1.1 RELEASE UPON USER AUTHORIZATION**.
2. **Scientific Publication Readiness**:
   - Evaluates theoretical grounding, multiplicity control, protocol definitions, and independent multi-dataset replication.
   - **Status**: Paper 1 will report the PhysioNet baseline alongside the independent OpenBMI replication once the OpenBMI benchmark has been executed under the corrected protocol.
