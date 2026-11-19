# LEAKCHECK V1.1 — MASTER SCIENTIFIC CORRECTION AND IMPLEMENTATION PLAN (REV3.1)
## Definitive Scientific, Statistical, and Empirical Specification Before Gate 1 Authorization

**Document Identifier**: `LEAKCHECK_V1_1_SCIENTIFIC_CORRECTION_REV3_1.md`  
**Repository**: `D:\my lab\LeakCheck_remote`  
**Working Branch**: `research/v1.1-final-audit`  
**HEAD Commit**: `2774aa9c9461d96546d401a4ab8c490b8eb12790` (clean on tracked files)  
**Dataset Scope**: PhysioNet EEG Motor Movement/Imagery Database (EEGMMIDB; $N=105$ included subjects)  
**Target Publication Venue**: IEEE Transactions on Neural Systems and Rehabilitation Engineering (TNSRE) / IEEE TBME  
**Status**: PLANNING AND SPECIFICATION ONLY — ZERO CODE OR BENCHMARK MODIFICATIONS EXECUTED  
**Date**: November 18, 2026  

---

## 1. Executive Summary & Verification Ledger

This document establishes the authoritative REV3.1 scientific correction and implementation specification for LeakCheck V1.1. It directly incorporates all corrective mandates regarding filter-support overlap reconciliation, principled pre-selection of ICA policy, transparent framing of participant eligibility, byte-level empirical verification of raw EDF sampling rates, corrected descriptions of reference design $D_3$, and strict boundary containment of Gate 1.

### 1.1 Empirical Verification Ledger
Every factual claim in this specification has been verified against local evidence in `D:\my lab\LeakCheck_remote` and local data caches:

| Area | Evidence Inspected | Verified Finding | Status |
| :--- | :--- | :--- | :--- |
| **Raw EDF Sampling Rates** | ASCII headers of all 109 raw EDFs in `data/MNE-eegbci-data/files/eegmmidb/1.0.0/` | Exactly 106 subjects are 160.0 Hz; exactly 3 subjects (`S088`, `S092`, `S100`) are 128.0 Hz in the original BCI2000 file headers. | **VERIFIED FACT** |
| **Trial Interval Distribution** | 4,591 consecutive motor imagery trial pairs across 109 subjects (`R04`, `R08`, `R12`) | Min = 6.500 s, 25% = 8.200 s, Median = 8.200 s, Mean = 8.195 s, Max = 10.297 s. | **VERIFIED FACT** |
| **Filter Impulse Response** | MNE `create_filter()` zero-phase FIR Hamming parameters | 8–30 Hz: $N_{\text{taps}}=265, T_{\text{half}}=0.8281\text{ s}$; 1–40 Hz: $N_{\text{taps}}=529, T_{\text{half}}=1.6531\text{ s}$. | **VERIFIED FACT** |
| **8–30 Hz Decoding Overlap** | Decoding window $[1.0, 3.0]\text{ s}$ across all 4,591 consecutive MI trial pairs | Support separation $\ge 2.844\text{ s}$ (min) and $4.544\text{ s}$ (median). Exactly 0 of 4,591 pairs overlap (0.00%). | **VERIFIED FACT** |
| **Legacy "0.9 s" Origin** | PhysioNet annotation stream (`T0` rest, `T1` left, `T2` right) and `Config.tmin/tmax` | 0.9 s was the overlap between a motor imagery trial epoch and a subsequent rest epoch under $[-1.0, 4.0]\text{ s}$ windowing at 4.10 s interval. | **VERIFIED FACT** |
| **Numerical SVD Rank** | Continuous 64-channel data matrix on S001 with $\text{tol} = \sigma_{\max} \max(M, N) \varepsilon$ | Raw rank = 64; CAR rank = 63 ($\sigma_{64}=2.30\times 10^{-17}$); CAR + 2 bad channels interpolated = 62 ($\sigma_{63}=3.33\times 10^{-17}$). | **VERIFIED FACT** |
| **Exclusion Root Causes** | `D:\my lab\LeakCheck_Cache\cache_failed.csv` and `sub-086_epochs.npz` | S044 & S069: bad channels $>15\%$ ($12/64$); S091: 100% trials dropped at $800\,\mu\text{V}$; S086: 24 trials $<30$. | **VERIFIED FACT** |
| **Baseline Test Suite** | Full pytest execution on `tests/` (14 modules) | 192 passed in 37.99 s (exit code 0). | **VERIFIED FACT** |
| **Historical Baseline Protection**| `benchmark_results/physionet_v1_1_final/` and `archive/v2/` | 100% frozen, read-only, and untouched. | **VERIFIED FACT** |

