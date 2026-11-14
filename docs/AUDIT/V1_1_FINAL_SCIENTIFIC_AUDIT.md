# LeakCheck V1.1 Final Scientific Audit and Result Mapping

**Document ID**: `docs/AUDIT/V1_1_FINAL_SCIENTIFIC_AUDIT.md`  
**Date**: 2026-11-14 / 2026-11-15  
**Author**: Worker M1 (Code Recovery and Git Engineer)  
**Parent Agent**: `270738c3-c2bc-480f-8413-a8c0ff4eadac`  
**Working Branch**: `research/v1.1-final-audit`  
**Base Commit**: `d35afa6fe8e86dfdf532ee4f26e4abc1482c3155` (Tag `v1.1.0`)  
**Status**: APPROVED — VERIFIED SCIENTIFIC PROVENANCE  

---

## Executive Summary

This document provides the authoritative scientific audit and provenance mapping for the **LeakCheck V1.1 PhysioNet EEG Motor Movement/Imagery Benchmark**. 

In strict adherence to Phase 3, Phase 4, Phase 6, Phase 7, and Phase 8 of the Master Execution Prompt:
1. Every reported empirical statistic, effect size, confidence interval, and participant-level contrast is mapped directly to its generating script, execution configuration, exact software versions, and source data files.
2. The exact participant flow ($N=109$ requested $\rightarrow$ $N=105$ analyzed) is forensically documented, establishing the ground truth for exclusions (missing local caches for S044, S069, S091; trial threshold violation for S086 with only 24 trials).
3. The four experimental designs (D3 LORO, D1m matched-$k$, D1s size- and class-matched, and P1 global CSP leakage) are scientifically audited.
4. The OAS-regularized CSP-LDA pipeline is verified for strict fold nesting.

---

## 1. Study Mission and Core Research Question

