# Multi-Dataset Acquisition & Validation Status (LeakCheck V2)

> [!NOTE]
> **Scientific Integrity & Evidence Tiering Standard**  
> In accordance with the project's strict empirical reporting standards, dataset status is classified into three transparent tiers:
> 1. **Full-Cohort Validated**: Complete cohort processed through LeakCheck pipelines with all participant and fold-level metrics logged, statistical contrasts computed, and manifests cryptographically sealed.
> 2. **Implemented & Unit-Tested**: Adapter class written, montage mapping established, and automated unit tests passing in `tests/test_datasets_adapters.py`.
> 3. **Registry Protocol / Ingesting**: Metadata cataloged in `registry/schemas/`, downloading or cloud caching scheduled.

---

## 1. Candidate Datasets Matrix (11 Datasets)

| # | Dataset ID | Reference Citation | Cohort ($N$) | Channels | Native $f_s$ | Tasks / Paradigm | Size (Raw) | Status | Adapter / Pipeline |
|---|---|---|:---:|:---:|:---:|---|:---:|:---:|---|
| 1 | **PhysioNet EEGMMIDB** | Goldberger et al. (2000), Schalk et al. (2004) | 109 (105 analyzed) | 64 | 160 Hz | Left/Right Fist MI (Runs 3, 7, 11) | ~3 GB | **Full-Cohort Validated** | `emi.datasets` / `scripts/run_physionet_benchmark.py` |
| 2 | **OpenBMI** | Lee et al. (2019), GigaScience / NEMAR `nm000338` | 54 (34 intact) | 62 | 1000 Hz | Left/Right Hand MI (Session 1, Runs 0 & 1) | ~45 GB | **Full-Cohort Validated** | `OpenBMIDatasetAdapter` / `scripts/run_openbmi_benchmark.py` |
| 3 | **Cho2017** | Cho et al. (2017), GigaScience | 52 | 64 | 512 Hz | Left/Right Hand MI | ~15 GB | **Implemented & Unit-Tested** | `Cho2017DatasetAdapter` / `tests/test_datasets_adapters.py` |
| 4 | **BNCI2014-001** | Tangermann et al. (2012), BCI Comp IV 2a | 9 | 22 | 250 Hz | 4-class MI (Left Hand, Right Hand, Feet, Tongue) | ~1.5 GB | **Implemented & Unit-Tested** | `BNCI2014_001_DatasetAdapter` / `tests/test_datasets_adapters.py` |
| 5 | **BNCI2014-004** | Leeb et al. (2008), BCI Comp IV 2b | 9 | 3 | 250 Hz | 2-class MI (Left vs Right Hand) across 5 sessions | ~800 MB | **Implemented & Unit-Tested** | `BNCI2014_004Adapter` / `tests/test_datasets_adapters.py` |
| 6 | **High-Gamma** | Schirrmeister et al. (2017), Human Brain Mapping | 14 | 128 (44 selected) | 500 Hz | 4-class MI (Right Hand, Left Hand, Both Feet, Rest) | ~12 GB | **Implemented & Unit-Tested** | `HighGammaAdapter` / `tests/test_datasets_adapters.py` |
| 7 | **Shin2017A** | Shin et al. (2017), J. Neurosci. Methods | 29 | 30 | 1000 Hz | Simultaneous EEG/NIRS Motor Imagery | ~8 GB | **Implemented & Unit-Tested** | `Shin2017AAdapter` / `tests/test_datasets_adapters.py` |
| 8 | **Weibo2014** | Faller et al. (2014), PLOS ONE | 10 | 60 | 200 Hz | Compound limb and simple limb MI | ~4 GB | **Implemented & Unit-Tested** | `Weibo2014Adapter` / `tests/test_datasets_adapters.py` |
| 9 | **Grosse-Wentrup2009** | Grosse-Wentrup et al. (2009), IEEE TBME | 10 | 128 | 500 Hz | High-density motor imagery with gamma band focus | ~3 GB | **Implemented & Unit-Tested** | `GrosseWentrup2009Adapter` / `tests/test_datasets_adapters.py` |
| 10 | **Zhou2016** | Zhou et al. (2016), Frontiers in Human Neurosci. | 4 | 16 | 250 Hz | Session-to-session variability across weeks | ~1 GB | **Implemented & Unit-Tested** | `Zhou2016Adapter` / `tests/test_datasets_adapters.py` |
| 11 | **Yang2025** | Yang et al. (2025), Scientific Data | 60+ | 64 | 500 Hz | Multi-day motor imagery and cognitive task battery | ~30 GB | **Implemented & Unit-Tested** | `Yang2025Adapter` / `tests/test_datasets_adapters.py` |