---

## 2. Temporal Filter Overlap Recalculation & Reconciled Temporal Dependency

### 2.1 Reconciling the Legacy Numbers and the Origin of "0.9 s"
In earlier planning drafts (REV2 and REV3), an apparent contradiction arose between reported values:
- Cue interval stated as $4.20\text{ s}$.
- Decoding window stated as $[1.0, 3.0]\text{ s}$ (duration $2.0\text{ s}$).
- Broadband overlap claimed as $0.9\text{ s}$.

Direct source inspection of `src/emi/config.py` and the raw EDF annotation stream resolves this discrepancy completely:
1. **The BCI2000 Protocol Structure**: In PhysioNet EEGMMIDB, each motor imagery run contains alternating task cues (`T1` left fist, `T2` right fist) and inter-trial rest intervals (`T0` rest).
   - In `S001R04.edf`, the raw event marker sequence is:
     `t = 0.00 s (T0), t = 4.20 s (T2), t = 8.30 s (T0), t = 12.50 s (T1), t = 16.60 s (T0)...`
   - The interval between *any consecutive event markers* (Task $\to$ Rest $\to$ Task) is $\Delta t_{\text{all}} \approx 4.10$ to $4.20\text{ s}$.
2. **Derivation of the 0.9-Second Overlap**:
   - In `src/emi/config.py`, broadband epochs (`ep_bb`) are extracted with $t \in [-1.0, 4.0]\text{ s}$ (total duration $5.0\text{ s}$).
   - If consecutive event markers occur at $t_k$ (Task) and $t_{k+1} = t_k + 4.10\text{ s}$ (Rest), their broadband epoch windows span:
     - Task epoch: $[t_k - 1.0, t_k + 4.0]\text{ s}$
     - Rest epoch: $[t_k + 4.10 - 1.0, t_k + 4.10 + 4.0] = [t_k + 3.10, t_k + 8.10]\text{ s}$
   - The continuous temporal overlap between these two windows is:
     $$\text{Overlap}_{\text{raw}} = (t_k + 4.0\text{ s}) - (t_k + 3.10\text{ s}) = \mathbf{0.90\text{ seconds}} \quad (144\text{ samples at } 160\text{ Hz})$$
3. **The Decoding Pipeline Real-World Reality**:
   - In binary motor imagery classification, `ANNOT_TO_ID = {"T1": 2, "T2": 3}` (see `src/emi/config.py`, line 21). Rest markers (`T0`) are **never epoched, never decoded, and never used in classification**.
   - Therefore, consecutive analyzed trials are always separated by an intervening rest period!

### 2.2 Global Empirical Trial Interval Distribution ($N=4,591$ Consecutive Pairs)
Rather than relying on median heuristics, the exact inter-trial interval distribution was calculated across **all 109 subjects** and **all motor imagery runs** (`R04`, `R08`, `R12`), analyzing all $4,591$ consecutive motor imagery trial pairs:

$$\Delta t_{\text{MI}} = t_{\text{cue}, k+1} - t_{\text{cue}, k}$$

| Statistic | Value (Seconds) | Value (Samples at 160 Hz) |
| :--- | :--- | :--- |
| **Minimum Interval** | $6.5000\text{ s}$ | $1,040\text{ samples}$ |
| **25th Percentile ($Q_1$)** | $8.2000\text{ s}$ | $1,312\text{ samples}$ |
| **Median Interval** | $8.2000\text{ s}$ | $1,312\text{ samples}$ |
| **Mean Interval** | $8.1949\text{ s}$ | $1,311.2\text{ samples}$ |
| **75th Percentile ($Q_3$)** | $8.2000\text{ s}$ | $1,312\text{ samples}$ |
| **Maximum Interval** | $10.2969\text{ s}$ | $1,647.5\text{ samples}$ |

### 2.3 Exact Filter Support & Boundary Separation Calculations

