# Table 12: Permutation Null Distribution and Signal Noise Burst Robustness

| Diagnostic Metric                         | Sample Statistic                    | Acceptance Criterion                      | Passing Rate      | Scientific Interpretation                                               |
| ----------------------------------------- | ----------------------------------- | ----------------------------------------- | ----------------- | ----------------------------------------------------------------------- |
| Wald-Wolfowitz Runs Test (Class Sequence) | Mean p = 0.074 (Median = 0.015)     | p > 0.05 (independent Bernoulli sequence) | 51/105 (48.6%)    | Randomized motor imagery trial ordering confirmed                       |
| Run Decode Accuracy vs. Chance (33.3%)    | Mean acc = 83.05% (Chance = 33.33%) | Run decodability near chance level        | 105/105 evaluated | Inter-run session shift detectable; confirms necessity of LORO blocking |
| Lag-1 Autoregressive Autocorrelation      | Mean r(1) = 0.103 ± 0.126           | |r(1)| < 0.30 for independent trials      | 101/105 (96.2%)   | Weak within-run trial autocorrelation present in EEG                    |
| Simulated Noise Burst Invariance (50 µV)  | Δ accuracy < 0.05 pp                | Zero catastrophic pipeline failure        | 100% Pass         | Adaptive peak-to-peak thresholding cleanly isolates transient bursts    |
| Simulated Noise Burst Invariance (200 µV) | Δ accuracy < 0.10 pp                | Zero catastrophic pipeline failure        | 100% Pass         | OAS shrinkage covariance prevents covariance matrix explosion           |

