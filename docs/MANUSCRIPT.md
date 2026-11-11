# LeakCheck: Auditing Data Leakage and Validation Protocols in Non-Invasive BCI Machine Learning

**Authors**: LeakCheck Research Engineering Group  
**Target Venue**: IEEE Transactions on Biomedical Engineering / Journal of Neural Engineering  
**Version**: 1.1.0 (November 2026)

---

## Abstract
Machine-learning models for electroencephalography (EEG) brain-computer interfaces (BCIs) are acutely vulnerable to validation contamination and methodological artifacts. Non-stationarity across recording runs, high dimensionality, and subtle preprocessing leaks frequently produce optimistic or misleading performance estimates. Here, we present **LeakCheck**, an open-source research and auditing framework designed to systematically quantify the direction and magnitude of validation-induced bias. Using controlled comparisons across $N=105$ participants of the PhysioNet EEG Motor Movement/Imagery dataset, we contrast clean leave-one-run-out (LORO) validation against both conventional random cross-validation and deliberately contaminated feature-space pipelines. We show that supervised spatial filtering leakage (Common Spatial Patterns fitted across all runs) produces a massive $+24.50$ percentage point (pp) median performance inflation (Hodges-Lehmann $95\%$ BCa CI: $[+22.22, +27.78]$ pp, $d_z = 1.771$, $p = 1.48 \times 10^{-18}$). Conversely, we demonstrate that contrary to widespread assumptions in the BCI literature, random trial-level cross-validation does not inflate performance relative to LORO; rather, strictly size- and class-matched random partitioning (`D1s`) produces a statistically significant $-2.68$ pp deflation (CI: $[-3.95, -1.47]$ pp, $p = 5.86 \times 10^{-5}$) caused by inter-run non-stationarity in mixed training folds. Furthermore, unconstrained $k$-fold cross-validation (`D1m`) exacerbates this deflation to $-4.47$ pp due to fold geometry and class-imbalance artifacts. We release LeakCheck as an extensible, reproducible software suite with 174 automated tests, multi-dataset adapters (OpenBMI), standalone Riemannian tangent space decoders, and foundational schemas for a federated EEG Benchmark Registry.

---

## 1. Introduction
Brain-computer interfaces (BCIs) translating sensorimotor rhythms into control commands rely heavily on statistical decoding algorithms. However, recent reproducibility crises across computational neuroscience and machine learning have highlighted the widespread prevalence of methodological contamination—ranging from spatial filter leakage and test-set hyperparameter tuning to improper cross-validation partitioning. 

In EEG decoding, evaluating models by randomly partitioning trials across time can violate temporal independence. Yet, whether random trial partitioning inflates or deflates performance in real multi-run EEG motor imagery benchmarks has remained unresolved due to conflicting definitions of baseline splits and uncontrolled fold sizing.

The objective of **LeakCheck** is to establish an empirical, reproducible framework that decouples feature-space contamination from temporal validation protocols, evaluating each mechanism using participant-level non-parametric inference.

---

## 2. Background and Related Work
Previous literature has explored discrete aspects of BCI validation:
- **Spatial filter contamination**: Lemm et al. (2011) and Farquhar & Hill (2013) demonstrated that supervised dimensionality reduction like Common Spatial Patterns (CSP) must be strictly nested inside cross-validation folds.
- **Benchmarking frameworks**: The Mother of All BCI Benchmarks (MOABB; Jayaram & Barachant, 2018) standardized cross-validation across public BCI datasets, establishing LORO as standard practice.
- **Deep learning validation**: Li et al. (2020) and Schirrmeister et al. (2017) highlighted that trial-level random shuffling can yield deceptive accuracy estimates in convolutional neural networks.

However, existing frameworks lack an integrated suite for injecting controlled synthetic contaminations, comparing them against paired clean baselines, and executing automated negative-control audits across cohorts.

---

## 3. Research Gap & Novelty
LeakCheck bridges the gap between theoretical validation criticism and automated empirical software auditing by integrating:
1. Matched validation-design contrasts isolating fold geometry from run boundaries.
2. Injected positive-control leakage mechanisms (P1–P7).
3. Participant-level paired statistical estimators (Hodges-Lehmann, BCa bootstrap CIs, TOST equivalence).
4. Negative-control permutation and circular-shift null models.
5. Reusable, multi-dataset architectural schemas for community benchmarking.

---

## 4. Research Questions & Hypotheses
- **RQ1**: Does random trial-level validation systematically inflate decoding performance relative to run-held-out validation?
- **RQ2**: Does matching fold sizes and class distributions (`D1s`) eliminate observed differences between random splitting and LORO?
- **RQ3**: What is the true effect size of global CSP leakage (`P1`) relative to validation-split effects?

**Hypotheses**:
- **H1**: Global CSP leakage (`P1`) produces severe positive inflation ($\Delta > +20$ pp, $d_z > 1.5$).
- **H2**: In multi-run EEG, random trial partitioning deflates accuracy relative to LORO due to inter-run non-stationarity and disrupted baseline continuity.

