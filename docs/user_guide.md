# LeakCheck User Guide

This user guide provides a complete reference for configuring, running, and extending audits and benchmarks in LeakCheck (`emi`).

---

## 1. Audit Workflow and Concepts

An EEG data leakage audit evaluates a machine learning pipeline across multiple **validation designs** and **leakage injection mechanisms** on identical participant recordings.

```
                  ┌──────────────────────────────────────────────┐
                  │          Clean Raw EEG Recording             │
                  └──────────────────────┬───────────────────────┘
                                         │ Label-blind bandpass & bad-channel rejection
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │            Preprocessed Epochs               │
                  │  X: (trials, channels, time), y: labels,      │
                  │  runs: block indices, times: time vector     │
                  └──────────────────────┬───────────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
   ┌───────────────────────────┐                   ┌───────────────────────────┐
   │     Clean Designs         │                   │  Leaky Designs (P1-P9)    │
   │  - D3 (Leave-One-Run-Out) │                   │  - P1 (Global CSP Fit)    │
   │  - D1s (Size-Matched Rnd) │                   │  - P2 (Global ICA Fit)    │
   │  - D4 (Chronological)     │                   │  - P5 (Global Normalizer) │
   └─────────────┬─────────────┘                   └─────────────┬─────────────┘
                 │                                               │
                 └───────────────────────┬───────────────────────┘
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │           Supervised Decoders                │
                  │  Shrinkage CSP-LDA, CSP-LR, Riemannian TS-LR │
                  └──────────────────────┬───────────────────────┘
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │     Metric Logging & Hypothesis Testing      │
                  │  Hodges-Lehmann median diff, BCa bootstrap CI│
                  └──────────────────────────────────────────────┘
```

---

## 2. CLI Tool: `scripts/run_leakcheck.py`

`scripts/run_leakcheck.py` is the primary command-line tool for auditing the PhysioNet EEGMMIDB dataset.

### Synopsis
```bash
python scripts/run_leakcheck.py [OPTIONS]
```

### Options Reference

| Argument | Type | Default | Description |
|---|---|---|---|
| `--subjects` | string | `1-109` | Comma-separated list or ranges of subject IDs (e.g. `1,2,5` or `1-10`). |
| `--designs` | string | `D3_loro,D1s_size_matched,P1_csp_on_all` | Comma-separated validation designs and leakage mechanisms to audit. |
| `--decoders` | string | `csp_lda` | Comma-separated decoders (`csp_lda`, `csp_lr`, `csp_svm`, `ts_lr`, `ts_lda`). |
| `--csp` | string | `mne` | CSP implementation engine: `mne` (MNE-Python) or `custom` (internal implementation). |
| `--csp-reg` | string | `oas` | Regularization method for covariance matrices: `oas`, `ledoit_wolf`, `empirical`, or `shrinkage`. |
| `--n-null` | integer | `0` | Number of label permutations for empirical null distribution testing. Set to `0` for fast execution. |
| `--n-repeats-matched` | integer | `5` | Number of random shuffle repetitions for `D1s_size_matched`. |
| `--n-jobs` | integer | `1` | Number of parallel worker processes. Set to `-1` to use all CPU cores. |
| `--outdir` | string | `results_audit` | Directory where output CSVs and summary reports are written. |
| `--seed` | integer | `42` | Global pseudo-random generator seed for reproducible cross-validation splits. |

### Practical Examples

#### Fast Smoke Test on Two Participants
```bash
python scripts/run_leakcheck.py \
    --subjects 1,2 \
    --designs D3_loro,D1s_size_matched,P1_csp_on_all \
    --decoders csp_lda,ts_lr \
    --n-jobs 2 \
    --outdir results_smoke
```

#### Full 105-Participant V1.1 Stabilization Benchmark
```bash
python scripts/run_leakcheck.py \
    --subjects 1-109 \
    --designs D3_loro,D1m_matched_k,D1s_size_matched,P1_csp_on_all \
    --decoders csp_lda \
    --csp mne \
    --csp-reg oas \
    --n-jobs 4 \
    --outdir benchmark_results/physionet_v1_1
```

