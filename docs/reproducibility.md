# Benchmark Reproducibility and Provenance Guide

This guide provides exact step-by-step instructions to reproduce all empirical benchmark results, statistical tables, and publication figures in LeakCheck V1.1 and V2.

---

## 1. Provenance and Hardware Baseline

All reported benchmarks were executed and verified on the following hardware baseline:
- **Operating System**: Windows 11 AMD64 (build 10.0.26200) / Linux x86_64 compatible
- **Processor**: Intel / AMD Multi-Core CPU (6–8 cores recommended)
- **System Memory**: 8 GB RAM (Peak resident set size $< 1.5\text{ GB}$)
- **GPU Acceleration**: None (CPU-only, deterministic floating-point execution)
- **Python Environment**: Python 3.10.19, MNE 1.10.2, NumPy 1.26.4, SciPy 1.15.2, Scikit-Learn 1.7.2, Pandas 2.3.3

---

## 2. Reproducing the PhysioNet V1.1 Benchmark ($N = 105$)

The PhysioNet EEG Motor Movement/Imagery benchmark assesses the headline size-matched random partition ($D_{1s}$) and spatial filter leakage ($P_1$) across 105 healthy participants.

### Step 1: Execute the Full-Cohort Audit
```bash
python scripts/run_leakcheck.py \
    --subjects 1-109 \
    --designs D3_loro,D1m_matched_k,D1s_size_matched,P1_csp_on_all \
    --decoders csp_lda \
    --csp mne \
    --csp-reg oas \
    --n-jobs 4 \
    --seed 42 \
    --outdir benchmark_results/physionet_v1_1
```

*Expected Runtime*: Approximately 12–15 minutes on 4 CPU cores.

### Step 2: Verify Summary Output
Inspect `benchmark_results/physionet_v1_1/inflation_table.csv`. The Hodges-Lehmann non-parametric differences must match the published statistics exactly:

| Contrast | Contrast Type | Mean Diff | Median Diff | Hodges-Lehmann ($\Delta_{\text{HL}}$) | 95% BCa Bootstrap CI | Wilcoxon $p_{\text{Holm}}$ | Cohen's $d_z$ |
|---|---|---:|---:|---:|---:|---:|---:|
| **P1 vs D3** | Supervised Spatial Leakage | $+24.82$ pp | $+23.26$ pp | **$+24.50$ pp** | $[+21.75, +27.78]$ pp | $2.42 \times 10^{-18}$ | $+1.771$ |
| **D1s vs D3** | Size-Matched Random | $-2.77$ pp | $-2.61$ pp | **$-2.68$ pp** | $[-3.94, -1.46]$ pp | $5.86 \times 10^{-5}$ | $-0.449$ |
| **D1m vs D3** | $k$-Matched Random ($k=3$) | $-4.67$ pp | $-4.00$ pp | **$-4.47$ pp** | $[-5.80, -3.11]$ pp | $1.10 \times 10^{-8}$ | $-0.685$ |

---

## 3. Reproducing the OpenBMI V2 Benchmark ($N = 34$)

The OpenBMI V2 benchmark evaluates 34 intact participants across 62 channels, comparing Shrinkage CSP-LDA and Riemannian Tangent Space Logistic Regression (`ts_lr`).

### Step 1: Ensure Dataset Files are Unpacked
Place raw OpenBMI session MAT files in `data/OpenBMI/` (or specify via `--data-dir`):
```
data/OpenBMI/sess01_subj*.mat
```

### Step 2: Execute the Benchmark Runner
```bash
python scripts/run_openbmi_benchmark.py \
    --data-dir data/OpenBMI \
    --subjects 1-54 \
    --decoders csp_lda,ts_lr \
    --designs D3_loro,D1s_size_matched,P1_csp_on_all \
    --target-fs 160.0 \
    --n-repeats-matched 5 \
    --seed 42 \
    --outdir benchmark_results/openbmi_v2
```

*Expected Runtime*: Approximately 44 minutes (2,631 seconds) single-threaded on 8 GB RAM.

### Step 3: Verify Cryptographic Artifact Hashes
Verify the integrity of the generated CSV files against their sealed SHA-256 digests:

```bash
# PowerShell
Get-FileHash benchmark_results\openbmi_v2\*.csv -Algorithm SHA256

# Linux / macOS
sha256sum benchmark_results/openbmi_v2/*.csv
```

| File | Rows | Verified SHA-256 Digest |
|---|---:|---|
| `participant_eligibility.csv` | 34 | `a14ff1fe8b63b272fdf6dd21e7895b6c8eb7422f6760df768b59e4ec3cb462cb` |
| `fold_metrics.csv` | 2,992 | `b374086cb48d3db39ca0be2fb635a9feefba00fa882a17f694bf4736f8a49ba3` |
| `participant_metrics.csv` | 204 | `47eae3f4435b5420377f0a8276f7f6f5d81b95f2d019dbca6157dbe9b1686708` |
| `design_comparisons.csv` | 4 | `52d878029c5bfd240d0246a48d88e00188686d1f9a2e37905fec5859714a79ad` |

### Step 4: Verify Empirical Statistics
Inspect `benchmark_results/openbmi_v2/design_comparisons.csv`:

| Decoder | Contrast | Hodges-Lehmann ($\Delta_{\text{HL}}$) | 95% BCa Bootstrap CI | Wilcoxon $p_{\text{Holm}}$ | Cohen's $d_z$ |
|---|---|---:|---:|---:|---:|
| **CSP-LDA** | P1 vs D3 | **$+6.25$ pp** | $[+3.25, +8.23]$ pp | $1.87 \times 10^{-4}$ | $+0.745$ |
| **CSP-LDA** | D1s vs D3 | **$+2.84$ pp** | $[+1.46, +4.98]$ pp | $1.87 \times 10^{-4}$ | $+0.751$ |
| **TS-LR** | P1 vs D3 | **$+0.75$ pp** | $[+0.25, +1.50]$ pp | $0.0203$ | $+0.417$ |
| **TS-LR** | D1s vs D3 | **$+2.94$ pp** | $[+1.66, +4.51]$ pp | $1.94 \times 10^{-4}$ | $+0.771$ |

---

## 4. Reproducing Publication Figures

To generate the publication-ready vector and raster figures from the benchmark CSVs:

```bash
python scripts/plot_openbmi_figures.py
```

Generated outputs are placed in `figures/openbmi_v2/`:
1. `paired_accuracy_openbmi_csp_lda.png` / `.pdf`: Paired participant-level dot-and-line scatter plots comparing $D_3$, $D_{1s}$, and $P_1$ for CSP-LDA.
2. `paired_accuracy_openbmi_ts_lr.png` / `.pdf`: Paired participant-level dot-and-line scatter plots for Riemannian TS-LR.
3. `inflation_openbmi.png` / `.pdf`: Paired difference distributions ($\Delta = \text{Design} - D_3$) with Hodges-Lehmann medians and 95% BCa error bars.
