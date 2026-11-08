# LeakCheck Installation Guide

This guide details how to install and verify **LeakCheck** (Python package: `emi`) across Windows, Linux, and macOS environments.

---

## 1. System Requirements

- **Python Version**: Python 3.10, 3.11, or 3.12 (Python 3.10+ required for union type syntax `X | Y`).
- **Operating Systems**:
  - Windows 10 / Windows 11 (tested on Windows 11 AMD64)
  - Ubuntu Linux 20.04 LTS / 22.04 LTS / Debian 11+
  - macOS 12+ (Intel or Apple Silicon)
- **Memory**: Minimum 4 GB RAM (8 GB recommended for full-cohort parallel execution). Full PhysioNet ($N=105$) and OpenBMI ($N=34$) benchmarks operate in $<1.5\text{ GB}$ peak resident set size when executing sequentially or under 4 worker threads.
- **Acceleration**: CPU-only; no GPU or CUDA required. All filters and covariance algorithms utilize vectorised NumPy/SciPy linear algebra.

---

## 2. Package Distribution Notice

> [!NOTE]
> **Source and Repository Installation Only**  
> LeakCheck is distributed as an open-science research package directly via GitHub. It is **not** currently distributed on the public PyPI index under the name `emi` to avoid namespace collisions with legacy packages. Do not run `pip install emi` from PyPI; always install directly from the verified repository or local source directory.

---

## 3. Recommended Installation (Conda / Mamba)

Using a dedicated Conda environment is recommended to ensure clean scientific dependency isolation:

```bash
# 1. Create a fresh conda environment with Python 3.10
conda create -n leakcheck python=3.10 -y
conda activate leakcheck

# 2. Clone the repository
git clone https://github.com/JOYJIT-06/LeakCheck.git
cd LeakCheck

# 3. Install in editable mode with development dependencies
pip install -e .
```

---

## 4. Standard Installation (Python venv)

If using standard Python `venv`:

### On Linux / macOS:
```bash
# 1. Clone repository
git clone https://github.com/JOYJIT-06/LeakCheck.git
cd LeakCheck

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Upgrade pip and install
pip install --upgrade pip
pip install -e .
```

### On Windows (PowerShell):
```powershell
# 1. Clone repository
git clone https://github.com/JOYJIT-06/LeakCheck.git
cd LeakCheck

# 2. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Upgrade pip and install
python -m pip install --upgrade pip
pip install -e .
```

---

## 5. Core Dependencies

The package dependencies specified in `pyproject.toml` are:

| Package | Version Range | Purpose |
|---|---|---|
| `mne` | `>=1.7, <1.14` | Raw EEG I/O, filtering, electrode montages, epoch slicing |
| `numpy` | `>=1.23` | High-performance array manipulation and linear algebra |
| `scipy` | `>=1.9` | Filter design, signal processing, non-parametric Wilcoxon-Pratt statistics |
| `scikit-learn` | `>=1.1` | Cross-validation splitters, Linear Discriminant Analysis, Logistic Regression |
| `pandas` | `>=1.5` | Structured metric aggregation, tabular reporting |
| `matplotlib` | `>=3.5` | Publication figure generation (scatter, inflation, forest plots) |
| `joblib` | `>=1.2` | Multiprocessing parallelisation across participants |

### Optional Riemannian Dependencies
LeakCheck includes native, pure-NumPy implementations of `CovarianceTransformer` and `TangentSpaceTransformer` in `src/emi/decoders.py`. If `pyriemann` is installed (`pip install pyriemann`), LeakCheck automatically detects it and can use it interchangeably; however, `pyriemann` is **not required**, preventing C-extension build failures on Windows.

---

## 6. Installation Verification

To confirm that the package is correctly installed and ready for benchmarking, run the following verification steps:

### Check Package Import and Version
```bash
python -c "import emi; print(f'LeakCheck (emi) version {emi.__version__} successfully imported.')"
```
*Expected output:* `LeakCheck (emi) version 1.1.0 successfully imported.`

### Run Quick Synthetic Demonstration
Execute the self-contained synthetic benchmark (runs in $<2$ seconds without downloading external data):
```bash
python scripts/quickstart_demo.py
```

### Run Automated Unit Test Suite
Execute the full test suite (186 tests covering preprocessing, splitters, decoders, leakage injection, statistics, and multi-dataset adapters):
```bash
pytest tests -q
```
*Expected output:* `186 passed in ~60s`.

---

## 7. Building Wheels from Source

To build distributable binary wheel and source distribution tarballs:

```bash
pip install build
python -m build
```
The built artifacts will appear in the `dist/` directory:
- `dist/emi-1.1.0-py3-none-any.whl`
- `dist/emi-1.1.0.tar.gz`

These wheels can be transferred to air-gapped compute nodes or HPC clusters and installed with:
```bash
pip install dist/emi-1.1.0-py3-none-any.whl
```
