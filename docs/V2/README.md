# LeakCheck V2: Multi-Dataset EEG Leakage Auditing Framework (Development Milestone)

> [!IMPORTANT]
> **V2 Development Status Notice**  
> This directory documents **LeakCheck V2.0.0-dev**, an ongoing research and development framework for multi-dataset EEG leakage auditing. V2 is maintained on the `v2-dev` development line and is **strictly separate** from the stabilized **LeakCheck v1.1.0** release.

---

## 1. V2 Research Identity & Objectives

While LeakCheck V1.1 established the baseline single-dataset benchmark on PhysioNet EEGMMIDB ($N=105$), V2 extends the framework to:
1. **Multi-Dataset Polymorphism**: Standardize neuroimaging ingestion across distinct recording montages, sampling rates, and trial paradigms via the `BaseEEGDataset` interface.
2. **Empirical Cross-Cohort Validation**: Benchmark large-scale multi-session cohorts (specifically OpenBMI, $N=34$, 62 channels).
3. **Riemannian Geometry Decoders**: Evaluate the resilience of covariance-based tangent space decoders (`ts_lr`, `ts_lda`) against classical spatial filtering (CSP-LDA).
4. **Leakage Mechanism Expansion (P1–P9)**: Formalize nine distinct leakage pathways in the EEG Benchmark Registry.
5. **Open Benchmark Registry**: Establish machine-readable JSON schemas (`registry/schemas/`) for open meta-analyses.

---

## 2. Dataset Validation Status Matrix

Per strict scientific reporting guidelines, dataset capabilities are classified according to empirical evidence:

| Dataset | Cohort | Montage | Sampling Rate | Paradigm | Evidence Level | Validation Record |
|---|---|---|---|---|:---:|---|
| **PhysioNet EEGMMIDB** | $N=105$ analyzed | 64 EEG | 160 Hz | Left vs Right Fist MI | **Full-Cohort Validated** | `benchmark_results/physionet_v1_1/` |
| **OpenBMI (Lee et al. 2019)** | $N=34$ intact | 62 EEG | 1000 Hz $\to$ 160 Hz | Left vs Right Hand MI | **Full-Cohort Validated** | `benchmark_results/openbmi_v2/` |
| **BNCI2014-001 (BCI IV-2a)** | $N=9$ | 22 EEG | 250 Hz | 4-class Motor Imagery | **Implemented & Unit-Tested** | `tests/test_datasets_adapters.py` |
| **Cho et al. (2017)** | $N=52$ | 64 EEG | 512 Hz | Left vs Right Hand MI | **Implemented & Unit-Tested** | `tests/test_datasets_adapters.py` |

*Note: Adapters and unit tests demonstrate software operability, but are not claimed as full-cohort scientific validation until complete cohort runs are logged.*

---

## 3. Verified OpenBMI V2 Benchmark Results ($N = 34$)

The OpenBMI replication benchmark was executed across all 34 intact participants on Session 1 (Run 0: offline screening, Run 1: online feedback), comparing Shrinkage CSP-LDA and Riemannian Tangent Space Logistic Regression (`ts_lr`).

### 3.1 Empirical Summary Table
Source: `benchmark_results/openbmi_v2/design_comparisons.csv`

| Decoder | Contrast | Contrast Meaning | Hodges-Lehmann ($\Delta_{\text{HL}}$) | 95% BCa Bootstrap CI | Wilcoxon $p_{\text{raw}}$ | Wilcoxon $p_{\text{Holm}}$ | Cohen's $d_z$ |
|---|---|---|---:|---:|---:|---:|---:|
| **CSP-LDA** | **P1 vs D3** | Supervised Spatial Contamination | **$+6.25$ pp** | $[+3.25, +8.23]$ pp | $1.47 \times 10^{-4}$ | $1.87 \times 10^{-4}$ | $+0.745$ |
| **CSP-LDA** | **D1s vs D3** | Size-Matched Random Partition | **$+2.84$ pp** | $[+1.46, +4.98]$ pp | $9.38 \times 10^{-5}$ | $1.87 \times 10^{-4}$ | $+0.751$ |
| **TS-LR** | **P1 vs D3** | Supervised Spatial Contamination | **$+0.75$ pp** | $[+0.25, +1.50]$ pp | $0.0203$ | $0.0203$ | $+0.417$ |
| **TS-LR** | **D1s vs D3** | Size-Matched Random Partition | **$+2.94$ pp** | $[+1.66, +4.51]$ pp | $9.68 \times 10^{-5}$ | $1.94 \times 10^{-4}$ | $+0.771$ |