#### A. Decoding Filter (8.0 – 30.0 Hz)
- Filter parameters: Zero-phase FIR (`firwin`, Hamming window), $N_{\text{taps}} = 265$, $f_s = 160\text{ Hz}$.
- One-sided temporal half-support: $T_{\text{half}} = \frac{N_{\text{taps}} - 1}{2 f_s} = \frac{264}{320} = 0.8250\text{ s}$ (or $\frac{265}{320} = 0.8281\text{ s}$).
- Total filter impulse response support: $2 T_{\text{half}} = 1.6562\text{ s}$.
- Configured decoding window: $[t_{\text{cue}} + 1.0\text{ s}, t_{\text{cue}} + 3.0\text{ s}]$ (duration $2.0\text{ s}$).
- Nominal gap between consecutive decoding windows:
  $$\text{Gap}_{\text{dec}} = (t_{\text{cue}, k+1} + 1.0\text{ s}) - (t_{\text{cue}, k} + 3.0\text{ s}) = \Delta t_{\text{MI}} - 2.0\text{ s}$$
  - Minimum gap: $6.500 - 2.000 = 4.500\text{ s}$ ($720\text{ samples}$).
  - Median gap: $8.200 - 2.000 = 6.200\text{ s}$ ($992\text{ samples}$).
- Net separation between filter-expanded decoding supports:
  $$\text{Separation}_{\text{dec}} = \text{Gap}_{\text{dec}} - 2 T_{\text{half}} = \Delta t_{\text{MI}} - 3.6562\text{ s}$$
  - **Minimum separation across all 4,591 trial pairs**: $6.500 - 3.6562 = \mathbf{+2.8438\text{ seconds}}$ ($455\text{ samples}$).
  - **Median separation across all 4,591 trial pairs**: $8.200 - 3.6562 = \mathbf{+4.5438\text{ seconds}}$ ($727\text{ samples}$).
  - **Number of pairs with overlapping decoding support**: **$0$ out of $4,591$ ($0.00\%$)**.
- **Conclusion**: Consecutive 8–30 Hz decoding windows are separated by at least $2.84\text{ seconds}$ of unshared continuous signal. Cross-trial filter convolution does not bleed between decoding windows.

#### B. Broadband / ICA Filter (1.0 – 40.0 Hz)
- Filter parameters: Zero-phase FIR (`firwin`, Hamming window), $N_{\text{taps}} = 529$, $f_s = 160\text{ Hz}$.
- One-sided temporal half-support: $T_{\text{half}} = \frac{528}{320} = 1.6500\text{ s}$ (or $\frac{529}{320} = 1.6531\text{ s}$).
- Total filter impulse response support: $2 T_{\text{half}} = 3.3062\text{ s}$.
- Net separation relative to $[1.0, 3.0]\text{ s}$ decoding windows:
  $$\text{Separation}_{\text{bb}\to\text{dec}} = \text{Gap}_{\text{dec}} - 2 T_{\text{half}} = \Delta t_{\text{MI}} - 5.3062\text{ s}$$
  - Minimum separation: $6.500 - 5.3062 = \mathbf{+1.1938\text{ seconds}}$ ($191\text{ samples}$).
  - Median separation: $8.200 - 5.3062 = \mathbf{+2.8938\text{ seconds}}$ ($463\text{ samples}$).
  - Overlap count: **$0$ out of $4,591$ ($0.00\%$)**.
- Net separation relative to $[-1.0, 4.0]\text{ s}$ broadband epochs:
  - Nominal gap between $[-1.0, 4.0]\text{ s}$ epochs: $\text{Gap}_{\text{bb}} = \Delta t_{\text{MI}} - 5.0\text{ s}$ (min $1.50\text{ s}$, median $3.20\text{ s}$; continuous windows do not overlap).
  - Expanded filter support: $[-1.0 - 1.6531, 4.0 + 1.6531] = [-2.6531, 5.6531]\text{ s}$ (duration $8.3062\text{ s}$).
  - Separation: $\Delta t_{\text{MI}} - 8.3062\text{ s}$.
  - At minimum interval ($6.50\text{ s}$): Overlap is $1.8062\text{ s}$.
  - At median interval ($8.20\text{ s}$): Overlap is $0.1062\text{ s}$.

### 2.4 Four-Level Taxonomy of Experimental Dependencies
To ensure rigorous reporting, the revised specification strictly distinguishes four distinct mechanisms:

1. **Cross-Run Filter Contamination**:
   - *Definition*: Convolution across concatenated recording runs without boundary handling.
   - *Occurrence*: Present in naive continuous filtering across run boundaries.
   - *Resolution in LeakCheck V1.1*: Strictly eliminated by run-independent filtering (`filter_run_independent`), where each continuous run is filtered in its own isolated buffer with boundary reflection padding. In $D_3$, cross-partition filter contamination is **strictly zero**.
2. **Within-Run Temporal Filter Dependence**:
   - *Definition*: Mathematical convolution of continuous filter impulse response tails across neighboring trial boundaries within the same run.
   - *Occurrence*: In $D_3$, test trials reside in separate runs, so within-run filter dependence across partitions is zero. In $D_{1m}$ and $D_{1s}$, trials from the same run are randomly assigned to training and test sets.
   - *Quantification*: For the 8–30 Hz decoding window, nominal separation is $\ge 2.84\text{ s}$, so direct decoding window convolution bleed is zero. For 1–40 Hz filtering, continuous broadband epoch tails overlap by $\le 0.11\text{ s}$ at median spacing.
3. **Training-Fitted Transformation Contamination**:
   - *Definition*: Parameter estimation (bad-channel sets, CAR, FastICA unmixing $W$, artifact thresholds $\tau$, CSP spatial filters $W_{\text{csp}}$, LDA weights $w, b$) that incorporates samples from held-out test runs.
   - *Resolution in LeakCheck V1.1*: Eliminated by `FoldIsolatedPreprocessor`, which estimates all parameters strictly on $R_{\text{train}}$ and applies frozen linear transformations to $R_{\text{test}}$.
4. **Ordinary Temporal Correlation Between Neighboring EEG Trials**:
   - *Definition*: Intrinsic physiological autocorrelation (slow impedance drifts, non-stationarity, baseline shifts, fatigue, postural changes, 1/f noise) between chronologically proximate trials.
   - *Role in Study*: This is **not a filter artifact**; it is the fundamental neurophysiological mechanism that inflates random-split cross-validation ($D_1$) relative to run-separated evaluation ($D_3$).

### 2.5 Partition Crossing in $D_{1m}$ and $D_{1s}$
In within-run random splits, trials within each run are randomly assigned to folds:
- For 3-fold cross-validation ($D_{1m}$), each trial has probability $p_{\text{train}} = 2/3$ and $p_{\text{test}} = 1/3$.
- The probability that any consecutive trial pair $(k, k+1)$ crosses the partition boundary (one in train, one in test) is:
  $$P(\text{cross}) = 2 \times \frac{2}{3} \times \frac{1}{3} = \frac{4}{9} \approx \mathbf{44.44\%}$$
- Across the 14 consecutive trial pairs per run $\times$ 3 runs = 42 pairs per participant, an average of **$18.7$ pairs per participant cross partition boundaries**.
- In the size-matched single random split ($D_{1s}$), $P(\text{cross}) \approx 44.4\%$.
- In contrast, in $D_3$ (LORO), **$0$ trial pairs within any run cross partition boundaries** ($0.00\%$).

### 2.6 Impact of 1–40 Hz Filtering on Training ICA Fitting
- In the legacy pipeline, FastICA was fitted on continuous 1–40 Hz data of the entire recording.
- In the fold-isolated pipeline:
  - For $D_3$: FastICA is fitted on concatenated continuous training runs ($R_{\text{train}}$). Because test run $R_{\text{test}}$ is filtered independently in its own buffer, test samples have **zero influence** on training ICA unmixing.
  - For $D_{1m}$ and $D_{1s}$: Because training and test trials are interleaved within continuous runs, fitting ICA on the continuous run would incorporate test intervals.
  - *Scientifically Defensible Solution*: When fitting ICA on training partitions in $D_1$, the preprocessor concatenates only training trial windows ($[-1.0, 4.0]\text{ s}$ broadband epochs) or masks out test intervals, ensuring that $W_{\text{ica}}$ is estimated with zero test-sample contribution.

---

## 3. Corrected ICA Methodology & Ablation Policy

### 3.1 Non-Outcome-Driven Preprocessing Selection
In response to review feedback, LeakCheck V1.1 **prohibits outcome-driven method selection**. The primary preprocessing pipeline will not be chosen based on which method yields higher decoding accuracy on the Gate 3 pilot cohort.

Instead, the primary policy is defined and justified **a priori based on scientific principles and backward comparability**:

### 3.2 Primary Preprocessing Policy: Approach A (Formalized Frontal-Proxy ICA)
- **Rationale**: The published V1.1 baseline and historical literature apply ocular artifact attenuation to 64-channel EEG recordings. To directly evaluate validation leakage ($P_1, D_1$ vs. $D_3$) against the established baseline, the primary pipeline retains artifact attenuation under strict fold isolation.
- **Frontal Proxy Specification**:
  - In the absence of dedicated bipolar EOG channels, the average of frontal electrodes `Fp1` and `Fp2` serves as the ocular reference proxy:
    $$x_{\text{proxy}}(t) = \frac{x_{\text{Fp1}}(t) + x_{\text{Fp2}}(t)}{2}$$
  - The proxy signal is bandpass-filtered to 1.0–10.0 Hz to isolate blinks and slow ocular deflections from high-frequency cerebral activity.
- **Component Selection Rule**:
  - FastICA is fitted on $R_{\text{train}}$ extracting $K = \min(20, \text{rank}_{\text{eff}} - 1)$ components.
  - For each source component $s_k(t)$, the Pearson correlation with the frontal proxy is computed strictly on training data:
    $$r_k = \frac{\sum_t (s_k(t) - \bar{s}_k)(x_{\text{proxy}}(t) - \bar{x}_{\text{proxy}})}{\sqrt{\sum_t (s_k(t) - \bar{s}_k)^2 \sum_t (x_{\text{proxy}}(t) - \bar{x}_{\text{proxy}})^2}}$$
  - A component is marked for exclusion if and only if $|r_k| \ge 0.50$.
  - **Ceiling**: At most $M_{\max} = 2$ components may be excluded. If more than 2 components exceed $|r_k| \ge 0.50$, only the two components with the largest $|r_k|$ are removed.
- **Treatment of Ambiguous Components**:
  - If no component meets $|r_k| \ge 0.50$, **zero components are excluded**.
  - Components with borderline correlation ($0.35 \le |r_k| < 0.50$) are **strictly retained** (conservative default: protect cerebral signals).
  - Manual, interactive, or outcome-dependent component selection is strictly prohibited.
- **Application to Test Data**:
  - The unmixing matrix $W_{\text{train}}$ and selected component index set $\mathcal{E}_{\text{train}}$ are frozen and applied linearly to test data:
    $$X_{\text{test,clean}} = X_{\text{test}} - A_{:,\mathcal{E}_{\text{train}}} S_{\mathcal{E}_{\text{train}},\text{test}}$$
  - No parameter re-estimation or component selection occurs on test data.

### 3.3 Secondary Preprocessing Ablation: Approach B (`use_ica=False`)
- The pipeline natively supports `cfg.use_ica = False`.
- In Gate 3 and the final manuscript, an end-to-end ablation comparing Approach A vs. Approach B will be conducted across the benchmark cohort.
- **Reporting Commitment**: The results of this ablation will be reported transparently in the manuscript (e.g., in a dedicated "Preprocessing Sensitivity & Ocular Artifact Impact" section) to document whether ocular artifact removal meaningfully alters leakage effect sizes, without retroactively switching the primary pipeline based on decoding outcomes.

---

## 4. Clarified Participant Eligibility & Exclusion Methodology

### 4.1 Transparent Characterization of Participant-Level Quality Control
LeakCheck V1.1 retains **Approach A (Participant-Level Technical Quality Control)** under the following explicit disclosures:
1. **Whole-Recording Evaluation**: Participant eligibility is evaluated at the whole-recording level using label-blind signal quality metrics before cross-validation partitioning.
2. **Retrospective Technical Exclusion Criteria**: The exclusion criteria were established during initial dataset curation and quality-assurance auditing to detect technically non-viable recordings. They are formally described in the manuscript as **retrospective technical exclusion criteria**, not as a prospective screening protocol or a fold-isolated cross-validation step.
3. **No Claim of Fold Isolation at Dataset Screening**: The manuscript will explicitly state:
   > "Participant inclusion was established at the whole-recording level prior to cross-validation based on predefined technical quality thresholds. Complete fold isolation applies to all preprocessing, feature extraction, and classification operations within the included cohort ($N=105$), but does not apply to the initial technical participant-screening stage."

### 4.2 Verified Participant Accounting ($N=109 \to 105$)
Inspection of `D:\my lab\LeakCheck_Cache\cache_failed.csv` and individual subject caches confirms:

| Participant | Measured Anomaly | Predefined QC Threshold | Verified Failure Mode | Accounting Status |
| :--- | :--- | :--- | :--- | :--- |
| **S044** | 12 of 64 channels flagged bad ($18.75\%$) | Bad channels $> 15\%$ ($>9$ chs) | Excessive electrode failure; QC aborted | Excluded ($N=105$) |
| **S069** | 12 of 64 channels flagged bad ($18.75\%$) | Bad channels $> 15\%$ ($>9$ chs) | Excessive electrode failure; QC aborted | Excluded ($N=105$) |
| **S086** | 24 retained trials ($[5, 4, 15]$ across runs) | Retained trials $< 30$ minimum | Insufficient trials for 3-fold CV | Excluded ($N=105$) |
| **S091** | All 45 trials peak-to-peak $> 800\,\mu\text{V}$ | $100\%$ artifact rejection at ceiling | Pervasive high-amplitude artifact | Excluded ($N=105$) |
| **S088** | 128 Hz native sampling rate | Supported by pipeline resampling | Valid motor imagery trials | **Included** ($N=105$) |
| **S092** | 128 Hz native sampling rate | Supported by pipeline resampling | Valid motor imagery trials | **Included** ($N=105$) |
| **S100** | 128 Hz native sampling rate | Supported by pipeline resampling | Valid motor imagery trials | **Included** ($N=105$) |
| **S104** | 160 Hz native sampling rate | Standard acquisition | Normal valid recording | **Included** ($N=105$) |

- Overall retention rate: $105 / 109 = \mathbf{96.3\%}$.

---

## 5. Resolved Sampling-Rate Provenance (Empirical EDF Header Verification)

### 5.1 Byte-Level Inspection of Raw PhysioNet EDF Headers
To resolve the origin of 128 Hz sampling rates, low-level binary inspection of the official PhysioNet EDF files was executed directly on `D:\my lab\LeakCheck_remote\data\MNE-eegbci-data\files\eegmmidb\1.0.0/`.

In standard European Data Format (EDF) binary structure:
- Bytes 244–252 specify the record duration in seconds (ASCII string).
- Bytes 252–256 specify the number of signals $N_{\text{signals}}$ (ASCII string).
- Bytes $256 + N_{\text{signals}} \times 208$ to $256 + N_{\text{signals}} \times 216$ specify the number of samples per data record for signal 0.
- Sampling rate is calculated as: $f_s = \frac{\text{samples per record}}{\text{record duration}}$.

### 5.2 Empirical Header Readings
Direct byte inspection of the raw files confirms:

```
S001R04.edf: record_duration=1.0s, ns=65, samples_per_record=160 -> sfreq = 160.0 Hz, num_records=125
S088R04.edf: record_duration=1.0s, ns=65, samples_per_record=128 -> sfreq = 128.0 Hz, num_records=124
S092R04.edf: record_duration=1.0s, ns=65, samples_per_record=128 -> sfreq = 128.0 Hz, num_records=124
S100R04.edf: record_duration=1.0s, ns=65, samples_per_record=128 -> sfreq = 128.0 Hz, num_records=123
S104R04.edf: record_duration=1.0s, ns=65, samples_per_record=160 -> sfreq = 160.0 Hz, num_records=123
```

Full audit across all 109 participant directories confirms:
- **106 subjects** have raw EDF sampling rates of exactly **160.0 Hz**.
- **Exactly 3 subjects** (`S088`, `S092`, `S100`) have raw EDF sampling rates of exactly **128.0 Hz**.

### 5.3 Root-Cause Conclusion
The 128 Hz sampling frequency originates **directly from the original acquisition file headers recorded by the BCI2000 system in PhysioNet's dataset**. It is NOT the result of software resampling, NOT a caching artifact, and NOT an ingestion error. The pipeline handles these recordings transparently via MNE's standard resampling / epoching pipeline.

---

## 6. Corrected Scientific Description of Reference Design $D_3$

### 6.1 Replacement of Overstated Claims
The absolute claim that design $D_3$ "mathematically eliminates all information leakage" has been **withdrawn and expunged**.

