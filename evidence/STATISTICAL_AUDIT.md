# STATISTICAL METHODS & NUMERICAL AUDIT

**Audit Date**: November 18, 2026 (Stage 2 / Day 2)  
**Lead Auditor**: AGENT 2 (Biostatistician & Numerical Validation Specialist)  
**Reviewer**: LEAD (Scientific Project Director)  
**Target Codebase**: `src/emi/leakstats.py`, `recalculate_all_stats.py`, `analysis/R_validation/reproduce_statistics.R`  

---

## 1. Pratt Signed-Rank Test Audit

### 1.1 Mathematical Formulation & Verification
In `src/emi/leakstats.py` (`wilcoxon_pratt`), paired participant accuracy differences are $d_i = 100(A_{\mathrm{leaky},i} - A_{\mathrm{reference},i})$ for $i = 1, \dots, N$ ($N=105$).

1. **Zero Difference Classification**:
   - Observations satisfying $|d_i| \le 10^{-9}\text{ percentage points}$ are classified as zeros.
   - Count of zero differences: $t_0 = \sum_{i=1}^N \mathbb{I}(|d_i| \le 10^{-9})$.
2. **Ranking Procedure**:
   - Absolute differences $|d_i|$ (including zeros) are ranked jointly from $1$ to $N$, with average ranks assigned to ties. Let $R_i$ be the rank of observation $i$.
3. **Test Statistic**:
   $$W^+ = \sum_{i: d_i > 0} R_i$$
4. **Expected Null Mean**:
   $$\mu_W = \frac{N(N+1) - t_0(t_0+1)}{4}$$
5. **Null Variance & Verified Defect in Legacy Code**:
   - *Verified Defect*: In the legacy implementation, the variance formula included the zero group $t_0$ inside the general tie correction summation $\sum_{j=1}^K (t_j^3 - t_j)$, effectively subtracting the zero tie adjustment twice.
   - *Corrected Cureton (1967) Formula*:
     $$\sigma_W^2 = \frac{N(N+1)(2N+1) - t_0(t_0+1)(2t_0+1) - \frac{1}{2}\sum_{j \in \text{nonzero}} (t_j^3 - t_j)}{24}$$
   - *Confirmation*: Matches SciPy 1.14.1 reference implementation `scipy.stats._wilcoxon._wilcoxon_statistic` exactly.
6. **Continuity-Corrected Z-Score & P-Value**:
   $$z = \frac{W^+ - \mu_W - 0.5 \cdot \text{sgn}(W^+ - \mu_W)}{\sigma_W}, \quad p = 2 \cdot (1 - \Phi(|z|))$$

---

## 2. Effect Estimates Audit

The audit establishes three distinct estimators that must not be conflated:
1. **Mean Paired Difference**:
   $$\bar{d} = \frac{1}{N}\sum_{i=1}^N d_i$$
   Parametric measure of average shift; sensitive to outliers.
2. **Median Paired Difference**:
   $$\tilde{d} = \text{median}(d_1, \dots, d_N)$$
   Standard sample median; does not reflect paired symmetry.
3. **Hodges-Lehmann Pseudomedian**:
   $$\hat{\theta}_{\mathrm{HL}} = \text{median}_{1 \le i \le j \le N} \left(\frac{d_i + d_j}{2}\right)$$
   Computed over all $M = \frac{N(N+1)}{2} = \frac{105 \times 106}{2} = 5{,}565$ Walsh averages. The natural non-parametric location estimator associated with the Wilcoxon signed-rank test.

---

## 3. BCa Bootstrap Confidence Intervals Audit

1. **Resampling Unit**: Paired participant differences $(d_1, \dots, d_N)$ are resampled with replacement at the participant level ($N=105$).
2. **Replication Count**: $B = 10{,}000$ bootstrap iterations.
3. **RNG Convergence & Parity Defect**:
   - In legacy code, Python (`numpy.random.seed(42)`) and R (`set.seed(42)`) used different pseudorandom number generator algorithms (PCG64 / Mersenne Twister), causing minor discrepancies in the 3rd decimal place of confidence interval bounds.
   - *Required Correction*: Pre-generate a shared $10{,}000 \times 105$ integer index CSV matrix (`docs/STATISTICS/bootstrap_resample_indices_b10000_n105.csv`) so that Python and R evaluate identical bootstrap resamples.
4. **Acceleration $a$**: Evaluated via analytical leave-one-out jackknife:
   $$a = \frac{\sum_{i=1}^N (\bar{\theta}_{(\cdot)} - \hat{\theta}_{(i)})^3}{6 \left[\sum_{i=1}^N (\bar{\theta}_{(\cdot)} - \hat{\theta}_{(i)})^2\right]^{3/2}}$$
5. **Bias Correction $z_0$**:
   $$z_0 = \Phi^{-1}\left(\frac{1}{B}\sum_{b=1}^B \mathbb{I}(\hat{\theta}_b^* < \hat{\theta}_{\mathrm{HL}})\right)$$
6. **Quantile Interpolation**: Type 7 linear interpolation in both languages.

---

## 4. Multiplicity Correction Audit

1. **Confirmatory Family ($m=3$)**:
   - $C_1$: $P_1$ vs. $D_3$ (intentional global CSP leakage vs. reference)
   - $C_2$: $D_{1s}$ vs. $D_3$ (size-matched random split leakage vs. reference)
   - $C_3$: $D_{1m}$ vs. $D_3$ (matched-K random split leakage vs. reference)
2. **Correction Procedure**: Holm step-down FWER control:
   - Rank raw p-values: $p_{(1)} \le p_{(2)} \le p_{(3)}$.
   - Adjusted p-values: $p_{\mathrm{adj},(k)} = \min\left(1, \max_{j \le k} (m - j + 1) p_{(j)}\right)$.
3. **Exploratory Contrast**: $D_{1s}$ vs. $D_{1m}$ (partition mechanics: 20 random splits vs. 3-fold cross-validation) is treated as an exploratory comparison reported separately.

---

## 5. Audit Summary & Classification

| Item | Component | Legacy State | Expected State | Classification |
| :--- | :--- | :--- | :--- | :--- |
| **STAT-01** | Pratt Wilcoxon Variance | Double zero-tie subtraction | Single zero-tie subtraction (Cureton 1967) | **VERIFIED DEFECT** |
| **STAT-02** | Python/R Bootstrap Parity | Independent PRNG generators | Shared $10{,}000 \times 105$ CSV index matrix | **VERIFIED DEFECT** |
| **STAT-03** | Hodges-Lehmann Walsh Median | 5,565 Walsh averages | Correctly implemented | **VERIFIED CORRECT** |
| **STAT-04** | Holm FWER Correction | 3 primary contrasts | Correctly implemented | **VERIFIED CORRECT** |
| **STAT-05** | TOST Equivalence Tests | In `src/emi/leakstats.py` | Retain for API stability; exclude from paper | **VERIFIED CORRECT** |