---

## 3. CLI Tool: `scripts/run_openbmi_benchmark.py`

`scripts/run_openbmi_benchmark.py` audits the 62-channel OpenBMI dataset (Lee et al. 2019) across both Shrinkage CSP-LDA and Riemannian Tangent Space Logistic Regression (`ts_lr`).

### Synopsis
```bash
python scripts/run_openbmi_benchmark.py \
    --data-dir data/OpenBMI \
    --subjects 1-54 \
    --decoders csp_lda,ts_lr \
    --designs D3_loro,D1s_size_matched,P1_csp_on_all \
    --target-fs 160.0 \
    --n-repeats-matched 5 \
    --outdir benchmark_results/openbmi_v2
```

### Options Reference
- `--data-dir`: Path to the directory holding unpacked OpenBMI `.mat` session files (e.g., `sess01_subj01_EEG_MI.mat`).
- `--subjects`: Participants to evaluate (1–54).
- `--target-fs`: Decimation target sampling rate (default `160.0` Hz, downsampling from raw `1000.0` Hz).
- `--decoders`: Decoders to audit (default `csp_lda,ts_lr`).
- `--designs`: Validation designs and leakage mechanisms (default `D3_loro,D1s_size_matched,P1_csp_on_all`).
- `--n-repeats-matched`: Shuffle repeats for size-matched partitions (default `5`).

---

## 4. Supported Decoders

LeakCheck supports classical spatial filtering and modern Riemannian geometry pipelines:

| Decoder Key | Full Name | Spatial Transform | Classifier | Native Feature |
|---|---|---|---|---|
| `csp_lda` | Shrinkage CSP-LDA | MNE / Custom CSP | Linear Discriminant Analysis | OAS / Ledoit-Wolf shrinkage |
| `csp_lr` | CSP Logistic Regression | MNE / Custom CSP | $L_2$-penalized Logistic Regression | Log-variance features |
| `csp_svm` | CSP Support Vector Machine | MNE / Custom CSP | Linear Support Vector Classifier | Maximum margin hyperplane |
| `ts_lr` | Riemannian Tangent Space LR | Covariance $\to$ Tangent Space | $L_2$-penalized Logistic Regression | Pure NumPy Fréchet mean |
| `ts_lda` | Riemannian Tangent Space LDA | Covariance $\to$ Tangent Space | Shrinkage LDA | Riemannian geodesic projection |

---

## 5. Output Data Interpretation

Audits generate tidy tabular datasets structured as follows:

### `fold_metrics.csv`
Contains evaluation metrics for every single cross-validation fold:
- `subject`: Participant identifier.
- `decoder`: Classifier evaluated.
- `design`: Validation design or leakage condition.
- `fold`: Fold index.
- `accuracy`: Proportion of correctly classified test trials in this fold.
- `balanced_accuracy`: Balanced accuracy ($(\text{TPR} + \text{TNR}) / 2$) accounting for class imbalance.
- `auroc`: Area under the Receiver Operating Characteristic curve.

### `participant_metrics.csv`
Contains pooled participant-level results aggregated across folds:
- `acc_pooled`: Accuracy calculated by pooling all predictions across folds.
- `bal_acc_pooled`: Participant-level balanced accuracy.
- `mean_fold_acc`: Arithmetic mean of fold-level accuracies.

### `design_comparisons.csv`
Contains paired participant-level contrast statistics:
- `contrast`: Comparison contrast (e.g. `P1_csp_on_all - D3_loro` or `D1s_size_matched - D3_loro`).
- `delta_hl`: Hodges-Lehmann non-parametric median paired difference.
- `ci_lower`, `ci_upper`: 95% Bias-Corrected and Accelerated (BCa) bootstrap confidence interval bounds.
- `p_val_raw`: Two-sided Wilcoxon-Pratt signed-rank test p-value.
- `p_val_holm`: Holm-Bonferroni multiplicity-adjusted p-value.
- `cohen_dz`: Within-subject effect size $d_z = \frac{\bar{D}}{s_D}$.
