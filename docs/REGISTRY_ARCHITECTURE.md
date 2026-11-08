# EEG Benchmark Registry Architecture

## 1. Vision and Ecosystem Positioning

The **EEG Benchmark Registry** is a federated, open-science infrastructure designed to catalog, standardize, and validate:
- Public and private EEG datasets.
- Preprocessing and signal cleaning pipelines.
- Decoding and machine-learning models.
- Cross-validation protocols and benchmark definitions.
- Empirical leakage audits and negative-control verifications.
- Reproducibility records and software environment snapshots.

LeakCheck provides the core validation and leakage-auditing engine within this registry ecosystem.

```
+-------------------------------------------------------------+
|                  EEG Benchmark Registry                     |
+-------------------------------------------------------------+
                               |
         +---------------------+---------------------+
         |                                           |
         v                                           v
+------------------+                       +-------------------+
| Dataset Metadata |                       | Benchmark Record  |
|  (BIDS / Schema) |                       | (Protocols D1-D6) |
+------------------+                       +-------------------+
         |                                           |
         +---------------------+---------------------+
                               |
                               v
               +-------------------------------+
               |    LeakCheck Auditing Engine  |
               | (Nulls, P1-P7, TOST, HL Diff) |
               +-------------------------------+
                               |
                               v
               +-------------------------------+
               |   Reproducibility Record      |
               |   (Git, Env, Hashes, Provenance)|
               +-------------------------------+
```

---

## 2. Core Entities and Schemas

### 2.1 Dataset Entity (`dataset.schema.json`)
Defines raw data provenance, recording modalities, channel montages, participant demographics, sampling frequencies, and BIDS compliance.

### 2.2 Preprocessing Pipeline (`pipeline.schema.json`)
Specifies deterministic filtering bands, bad channel outlier criteria, rereferencing schemes, ICA artifact policies, and label-blind trial rejection thresholds.

### 2.3 Benchmark Protocol (`benchmark.schema.json`)
Defines the cross-validation partitioning structure (D1–D6), target task definitions (e.g. left vs. right hand motor imagery), fold generation random seeds, and primary evaluation metrics.

### 2.4 Leakage Mechanism Specification (`leakage_mechanism.schema.json`)
Catalogs data contamination failure modes (P1–P7), defining the exact code intervention, comparator clean pipeline, and expected direction of bias.

### 2.5 Reproducibility Record (`reproducibility_record.schema.json`)
Captures complete computational provenance: Git commit hashes, software package dependencies (NumPy, SciPy, MNE, Scikit-Learn), dataset file checksums (SHA-256), and execution runtimes.
