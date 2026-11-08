# Leakage Taxonomy Migration and Canonical Mapping Document

> [!IMPORTANT]
> **Scientific Integrity & Historical Provenance Standard**  
> In compliance with Section 10.2 of the LeakCheck Master Directive, this document establishes the formal, canonical mapping between earlier historical leakage mechanism designations (used during exploratory V0.x–V1.0 prototyping) and the finalized V1.1 / V2 taxonomy (P1–P9). Historical benchmark outputs must never be silently renumbered or merged without transparent reconciliation.

---

## 1. Canonical Mapping Matrix (Historical vs. V2 Taxonomy)

| Historical ID | Historical Name / Definition | V2 Canonical ID | V2 Canonical Definition | Implementation Reference | Mapping Relationship | Direct Comparability |
|:---:|---|:---:|---|---|:---:|:---:|
| **P1** | Global CSP on all trials and labels | **P1** | Supervised Spatial Filter Contamination (CSP generalized eigenvectors fitted on all trials and labels) | `src/emi/pipeline.py` & `scripts/run_openbmi_benchmark.py` (`run_p1_csp_on_all_for_subject`) | **Exact Match** | **Fully Comparable** across cohorts |
| **P2** | Preprocessing/ICA fitted on pooled runs | **P2** | Global Continuous ICA Unmixing (ocular unmixing matrix fitted across concatenated recording runs) | Specified in `docs/V2/P2_SCIENTIFIC_DESIGN.md` | **Exact Match** | **Conceptually Aligned**; historical runs were exploratory |
| **P3 (hist)** | Global Feature Scaling / Normalization | **P5** | Global Feature Normalization (Z-score scaling $\mu, \sigma$ fitted across pooled train+test features) | Prototyped in `src/emi/pipeline.py` (`StandardScaler` fitted on all data) | **Re-indexed** (Moved P3 $\to$ P5) | **Must not be merged** with V2 P3 (Temporal Filtering) |
| **P4 (hist)** | Supervised Feature / Channel Selection | **P7** | Global Feature Selection (channel or frequency-band selection using ANOVA/mutual info on pooled data) | Formalized in registry schema `registry/schemas/leakage_mechanism.schema.json` | **Re-indexed** (Moved P4 $\to$ P7) | **Must not be merged** with V2 P4 (Temporal Window Peeking) |
| **P5 (hist)** | Hyperparameter snooping on test set | **P6** | Cross-Validation Hyperparameter Snooping (regularization $C$ or CSP components tuned to maximize test score) | Prototyped in `src/emi/pipeline.py` | **Re-indexed** (Moved P5 $\to$ P6) | **Must not be merged** with V2 P5 (Normalization) |
| **P6 (hist)** | Overlapping Epoch / Window Leakage | **P8** | Sliding Window Overlap Leakage (overlapping temporal sub-epochs allocated to different CV folds) | Formalized in registry schema | **Re-indexed** (Moved P6 $\to$ P8) | **Must not be merged** with V2 P6 (Hyperparameter Snooping) |
| **P7 (hist)** | Data Augmentation Contamination | **P8 / P9 variant** | Transductive data augmentation across fold boundaries | Documented in `docs/leakage_mechanisms.md` | **Subsumed** into structural pseudo-replication | **Unresolved**; separate protocol required |
| *None* | *Not formally isolated in early prototypes* | **P3 (new)** | Global Temporal Filtering (continuous FIR/IIR filtering crossing fold boundaries without filter warm-up) | Formalized in registry schema | **New Canonical Mechanism** | No historical V1.0 counterpart |
| *None* | *Not formally isolated in early prototypes* | **P4 (new)** | Temporal Window Peeking (optimizing post-cue classification window using test accuracy) | Formalized in registry schema | **New Canonical Mechanism** | No historical V1.0 counterpart |
| *None* | *Not formally isolated in early prototypes* | **P9 (new)** | Subject Identity Confounding (trials from the same subject partitioned across train and test in cross-subject models) | Formalized in registry schema | **New Canonical Mechanism** | No historical V1.0 counterpart |

---

## 2. Detailed Technical Reconciliations

### 2.1 Mechanism P1 (Supervised Spatial Filter Contamination)
- **Status**: Stable across all project versions.
- **Implementation**: The CSP generalized eigenvalue problem $\mathbf{\Sigma}_1 \mathbf{w} = \lambda \mathbf{\Sigma}_2 \mathbf{w}$ is fitted using all trials and their ground-truth labels $\mathbf{y}_{\text{all}}$.
- **Empirical Baseline**:
  - PhysioNet EEGMMIDB ($N=105$): $+24.50$ pp inflation ($95\%\ \text{BCa CI}: [+22.22, +27.78]$ pp, $p_{\text{Holm}} = 4.43 \times 10^{-18}, d_z = +1.771$).
  - OpenBMI ($N=34$): $+6.25$ pp inflation ($95\%\ \text{BCa CI}: [+3.25, +8.23]$ pp, $p_{\text{Holm}} = 1.87 \times 10^{-4}, d_z = +0.745$).

### 2.2 Mechanism P2 (Unsupervised ICA Spatial Decomposition)
- **Status**: Architecturally specified in V2 (`docs/V2/P2_SCIENTIFIC_DESIGN.md`).
- **Implementation**: FastICA or Infomax unmixing matrix $\mathbf{W}$ estimated on continuous EEG concatenated across runs versus run-nested unmixing matrices.
- **Critical Distinction**: Unsupervised nature means labels do not leak, but cross-run non-stationarities and subject state transitions are shared across train/test splits.

### 2.3 Mechanisms P3, P4, P5, P6, P7 Re-Indexing
- In early prototypes (prior to commit `002dc4f`):
  - Normalization leakage was labeled `P3`. In V2, it is canonically `P5`.
  - Feature selection leakage was labeled `P4`. In V2, it is canonically `P7`.
  - Hyperparameter snooping was labeled `P5`. In V2, it is canonically `P6`.
- **Policy**: Any historical logs or tables referencing `P3_scaling` or `P4_channel_select` must be cited with their full string names and mapped to V2 canonical IDs (P5 and P7, respectively) to prevent confusion with V2 P3 (Temporal Filter Leakage) and V2 P4 (Temporal Window Snooping).

---

## 3. Validation Design Separation: $D_{1m}$ vs. $D_{1s}$

In addition to the leakage mechanism migration, the cross-validation partition taxonomy was refined between V1.0 and V1.1:

| Partition ID | Partition Name | Fold Cardinality | Balancing Constraint | Scientific Purpose | Observed Effect on PhysioNet |
|:---:|---|---|---|---|:---:|
| **$D_3$** | Leave-One-Run-Out (LORO) | Natural run size ($15$ trials/fold) | Natural run balance ($7\text{--}8$ trials/class) | Clean reference baseline | $0.00$ pp (Reference) |
| **$D_{1m}$** | $k$-Matched Random Splitting | Arbitrary $k=3$ split ($15$ trials/fold) | Stratified overall | Evaluates impact of breaking run structure with fixed $k$ | **$-4.47$ pp deflation** ($p = 1.08 \times 10^{-8}$) |
| **$D_{1s}$** | Size- and Class-Matched Random Partition | Exactly matches each run's trial count | Exactly matches each run's per-class count | Isolates pure temporal shuffling by holding fold sample size constant | **$-2.68$ pp deflation** ($p = 5.86 \times 10^{-5}$) |

**Inviolable Rule**: Results from $D_{1m}$ and $D_{1s}$ must **never** be averaged, combined, or reported under a generic "random CV" label. They represent distinct experimental conditions that isolate fold size artifacts from temporal structure disruption.
