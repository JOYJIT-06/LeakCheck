# Troubleshooting and Frequently Asked Questions (FAQ)

This guide covers common questions, configuration pitfalls, dataset errors, and environment edge cases in LeakCheck.

---

## 1. Installation and Import Issues

### Q: `ModuleNotFoundError: No module named 'pyriemann'`
**Answer**: `pyriemann` is strictly optional and **not required**.
LeakCheck includes pure NumPy and SciPy implementations of `CovarianceTransformer` and `TangentSpaceTransformer` in `src/emi/decoders.py`. You do not need to install `pyriemann` or install MSVC C++ build tools on Windows. The Riemannian decoders (`ts_lr`, `ts_lda`) run out of the box using vectorised linear algebra.

### Q: `pip install emi` installs an unrelated package
**Answer**: LeakCheck is an open-science academic framework and is **not** hosted on PyPI under `emi`.
Always install directly from the source repository:
```bash
pip install -e .
```

### Q: Python version incompatibility
**Answer**: LeakCheck requires **Python 3.10 or newer** due to PEP 604 union type expressions (`X | Y`). If you are running Python 3.9 or earlier, upgrade your environment:
```bash
conda create -n leakcheck python=3.10
```

---

## 2. Dataset and I/O Issues

### Q: MNE PhysioNet automated download stalls or fails
**Answer**: By default, MNE downloads PhysioNet data to `~/mne_data/MNE-eegbci-data/`. If downloading stalls due to university proxy or network throttling:
1. Ensure your firewall allows HTTPS connections to `physionet.org`.
2. Alternatively, pre-download the participant EDF files into `~/mne_data/MNE-eegbci-data/physionet.org/files/eegmmidb/1.0.0/`.
3. LeakCheck automatically detects existing files and does not re-download them.

### Q: OpenBMI `MatReadError` or corrupted `.mat` files
**Answer**: OpenBMI `.mat` archives are large (~300 MB per participant). If an HTTP download is interrupted, SciPy's MATLAB parser will raise `MatReadError`.
- LeakCheck's `src/emi/datasets_openbmi.py` catches this exception automatically, records `status="corrupted"` in `participant_eligibility.csv`, and continues evaluating remaining participants.
- To re-download a single participant, delete the truncated file and fetch it from the NEMAR repository.

### Q: Windows Long Path Errors (`FileNotFoundError`)
**Answer**: Windows has a historical 260-character path limit (`MAX_PATH`). While LeakCheck uses standard short paths, if your clone directory is deeply nested:
1. Clone the repository into a shorter path (e.g. `D:\LeakCheck` or `C:\dev\LeakCheck`).
2. Or enable Win32 Long Paths in PowerShell (Administrator):
   ```powershell
   New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
       -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
   ```

---

## 3. Auditing and Scientific Runtime Questions

### Q: Why is `P1_csp_on_all` marked N/A or missing for `ts_lr`?
**Answer**: Mechanism `P1` tests the leakage caused by fitting Common Spatial Pattern (CSP) spatial filters across all trials. Riemannian decoders (`ts_lr`, `ts_lda`) project covariance matrices directly into tangent spaces and do **not** use CSP spatial filtering.
In `src/emi/leakcheck.py`, `p1_csp_on_all` raises `NotApplicable` for any decoder where `DecoderSpec.uses_csp = False`. The audit engine cleanly skips this design for Riemannian decoders.

### Q: Memory limits on systems with 8 GB RAM
**Answer**: Each participant epoch array requires between 50 MB and 150 MB of memory. When running with `--n-jobs -1` on high-core machines, spawning 8 or 16 parallel workers can momentarily spike memory usage.
- On 8 GB RAM systems, use `--n-jobs 2` or `--n-jobs 4`.
- The sequential runner `scripts/run_openbmi_benchmark.py` operates stably under $1.5\text{ GB}$ peak resident memory.

### Q: Permutation null testing is slow
**Answer**: Running full label permutation tests (`--n-null 200` or `1000`) computes 200–1,000 complete cross-validation loops per subject.
- For rapid testing or CI pipelines, pass `--n-null 0`.
- Use non-zero null permutations only when testing empirical chance levels against theoretical 50% chance levels.
