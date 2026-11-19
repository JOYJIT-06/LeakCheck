# Table 7: BCa Bootstrap Resampling Parameters, Confidence Intervals, and Convergence

| Contrast                            | Bootstrap Resamples B | Resample Matrix Hash | Estimator Type                | Point Estimate (pp) | 95% BCa Lower Bound (pp) | 95% BCa Upper Bound (pp) | Confidence Margin Width (pp) | CI Method        | Deterministic Seed |
| ----------------------------------- | --------------------- | -------------------- | ----------------------------- | ------------------- | ------------------------ | ------------------------ | ---------------------------- | ---------------- | ------------------ |
| D1s − D3 (Size-Matched Headline)    | 10,000                | 2aeb5c4176b5ef7e     | Hodges-Lehmann Location Shift | -4.78               | -6.44                    | -3.06                    | 3.39                         | BCa (Efron 1987) | 42                 |
| D1m − D3 (k-Matched Random)         | 10,000                | 2aeb5c4176b5ef7e     | Hodges-Lehmann Location Shift | -7.59               | -9.24                    | -5.79                    | 3.45                         | BCa (Efron 1987) | 42                 |
| P1 − D3 (Global Supervised Leakage) | 10,000                | 2aeb5c4176b5ef7e     | Hodges-Lehmann Location Shift | +22.22              | +19.65                   | +25.00                   | 5.35                         | BCa (Efron 1987) | 42                 |