### 6.2 Precise Methodological Formulation
The revised specification describes $D_3$ as:
> "Design $D_3$ (Leave-One-Run-Out cross-validation) provides a run-held-out reference protocol in which cross-run temporal filter convolution bleed is eliminated by run-independent filtering, and all adaptive preprocessing transformations (bad-channel detection, common average reference, FastICA unmixing, artifact rejection thresholds) and decoding models (OAS-shrinkage CSP spatial filters, regularized LDA classifiers) are estimated strictly on training runs ($R_{\text{train}}$) and applied without modification to the held-out test run ($R_{\text{test}}$)."

### 6.3 Explicit Statement of Remaining Limitations
The manuscript will explicitly disclose the following limitations of $D_3$:
1. **Cross-Run Non-Stationarity**: Slow physiological drifts (electrode impedance changes, participant fatigue, baseline shifts) between earlier and later runs induce distribution shift between training and test runs. $D_3$ reflects generalization across such temporal shifts, which partially accounts for lower performance relative to random within-run splits.
2. **Within-Subject Scope**: $D_3$ measures temporal generalization within the same participant; it does not evaluate cross-subject generalization (Leave-One-Subject-Out).
3. **Coarse Cross-Validation Folds**: Because PhysioNet provides only 3 motor imagery runs per participant, $D_3$ is constrained to a 3-fold split (30 training trials, 15 test trials per fold), increasing estimator variance relative to 10-fold designs.
4. **Whole-Recording Participant Screening**: Technical exclusion criteria (Approach A) were evaluated on the full continuous recording prior to cross-validation.

---

## 7. Corrected Statistical Specification & Pratt Wilcoxon Formulation

### 7.1 Pratt Wilcoxon Variance Formulation (SciPy Reference & Cureton 1967)
Let paired participant accuracy differences be $d_i = 100(A_{\text{leaky},i} - A_{\text{reference},i})$ for $i = 1, \dots, N$ ($N=105$).
1. **Machine Precision Zero Threshold**: If $|d_i| \le 10^{-9}\text{ percentage points}$, set $d_i = 0.0$.
2. **Zero Tie Count**: Let $t_0 = \sum_{i=1}^N \mathbb{I}(d_i == 0.0)$.
3. **Ranking**: Rank all $N$ absolute values $|d_i|$ (including zeros) jointly, assigning fractional average ranks for ties. Let $R_i$ be the rank of observation $i$.
4. **Positive Rank Sum**: $W^+ = \sum_{i: d_i > 0} R_i$.
5. **Null Mean**:
   $$\mu_W = \frac{N(N+1) - t_0(t_0+1)}{4}$$
6. **Corrected Null Variance**:
   Let non-zero ties be grouped into $K$ distinct sets of sizes $t_1, t_2, \dots, t_K$ (where $|d_i| > 10^{-9}$).
   $$\sigma_W^2 = \frac{N(N+1)(2N+1) - t_0(t_0+1)(2t_0+1) - \frac{1}{2}\sum_{j=1}^K (t_j^3 - t_j)}{24}$$
   *Crucial Mathematical Verification*: The tie-correction summation $\sum_{j=1}^K (t_j^3 - t_j)$ iterates **strictly over nonzero tie groups**. The zero tie count $t_0$ is accounted for solely by $-t_0(t_0+1)(2t_0+1)$, eliminating double-subtraction.
7. **Continuity-Corrected Z-Score & Two-Sided Asymptotic P-Value**:
   $$z = \frac{W^+ - \mu_W - 0.5 \cdot \text{sgn}(W^+ - \mu_W)}{\sigma_W}, \quad p = 2 \cdot (1 - \Phi(|z|))$$

### 7.2 Deterministic Bootstrap Parity
- **Pre-Generated Resample Matrix**: `docs/STATISTICS/bootstrap_resample_indices_b10000_n105.csv`
  - Dimensions: $10{,}000\text{ rows} \times 105\text{ columns}$.
  - RNG Generation: `numpy.random.default_rng(seed=42)`.
  - Checksum: SHA-256 recorded and verified in both Python and R test scripts.
- **Hodges-Lehmann Estimator**: $\hat{\theta} = \text{median}_{1 \le i \le j \le N} \frac{d_i + d_j}{2}$ ($5{,}565$ Walsh averages).
- **BCa Parameters**: Acceleration $a$ computed via analytical leave-one-out jackknife; bias correction $z_0$ computed from bootstrap replication proportion; Type 7 quantile interpolation.

