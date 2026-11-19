# Table 5: SVD Numerical Rank and Conditioning Across Preprocessing Transformations

| Pipeline Processing Stage             | Spatial Matrix Dimensions | Theoretical Degrees of Freedom | Empirical SVD Rank | Condition Number κ | Null Singular Value        | Numerical Status                                          |
| ------------------------------------- | ------------------------- | ------------------------------ | ------------------ | ------------------ | -------------------------- | --------------------------------------------------------- |
| Raw Unreferenced Recording            | 64 × 64                   | 64                             | 64                 | 1.24 × 10²         | None (> 10⁻²)              | Full rank; well-conditioned                               |
| Post-Common Average Reference (CAR)   | 64 × 64                   | 63                             | 63                 | 1.85 × 10¹⁴        | < 1.00 × 10⁻¹⁴             | Structural rank deficiency of 1; null space dimension 1   |
| Post-Bad Channel Interpolation (1 ch) | 64 × 64                   | 63                             | 63                 | 2.10 × 10¹⁴        | < 1.00 × 10⁻¹⁴             | Spherical spline preserves CAR null space                 |
| Post-Bad Channel Interpolation (2 ch) | 64 × 64                   | 62                             | 62                 | 3.45 × 10¹⁴        | < 1.00 × 10⁻¹⁴             | 2 null singular values (< 10⁻¹⁴); rank = 64 - N_bad - 1   |
| OAS-Regularized Covariance Matrix     | 64 × 64                   | 64                             | 64                 | 1.18 × 10²         | Eigenvalue floor λ_min > 0 | Strictly positive definite; invertibility 100% guaranteed |

