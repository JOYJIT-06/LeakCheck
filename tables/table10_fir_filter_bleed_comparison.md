# Table 10: Run-Independent FIR Filter Boundary Isolation and Cross-Run Bleed Verification

| Filtering Architecture             | Filter Specification                       | Boundary Handling                                    | Impulse Bleed Across Boundary      | Temporal Convolution Support                | Leakage Mechanism Risk                        | Audit Status         |
| ---------------------------------- | ------------------------------------------ | ---------------------------------------------------- | ---------------------------------- | ------------------------------------------- | --------------------------------------------- | -------------------- |
| Legacy Concatenated Filtering      | FIR bandpass [8–30 Hz], Hamming, order 330 | Continuous filtering across run boundaries           | > 1.000 V (severe non-zero bleed)  | Spans 1.031 s into adjacent run             | P6 (Autoregressive trial cross-contamination) | REJECTED (Flawed)    |
| Repaired Run-Independent Filtering | FIR bandpass [8–30 Hz], Hamming, order 330 | Isolated buffer per run with reflect_limited padding | 0.000 V (exact bitwise zero bleed) | Strictly contained within single run buffer | Zero boundary bleed; physically isolated      | VERIFIED & VALIDATED |