---

## 2. In-Depth Profiles of Priority Cohorts

### 2.1 PhysioNet EEGMMIDB ($N = 105$)
- **Accession**: PhysioNet `eegmmidb/1.0.0`
- **License**: Open Data Commons Attribution License (ODC-By) v1.0
- **Montage**: 64-channel 10–10 system, BCI2000 standard.
- **Protocol Evaluated**: Left fist vs right fist motor imagery (Runs 3, 7, 11), totaling 45 trials per subject.
- **Empirical Findings**:
  - Supervised CSP Spatial Contamination ($P_1$): $+24.50$ pp inflation ($p = 1.48 \times 10^{-18}$, rank biserial $+0.998$).
  - Size-Matched Random Trial Partitioning ($D_{1s}$): $-2.68$ pp deflation ($p = 5.86 \times 10^{-5}$, rank biserial $-0.452$). Non-stationarity across stationary runs creates noisy inter-run interpolations that impair generalization.

### 2.2 OpenBMI / Lee et al. 2019 ($N = 34$)
- **Accession**: NEMAR `nm000338`, GigaScience Open Access
- **License**: Creative Commons Zero (CC0)
- **Montage**: 62-channel scalp EEG, standard 10–20 international system.
- **Protocol Evaluated**: Left hand vs right hand motor imagery, Session 1 (Run 0: offline calibration without feedback; Run 1: online evaluation with continuous feedback). 100 trials per class, 200 total trials per subject.
- **Empirical Findings**:
  - CSP-LDA $P_1$: $+6.25$ pp inflation ($p = 1.47 \times 10^{-4}$).
  - CSP-LDA $D_{1s}$: $+2.84$ pp inflation ($p = 9.38 \times 10^{-5}$). In sharp contrast to PhysioNet, trial mixing interpolates across offline and online regimes, artificially easing classification relative to cross-run extrapolation.
  - TS-LR $P_1$: $+0.75$ pp ($p = 0.0203$). Tangent space logistic regression exhibits $>8\times$ greater resilience to supervised spatial contamination than CSP-LDA.

### 2.3 Cho et al. 2017 ($N = 52$)
- **Accession**: GigaScience Database (`10.5524/100295`)
- **License**: CC0 Public Domain Dedication
- **Montage**: 64 EEG channels, sampling rate 512 Hz.
- **Protocol**: Left hand vs right hand motor imagery (100–120 trials per class). Provides high statistical power for cross-subject transfer and covariance stability testing.
- **Adapter**: `Cho2017DatasetAdapter` in `src/emi/datasets_adapters.py`, verified with unit test `test_cho2017_adapter_initialization`.

### 2.4 BNCI2014-001 (BCI Competition IV 2a) ($N = 9$)
- **Accession**: BNCI Horizon 2020 repository
- **Montage**: 22 EEG channels + 3 EOG channels, sampling rate 250 Hz.
- **Protocol**: 4-class motor imagery (Left hand, Right hand, Both feet, Tongue) recorded over 2 sessions on separate days.
- **Adapter**: `BNCI2014_001_DatasetAdapter` in `src/emi/datasets_adapters.py`, verified with unit test `test_bnci2014_001_adapter_initialization`.

---

## 3. Storage and Bandwidth Optimization Strategy

1. **Local Working Footprint**:
   - Only lightweight metadata, adapters, scripts, and aggregated metrics CSVs are stored permanently on local developer disks.
   - Raw binary files (`.mat`, `.gdf`, `.edf`) are stored on external high-capacity cloud drives (Dropbox `/LeakCheck_Cloud/datasets` and Google Drive).
2. **Streaming and Ephemeral Download**:
   - Benchmark runners utilize streaming cache downloads with automatic post-execution cleanup options for resource-constrained environments.
3. **Reproducible Preprocessing Manifests**:
   - Each dataset's preprocessed trial structure is deterministic: bandpass filtered (8–30 Hz FIR), downsampled to 160 Hz or 250 Hz, trial windowing ($t \in [0.5, 2.5]$ s post-cue), and peak-to-peak artifact thresholding ($150\ \mu\text{V}$).
