# Research Grant & Doctoral Proposal: Automated Data-Leakage Auditing and Federated Benchmarking for Reproducible Brain-Computer Interfaces

**Project Title**: LeakCheck & The EEG Benchmark Registry: A Rigorous Methodology for Trustworthy Neural Decoding  
**Principal Investigator / Candidate**: Computational Neuroscience & BCI Research Group  
**Target Mechanism**: NIH R01 / NSF Information & Intelligent Systems / ERC Starting Grant  
**Project Duration**: 36 Months  

---

## 1. Project Summary & Specific Aims

Non-invasive Brain-Computer Interfaces (BCIs) and machine learning applied to electroencephalography (EEG) hold transformative potential for neurorehabilitation, communication prostheses, and cognitive monitoring. However, translating BCI algorithms into real-world clinical and consumer settings is severely impeded by a reproducibility crisis. Methodological oversights—specifically data leakage, temporal autocorrelation contamination, and improperly nested preprocessing—systematically distort reported decoding accuracies.

The objective of this research program is to establish the first comprehensive, automated, and mathematically grounded framework for identifying, quantifying, and mitigating data leakage in non-invasive neural decoding. We propose two synergistic research thrusts: **LeakCheck**, an automated algorithmic auditing engine, and the **EEG Benchmark Registry**, an open-science, federated infrastructure for cross-dataset verification.

### Specific Aim 1: Formalize and Empirically Quantify the EEG Leakage Taxonomy (Months 1–18)
- Characterize 9 distinct data leakage pathways (P1–P9) spanning spatial filter contamination, continuous temporal filtering, overlapping epoch segmentation, test-fold hyperparameter selection, and pre-split data augmentation.
- Empirically evaluate these mechanisms across 5 diverse, multi-session BCI datasets ($>300$ participants total: PhysioNet, OpenBMI, Cho2017, BNCI2014, and High-Gamma).
- Quantify effect sizes using non-parametric Hodges-Lehmann paired estimators, BCa bootstrap confidence intervals, and Two One-Sided Tests (TOST) for equivalence.

### Specific Aim 2: Develop a Standalone, Automated Auditing Engine (LeakCheck V2) (Months 12–28)
- Implement automated static analysis and dynamic instrumentation tools that inspect BCI decoding scripts and pipeline graphs.
- Automatically flag contaminated operations (e.g. out-of-fold spatial filtering, global normalization, unbuffered epoch overlap).
- Implement integrated negative-control verification modules running within-run label permutations and circular-shift null models to detect pseudo-performance and guard against nominal false positives.

### Specific Aim 3: Deploy the Federated EEG Benchmark Registry (Months 20–36)
- Build an open-access, community-governed registry schema cataloging datasets, pipelines, decoders, benchmarks, and reproducibility records.
- Establish standardized validation tiers (Discovered $\rightarrow$ Installation-Tested $\rightarrow$ Pipeline-Validated $\rightarrow$ Scientifically Benchmarked).
- Release reference implementations, containerized benchmark environments, and interactive visualization dashboards for community adoption.

---

## 2. Research Strategy & Methodological Innovation

### 2.1 The Core Scientific Innovation: Decoupling Geometry from Stationarity
Traditional BCI validation often treats cross-validation as a binary choice between $k$-fold cross-validation and leave-one-run-out (LORO). Our preliminary work on LeakCheck V1.1 ($N=105$) demonstrates that this dichotomy is fundamentally flawed:
1. Conventional random $k$-fold cross-validation (`D1m`) exhibits a $-4.47$ pp deflation relative to LORO.
2. When fold sizes and class distributions are strictly matched (`D1s`), performance recovers $+1.79$ pp, revealing that $\approx 40\%$ of the observed difference is an artifact of fold geometry mismatch.
3. The remaining $-2.68$ pp deflation ($p = 5.86 \times 10^{-5}$) proves that mixing trials across runs harms model generalization because training folds are forced to bridge inter-run non-stationarities, whereas LORO tests on a single continuous recording block.

This proposal will systematically extend this geometric decomposition to multi-day, cross-session transfer protocols (`D6_loso_session` and `D7_loso_subject`), formulating an analytical framework that separates temporal non-stationarity from algorithmic generalization.

### 2.2 Algorithmic Spectrum: From Classical Spatial Filters to Foundation Models
The proposed framework will systematically audit four distinct decoding paradigms:
1. **Classical Filter-Bank Spatial Decoders**: CSP-LDA, FBCSP, CSP-SVM.
2. **Riemannian Geometry Classifiers**: Covariance estimation (OAS, Ledoit-Wolf) projected onto Riemannian tangent space (`ts_lr`).
3. **Deep Convolutional Architectures**: Compact neural networks (EEGNet, DeepConvNet, FBCNet).
4. **Self-Supervised Foundation Models**: Transformer architectures pretrained on large-scale unlabeled EEG databases (e.g., TUH EEG).

---

## 3. Work Plan, Milestones & Deliverables

| Year | Period | Focus Area | Key Deliverables |
|---|---|---|---|
| **Year 1** | Q1–Q2 | Leakage Taxonomy & Multi-Dataset Harmonization | OpenBMI ($N=54$) and Cho2017 ($N=52$) dataset adapters, schema harmonization. |
| | Q3–Q4 | Continuous Preprocessing Audits | Fold-nested continuous filtering/ICA modules; empirical evaluation of mechanism P2. |
| **Year 2** | Q1–Q2 | Dynamic Auditing Engine (LeakCheck V2) | Automated AST static analyzer and runtime hook detecting data leakage in arbitrary Python BCI code. |
| | Q3–Q4 | Deep Learning & Riemannian Auditing | Comprehensive comparison across CSP-LDA, Riemannian Tangent Space, and EEGNet. |
| **Year 3** | Q1–Q2 | EEG Benchmark Registry Deployment | Public launch of `eeg-benchmark-registry.org` with REST APIs, schemas, and indexed baseline records. |
| | Q3–Q4 | Community Dissemination & Standards Workshop | IEEE/NeurIPS tutorial, open-source documentation, and final benchmark whitepaper. |

---

## 4. Significance, Broader Impact & Open Science Commitment
By establishing verifiable standards and providing an automated auditing tool, this project directly addresses the reproducibility crisis in neural engineering. Every line of code, benchmark result, and dataset schema produced under this grant will be released under permissive open-source licenses (MIT/Apache 2.0), ensuring immediate utility for academic researchers, clinical trialists, and commercial neurotechnology developers worldwide.
