# LeakCheck V2 Benchmark Pre-Registration Template

*This protocol serves as a formal template for prospective benchmarking studies evaluating EEG leakage mechanisms and validation protocols across multi-dataset and multi-session corpora.*

---

## 1. Study Information
- **Title**: Prospective Auditing of Data Leakage and Validation Protocols in Non-Invasive BCI Machine Learning.
- **Authors & Affiliations**: LeakCheck Research Engineering Group.
- **Software Repository**: `https://github.com/JOYJIT-06/LeakCheck.git` (Version: `1.1.0+`).
- **Preregistration Date**: November 2026.

---

## 2. Hypotheses and Primary Contrasts

### Hypothesis 1 (Cross-Run Non-Stationarity vs. Random Partitioning)
- **Primary Contrast**: `D1s_size_matched` vs. `D3_loro`.
- **Direction**: In multi-run EEG motor imagery benchmarks, random trial partitioning across runs will exhibit a negative performance difference (deflation) relative to leave-one-run-out evaluation, due to inter-run non-stationarity and disrupted contiguous background dynamics.
- **Confirmatory Metric**: Hodges-Lehmann median difference $\Delta_{\text{HL}}$ and $95\%$ BCa confidence interval.

### Hypothesis 2 (Spatial Filter Contamination Dominance)
- **Primary Contrast**: `P1_csp_on_all` vs. `D3_loro`.
- **Direction**: Fitting supervised spatial filters (CSP) across all data prior to partitioning will result in massive positive performance inflation ($\Delta_{\text{HL}} > +20.0$ pp, $d_z > 1.5$, $p < 10^{-10}$), completely obscuring genuine brain-computer interface signal decodability.

### Hypothesis 3 (Negative Control Integrity)
- Under label permutation (`perm`) and circular label shift (`shift`), clean validation designs (`D3_loro`) will yield false positive rates bounded by nominal $\alpha = 0.05$.

---

## 3. Data Scope & Technical Exclusion Criteria

### Included Datasets
1. **PhysioNet EEG Motor Movement/Imagery**: 109 subjects, 64 channels, 160 Hz (runs 4, 8, 12).
2. **OpenBMI (Lee et al. 2019)**: 54 subjects, 62 channels, session-1 motor imagery.

### Explicit Exclusion Rules (Fixed in Advance)
Participants are excluded *solely* on technical quality criteria, never on decoding accuracy:
1. Fewer than 30 total valid trials kept after artifact rejection.
2. Fewer than 10 valid trials in either motor imagery class.
3. Any run containing fewer than 8 trials or containing only one class.
4. Fewer than 3 recording runs available for leave-one-run-out evaluation.
5. Incomplete or truncated download files (e.g. OpenBMI subjects 1, 4, 11, 40, 41).

---

## 4. Analysis Pipeline Specifications

- **Preprocessing**: Bandpass filtering (1–40 Hz), bad channel detection via robust variance/correlation outliers ($z > 4.0$), average rereferencing, ICA ocular artifact removal (maximum 2 components).
- **Epoching**: Cue onset to +4.0 s; decoding analysis window +1.0 s to +3.0 s.
- **Decoders**:
  1. `csp_lda`: 4 Common Spatial Pattern components regularized via OAS covariance + Linear Discriminant Analysis (LSQR solver).
  2. `csp_lr`: 4 CSP components + Logistic Regression ($C = 1.0$).
  3. `ts_lr`: Normalized covariance estimation + Riemannian tangent space projection + Logistic Regression ($C = 1.0$).
- **Statistical Tests**: Paired Hodges-Lehmann median difference, $95\%$ BCa bootstrap confidence interval (2,000 resamples), Wilcoxon signed-rank test with Holm-Bonferroni correction, Two One-Sided Tests (TOST) against $\pm 2.0$ pp equivalence bounds.
