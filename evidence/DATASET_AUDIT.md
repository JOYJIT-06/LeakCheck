# DATASET, SAMPLING RATE & PARTICIPANT FLOW AUDIT

**Audit Date**: November 18, 2026 (Stage 2 / Day 2)  
**Lead Auditor**: AGENT 4 (Rank, CSP, ICA & EDF Specialist) & AGENT 5 (Dataset & Design Specialist)  
**Reviewer**: LEAD (Scientific Project Director)  
**Dataset**: PhysioNet EEG Motor Movement/Imagery Database (EEGMMIDB)  
**Raw Data Path**: `data/MNE-eegbci-data/files/eegmmidb/1.0.0/`  

---

## 1. Raw EDF Sampling Rates Audit

### 1.1 Empirical Byte-Level Header Audit
Direct inspection of the ASCII header records across all 327 EDF files (`R04`, `R08`, `R12` for all 109 subjects) reveals:
- **106 Subjects**: Recorded at exactly **160.0 Hz** ($1.0\text{ s}$ record duration, $160$ samples per record, $65$ signals).
- **Exactly 3 Subjects (`S088`, `S092`, `S100`)**: Recorded at exactly **128.0 Hz** ($1.0\text{ s}$ record duration, $128$ samples per record, $65$ signals).

### 1.2 Provenance of the 128 Hz Anomaly
The 128 Hz sampling frequency originates **directly from the original BCI2000 acquisition files on PhysioNet**, not from software resampling, caching corruption, or parser error.

```
S001R04.edf: record_duration=1.0s, ns=65, samples_per_record=160 -> sfreq = 160.0 Hz
S088R04.edf: record_duration=1.0s, ns=65, samples_per_record=128 -> sfreq = 128.0 Hz
S092R04.edf: record_duration=1.0s, ns=65, samples_per_record=128 -> sfreq = 128.0 Hz
S100R04.edf: record_duration=1.0s, ns=65, samples_per_record=128 -> sfreq = 128.0 Hz
S104R04.edf: record_duration=1.0s, ns=65, samples_per_record=160 -> sfreq = 160.0 Hz
```

---

## 2. Event and Trial Pair Count Reconciliation

### 2.1 Complete Participant-by-Run Verification
Every event marker across all 327 runs was parsed directly from the raw EDF annotations (`T1` left fist, `T2` right fist):
- Total valid motor imagery cues ($T_1 + T_2$): **4,918 cues**.
- Total consecutive within-run trial pairs: **4,591 pairs**.

### 2.2 Reconciling the Nominal $4,578$ vs. Empirical $4,591$ Count
- Nominal expectation: $109 \times 3 \times (15 - 1) = 4,578$ pairs.
- Net empirical deviation: $+13$ pairs.
- **Root Cause**:
  1. `S088`: 19 MI cues in R04, R08, R12 $\implies 18 \times 3 = 54$ pairs ($+12$ pairs).
  2. `S092`: 19 MI cues in R04, R08, R12 $\implies 18 \times 3 = 54$ pairs ($+12$ pairs).
  3. `S100`: 12 MI cues in R04, R08, R12 $\implies 11 \times 3 = 33$ pairs ($-9$ pairs).
  4. `S104`: 13 MI cues in R08 $\implies 12$ pairs ($-2$ pairs).
  5. Remaining 105 subjects: Exactly 15 cues per run $\implies 14 \times 3 = 42$ pairs each ($0$ deviation).
  $$\text{Net Deviation} = +12 + 12 - 9 - 2 = \mathbf{+13\text{ pairs}} \implies 4,578 + 13 = \mathbf{4,591\text{ pairs}}.$$

---

## 3. Participant Flow & Exclusion Provenance

Inspection of `D:\my lab\LeakCheck_Cache\cache_failed.csv` and subject caches confirms:

| Participant | Raw Data Status | Measured Anomaly | Exclusion Criterion | Verified Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **S044** | Complete EDF | 12 of 64 channels bad ($18.75\%$) | Bad channels $>15\%$ | Excluded ($N=105$) |
| **S069** | Complete EDF | 12 of 64 channels bad ($18.75\%$) | Bad channels $>15\%$ | Excluded ($N=105$) |
| **S086** | Complete EDF | 24 retained trials ($[5, 4, 15]$) | Retained trials $<30$ | Excluded ($N=105$) |
| **S091** | Complete EDF | All 45 trials $\text{PTP}_{95} > 800\,\mu\text{V}$ | 100% artifact rejected | Excluded ($N=105$) |
| **S088, S092, S100** | Complete EDF | 128 Hz native sampling rate | Supported by pipeline | **Included** ($N=105$) |
| **S104** | Complete EDF | 160 Hz native sampling rate | Normal | **Included** ($N=105$) |

- Total requested: $109 \to$ Excluded: $4 \to$ **Included in benchmark: $105$ ($96.3\%$ retention)**.

---

## 4. Numerical Rank & Geometry Audit

1. **Numerical SVD Rank Formulation**: $\text{tol} = \sigma_{\max} \max(M, N) \varepsilon$.
2. **Empirical Rank Verification on S001**:
   - Raw continuous rank: $64$ ($\sigma_{\min} = 6.41 \times 10^{-4} \gg \text{tol} \approx 1.15 \times 10^{-12}$).
   - CAR rank: $63$ ($\sigma_{64} = 2.30 \times 10^{-17} \ll \text{tol}$).
   - CAR + 2 bad channels interpolated: $62$ ($\sigma_{63} = 3.33 \times 10^{-17}, \sigma_{64} = 2.33 \times 10^{-18}$).
3. **Regularization Safeguard**: OAS shrinkage covariance in `RankSafeCSP` safely conditions the rank-deficient covariance matrices across all folds.

---

## 5. Audit Summary & Classification

| Item | Component | Legacy State | Expected State | Classification |
| :--- | :--- | :--- | :--- | :--- |
| **DATA-01** | Raw Sampling Rates | Assumed 160 Hz everywhere | 106 @ 160 Hz, 3 @ 128 Hz (BCI2000 native) | **VERIFIED FACT** |
| **DATA-02** | MI Trial Pair Count | Reported 4,591 pairs | 4,591 verified to the exact integer | **VERIFIED FACT** |
| **DATA-03** | Participant Flow | Discrepancy between log & cause | Root causes verified in `cache_failed.csv` | **VERIFIED CORRECT** |
| **DATA-04** | Numerical SVD Rank | Heuristic formula | Standard dimension-aware tolerance | **VERIFIED CORRECT** |