### 3.2 Key Scientific Insights from OpenBMI
1. **Regime-Dependent Partition Directionality**: On OpenBMI, $D_{1s}$ produces an **inflation of $+2.84$ pp** (CSP-LDA) and **$+2.94$ pp** (TS-LR), contrasting sharply with the $-2.68$ pp deflation observed on PhysioNet. On OpenBMI, Run 0 (offline screening) and Run 1 (online feedback) represent distinct operational regimes; random trial pooling allows decoders to interpolate between regimes rather than having to extrapolate from an offline state to an online feedback state.
2. **Investigation of the TS-LR $+0.75$ pp P1 Effect**: In `scripts/run_openbmi_benchmark.py` (`run_p1_csp_on_all_for_subject`), the Riemannian reference covariance matrix $\mathbf{C}_{\text{ref}}$ (the geometric mean) and the subsequent `StandardScaler` are fitted across all 200 covariance matrices. Because Riemannian Fréchet mean estimation does not use trial labels, label information is not leaked directly. However, incorporating test covariance matrices into $\mathbf{C}_{\text{ref}}$ slightly shifts the tangent space origin toward the test distribution, creating a subtle $+0.75$ pp effect ($p = 0.0203$). TS-LR is over $8\times$ more resilient to global contamination than CSP-LDA ($+6.25$ pp).

### 3.3 Sealed Artifact Hashes
All output files in `benchmark_results/openbmi_v2/` have been cryptographically sealed:
- `participant_eligibility.csv`: `a14ff1fe8b632d2852af86931d374b273375a43f5575865a3e56c9427e0bdf0a`
- `fold_metrics.csv`: `b374086c29ae871de3a9b9d5620b35b94abe81b1360885a9940087c59dc928c6`
- `participant_metrics.csv`: `47eae3f4435b56568cff6583dfd479d8e445e6d21d7aa70f94e23a84365706b0`
- `design_comparisons.csv`: `52d878029c5bd59b424272b89278fffa6290c0e5a78a81d809cf39e002f4017b`

---

## 4. Leakage Mechanisms (P1–P9) Evidence Matrix

| Key | Mechanism | Rationale | Evidence Level | Validated Cohort |
|---|---|---|:---:|---|
| **P1** | Global CSP Spatial Filtering | Supervised eigenvectors fitted on all trials encode test labels. | **Full-Cohort Validated** | PhysioNet ($N=105$), OpenBMI ($N=34$) |
| **P2** | Global Continuous ICA Unmixing | Ocular unmixing matrix fitted across concatenated runs. | **Architecturally Specified** | In development (`docs/V2/P2_SCIENTIFIC_DESIGN.md`) |
| **P3** | Global Temporal Filtering | Continuous bandpass filter crosses fold boundaries. | **Registry Protocol** | Formalized in schema |
| **P4** | Temporal Window Snooping | Post-cue time window selected by optimizing test accuracy. | **Registry Protocol** | Formalized in schema |
| **P5** | Global Feature Normalization | Z-score scaling parameters computed using test feature distributions. | **Prototype Implemented** | Unit tested in pipeline |
| **P6** | Hyperparameter Snooping | Regularization $C$ or component count selected on test folds. | **Prototype Implemented** | Unit tested in pipeline |
| **P7** | Global Feature Selection | Supervised channel/frequency selection computed across pooled data. | **Registry Protocol** | Formalized in schema |
| **P8** | Sliding Window Overlap | Overlapping temporal sub-epochs cross train/test splits. | **Registry Protocol** | Formalized in schema |
| **P9** | Subject Identity Snooping | Trials from the same subject appear in train and test of cross-subject models. | **Registry Protocol** | Formalized in schema |

---

## 5. Decoders Validation Matrix

| Decoder | Family | Feature Transform | Classification Engine | Evidence Level |
|---|---|---|---|:---:|
| **`csp_lda`** | Classical Spatial | OAS Shrinkage CSP | Linear Discriminant Analysis | **Full-Cohort Validated** |
| **`csp_lr`** | Classical Spatial | OAS Shrinkage CSP | $L_2$-regularized Logistic Regression | **Unit-Tested & Operational** |
| **`csp_svm`** | Classical Spatial | OAS Shrinkage CSP | Linear Support Vector Classifier | **Unit-Tested & Operational** |
| **`ts_lr`** | Riemannian Manifold | Covariance $\to$ Tangent Space | $L_2$-regularized Logistic Regression | **Full-Cohort Validated** |
| **`ts_lda`** | Riemannian Manifold | Covariance $\to$ Tangent Space | Shrinkage LDA | **Unit-Tested & Operational** |

---

## 6. How to Run V2 Benchmarks

To reproduce the OpenBMI V2 benchmark:
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

To run the V2-specific test suite:
```bash
pytest -m "v2" -q
# Output: 15 passed in ~14s
```
