# SCIENTIFIC PROTOCOL & VALIDATION DESIGN AUDIT

**Audit Date**: November 18, 2026 (Stage 2 / Day 2)  
**Lead Auditor**: LEAD (Scientific Project Director) & AGENT 5 (Dataset & Design Specialist)  
**Scope**: Experimental Designs, Leakage Mechanisms, and Comparative Hypotheses  

---

## 1. Experimental Validation Designs

LeakCheck V1.1 defines four core validation designs across all $N=105$ eligible participants:

| Design | Name | Partition Strategy | Training Size | Testing Size | Evaluation Mechanics | Primary Role |
| :---: | :--- | :--- | :---: | :---: | :--- | :--- |
| **$D_3$** | Leave-One-Run-Out (LORO) | 3-fold run-held-out (Runs 4, 8 vs 12; 4, 12 vs 8; 8, 12 vs 4) | 30 trials | 15 trials | Run-independent filtering; fold-isolated models | **Primary Reference Protocol** |
| **$D_{1m}$** | Matched-K Random Split | 3-fold random CV across interleaved within-run trials | 30 trials | 15 trials | 5 repeats $\times$ 3 folds = 15 fits | Interleaved random-split comparator |
| **$D_{1s}$** | Size-Matched Random Split | Repeated random 2/3 train, 1/3 test split | 30 trials | 15 trials | 20 independent repeated splits | Repeated random-split comparator |
| **$P_1$** | Global CSP Positive Control | CSP fitted globally across all 45 trials; LORO test split | 30 trials | 15 trials | 3 folds using global spatial filters | **Intentional Positive Control** |

---

## 2. Validation Leakage Mechanisms ($P_1 – P_9$)

The framework systematically investigates nine potential leakage mechanisms:

1. **$P_1$ (Global Spatial Filtering)**: Fitting CSP across training and test trials simultaneously. Produces severe upward validation bias ($+24.50\text{ pp}$).
2. **$P_2$ (Global Normalization / Scaling)**: Estimating channel means and variances using all trials.
3. **$P_3$ (Feature Selection Bleed)**: Ranking or selecting spatial components using test labels.
4. **$P_4$ (Hyperparameter Tuning Bleed)**: Optimizing regularization parameters $\lambda$ on test folds.
5. **$P_5$ (Data Augmentation Bleed)**: Synthesizing trials from unpartitioned data distributions.
6. **$P_6$ (Channel Selection Bleed)**: Pruning channels based on whole-session discriminability.
7. **$P_7$ (Transductive ICA Unmixing)**: Unmixing continuous test data using full-recording ICA.
8. **$P_8$ (Temporal Boundary Leakage)**: Shared FIR filter tails and within-run temporal autocorrelation in random trial splits.
9. **$P_9$ (Label Permutation Null Corruption)**: Shuffling labels after feature extraction rather than before preprocessing.

---

## 3. Confirmatory Comparative Hypotheses

The confirmatory statistical architecture tests three pre-specified pairwise contrasts under Holm FWER control:
1. **$H_1$: $P_1$ vs. $D_3$ (Spatial Filter Leakage)**: Demonstrates that global CSP produces statistically significant, massive performance inflation.
2. **$H_2$: $D_{1s}$ vs. $D_3$ (Size-Matched Validation Bias)**: Tests whether size-matched random partitioning inflates performance relative to run-held-out cross-validation.
3. **$H_3$: $D_{1m}$ vs. $D_3$ (Matched-K Validation Bias)**: Tests whether 3-fold interleaved partitioning inflates performance relative to run-held-out cross-validation.

---

## 4. Scientific Audit Conclusion

The four experimental designs isolate the intended validation leakage mechanisms cleanly. Preprocessing and feature extraction pipelines conform to IEEE TNSRE neuroengineering standards, provided that fold isolation is enforced for adaptive operations in Day 4.
