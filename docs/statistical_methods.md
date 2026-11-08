# Statistical Methods and Non-Parametric Inference

This document details the statistical methodology employed by LeakCheck to evaluate validation design differences and leakage effects with rigorous, publication-grade non-parametric inference.

---

## 1. Participant-Level Inference Principle

In neuroimaging machine learning, cross-validation folds within a single participant are non-independent. Reporting statistical significance (e.g. t-tests or ANOVA) across individual folds or single trials is a severe pseudoreplication error that drastically inflates Type I error rates.

**LeakCheck enforces strict participant-level aggregation**:
1. All cross-validation predictions are pooled to compute a single scalar accuracy metric per participant per design:
   $$A_{i, \text{design}} = \frac{1}{M_{\text{trials}}} \sum_{k=1}^K \sum_{j \in \mathcal{T}_k} \mathbb{I}(\hat{y}_j = y_j)$$
2. All hypothesis tests and confidence intervals are computed on the paired participant-level differences:
   $$D_i = A_{i, \text{contrast}} - A_{i, \text{baseline}} \quad \text{for } i \in \{1, \dots, N\}$$

---

## 2. Hodges-Lehmann Estimator ($\Delta_{\text{HL}}$)

Because classification accuracy differences in BCI cohorts are bounded, heteroskedastic, and often skewed, the sample mean can be biased by extreme outliers. LeakCheck employs the **Hodges-Lehmann pseudo-median estimator**:

$$\Delta_{\text{HL}} = \operatorname{median}_{1 \le i \le j \le N} \left( \frac{D_i + D_j}{2} \right)$$

### Properties
- Consistent estimator of the median difference for symmetric continuous distributions.
- Highly resistant to single-participant anomalies (breakdown point $\approx 29\%$).
- Directly dual to the Wilcoxon signed-rank test statistic.

---

## 3. Bias-Corrected and Accelerated (BCa) Bootstrap CIs

To provide distribution-free confidence intervals that adjust for both median bias and skewness in the bootstrap distribution, LeakCheck computes 95% BCa confidence intervals using $B = 2{,}000$ bootstrap resamples.

### Mathematical Formulation
Let $\hat{\theta} = \Delta_{\text{HL}}(\mathbf{D})$ be the sample estimate, and $\hat{\theta}^*_{(b)}$ be the estimate from the $b$-th bootstrap replicate.
The interval endpoints are determined by percentiles $\alpha_1, \alpha_2$ of the bootstrap distribution:

$$\alpha_1 = \Phi \left( \hat{z}_0 + \frac{\hat{z}_0 + z_{\alpha/2}}{1 - \hat{a}(\hat{z}_0 + z_{\alpha/2})} \right)$$
$$\alpha_2 = \Phi \left( \hat{z}_0 + \frac{\hat{z}_0 + z_{1 - \alpha/2}}{1 - \hat{a}(\hat{z}_0 + z_{1 - \alpha/2})} \right)$$

where:
- $\Phi$ is the standard normal cumulative distribution function.
- $\hat{z}_0 = \Phi^{-1} \left( \frac{1}{B} \sum_{b=1}^B \mathbb{I}(\hat{\theta}^*_{(b)} < \hat{\theta}) \right)$ is the bias-correction parameter.
- $\hat{a} = \frac{\sum_{i=1}^N (\bar{U} - U_{(i)})^3}{6 \left[ \sum_{i=1}^N (\bar{U} - U_{(i)})^2 \right]^{3/2}}$ is the acceleration parameter estimated via jackknife resampling ($U_{(i)} = \hat{\theta}_{(i)}$).

---

## 4. Wilcoxon-Pratt Signed-Rank Test

To test the null hypothesis $H_0: \Delta = 0$ without assuming normality, LeakCheck uses the two-sided **Wilcoxon signed-rank test with Pratt zero-handling**:

1. Compute absolute differences $|D_i|$.
2. Rank all $|D_i|$ including zero differences ($D_i = 0$).
3. The test statistic $W$ sums the ranks of positive differences:
   $$W = \sum_{i: D_i > 0} \operatorname{rank}(|D_i|)$$
4. The exact distribution or continuity-corrected asymptotic normal approximation computes the two-sided p-value $p_{\text{raw}}$.

> [!NOTE]
> Unlike standard Wilcoxon-Wilcox zero-handling (which discards ties $D_i = 0$ and artificially reduces sample size), the **Pratt modification** retains zero differences during ranking, preserving the full sample size $N$ and providing conservative Type I error control.

---

## 5. Multiplicity Correction: Holm-Bonferroni

When testing multiple design comparisons against the baseline ($D_3$), raw p-values are adjusted using the step-down **Holm-Bonferroni method** to control the Family-Wise Error Rate (FWER) at $\alpha = 0.05$:

1. Sort raw p-values in ascending order: $p_{(1)} \le p_{(2)} \le \dots \le p_{(m)}$.
2. Compare each $p_{(k)}$ against the adjusted threshold:
   $$\alpha_k = \frac{\alpha}{m - k + 1}$$
3. Reject $H_{(k)}$ if $p_{(j)} \le \alpha_j$ for all $j \le k$.
4. The adjusted p-value is:
   $$p_{(k)}^{\text{Holm}} = \min \left( 1, \max_{j \le k} \left[ (m - j + 1) p_{(j)} \right] \right)$$

---

## 6. Within-Subject Effect Size ($d_z$)

To measure practical significance independent of sample size, LeakCheck computes the within-subject standardized mean difference:

$$d_z = \frac{\bar{D}}{s_D} = \frac{\frac{1}{N} \sum_{i=1}^N D_i}{\sqrt{\frac{1}{N - 1} \sum_{i=1}^N (D_i - \bar{D})^2}}$$

- $|d_z| \ge 0.2$: Small effect
- $|d_z| \ge 0.5$: Medium effect
- $|d_z| \ge 0.8$: Large effect ($d_z = 1.771$ observed for P1 spatial filter leakage)

---

## 7. Cross-Cohort Random-Effects Meta-Analysis

To synthesize findings across multiple cohorts (e.g. PhysioNet and OpenBMI), LeakCheck implements the DerSimonian-Laird random-effects model:

$$\theta_{\text{pooled}} = \frac{\sum_k w_k^* \hat{\theta}_k}{\sum_k w_k^*}, \quad w_k^* = \frac{1}{\operatorname{Var}(\hat{\theta}_k) + \tau^2}$$

where $\tau^2$ is the between-study variance estimated via Cochran's $Q$:
$$Q = \sum_k w_k (\hat{\theta}_k - \bar{\theta})^2, \quad \tau^2 = \max\left(0, \frac{Q - (K - 1)}{\sum_k w_k - \frac{\sum_k w_k^2}{\sum_k w_k}}\right)$$
$$I^2 = \max\left(0, \frac{Q - (K - 1)}{Q}\right) \times 100\%$$