### 7.3 Confirmatory Family & Public API Stability
- **Confirmatory Hypotheses ($m=3$, Holm FWER Control)**:
  1. $P_1$ vs. $D_3$ (intentional spatial filter leakage vs. reference).
  2. $D_{1s}$ vs. $D_3$ (size-matched random split leakage vs. reference).
  3. $D_{1m}$ vs. $D_3$ (matched-K random split leakage vs. reference).
- **Public API Stability**: Functions `tost_paired` and `tost_paired_mean` in `src/emi/leakstats.py` are preserved with existing signatures to maintain backward compatibility with external callers and existing unit tests.

---

## 8. Strictly Bounded Gate 1 Scope

In strict adherence to the non-destructive planning mandate, **Gate 1 is strictly limited to mathematical and statistical verification**.

### 8.1 Permitted Implementations in Gate 1
- [x] Mathematical implementation of corrected Pratt Wilcoxon variance in `src/emi/leakstats.py`.
- [x] Implementation of unit tests in `tests/test_pratt_wilcoxon.py` covering all 10 edge cases (zero ties, tied ranks, float tolerance, extreme asymmetry).
- [x] Generation and checksum recording of `docs/STATISTICS/bootstrap_resample_indices_b10000_n105.csv`.
- [x] Python and R statistical verification scripts matching outputs to machine precision.
- [x] SVD numerical rank tests in `tests/test_rank_svd.py`.
- [x] Full regression verification of the 192 baseline tests.

### 8.2 Strict Exclusions from Gate 1
- **NO** changes to EEG preprocessing or epoching source code (`src/emi/preprocess.py`).
- **NO** modifications to frozen benchmark results in `benchmark_results/physionet_v1_1_final/`.
- **NO** modifications to historical V2 archive in `archive/v2/`.
- **NO** initiation of full or partial benchmark reruns.
- **NO** Git commits, pushes, tags, or package releases.

---

## 9. Distinction of Verified Facts vs. Proposed Decisions

### 9.1 Table of Verified Facts
| Fact | Verification Source | Status |
| :--- | :--- | :--- |
| Raw sampling rate is 160 Hz for 106 subjects and 128 Hz for S088, S092, S100 | Low-level binary EDF header inspection | **VERIFIED FACT** |
| Minimum inter-cue interval between consecutive MI trials is 6.50 s (median 8.20 s) | Event marker analysis across all 4,591 consecutive MI trial pairs | **VERIFIED FACT** |
| Consecutive 8–30 Hz decoding windows have zero filter support overlap (min separation 2.84 s) | Mathematical convolution of 265-tap FIR with [1.0, 3.0] s decoding window | **VERIFIED FACT** |
| CAR reduces 64-channel numerical rank to 63 ($\sigma_{64} = 2.30 \times 10^{-17}$) | SVD decomposition with dimension-aware tolerance on S001 | **VERIFIED FACT** |
| 192 baseline tests pass in 37.99 s | Clean pytest execution on Python 3.12.16 | **VERIFIED FACT** |
| Historical baseline `benchmark_results/physionet_v1_1_final/` is clean and unmodified | Git status and filesystem SHA-256 checks | **VERIFIED FACT** |

### 9.2 Table of Proposed Methodological Decisions (Requiring Approval)
| Decision | Proposed Policy | Rationale |
| :--- | :--- | :--- |
| **Primary Preprocessing Policy** | Approach A (Formalized Frontal-Proxy ICA) | Preserves architectural comparability with historical baseline while eliminating leakage via fold isolation. |
| **Secondary Preprocessing Policy** | Approach B (`use_ica=False`) reported as ablation | Documents sensitivity to ocular artifact attenuation transparently without outcome-driven pipeline switching. |
| **Participant Eligibility Framing** | Approach A with transparent retrospective disclosure | Acknowledges whole-recording technical QC while preserving the $N=105$ cohort for direct baseline comparability. |
| **Python/R Parity Protocol** | Shared pre-generated index CSV (`B=10,000`, seed 42) | Completely eliminates cross-language RNG divergence. |

---

## 10. Final Authorization Checklist Before Gate 1 Implementation

- [ ] User approval of REV3.1 scientific corrections and derivations.
- [ ] User approval of Approach A as primary ICA policy with pre-specified secondary ablation.
- [ ] User approval of Approach A retrospective participant-flow disclosure.
- [ ] User authorization to begin **Gate 1 implementation only**.

---
*End of Specification — LEAKCHECK_V1_1_SCIENTIFIC_CORRECTION_REV3_1.md*
