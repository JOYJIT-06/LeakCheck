# LeakCheck

A reproducible benchmarking and audit framework for evaluating validation designs and detecting data leakage in electroencephalography (EEG) decoding pipelines.

---

## 1. Project Overview

**LeakCheck** (`src/emi/`) is an open-source benchmarking and auditing toolkit designed to evaluate how cross-validation strategies and data-processing boundaries impact motor-imagery EEG decoding performance. It provides leak-free, run-held-out validation baselines alongside controlled contamination models to empirically quantify and expose methodological validation bias.

## 2. What LeakCheck Does

LeakCheck enables researchers and practitioners to audit EEG machine learning workflows for subtle information leakage. It systematically separates cross-validation partitioning structure (inter-run transfer vs. trial-level random splitting) from true supervised data contamination (fitting filters or transformers using test labels). By executing strictly nested, fold-isolated pipelines, LeakCheck establishes reliable, reproducible baselines for brain-computer interface (BCI) evaluation.

## 3. Scientific Problem Investigated

In EEG classification and BCI literature, two distinct methodological issues are frequently conflated under the broad term *"data leakage"*:

1. **Supervised Feature Extraction Contamination**: Fitting supervised filters (such as Common Spatial Patterns, CSP) across the entire dataset—including test trials and class labels—prior to cross-validation splitting. This leaks held-out label information directly into the feature space, creating severe artificial accuracy inflation.
2. **Validation Partitioning & Run-Independence**: Choosing between run-held-out cross-validation (holding out complete recording blocks) and trial-level random cross-validation across pooled runs. In the presence of inter-run non-stationarities, sensor impedance changes, or temporal autocorrelation, random pooling alters the operational generalization target, often producing performance discrepancies that are mistakenly attributed to label leakage.

LeakCheck dissociates these phenomena experimentally, providing an empirical standard to distinguish true supervised contamination from cross-validation partitioning effects.

## 4. Main Features of Current Implemented Version

* **Run-Held-Out Operational Reference (`D3_loro`)**: 3-fold Leave-One-Run-Out cross-validation holding out complete physical recording blocks (Runs 4, 8, and 12).
* **Matched-$k$ Random Partitioning (`D1m_matched_k`)**: 5-repeat 3-fold stratified random trial splitting across pooled runs with matched fold count ($k=3$).
* **Size- and Class-Matched Random Partitioning (`D1s_size_matched`)**: 20-repeat random trial splitting strictly constrained to match the exact per-fold train/test sample sizes and class distributions of `D3_loro`.
* **Supervised Contamination Positive Control (`P1_csp_on_all`)**: Supervised OAS-CSP fitted on all trials and labels prior to splitting, establishing an empirical upper bound on leakage-induced inflation.
* **Pratt-Wilcoxon Signed-Rank Tests**: Exact non-parametric paired hypothesis testing handling zero differences via the Pratt method, with Holm-Bonferroni family-wise error rate adjustment.
* **Fold-Isolated Preprocessors**: Preprocessing operations (channel interpolation, montage referencing, and spatial filtering) fitted strictly within training folds to eliminate test-set information bleed.
* **Run-Independent FIR Filtering**: Continuous zero-phase bandpass filtering executed independently within each physical recording run, eliminating cross-run boundary convolution artifacts.

## 5. Supported Datasets & Implemented Methods

