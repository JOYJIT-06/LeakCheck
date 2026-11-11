# Validation Benchmark Protocols

This document defines the formal validation designs supported by LeakCheck, detailing their partitioning mathematics, intended evaluation targets, and prevention of cross-run information snooping.

---

## 1. Design Overview

In neuroimaging and brain-computer interface research, machine learning decoders are frequently evaluated using naive cross-validation schemes that pool and shuffle trials across recording blocks. LeakCheck formally defines and evaluates six distinct validation architectures:

| Design Key | Name | Structure | Operational Target | Information Isolation |
|---|---|---|---|---|
| **`D3_loro`** | Leave-One-Run-Out (LORO) | $K$-fold cross-validation where each fold corresponds to an entire physical recording run. | Real-world online deployment across sessions/blocks. | **Complete Run Isolation**: Training and test sets never share recording blocks. |
| **`D1s_size_matched`** | Size-Matched Random Partition | $K$-fold random partition where each fold has **identical sample size and class balance** to `D3_loro`. | Tests whether trial shuffling per se distorts generalisation estimates. | Shuffled: Trials from the same run appear in both train and test partitions. |
| **`D1m_matched_k`** | $k$-Matched Random Partition | Standard stratified $K$-fold cross-validation where $k = K_{\text{runs}}$. | Conventional BCI literature benchmark. | Shuffled: Run identities discarded; trials distributed uniformly. |
| **`D1_kfold`** | Standard 5-fold / 10-fold CV | Standard $k$-fold cross-validation across all pooled trials. | Naive machine learning baseline. | Shuffled: Arbitrary fold boundaries without run or size alignment. |
| **`D4_chrono`** | Chronological Forward Split | Train on runs $1 \dots K-1$, test on the subsequent run $K$. | Simulates prospective forward deployment over time. | Temporal isolation: No future data available to training fold. |
| **`D5_within_run`** | Within-Run Cross-Validation | Independent cross-validation performed inside each run, then averaged. | Measures instantaneous, intra-run decoder capacity. | Intra-run only: Decoders never generalize across recording blocks. |

---

## 2. Mathematical Formalization

Let a participant recording be denoted as $\mathcal{D} = \{(\mathbf{x}_i, y_i, r_i)\}_{i=1}^N$, where:
- $\mathbf{x}_i \in \mathbb{R}^{C \times T}$ is the single-trial EEG epoch with $C$ channels and $T$ time samples.
- $y_i \in \{0, 1\}$ is the class label (e.g., Left vs. Right hand motor imagery).
- $r_i \in \{1, \dots, K\}$ is the recording run or block index.

### 2.1 Design $D_3$: Leave-One-Run-Out (LORO)
For each run $k \in \{1, \dots, K\}$:
$$\mathcal{D}_{\text{test}}^{(k)} = \{(\mathbf{x}_i, y_i, r_i) \mid r_i = k\}$$
$$\mathcal{D}_{\text{train}}^{(k)} = \{(\mathbf{x}_i, y_i, r_i) \mid r_i \neq k\}$$

The model is fit strictly on $\mathcal{D}_{\text{train}}^{(k)}$ (including spatial filtering, normalization, and classifier training) and evaluated on $\mathcal{D}_{\text{test}}^{(k)}$.

### 2.2 Design $D_{1s}$: Size- and Class-Matched Random Partition
The headline open question in BCI validation was whether performance differences between $D_1$ and $D_3$ were driven by sample size artifacts or inter-run non-stationarity. $D_{1s}$ isolates this question by enforcing strict cardinality matching:

Let $N_{k, c} = |\{i \mid r_i = k \land y_i = c\}|$ be the number of class-$c$ trials in run $k$ under $D_3$. For repetition $m \in \{1, \dots, M\}$:
1. Pool all trials across runs: $\mathcal{D}_c = \{(\mathbf{x}_i, y_i) \mid y_i = c\}$.
2. For each fold $k \in \{1, \dots, K\}$, randomly sample exactly $N_{k, c}$ trials without replacement from $\mathcal{D}_c$ to form the test partition $\mathcal{S}_{\text{test}}^{(k, m)}$.
3. Assign the remaining trials to $\mathcal{S}_{\text{train}}^{(k, m)}$.

By construction:
$$|\mathcal{S}_{\text{test}}^{(k, m)}| \equiv |\mathcal{D}_{\text{test}}^{(k)}| \quad \text{and} \quad |\{i \in \mathcal{S}_{\text{test}}^{(k, m)} \mid y_i = c\}| \equiv |\{i \in \mathcal{D}_{\text{test}}^{(k)} \mid y_i = c\}|$$

Any divergence between $D_{1s}$ and $D_3$ is therefore attributable **purely to the distribution of runs**, completely ruling out sample size or class imbalance confounds.

---

## 3. Directionality of Partition Effects

A major scientific contribution of LeakCheck is uncovering that the direction of the partition effect ($\Delta = D_{1s} - D_3$) is **paradigm- and non-stationarity-dependent**:

```
PhysioNet EEGMMIDB (Runs 4, 8, 12):
  Stationary motor imagery across identical blocks.
  Slow sensor impedance drift over time creates inter-run distribution shifts.
  Result: D1s deflates performance relative to D3 (Δ_HL = -2.68 pp, p = 5.86e-5).
  Why: Mixing trials across runs forces the decoder to fit noisy cross-block interpolations.

OpenBMI (Session 1: Run 0 vs. Run 1):
  Run 0 is offline calibration without feedback; Run 1 is online feedback.
  These represent two qualitatively distinct operational regimes.
  Result: D1s inflates performance relative to D3 (Δ_HL = +2.84 pp, p = 1.87e-4).
  Why: Pooling trials enables the decoder to interpolate within both regimes rather
  than having to extrapolate from an offline state to an online feedback state.
```

---

## 4. LeakCheck Splitting Engine

The splitting algorithms are implemented in `src/emi/splitters.py` and strictly guarantee:
1. **Zero Index Overlap**: $\mathcal{I}_{\text{train}} \cap \mathcal{I}_{\text{test}} = \emptyset$ for every fold.
2. **Determinism**: Split seeds are logged and reproducible.
3. **Multiplicity Controls**: When repeated random splits are used (e.g. $M = 5$ repetitions), metrics are pooled across all evaluated test folds before computing participant-level statistics.
