# LeakCheck V1.1 Comprehensive Audit â€” Run Summary

- Run folder: `RUN_COMPREHENSIVE_20261117_233342`
- Repository: `D:\my lab\LeakCheck_remote`
- Interpreter: `D:\anaconda\envs\leakcheck\python.exe`
- Branch/commit and working-tree state: see `01_COMPREHENSIVE_AUDIT_TRANSCRIPT.txt`
- Release metadata and artifact checks: see transcript.
- Source AST parsing and package provenance: see transcript.
- Pytest collection exit code: **0**
- Pytest full-suite exit code: **0**
- Evidence inventory: `02_EVIDENCE_FILE_INVENTORY.csv` (450 files)

## Interpretation

- Exit code 0 means the corresponding pytest command completed successfully; inspect the transcript for exact counts and warnings.
- Non-zero exit codes require investigation; they are not silently treated as passes.
- File inventory is not proof that an experiment was executed or that a result is valid.
- This automated run does not independently validate participant-level statistics, EEG preprocessing correctness, leakage mechanisms, figure values, citation support, or manuscript claims.
- Missing evidence must remain UNVERIFIED/BLOCKED until primary evidence is examined.

## Read-only boundary

The script writes only its own audit output folder. Pytest temporary files are directed into that folder. Tests can still have their own side effects; inspect the test code and repository status after execution.
