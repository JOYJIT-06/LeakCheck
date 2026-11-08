# LeakCheck Quick-Start Guide

Get up and running with **LeakCheck** in under 5 minutes. This guide walks you through verifying your setup, running a self-contained leakage audit on synthetic EEG, and running your first single-participant audit on real neuroimaging data.

---

## 1. 60-Second Zero-Download Verification

LeakCheck includes a standalone synthetic generator that constructs a 3-run motor imagery session (60 trials, 16 channels, 160 Hz) and audits validation designs and leakage mechanisms without downloading any external datasets.

Run:
```bash
python scripts/quickstart_demo.py
```

### What Happens
1. **Synthetic Data Generation**: Generates 3 recording runs with distinct baseline DC-offsets and contralateral sensorimotor rhythm ($12\text{ Hz}$ mu/beta) modulations during motor imagery intervals.
2. **Audit Execution**:
   - Evaluates **$D_3$ (Clean Leave-One-Run-Out)**: Operational benchmark ensuring strict run-level isolation.
   - Evaluates **$D_{1s}$ (Size-Matched Random Partition)**: Tests whether random trial shuffling across runs inflates or deflates cross-validation accuracy.
   - Evaluates **$P_1$ (Supervised Spatial Filter Leakage)**: Demonstrates the artificial inflation caused by computing Common Spatial Pattern (CSP) filters globally on all data prior to fold splitting.
3. **Dual Decoder Comparison**: Contrasts Shrinkage CSP-LDA with Riemannian Tangent Space Logistic Regression (`ts_lr`).

### Sample Terminal Output
```
================================================================================
                    LeakCheck v1.1 Quick-Start Demonstration                     
================================================================================
Package: emi v1.1.0
Generating synthetic 3-run motor imagery dataset (60 trials, 16 channels, 160 Hz)...
Dataset generated in 0.01 s. No external downloads required.

Auditing validation designs and leakage mechanisms:
  1. D3_loro          : Clean Leave-One-Run-Out (operational benchmark)
  2. D1s_size_matched : Size- and class-matched pooled random partition
  3. P1_csp_on_all    : Supervised spatial filtering leakage (CSP on all trials)

Evaluating decoders: Shrinkage CSP-LDA and Riemannian TS-LR...

-------------------------------- AUDIT RESULTS --------------------------------
          Decoder D3 (LORO, %) D1s (Random, %) D1s Bias (pp) P1 (Leaky, %) P1 Inflation (pp)
Shrinkage CSP-LDA        96.7%           96.7%       -0.0 pp         98.3%           +1.7 pp
 Riemannian TS-LR       100.0%          100.0%       +0.0 pp           N/A      N/A (No CSP)
--------------------------------------------------------------------------------

Key Scientific Takeaways:
  * P1 Inflation : Supervised spatial filters fit on all trials encode test-set labels.
  * D1s vs D3    : Random trial pooling alters cross-run non-stationarity exposure.
  * Decoder Diff : Riemannian TS-LR is less vulnerable to global CSP-style contamination.

Demo completed successfully in 1.36 seconds!
================================================================================
```

---

## 2. Using the Python API in 3 Lines of Code

You can audit any NumPy-formatted EEG dataset directly in Python:

```python
import numpy as np
from emi.leakcheck import audit_subject

# X: (n_trials, n_channels, n_times)
# y: (n_trials,) with integer labels (e.g. 0 and 1)
# runs: (n_trials,) recording block or session identifiers (e.g. 0, 1, 2)
# times: (n_times,) time vector in seconds relative to cue onset

results_df = audit_subject(
    X=X,
    y=y,
    runs=runs,
    times=times,
    subject=1,
    decoders=["csp_lda", "ts_lr"],
    designs=["D3_loro", "D1s_size_matched", "P1_csp_on_all"],
    n_null=0,             # Set > 0 (e.g. 200) for permutation null distributions
    n_repeats_matched=5,  # Number of random shuffle repetitions for D1s
    seed=42,
)

# Display tabular comparison
print(results_df[["decoder", "design", "acc_pooled", "bal_acc_pooled"]])
```

---

## 3. Auditing a Real Participant via the Command Line

To run an audit on a single participant of the PhysioNet EEG Motor Movement/Imagery dataset (which will automatically download and cache participant 1 if not present locally):

```bash
python scripts/run_leakcheck.py \
    --subjects 1 \
    --designs D3_loro,D1s_size_matched,P1_csp_on_all \
    --decoders csp_lda \
    --n-null 0 \
    --outdir results_quickstart
```

### Output Files Produced
All outputs are structured under `results_quickstart/`:
- `results_quickstart/fold_metrics.csv`: Fold-level performance for each cross-validation split.
- `results_quickstart/participant_metrics.csv`: Aggregated accuracy, balanced accuracy, and AUROC per design.
- `results_quickstart/design_comparisons.csv`: Paired differences ($\Delta = \text{Design} - D_3$) capturing the empirical leakage or partition effect.

---

## 4. Next Steps

- For full parameter details and CLI options, see the [User Guide](user_guide.md).
- To understand each validation design ($D_1$–$D_6$), see [Benchmark Protocols](benchmark_protocols.md).
- To inspect how leakage mechanisms $P_1$–$P_9$ contaminate pipelines, see [Leakage Mechanisms](leakage_mechanisms.md).
- To prepare the OpenBMI dataset or configure custom adapters, see [Datasets Guide](datasets.md).
