# LeakCheck V2 Development Milestone Completion Audit

**Audit Date**: 2026-11-09  
**Auditor**: Independent Software QA & Methodological Verification Team  
**Milestone**: LeakCheck V2 Development Milestone (Target: V2.0.0-dev)  
**Development Branch**: `v2-dev`  
**Package**: `emi` v2.0.0.dev0  
**Verification Environment**: Windows 11 AMD64, Python 3.10.19, 8 GB RAM, CPU-only  

---

## 1. Executive Summary

This audit assesses the state of **LeakCheck V2**, the expanded multi-dataset research and leakage-auditing framework. 

V2 advances the project across five core pillars:
1. **Multi-Dataset Architecture (V2.1)**: Formalized `BaseEEGDataset` interface with plug-and-play adapters for PhysioNet, OpenBMI, BNCI2014-001, and Cho2017.
2. **Empirical OpenBMI Benchmark**: Completed full-cohort evaluation of $N=34$ intact participants across 62 channels.
3. **Riemannian Geometry Decoders (V2.3)**: Standalone pure-NumPy implementations of `CovarianceTransformer` and `TangentSpaceTransformer`, refuting the assumption of absolute Riemannian spatial immunity.
4. **Leakage Auditing Taxonomy (V2.2)**: Nine leakage mechanisms (P1–P9) defined with formal evidence classifications.
5. **EEG Benchmark Registry Foundation (V2.5)**: Standard JSON schemas (`registry/schemas/`) defining open meta-benchmarking contracts.

---

## 2. Pillar V2.1: Dataset Expansion & Evidence Classification

Per strict scientific integrity rules, dataset capabilities are classified by empirical evidence level:

| Dataset | Accession / Source | Cohort Size | Channels | Paradigm | Evidence Classification | Verification Artifacts |
|---|---|---|---|---|:---:|---|
| **PhysioNet EEGMMIDB** | PhysioNet v1.0.0 | $N=105$ analyzed | 64 EEG | Left vs Right Fist | **Full-Cohort Validated** | `benchmark_results/physionet_v1_1/` |
| **OpenBMI** | NEMAR `nm000338` | $N=34$ intact | 62 EEG | Left vs Right Hand | **Full-Cohort Validated** | `benchmark_results/openbmi_v2/` |
| **BNCI2014-001** | BCI Comp IV-2a | $N=9$ | 22 EEG | 4-class MI | **Implemented & Unit-Tested** | `tests/test_datasets_adapters.py` |
| **Cho et al. (2017)** | GigaScience | $N=52$ | 64 EEG | Left vs Right Hand | **Implemented & Unit-Tested** | `tests/test_datasets_adapters.py` |

> [!IMPORTANT]
> **Scientific Evidence Rule Enforced**: While adapters and unit tests exist and pass for BNCI2014-001 and Cho2017, they are **not** claimed as fully validated scientific benchmarks until full-cohort evaluation runs are logged.

---

## 3. Pillar V2.2 & V2.4: OpenBMI V2 Empirical Benchmark ($N = 34$)

The OpenBMI benchmark was executed using `scripts/run_openbmi_benchmark.py` across all 34 intact participants in 2,631.55 seconds.

### 3.1 Verification of Cryptographic Output Hashes
All output files in `benchmark_results/openbmi_v2/` match their sealed SHA-256 digests:

```text
52d878029c5bd59b424272b89278fffa6290c0e5a78a81d809cf39e002f4017b  design_comparisons.csv
b374086c29ae871de3a9b9d5620b35b94abe81b1360885a9940087c59dc928c6  fold_metrics.csv
a14ff1fe8b632d2852af86931d374b273375a43f5575865a3e56c9427e0bdf0a  participant_eligibility.csv
47eae3f4435b56568cff6583dfd479d8e445e6d21d7aa70f94e23a84365706b0  participant_metrics.csv
```

### 3.2 Independently Verified Statistical Results
Source: `benchmark_results/openbmi_v2/design_comparisons.csv`

