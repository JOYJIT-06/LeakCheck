# LeakCheck Scientific Methodology and Validation Protocols

## 1. Core Principles: Participant as the Unit of Analysis

In electroencephalography (EEG) and brain-computer interface (BCI) machine learning, pooling trials across participants creates severe pseudo-replication and ecological fallacies. In LeakCheck:
1. Every statistical summary, cross-validation split, and feature-transformation is evaluated **per participant**.
2. Group-level inference is computed across participant estimates ($N = 105$), using non-parametric paired estimators robust to outliers and skewed distributions.

---

## 2. Validation Designs Taxonomy (D1–D6)

| Design ID | Formal Name | Description | Grouping Constraint |
|---|---|---|---|
| **D1** | `D1_shuffled_kfold` | Unstratified random $k$-fold cross-validation ($k=5$). | None (trials shuffled across all runs). |
| **D2** | `D2_stratified_kfold` | Stratified random $k$-fold cross-validation ($k=5$). | Stratified by class labels; runs ignored. |
| **D1m** | `D1m_matched_k` | Stratified random $k$-fold where $k = \text{number of runs}$ (e.g., $k=3$). | Class stratified; $k$ matches LORO fold count. |
| **D1s** | `D1s_size_matched` | Size- and class-matched random split. | Exact trial counts and class balances match LORO folds, but trials are drawn randomly across runs. |
| **D3** | `D3_loro` | Clean Leave-One-Run-Out cross-validation. | Strict group holdout: no trial from held-out run enters training fold. |
| **D4** | `D4_chrono` | Chronological holdout (first $2/3$ train, final $1/3$ test). | Strict chronological order preserved. |
| **D4b** | `D4b_forward_chain` | Expanding-window forward chaining (walk-forward CV). | Test fold always occurs strictly after training fold in time. |
| **D5** | `D5_gap2` / `D5_gap4` | Chronological holdout with buffer gap ($g=2$ or $g=4$ trials discarded). | Evaluates temporal auto-correlation decay across adjacent trials. |
| **D6** | `D6_loso_session` | Leave-One-Session-Out cross-validation. | Across separate multi-day recording sessions. |

---

## 3. Data Leakage Taxonomy (P1–P7)

| Leakage ID | Mechanism | Correct Comparator | Leaky Pipeline Failure Mode |
|---|---|---|---|
| **P1** | Global Spatial Filtering | `D3_loro` | Fitting Common Spatial Patterns (CSP) across all runs before cross-validation. Spatial filters learn test labels. |
| **P2** | Global Artifact Removal | Clean fold-nested ICA | Fitting ICA or continuous temporal filters across test epochs. |
| **P3** | Global Channel Scaling | `P3_scale_inside` | Normalizing channels using mean/variance computed across all trials. |
| **P4** | Global Channel Selection | `P4_select_inside` | Selecting $K$ most informative channels using mutual information / ANOVA on all trials before CV. |
| **P5** | Test-Fold Hyperparameter Tuning | `P5_tune_nested` | Choosing optimal time window or regularizer by inspecting test-fold accuracy. |
| **P6** | Overlapping Window Splitting | `P6_overlap_loro` | Generating overlapping sub-windows from continuous trials and randomly partitioning them into train and test. |
| **P7** | Pre-Split Data Augmentation | `P7_aug_train_only` | Augmenting trials (jitter, noise injection) before partitioning, allowing augmented pairs into both train and test. |

---

## 4. Statistical Estimation and Hypothesis Testing

### 4.1 Paired Inflation Metric ($\Delta$)
For participant $i$, given leaky design $L$ and reference design $R$:
$$\Delta_i = \text{Accuracy}_i(L) - \text{Accuracy}_i(R) \quad (\text{expressed in percentage points})$$

### 4.2 Hodges-Lehmann Median Difference
Rather than assuming normality, the central location of $\Delta$ is estimated via the Hodges-Lehmann pseudo-median:
$$\widehat{\Delta}_{\text{HL}} = \text{median}\left\{ \frac{\Delta_i + \Delta_j}{2} \;\middle|\; 1 \le i \le j \le N \right\}$$

### 4.3 Bias-Corrected and Accelerated (BCa) Bootstrap Confidence Interval
Confidence intervals ($95\%$) for $\widehat{\Delta}_{\text{HL}}$ are computed via $B = 2,000$ BCa bootstrap resamples, correcting for both distribution asymmetry and acceleration.

### 4.4 Non-Parametric Significance
- **Wilcoxon Signed-Rank Test**: Tests null hypothesis $H_0: \Delta = 0$.
- **Family-Wise Error Rate Control**: Holm-Bonferroni step-down correction applied within each decoder family.
- **Cohen's $d_z$ Effect Size**:
  $$d_z = \frac{\overline{\Delta}}{s_{\Delta}}$$

### 4.5 Two One-Sided Tests (TOST) for Equivalence
To test whether an injected leakage or validation variation is negligible, TOST tests against equivalence bounds $[-\delta, +\delta]$ with default margin $\delta = 2.0$ pp:
$$H_0^-: \Delta \le -2.0 \quad \text{vs} \quad H_1^-: \Delta > -2.0$$
$$H_0^+: \Delta \ge +2.0 \quad \text{vs} \quad H_1^+: \Delta < +2.0$$
Equivalence is declared only when both one-sided null hypotheses are rejected ($p < 0.05$).

---

## 5. Negative Control Null Framework

Every decoding pipeline must be evaluated under label permutations:
1. **Within-Run Permutation (`perm`)**: Labels are permuted independently within each run, preserving per-run class ratios while breaking brain-behavior relationships.
2. **Circular Shift (`shift`)**: Labels are shifted circularly within each run, preserving autocorrelation and sequence transitions while misaligning trials.

A methodologically sound negative control must satisfy:
- Mean null accuracy: $50.0\% \pm \epsilon$.
- False positive rate (FPR) at nominal $\alpha = 0.05$: $\le 5\%$.
