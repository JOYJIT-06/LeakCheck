# LeakCheck V1.1.0 Release Checklist & Audit Report

**Release Target:** `v1.1.0`  
**Package:** `emi`  
**Proposed Title:** `LeakCheck v1.1.0 — Stabilized EEG Leakage Auditing Framework`  
**Repository:** `D:\my lab\LeakCheck_remote`  
**Target Release Date:** 12 November 2026  
**Audit Date:** 8 November 2026  
**Auditor:** Open-Source Software Release Engineer & Scientific Quality Auditor  

---

## 1. Release Source Identification & Freezing (A1)

- **Source Commit Hash:** `002dc4f4855a2b74983bbaf62eff7614430f9c51`
- **Active Working Branch:** `fix/v1.1-stabilization`
- **Base Version in Git:** `v1.0.0` (`002dc4f`)
- **Staging / Working Tree Differences:**
  - Complete stabilization patch captured in `V11_current_working.patch`.
  - V2 multi-dataset developments are isolated in untracked files (`src/emi/datasets_adapters.py`, `src/emi/datasets_base.py`, `registry/`, `benchmark_results/openbmi_v2/`).
- **Isolation Invariant:**
  - V1.1.0 distribution is built strictly from the stabilized codebase (`pyproject.toml` version `1.1.0`).
  - No provisional V2 code or unvalidated features are included in the V1.1.0 package manifest.

---

## 2. Software Verification Audit (A2)

1. **Automated Test Suite:**
   - **Command:** `pytest -v tests/`
   - **Result:** **186 passed, 0 failed** in 103.45 s (100% pass rate).
   - **Failures Investigated / Suppressed:** None. All tests pass deterministically.
2. **Distribution Artifacts in `dist/`:**
   - Wheel: `dist/emi-1.1.0-py3-none-any.whl` (51,842 bytes)
     - **SHA-256:** `A3D593D1FE3021B9F6CDD8B6E4296BDE2B95D6F09C36CCB46BCB1108E2E7B395`
   - Source Distribution: `dist/emi-1.1.0.tar.gz` (53,312 bytes)
     - **SHA-256:** `FAAEF77A9E3BDB19A2BC8347E2E73912369BB683FFB5DE22404D5ADC55C691FB`
3. **Clean-Environment Installation:**
   - Wheel installed cleanly via `pip install --no-deps --force-reinstall dist/emi-1.1.0-py3-none-any.whl`.
   - Verified clean import: `import emi; assert emi.__version__ == "1.1.0"`.
4. **Metadata & Dependencies:**
   - Declared dependencies: `numpy`, `scipy`, `mne>=1.7,<1.14`, `scikit-learn`, `pandas`, `matplotlib`, `joblib`.
   - Supported Python versions: `>=3.10`.

---

## 3. Documentation & Licensing Audit (A3)

- **`LICENSE`:** Verified MIT License present in repository root.
- **`README.md`:** Contains quickstart, installation, PhysioNet evaluation, CLI instructions, and dataset attribution.
- **`CHANGELOG.md`:** Documents V1.1 stabilization (OAS shrinkage CSP, reproducible seeds, robust BCa bootstrap, and diagnostic reporting).
- **Dataset Attribution:** Schalk et al. (2004) PhysioNet EEGMMIDB citation and PDDL licensing prominently noted.
- **Known Limitations:** Evaluates within-subject EEG motor imagery; does not currently perform cross-subject transfer.

---

## 4. Release Decision Gate (A5)

### Decision: **CONDITIONAL GO**

**Justification:**
All technical criteria for software packaging, testing (186 passing tests), wheel integrity, and documentation are satisfied. 

**Mandatory User Approval Boundary:**
In strict compliance with user operating rules, **all public release actions are STOPPED**:
- No Git tag `v1.1.0` has been pushed to remote.
- No GitHub release has been created or published.
- No packages have been uploaded to PyPI.
- Awaiting explicit user confirmation before executing public release commands.
