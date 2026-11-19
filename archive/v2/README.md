# LeakCheck V2 Preservation Archive

This directory houses the LeakCheck V2 multi-dataset development framework, empirical benchmark outputs, test suites, and scripts preserved in accordance with the project boundary mandate (`ORIGINAL_REQUEST.md` lines 503–524, 1437–1465).

## Purpose & Scope Isolation
- **LeakCheck V1.1 Release Scope**: The core LeakCheck V1.1 distribution package and publication evaluate solely the PhysioNet EEG Motor Movement/Imagery dataset ($N=105$).
- **V2 Preservation Mandate**: V2 development (including OpenBMI benchmark replication, multi-dataset adapter architecture, and cross-dataset evaluations) is preserved intact within this archive and on the Git branch `v2-dev`. It is excluded from the V1.1 distribution wheel (`.whl`), source distribution (`.tar.gz`), and core test suite to maintain 100% release purity and scope compliance.

## Archive Directory Structure
- `src/emi/`:
  - `datasets_openbmi.py`: OpenBMI (Lee et al. 2019) raw `.mat` loading, polyphase decimation, run-isolated FIR filtering, and schema-v2 caching.
  - `datasets_adapters.py`: Pluggable `BaseEEGDataset` adapters for 11 motor imagery datasets.
  - `datasets_base.py`: Abstract dataset base class (`BaseEEGDataset`), `DatasetMetadata`, and registry decorators.
  - `datasets_moabb.py`: Experimental bridge loader for MOABB candidate datasets.
- `tests/`:
  - `test_openbmi.py`: OpenBMI dataset loader tests.
  - `test_openbmi_benchmark.py`: OpenBMI benchmark execution and contrast tests.
  - `test_datasets_adapters.py`: Multi-dataset adapter contract and metadata validation tests.
- `scripts/`:
  - `run_openbmi_benchmark.py`: CLI pipeline runner for OpenBMI leakage benchmark.
  - `plot_openbmi_figures.py`: Plotting generator for OpenBMI figures.
  - `generate_openbmi_manifests.py`: Verification manifest generator for OpenBMI datasets.
  - `build_cache_moabb.py`: MOABB cache conversion script.
- `benchmark_results/`:
  - `openbmi_v2/`: Manifests, design comparisons, subject-level split indices (`sub-02` through `sub-44`), and fold metrics for OpenBMI.
- `figures/`:
  - `openbmi_v2/`: Vector and raster figures documenting OpenBMI leakage metrics.
- `registry/records/`:
  - `openbmi_v2_reproducibility.json`: Provenance and run hashes for OpenBMI benchmark runs.
- `docs/`:
  - Historical OpenBMI and V2 planning, download audit, and inventory reconciliation documents.

## Running V2 Assets
To run or develop with V2 assets:
1. Ensure the V2 source directory is in `PYTHONPATH`:
   ```bash
   export PYTHONPATH="archive/v2/src:src:$PYTHONPATH"
   ```
2. Execute the V2 test suite:
   ```bash
   pytest archive/v2/tests -v
   ```
3. Full continuous V2 development continues on branch `v2-dev`.