---

## 5. Datasets and Experimental Design

### 5.1 Primary Cohort: PhysioNet EEGMMIDB
- 109 subjects, 64 channels, 160 Hz.
- Tasks: Left fist vs. right fist imagined movement (runs 4, 8, 12).
- Exclusion: 1 subject excluded technically (Subject 86: 24 trials < 30); 3 missing from archive (44, 69, 91); $N = 105$ completed participants.

### 5.2 Independent Validation Cohort: OpenBMI
- Lee et al. (2019) 62-channel EEG dataset, 54 subjects.
- Preprocessed and downsampled from 1000 Hz to 160 Hz using `emi.datasets_openbmi`.

---

## 6. Validation Taxonomy (D1–D6) & Leakage Mechanisms (P1–P7)
- **`D3_loro`**: Leave-One-Run-Out cross-validation (clean reference).
- **`D1m_matched_k`**: Stratified random $k$-fold cross-validation ($k=3$).
- **`D1s_size_matched`**: Size- and class-matched random split (20 repeats), where test folds exactly duplicate LORO fold dimensions but draw trials randomly across runs.
- **`P1_csp_on_all`**: CSP fitted across all runs prior to partitioning (injected leakage).

---

## 7. Statistical Methodology
- **Unit of Analysis**: The individual participant ($N = 105$).
- **Location Estimator**: Hodges-Lehmann pseudo-median difference $\Delta_{\text{HL}}$:
  $$\Delta_{\text{HL}} = \text{median}\left\{ \frac{\Delta_i + \Delta_j}{2} \;\middle|\; 1 \le i \le j \le N \right\}$$
- **Uncertainty**: $95\%$ BCa bootstrap confidence intervals ($B = 2,000$).
- **Significance & Multiplicity**: Wilcoxon signed-rank test with Holm-Bonferroni correction within decoder families.
- **Equivalence Testing**: Two One-Sided Tests (TOST) against $\pm 2.0$ pp bounds.

---

## 8. Empirical Results ($N = 105$)

| Contrast | Contrast Category | Mean Diff | Median Diff | Hodges-Lehmann ($\Delta_{\text{HL}}$) | 95% BCa Bootstrap CI | Wilcoxon $p$ (Holm) | Cohen's $d_z$ |
|---|---|---:|---:|---:|---:|---:|---:|
| **P1 vs D3** | Injected Spatial Leakage | $+24.82$ pp | $+23.26$ pp | **$+24.50$ pp** | $[+22.22, +27.78]$ pp | $1.48 \times 10^{-18}$ | $+1.771$ |
| **D1m vs D3** | $k$-Matched Random ($k=3$) | $-4.67$ pp | $-4.00$ pp | **$-4.47$ pp** | $[-5.83, -3.14]$ pp | $1.08 \times 10^{-8}$ | $-0.685$ |
| **D1s vs D3** | Headline Size-Matched Random | $-2.77$ pp | $-2.61$ pp | **$-2.68$ pp** | $[-3.95, -1.47]$ pp | $5.86 \times 10^{-5}$ | $-0.449$ |

### Key Findings:
1. **The Deflation Reality of Random Splitting**:
   - `D1s` exhibits a statistically significant $-2.68$ pp deflation ($p = 5.86 \times 10^{-5}$) relative to LORO. Mixing trials across runs harms model generalization because training folds must fit heterogeneous drift across runs, whereas testing on a single contiguous run in LORO preserves within-run spectral continuity.
2. **Fold Sizing Explains Geometric Bias**:
   - Controlling for fold geometry (`D1s` vs `D1m`) recovers $+1.79$ pp of performance, demonstrating that unconstrained $k$-fold cross-validation imposes artificial degradation through class-ratio fluctuations.
3. **Feature Leakage Dominance**:
   - CSP contamination (`P1`) increases accuracy by $+24.50$ pp ($d_z = 1.771$), confirming that spatial filter leaks dwarf temporal validation discrepancies.

---

## 9. Negative Controls and Null Validation
Under within-run label permutation (`perm`), `D3_loro` achieved mean null accuracy of $49.99\%$ with an empirical false-positive rate of $3.2\%$ at nominal $\alpha = 0.05$ ($< 5\%$), verifying the nominal calibration of the negative control.

---

## 10. Discussion & Limitations
While LeakCheck V1.1 demonstrates rigorous empirical control across $N=105$ participants, certain limitations remain:
1. **Continuous Preprocessing**: Bandpass filtering and ICA blink removal are performed on continuous recordings prior to epoching (label-blind, but not fold-nested).
2. **Spatial Density**: Current findings reflect 64-channel montage; future work will evaluate low-density configurations (e.g. 8–16 channels).

---

## 11. Reproducibility & Open Science Statement
All code, raw per-participant logs, summary tables, figures, and execution configurations are open-source under the MIT license at `https://github.com/JOYJIT-06/LeakCheck.git`. Release artifacts for version `1.1.0` are packaged as standalone wheels and archived under `benchmark_results/physionet_v1_1/`.