| Decoder | Contrast | Contrast Type | Hodges-Lehmann ($\Delta_{\text{HL}}$) | 95% BCa Bootstrap CI | Wilcoxon $p_{\text{raw}}$ | Wilcoxon $p_{\text{Holm}}$ | Cohen's $d_z$ |
|---|---|---|---:|---:|---:|---:|---:|
| **CSP-LDA** | **P1 vs D3** | Supervised Spatial Leakage | **$+6.25$ pp** | $[+3.25, +8.23]$ pp | $1.47 \times 10^{-4}$ | $1.87 \times 10^{-4}$ | $+0.745$ |
| **CSP-LDA** | **D1s vs D3** | Size-Matched Random | **$+2.84$ pp** | $[+1.46, +4.98]$ pp | $9.38 \times 10^{-5}$ | $1.87 \times 10^{-4}$ | $+0.751$ |
| **TS-LR** | **P1 vs D3** | Supervised Spatial Leakage | **$+0.75$ pp** | $[+0.25, +1.50]$ pp | $0.0203$ | $0.0203$ | $+0.417$ |
| **TS-LR** | **D1s vs D3** | Size-Matched Random | **$+2.94$ pp** | $[+1.66, +4.51]$ pp | $9.68 \times 10^{-5}$ | $1.94 \times 10^{-4}$ | $+0.771$ |

### 3.3 Root-Cause Analysis: TS-LR $+0.75$ pp P1 Effect
Investigation of `run_p1_csp_on_all_for_subject()` in `scripts/run_openbmi_benchmark.py`:
- For `ts_lr`, the reference covariance matrix $\mathbf{C}_{\text{ref}}$ (Riemannian Fréchet mean) and the `StandardScaler` are fitted across all 200 trials.
- Because Riemannian mean estimation is unsupervised, class labels are never used.
- However, incorporating test covariance matrices into $\mathbf{C}_{\text{ref}}$ slightly shifts the tangent space projection origin toward the test distribution, creating a small but statistically significant $+0.75$ pp shift ($p = 0.0203$).
- **Conclusion**: Riemannian geometry decoders are **not mathematically immune** to global contamination, but exhibit **$>8\times$ higher resilience** than supervised CSP-LDA ($+6.25$ pp).

---

## 4. Pillar V2.3: Decoders Validation Matrix

| Decoder | Transformation Engine | Classification Engine | Real-Data Verification | Status |
|---|---|---|:---:|---|
| **`csp_lda`** | OAS Shrinkage CSP | Linear Discriminant Analysis | PhysioNet ($N=105$), OpenBMI ($N=34$) | **Full-Cohort Validated** |
| **`ts_lr`** | Riemannian Tangent Space | $L_2$-regularized Logistic Regression | OpenBMI ($N=34$) | **Full-Cohort Validated** |
| **`csp_lr`** | OAS Shrinkage CSP | $L_2$-regularized Logistic Regression | Unit tests & smoke tests | **Operational** |
| **`csp_svm`** | OAS Shrinkage CSP | Linear Support Vector Classifier | Unit tests & smoke tests | **Operational** |
| **`ts_lda`** | Riemannian Tangent Space | Shrinkage LDA | Unit tests & smoke tests | **Operational** |

---

## 5. Pillar V2.5: Developer & Community Infrastructure

The foundations for future integration with the broader EEG Benchmark Registry are established:
- `registry/schemas/dataset.schema.json`: Standard schema for dataset provenance and montage specifications.
- `registry/schemas/pipeline.schema.json`: Standard schema for preprocessing pipelines and filtering cutoffs.
- `registry/schemas/benchmark.schema.json`: Formal cross-validation protocol definitions ($D_1$–$D_6$).
- `registry/schemas/leakage.schema.json`: Formal leakage taxonomy (P1–P9) and detection rules.
- `registry/schemas/reproducibility.schema.json`: Machine-readable run manifests with environment digests.

---

## 6. V2 Test Suite Verification

Command:
```bash
pytest -m "v2" -q
```
**Results**:
- **15 passed** in 14.42 seconds (171 deselected).
- Covers dataset adapters, OpenBMI session loading, corruption handling, and benchmark runner functions.

---

## 7. Milestone Verdict

**VERDICT: PARTIALLY COMPLETE (OPENBMI MILESTONE COMPLETE, MULTI-COHORT EXPANSION ONGOING)**

The V2 research framework has achieved its primary empirical goal: multi-dataset benchmarking on OpenBMI ($N=34$) with dual decoders (CSP-LDA and Riemannian TS-LR), establishing the paradigm-dependence of cross-validation bias and measuring Riemannian decoder resilience. Full-cohort execution on BNCI2014-001 and Cho2017 remains scheduled for future multi-cohort campaigns.
