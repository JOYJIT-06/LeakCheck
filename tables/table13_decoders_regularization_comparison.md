# Table 13: Spatial Covariance Matrix Regularization and Decoder Numerical Conditioning

| Covariance Regularization Method     | Mathematical Formulation         | Condition Number κ      | Singular Matrix Failure Rate | Invertibility Guarantee                        | LeakCheck V1.1 Selection         |
| ------------------------------------ | -------------------------------- | ----------------------- | ---------------------------- | ---------------------------------------------- | -------------------------------- |
| Empirical Sample Covariance (SCM)    | Σ_emp = (1/N) X X^T              | > 10⁶ (ill-conditioned) | 38.5% on rank-deficient EEG  | None (fails when N <= P or post-CAR)           | REJECTED (Numerically unstable)  |
| Ledoit-Wolf Shrinkage                | Σ_LW = (1-α)Σ_emp + α(tr(Σ)/P)I  | 1.52 × 10²              | 0.0% (always full rank)      | Strictly positive definite (λ > 0)             | Supported (standard shrinkage)   |
| Oracle Approximating Shrinkage (OAS) | Σ_OAS = (1-ρ)Σ_emp + ρ(tr(Σ)/P)I | 1.18 × 10²              | 0.0% (always full rank)      | Strictly positive definite (lower MSE than LW) | PRIMARY STANDARD (csp_reg='oas') |