* **Dataset**: [PhysioNet EEG Motor Movement/Imagery Database](https://physionet.org/content/eegmmidb/1.0.0/) (`EEGMMIDB`; 64 channels, 160 Hz). Evaluates 2-class motor imagery (left hand vs. right hand, Runs 4, 8, and 12) across $N = 105$ eligible participants retained following technical screening.
* **Decoders & Pipelines**: Common Spatial Patterns (CSP) with Optimal Analytical Shrinkage (OAS) covariance regularization, paired with regularized Linear Discriminant Analysis (LDA) using Ledoit-Wolf shrinkage.

## 6. Installation Instructions

LeakCheck requires **Python >= 3.10**.

Clone the repository and install in editable mode:

```bash
git clone https://github.com/JOYJIT-06/LeakCheck.git
cd LeakCheck
python -m pip install -e .
```

To install testing and development dependencies:

```bash
python -m pip install -e ".[dev]"
```

## 7. Running Examples

### Quickstart Demonstration

Run a self-contained demonstration on synthetic 3-run motor imagery data (no dataset downloads required):

```bash
python scripts/quickstart_demo.py
```

### Benchmark Command-Line Interface

Inspect all available CLI options:

```bash
python scripts/run_benchmark.py --help
```

Run the benchmark runner across participants on PhysioNet EEGMMIDB:

```bash
python scripts/run_benchmark.py --dataset physionet --subjects 1-109 --designs D3_loro,D1s_size_matched,D1m_matched_k,P1_csp_on_all
```

### Statistical Verification

Recalculate summary statistics and hypothesis tests directly from participant result tables:

```bash
python recalculate_all_stats.py
```

## 8. How to Run Tests

Execute the comprehensive test suite with `pytest`:

```bash
pytest tests/ -v
```

For quiet execution:

```bash
pytest tests/ -q
```

## 9. Explanation of the Output

Benchmark executions generate standardized, machine-readable artifacts in `benchmark_results/`:

* **`inflation_by_subject.csv`**: Participant-level metrics containing reference accuracy (`acc_ref`, `D3_loro`), comparison accuracy (`acc_leaky`), and paired differences ($\Delta = \text{acc}_{\text{leaky}} - \text{acc}_{\text{ref}}$).
* **`inflation_table.csv`**: Cohort summary table reporting sample sizes, mean $\Delta$, median $\Delta$, Hodges–Lehmann location estimates ($\hat{\theta}_{\text{HL}}$), 95% BCa bootstrap confidence intervals, Pratt-Wilcoxon test statistics, and Holm-adjusted $p$-values.
* **`excluded_or_failed_subjects.csv`**: Operational audit trail recording participants excluded by predefined data-quality or trial-count criteria (S044, S069, S086, S091).
* **`tables/` and `figures/`**: Publication-ready LaTeX tables and vector figures (PDF, PNG, SVG) illustrating paired accuracy scatters, effect-size distributions, and rank spectra.

## 10. Minimal Repository Structure

```text
LeakCheck/
├── src/emi/            # Core library (preprocessing, splitters, decoders, statistics)
├── scripts/            # Benchmark runner, quickstart demo, and figure/table generators
├── tests/              # Comprehensive unit, integration, and statistical regression tests
├── benchmark_results/  # Benchmark results, participant metrics, and frozen baselines
├── figures/            # Publication figures (.pdf, .png, .svg)
├── tables/             # Publication summary tables (.tex, .csv)
├── docs/               # Detailed documentation, audit logs, and technical reports
├── pyproject.toml      # Project packaging and dependency configuration
└── LICENSE             # Apache License 2.0
```

## 11. Important Limitations & Scientific Cautions

1. **Single-Dataset Scope**: Current empirical findings are established on the PhysioNet EEGMMIDB corpus. Results regarding partitioning effects should not be generalized to all EEG paradigms without empirical validation.
2. **Positive Control Nature of P1**: The global CSP condition (`P1_csp_on_all`) is a deliberate positive control designed to quantify the ceiling effect of supervised test-label contamination; it does not represent recommended modeling practice.
3. **Operational Reference**: Leave-one-run-out (`D3_loro`) serves as the run-held-out operational benchmark in this study, not as an absolute ground truth of longitudinal real-world deployment performance.
4. **Direction of Random-Split Bias**: In PhysioNet EEGMMIDB, trial-level random splitting produced lower accuracy estimates than run-held-out validation due to cross-run non-stationarities. Random trial splitting does not universally inflate decoding accuracy.

## 12. Citation & License

This project is licensed under the [Apache License 2.0](LICENSE).

If you use LeakCheck in your research, please cite:

```bibtex
@article{leakcheck2026,
  title={LeakCheck: A Framework for Evaluating Validation Strategies and Supervised Contamination in EEG Decoding},
  author={LeakCheck Contributors},
  journal={arXiv preprint},
  year={2026}
}
```

When using the PhysioNet EEGMMIDB dataset, please cite:
* Schalk, G., et al. (2004). BCI2000: a general-purpose brain-computer interface system. *IEEE TBME*, 51(6), 1034–1043.
* Goldberger, A. L., et al. (2000). PhysioBank, PhysioToolkit, and PhysioNet. *Circulation*, 101(23), e215–e220.
