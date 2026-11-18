# INITIAL REPOSITORY & ARCHITECTURE AUDIT

**Repository**: `D:\my lab\LeakCheck_remote`  
**Date**: November 18, 2026 (Stage 1 / Day 1)  
**Lead Auditor**: LEAD (Scientific Project Director) & AGENT 6 (Software Engineering & QA)  
**Scope**: LeakCheck V1.1 Single-Dataset Architecture (PhysioNet EEGMMIDB)  

---

## 1. Source Modules and Responsibilities

The active codebase is located under `src/emi/` and comprises 12 core Python modules:

| Module | Size (Bytes) | Role & Responsibilities | Key Functions / Classes |
| :--- | :---: | :--- | :--- |
| `config.py` | 8,468 | Configuration dataclasses, default parameters, event maps | `Config`, `ANNOT_TO_ID`, `EVENT_ID` |
| `preprocess.py` | 13,425 | EEG filtering, CAR, bad channel detection, ICA, epoching | `filter_raw`, `build_epochs_full`, `car_reference` |
| `splitters.py` | 9,842 | Partition generators for $D_3, D_{1m}, D_{1s}$ | `loro_splits`, `matched_k_splits`, `size_matched_split` |
| `leakstats.py` | 14,210 | Pratt Wilcoxon, Hodges-Lehmann, BCa bootstrap, Holm | `wilcoxon_pratt`, `bca_ci_paired`, `hodges_lehmann` |
| `evaluation.py` | 11,350 | CSP filter estimation, LDA classification, pipeline runner | `evaluate_dataset`, `fit_csp_lda` |
| `diagnostics.py` | 10,120 | SVD rank checks, channel correlation, artifact diagnostics | `numerical_rank_svd`, `bad_channel_metrics` |
| `datasets.py` | 8,950 | PhysioNet raw EDF dataset loader and annotation parser | `load_physionet_subject`, `standardize_channels` |
| `cache.py` | 7,650 | Serialized epoch `.npz` storage and checksum validation | `get_cache_path`, `load_cached_epochs` |
| `constants.py` | 4,210 | Channel names, 10–10 montage mappings, standard constants | `STANDARD_1005_CHANNELS` |

---

## 2. Experimental Data Flow & Architecture

```
Raw EDFs (109 subjects) -> Load & Standardize -> Continuous 1-40 Hz FIR Filter -> CAR
                                                                                    |
                                                                                    v
Epochs (.npz cache) <- Adaptive Threshold Artifact Rejection <- FastICA De-blinking <- Bad Channel Detect & Interpolate
         |
         +--> D3 (Leave-One-Run-Out): Train on Runs 4, 8 -> Test on Run 12
         +--> D1m (Matched-K 3-Fold): 3-fold CV across interleaved trials
         +--> D1s (Size-Matched): 20 random repeated splits (2/3 train, 1/3 test)
         +--> P1 (Global CSP Positive Control): CSP fitted across all trials
         |
         v
Accuracy Matrix (105 included subjects) -> Pairwise Contrasts (P1 - D3, D1s - D3, D1m - D3)
                                                        |
                                                        v
Statistical Report: Hodges-Lehmann Walsh Median, Corrected Pratt Wilcoxon, 10,000 BCa CIs, Holm FWER
```

---

## 3. Verified Scope & Boundary Invariants

1. **Strict Single-Dataset Isolation**: Zero multi-dataset adapters or external data dependencies present in `src/emi/`.
2. **Archival Quarantine**: All historical V2 files reside exclusively in `archive/v2/`.
3. **Frozen Benchmark Protection**: `benchmark_results/physionet_v1_1_final/` remains 100% read-only.
4. **Active Runtime**: Verified against Python 3.12.16 with MNE 1.8.0 and SciPy 1.14.1.