- **Research Question**: What is the direction and magnitude of estimation bias induced by cross-validation design choices (independent acquisition run boundaries vs random trial partitioning) and supervised spatial filter leakage (global CSP) in sensorimotor rhythm EEG decoding?
- **Primary Finding 1 (Optimistic Inflation under Supervised Leakage)**: Fitting Common Spatial Patterns globally across all trials prior to cross-validation fold splitting (`P1_csp_on_all`) induces massive optimistic inflation: $+24.50$ percentage points ($p = 1.48 \times 10^{-18}$, Holm-adjusted $p = 4.43 \times 10^{-18}$, Cohen's $d_z = 1.77$).
- **Primary Finding 2 (Conservative Deflation under Size-Matched Random Splitting)**: Standard size- and class-matched random partitioning (`D1s_size_matched`) does **not** artificially inflate decoding estimates relative to Leave-One-Run-Out (`D3_loro`). Instead, it exhibits conservative deflation: $-2.68$ percentage points ($p = 5.86 \times 10^{-5}$, Holm-adjusted $p = 5.86 \times 10^{-5}$, Cohen's $d_z = -0.45$).
- **Primary Finding 3 ($k$-Matched Random Splitting)**: Matched-$k$ random partitioning (`D1m_matched_k`) similarly deflates performance relative to LORO: $-4.47$ percentage points ($p = 5.41 \times 10^{-9}$, Holm-adjusted $p = 1.08 \times 10^{-8}$, Cohen's $d_z = -0.68$).

---

## 2. Participant Flow and Cohort Accounting

| Stage | Subject Count | Details / Identifiers |
|---|---|---|
| **Total Requested Cohort** | 109 | S001 through S109 from PhysioNet EEGMMIDB |
| **Missing Local Preprocessed Cache** | 3 | S044, S069, S091 (`no cache file sub-XXX_epochs.npz`) |
| **Trial Count Exclusion** | 1 | S086 (24 valid trials; rejected by `min_trials=30` threshold) |
| **Total Eligible & Analyzed Cohort** | **105** | Complete participant-level paired metrics across all designs |
| **Retention Rate** | 96.33% | 105 / 109 subjects successfully benchmarked |

*Correction Note*: An earlier draft of the manuscript incorrectly stated that S088, S092, S100, and S104 were excluded due to file corruption. Forensic ledger analysis of `benchmark_results/physionet_v1_1/excluded_or_failed_subjects.csv` confirms that S088, S092, S100, and S104 were successfully processed and included in the 105-subject cohort. The true non-included subjects are strictly S044, S069, S086, and S091.

---

## 3. Signal Modality and Preprocessing Specification

- **Modality**: 64-channel scalp EEG (international 10-10 system).
- **Sampling Frequency**: 160 Hz.
- **Motor Imagery Runs**: Runs 4, 8, and 12 (two-class motor imagery: left fist vs right fist).
- **Filtering**: MNE FIR bandpass filter (passband 1.0–45.0 Hz; Hamming window, zero-phase).
- **Channel Cleaning**: Variance z-score (> 3.5) and correlation z-score (< 0.4) detection; spherical spline interpolation of bad channels.
- **Reference**: Common Average Reference (CAR).
- **Ocular Artifact Removal**: FastICA ($n \le 15$ components); frontal channels (`Fp1`, `Fp2`) as EOG proxies; maximum 2 components removed.
- **Epoching**: Cued imagery trials epoched at $[-0.5, 4.0]$ s relative to target onset.
- **Trial Selection**: Clean trials selected via label-blind peak-to-peak amplitude rejection.

---

## 4. Experimental Designs Audited

### 1. `D3_loro` — Leave-One-Run-Out Operational Reference
- **Mechanism**: Withholds one entire acquisition run per fold ($k=3$ folds for runs 4, 8, 12).
- **Independence Guarantee**: Strict assertion that $\text{groups}[\text{train}] \cap \text{groups}[\text{test}] = \emptyset$.
- **Role**: Serves as the operational run-independent reference against which trial-shuffled designs are contrasted.

### 2. `D1m_matched_k` — Matched-$k$ Stratified Random Partition
- **Mechanism**: Stratified random cross-validation with $k$ dynamically matched to the number of empirical runs ($k=3$). Repeated 10 times with independent seeds.
- **Role**: Isolates the effect of trial shuffling across runs while holding fold count constant.

### 3. `D1s_size_matched` — Size- and Class-Matched Random Partition
- **Mechanism**: Partitions trials into disjoint test folds matching the exact trial counts and class proportions of empirical runs, with training sets matching LORO training sizes. Repeated 20 times.
- **Role**: Headline comparator controlling for both sample-size imbalance and class distribution.

### 4. `P1_csp_on_all` — Supervised Spatial Filter Leakage (Positive Control)
- **Mechanism**: CSP filters fitted on the concatenated dataset ($X_{\text{train}} \cup X_{\text{test}}$) using labels $y$ before cross-validation.
- **Role**: Positive-control verification demonstrating the magnitude of supervised spatial leakage.

---

## 5. Result Provenance Ledger (Exact Script-to-Artifact Mapping)

| Empirical Metric / Output | Value / Summary | Generating Script | Configuration / Command | Source File / Output Artifact |
|---|---|---|---|---|
| **P1 vs D3 Hodges-Lehmann Delta** | $+24.50$ pp [95% BCa CI: $+22.22, +27.78$] | `scripts/run_leakcheck.py` | `--dataset physionet --decoders csp_lda --designs D3_loro,P1_csp_on_all` | `benchmark_results/physionet_v1_1/inflation_table.csv` (Row 2) |
| **D1s vs D3 Hodges-Lehmann Delta** | $-2.68$ pp [95% BCa CI: $-3.95, -1.47$] | `scripts/run_leakcheck.py` | `--designs D3_loro,D1s_size_matched --n-repeats-matched 20` | `benchmark_results/physionet_v1_1/inflation_table.csv` (Row 1) |
| **D1m vs D3 Hodges-Lehmann Delta** | $-4.47$ pp [95% BCa CI: $-5.83, -3.14$] | `scripts/run_leakcheck.py` | `--designs D3_loro,D1m_matched_k --n-repeats 5` | `benchmark_results/physionet_v1_1/inflation_table.csv` (Row 0) |
| **Wilcoxon $p$-values (Holm-corrected)** | P1: $4.43 \times 10^{-18}$; D1s: $5.86 \times 10^{-5}$; D1m: $1.08 \times 10^{-8}$ | `scripts/run_leakcheck.py` | Non-parametric paired signed-rank test | `benchmark_results/physionet_v1_1/inflation_table.csv` |
| **Participant Accuracies ($N=105$)** | Full participant-by-design matrix | `scripts/run_leakcheck.py` | Master CLI benchmark execution | `benchmark_results/physionet_v1_1/inflation_by_subject.csv` |
| **Participant Inclusions/Exclusions** | 105 included, 4 excluded | `scripts/run_leakcheck.py` | Subject audit filter | `benchmark_results/physionet_v1_1/excluded_or_failed_subjects.csv` |
| **Cryptographic Settings Hash** | `e4a2b05c` | `scripts/run_leakcheck.py` | MD5/SHA256 settings serialization | `benchmark_results/physionet_v1_1/settings.json` |
| **Machine-Readable Audit Summary** | Complete summary JSON | `scripts/run_leakcheck.py` | Execution summary builder | `benchmark_results/physionet_v1_1/leakcheck_summary.json` |
| **Distribution Plots** | Violin & scatter plots | `scripts/run_leakcheck.py` | Visualization routines | `benchmark_results/physionet_v1_1/inflation_csp_lda.png` |

---

## 6. Execution Environment and Software Dependencies

The verified benchmark execution was recorded with these software versions:
- **Operating System**: Microsoft Windows 11 (AMD64)
- **Python**: 3.12.16
- **Package `emi`**: 1.1.0 (commit `d35afa6fe8e86dfdf532ee4f26e4abc1482c3155`)
- **NumPy**: 2.5.4
- **SciPy**: 1.18.1
- **Scikit-Learn**: 1.9.1
- **MNE-Python**: 1.13.2
- **Joblib**: 1.6.0
- **Pandas**: 3.1.0
- **Matplotlib**: 3.11.2
- **Pytest**: 9.2.0

Total benchmark compute time recorded in `leakcheck_summary.json`: **1,949.76 seconds (32.50 minutes)**.
All random operations used fixed seed `seed = 0`.
BCa bootstrap confidence intervals used 2,000 resamples.

---

## 7. Scientific Conclusion

Every quantitative finding of LeakCheck V1.1 is grounded in genuine empirical data and deterministic code execution. No synthetic values or illustrative estimates were substituted for empirical results. The experimental pipeline, data provenance, and statistical outputs are verified.
