# Auditing Validation Design and Preprocessing Contamination in Motor-Imagery EEG: A Two-Dataset Empirical Study

**Author:** Joyjit Das  
**Working draft:** 0.1 — 11 November 2026  
**Repository:** https://github.com/JOYJIT-06/LeakCheck

> Working Markdown draft, not a submission-ready or submitted preprint. Reported values are copied from the participant-level summary artifacts and must be independently recomputed before submission.

## Abstract
Validation design and preprocessing choices can alter reported motor-imagery EEG decoding performance. We report participant-level paired comparisons in PhysioNet EEGMMIDB (105 completed participants) and OpenBMI Session 1 (34 intact participants). In PhysioNet, supervised global Common Spatial Patterns (CSP) fitting produced a Hodges–Lehmann (HL) difference of +24.50 percentage points (pp) relative to leave-one-run-out (LORO; 95% BCa CI [22.22,27.78] pp; Holm-adjusted p=4.43×10⁻¹⁸). Size- and class-matched random partitioning (D1s) differed from LORO by −2.68 pp (95% BCa CI [−3.95,−1.47]; adjusted p=5.86×10⁻⁵); matched-k random partitioning (D1m) differed by −4.47 pp (95% BCa CI [−5.83,−3.14]; adjusted p=1.08×10⁻⁸). In OpenBMI, D1s-minus-LORO was +2.84 pp for CSP-LDA (95% BCa CI [1.46,4.98]; adjusted p=1.87×10⁻⁴) and +2.94 pp for TS-LR (95% BCa CI [1.66,4.51]; adjusted p=1.94×10⁻⁴). Supervised global CSP P1 produced +6.25 pp for CSP-LDA (95% BCa CI [3.25,8.23]; adjusted p=1.87×10⁻⁴). A separate TS-LR control that fitted a global tangent-space reference and scaler without labels produced +0.75 pp (95% BCa CI [0.25,1.50]; p=0.0203); it is not supervised P1. D1s effect directions differed across datasets, so random trial splitting cannot be characterized as universally optimistic or pessimistic relative to LORO. Conclusions are limited to these cohorts, tasks and pipelines.

## 1. Introduction
EEG decoding studies rely on validation procedures to estimate generalization. Data-dependent transformations such as CSP must be fitted inside the training partition. Trial-shuffled and run-held-out designs estimate different forms of generalization, and differences in training size/class balance can confound their comparison. This study reports size/class-matched random-versus-LORO contrasts separately from deliberately contaminated preprocessing controls.

## 2. Methods
### 2.1 Cohorts
PhysioNet: 109 requested, 105 completed; 64 channels, 160 Hz, runs 4, 8 and 12, OAS CSP-LDA. Run artifact exclusions: subjects 44,69,91 missing cache files; subject 86 had 24 trials (<30).
OpenBMI: 34 intact Session 1 participants; 62 channels, 200 trials (100/class), native 1000 Hz resampled to 250 Hz; half-open epochs [−0.5,4.0) s, run-isolated 8–30 Hz FIR, baseline [−0.5,0) s, 150 μV non-destructive artifact flag.
### 2.2 Designs and contamination
D3 is LORO. D1s pools trials while matching D3 fold sample sizes and class counts. D1m is matched-k random partitioning in PhysioNet. CSP-LDA P1 fits supervised CSP using all trials and labels before splitting, while the classifier is trained on training-fold features only. OpenBMI TS-LR's historical global-reference condition fits a tangent-space reference and scaler across all trials without labels; it is a distinct unsupervised control (T1), not P1.
### 2.3 Statistics
Participant is the independent unit. Repeated folds are aggregated within participant. Differences are percentage points. HL pseudo-median, 95% BCa CI, two-sided Wilcoxon signed-rank p-values with Holm adjustment, and Cohen's dz are reported.

## 3. Results

### 3.1 PhysioNet
| Contrast | N | Mean pp | Median pp | HL pp | 95% BCa CI pp | Raw p | Holm p | dz |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| P1 global CSP−D3 |105|+24.815|+23.256|+24.503|[22.222,27.778]|1.477e−18|4.431e−18|1.771|
| D1s−D3 |105|−2.771|−2.614|−2.677|[−3.946,−1.471]|5.859e−5|5.859e−5|−0.449|
| D1m−D3 |105|−4.666|−4.000|−4.470|[−5.835,−3.136]|5.413e−9|1.083e−8|−0.685|

The V1.1 summary records n_null=0; no null-model inference is claimed.

### 3.2 OpenBMI
| Contrast | N | Mean pp | Median pp | HL pp | 95% BCa CI pp | Raw p | Holm p | dz |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| CSP-LDA P1 global CSP−D3 |34|+5.603|+7.000|+6.250|[3.250,8.229]|1.466e−4|1.872e−4|0.745|
| CSP-LDA D1s−D3 |34|+3.372|+1.850|+2.837|[1.463,4.975]|9.359e−5|1.872e−4|0.751|
| TS-LR D1s−D3 |34|+3.110|+2.488|+2.938|[1.663,4.513]|9.722e−5|1.944e−4|0.771|
| TS-LR T1 global reference/scaling−D3 |34|+0.853|+0.500|+0.750|[0.250,1.500]|0.02029|0.02029|0.417|

The TS-LR T1 control is not supervised CSP P1. Existing OpenBMI CSVs and figures require relabeling and hash refresh before final citation.

## 4. Discussion
Supervised global CSP fitting produced substantial positive performance differences in the evaluated CSP-LDA configurations. D1s-minus-D3 was negative in PhysioNet and positive in OpenBMI. This dataset-dependent direction cautions against universal claims about random-split bias. The TS-LR global-reference/scaling control showed a smaller shift than CSP-LDA P1, but is a different, unsupervised contamination pathway. The results do not establish general immunity or general susceptibility for all Riemannian methods.

## 5. Limitations
1. Full-cohort empirical evidence is limited to these two datasets; OpenBMI is Session 1 only.
2. Both benchmark manifests record emi 1.1.0, while the development source declares 2.0.0.dev0. A rerun under the exact final V2 commit is needed before claiming results were generated by final V2.
3. PhysioNet V1.1 has n_null=0.
4. P2 continuous ICA is not integrated as specified; P8 lacks a separate global contaminated comparator; P9 is not a distinct injection. P3–P7 have synthetic probes and naming/alias conflicts.
5. Electrode drift and operational-state explanations are hypotheses, not directly measured causes.
6. The manuscript and figures need final independent reconciliation and review. No prospective preregistration is claimed.

## 6. Conclusion
In the evaluated cohorts, supervised global CSP fitting produced substantial positive differences, while the direction of size-matched random-versus-LORO differences varied by dataset. The evidence supports a focused two-dataset preprint after independent recalculation, output relabeling, CI verification and manuscript review; it does not support claiming all proposed leakage mechanisms or registry datasets are scientifically validated.
