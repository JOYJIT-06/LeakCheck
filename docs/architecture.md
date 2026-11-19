# Software Architecture and Design Contracts

This document outlines the architectural principles, component seams, and extensibility patterns of the **LeakCheck** framework (`emi`).

---

## 1. Architectural Principles

LeakCheck is built on five core scientific software engineering principles:
1. **Label-Blind Transformations**: All signal preprocessing (filtering, bad-channel interpolation, ICA ocular artifact removal) must never access trial class labels.
2. **Strict Pipeline Encapsulation**: Any parameter learned from data (CSP spatial filters, whitening transforms, Riemannian Fréchet reference points, normalization scalers) must be fit solely on the designated training fold.
3. **Immutability of Historical Evidence**: Previous benchmark outputs (e.g. `benchmark_results/physionet_v1/`) are cryptographically sealed and never mutated by newer runs.
4. **Zero Proprietary Dependencies**: Core algorithms rely exclusively on foundational scientific Python packages (NumPy, SciPy, Scikit-Learn, MNE, Pandas).
5. **Multi-Dataset Polymorphism**: A unified abstract interface (`BaseEEGDataset`) decouples decoding and auditing engines from raw neuroimaging file formats (EDF, GDF, MAT, BIDS).

---

## 2. Layered Component Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CLI & Script Runners Layer                            │
│   scripts/run_leakcheck.py              scripts/run_Multi-Dataset_benchmark.py    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                    Auditing & Cross-Validation Engine                       │
│   src/emi/leakcheck.py                  src/emi/splitters.py                │
│   - audit_subject()                     - loro_splits()                     │
│   - Design dispatch table               - size_matched_random_repeats()     │
│   - Injected leakage hooks (P1-P9)      - chrono_holdout()                  │
└──────────────────┬───────────────────────────────────────────┬──────────────┘
                   │                                           │
┌──────────────────▼──────────────────────┐ ┌──────────────────▼──────────────┐
│         Decoders & Transformers         │ │       Datasets & Ingestion          │
│   src/emi/decoders.py                   │ │   src/emi/data.py               │
│   - mne_csp_factory()                   │ │   src/emi/preprocess.py         │
│   - CovarianceTransformer (NumPy)       │ │   - PhysioNet EEGMMIDB          │
│   - TangentSpaceTransformer (NumPy)     │ │   - (Multi-dataset in archive/) │
│   - DecoderSpec registry                │ │   - Epoch Caching (data/cache)  │
└──────────────────┬──────────────────────┘ └──────────────────┬──────────────┘
                   │                                           │
┌──────────────────▼───────────────────────────────────────────▼──────────────┐
│                    Statistical & Registry Standards                         │
│   src/emi/stats.py                      registry/schemas/                   │
│   - hodges_lehmann()                    - dataset.schema.json               │
│   - bca_bootstrap_ci()                  - pipeline.schema.json              │
│   - wilcoxon_pratt()                    - benchmark.schema.json             │
│   - holm_bonferroni()                   - leakage.schema.json               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Subsystems

### 3.1 Datasets and Ingestion (`src/emi/data.py`, `src/emi/preprocess.py`)
Provides deterministic ingestion, filtering, and epoching for PhysioNet EEGMMIDB recordings.
- **`src/emi/data.py`**: Fetches and parses PhysioNet BCI2000 EDF files, handles channel layout, and verifies subject eligibility.
- **`src/emi/preprocess.py`**: Label-blind 5th-order Butterworth bandpass filtering (8.0–30.0 Hz), epoch windowing ([+1.0, +3.0] s), and peak-to-peak artifact rejection.
- **`branch 

### 3.2 Splitting Engine (`src/emi/splitters.py`)
Deterministic, index-safe partitioning functions:
- `loro_splits(runs)`: Yields train/test index pairs grouping by recording block.
- `size_matched_random_repeats(runs, y, n_repeats, seed)`: Exact cardinality matching per class and fold.
- `kfold_stratified_repeats(y, n_splits, n_repeats, seed)`: Standard repeated stratified $k$-fold cross-validation.

### 3.3 Decoders and Feature Extractors (`src/emi/decoders.py`)
Implements both spatial filtering and Riemannian manifold pipelines:
- **`DecoderSpec`**: Declarative contract specifying `(name, factory, uses_csp, uses_riemannian, description)`.
- **`CovarianceTransformer`**: Computes empirical, OAS, or Ledoit-Wolf sample covariance matrices.
- **`TangentSpaceTransformer`**: Maps symmetric positive-definite (SPD) covariance matrices to the Euclidean tangent space at the Riemannian geometric mean (Fréchet mean) via:
  $$\mathbf{S} = \mathbf{C}_{\text{ref}}^{1/2} \log\left(\mathbf{C}_{\text{ref}}^{-1/2} \mathbf{C} \mathbf{C}_{\text{ref}}^{-1/2}\right) \mathbf{C}_{\text{ref}}^{1/2}$$

### 3.4 Non-Parametric Statistics (`src/emi/stats.py`)
- Provides verified implementations of `hodges_lehmann()`, `bca_bootstrap_ci()`, `wilcoxon_pratt()`, and `holm_bonferroni()`.
- Guarantees zero pseudoreplication by requiring participant-aggregated paired difference vectors.

---

## 4. EEG Benchmark Registry Standards (`registry/schemas/`)

To support open science and reproducible meta-benchmarks, LeakCheck introduces standard JSON schemas:
- `dataset.schema.json`: Formal schema for neuroimaging dataset provenance, licensing, and electrode layouts.
- `pipeline.schema.json`: Preprocessing cutoffs, filtering orders, and artifact rejection criteria.
- `benchmark.schema.json`: Cross-validation protocols ($D_1$–$D_6$), seeds, and metric definitions.
- `leakage.schema.json`: Formal definitions of leakage types (P1–P9) and mathematical contamination pathways.
- `reproducibility.schema.json`: Environment hashes, package dependencies, CPU models, and result checksums.

---

## 5. Adding New Extensions

### Adding a New Decoder
1. Define a pipeline factory function in `src/emi/decoders.py`:
   ```python
   def make_my_decoder(seed: int = 0) -> Pipeline:
       return Pipeline([
           ("cov", CovarianceTransformer(estimator="oas")),
           ("ts", TangentSpaceTransformer()),
           ("clf", ElasticNet(random_state=seed)),
       ])
   ```
2. Register the decoder in `DECODER_SPECS`:
   ```python
   DECODER_SPECS["my_decoder"] = DecoderSpec(
       name="my_decoder",
       factory=make_my_decoder,
       uses_csp=False,
       uses_riemannian=True,
       description="ElasticNet Tangent Space Decoder",
   )
   ```

### Multi-Dataset Research Scope
Pluggable multi-dataset adapters and cross-dataset benchmarks are maintained in Git history on branch `v2-dev` to ensure strict release isolation for the standalone V1.1 PhysioNet study.
