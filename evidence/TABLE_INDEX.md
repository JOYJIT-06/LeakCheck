# LeakCheck V1.1 Evidence Package: Statistical Summary Table Index

**Benchmark Cohort**: PhysioNet EEGMMIDB Motor Imagery ($N = 105$ analyzed participants, $N = 4$ screened exclusions)  
**Authoritative Benchmark Directory**: `benchmark_results/physionet_v1_1/`  
**Generated Format**: Both Comma-Separated Values (`.csv`) and GitHub-Flavored Markdown (`.md`)  
**Generation Script**: `scripts/generate_tables.py`  
**Cryptographic Verification**: Strict SHA-256 integrity hashes computed for every table artifact  

---

## Master Table Inventory

| Table ID | Title | CSV Artifact & SHA-256 | Markdown Artifact & SHA-256 | Benchmark Data Source | Verification |
|:---|:---|:---|:---|:---|:---:|
| **Table 1** | Participant Flow, Inclusion/Exclusion Criteria, and Benchmark Demographics | [`table01_participant_flow_demographics.csv`](../tables/table01_participant_flow_demographics.csv)<br>`cff28780f844edfc310762c61597604978c38cd3c19aef2d94d93cb100bb860f` | [`table01_participant_flow_demographics.md`](../tables/table01_participant_flow_demographics.md)<br>`c64297ff05c86359919eb70839d55008141aa0fd341431e39bdd133a6420a650` | `benchmark_results/physionet_v1_1/participant_flow_manifest.json, subject_info.csv, excluded_or_failed_subjects.csv` | **VERIFIED** |
| **Table 2** | Primary Benchmark Comparison Matrix Across Validation Schemes | [`table02_benchmark_comparison_matrix.csv`](../tables/table02_benchmark_comparison_matrix.csv)<br>`38f907e3480abe56d53019f4496c8ad22371b6f70f84113dec7939d5721ea7ad` | [`table02_benchmark_comparison_matrix.md`](../tables/table02_benchmark_comparison_matrix.md)<br>`0a3deabdc99d325942d736abfcf131b1fcd9646d4924f2592370f9457507281e` | `benchmark_results/physionet_v1_1/inflation_table.csv` | **VERIFIED** |
| **Table 3** | Comprehensive Taxonomy of EEG Cross-Validation Leakage Mechanisms (P1–P10) | [`table03_leakage_mechanisms_taxonomy.csv`](../tables/table03_leakage_mechanisms_taxonomy.csv)<br>`652847605b004108f3fd713997b2be1656030fec34f0169bad7c4f4e5c48d8ad` | [`table03_leakage_mechanisms_taxonomy.md`](../tables/table03_leakage_mechanisms_taxonomy.md)<br>`897b3abb7cdec7b4f1adfa649457feef1190bf141e28a53a0893cf22498a8961` | `evidence/SCIENTIFIC_AUDIT.md, src/emi/preprocess.py, src/emi/leakstats.py` | **VERIFIED** |
| **Table 4** | Cohort Sampling Rate Distribution and Covariance Invariance Diagnostics | [`table04_sampling_rate_distribution.csv`](../tables/table04_sampling_rate_distribution.csv)<br>`aa71c506df9ede8358604bea35e10d170c79422b2f43cbd8c05e6c2a9817e5ea` | [`table04_sampling_rate_distribution.md`](../tables/table04_sampling_rate_distribution.md)<br>`ab9a7924a111e1b4445aafdc0c8ac57bf840d0ca553c28fee0cc28e24572307b` | `benchmark_results/physionet_v1_1/subject_info.csv` | **VERIFIED** |
| **Table 5** | SVD Numerical Rank and Conditioning Across Preprocessing Transformations | [`table05_svd_rank_diagnostics.csv`](../tables/table05_svd_rank_diagnostics.csv)<br>`242f56e20dbd826b2f5de6b4d5bebbc27f8d4e6d4d94f552b52b65455af3d149` | [`table05_svd_rank_diagnostics.md`](../tables/table05_svd_rank_diagnostics.md)<br>`f673d9d8fe830b4290094fad8167a376dc50534b4cb3f4beecb4c64e14d562e0` | `evidence/DATASET_AUDIT.md, src/emi/diagnostics.py, tests/test_rank_svd.py` | **VERIFIED** |
| **Table 6** | Pratt Signed-Rank Test Statistics, Zero-Tie Deductions, and Exact P-Values | [`table06_pratt_wilcoxon_statistics.csv`](../tables/table06_pratt_wilcoxon_statistics.csv)<br>`de8f28718b24566dc3f0e56451167f26591d6dbdfa444c6a9d54bff231c4a494` | [`table06_pratt_wilcoxon_statistics.md`](../tables/table06_pratt_wilcoxon_statistics.md)<br>`0e9cd502254c02cf45eed60121cdbe25cf987494c495c7c2ba6d6d0cff33d578` | `benchmark_results/physionet_v1_1/inflation_table.csv, inflation_by_subject.csv` | **VERIFIED** |
| **Table 7** | BCa Bootstrap Resampling Parameters, Confidence Intervals, and Convergence | [`table07_bca_bootstrap_resampling.csv`](../tables/table07_bca_bootstrap_resampling.csv)<br>`a322eb7508580862ea91566e8c164b5cd0aec91be6f0ef25d10695e776bd6555` | [`table07_bca_bootstrap_resampling.md`](../tables/table07_bca_bootstrap_resampling.md)<br>`97df93f0b2d0e278f879110549f4b3be7afae370e7e834fc43b6b7b9ae126e83` | `benchmark_results/physionet_v1_1/inflation_table.csv, docs/STATISTICS/bootstrap_resample_indices_b10000_n105.csv` | **VERIFIED** |
| **Table 8** | Parametric and Nonparametric Effect Size Estimates and Location Shifts | [`table08_hodges_lehmann_effect_sizes.csv`](../tables/table08_hodges_lehmann_effect_sizes.csv)<br>`424d334ee95ae97d09089abe39fc5ff4d9b594847bb864034321afb56a73cc1f` | [`table08_hodges_lehmann_effect_sizes.md`](../tables/table08_hodges_lehmann_effect_sizes.md)<br>`64a4a8668f4cac5b27ec1ef1fb22305ef038bc5e07647b00f2958803b16c7801` | `benchmark_results/physionet_v1_1/inflation_table.csv, inflation_by_subject.csv` | **VERIFIED** |
| **Table 9** | Two One-Sided Tests (TOST) Equivalence Bounds and Statistical Decisions | [`table09_tost_equivalence_bounds.csv`](../tables/table09_tost_equivalence_bounds.csv)<br>`9ca6272c6f5c3cdd870b675c291106c7833418307f0e70f317ee24e16997a39c` | [`table09_tost_equivalence_bounds.md`](../tables/table09_tost_equivalence_bounds.md)<br>`c53eaa950c80ff18644df054a8a81283c6fd15777ff3c8ed3573a500b7a0ef9d` | `benchmark_results/physionet_v1_1/inflation_table.csv` | **VERIFIED** |
| **Table 10** | Run-Independent FIR Filter Boundary Isolation and Cross-Run Bleed Verification | [`table10_fir_filter_bleed_comparison.csv`](../tables/table10_fir_filter_bleed_comparison.csv)<br>`bca2c06991dabb3459fe2a51598a67f9a75bf6afc96b2cca164c92da7231e617` | [`table10_fir_filter_bleed_comparison.md`](../tables/table10_fir_filter_bleed_comparison.md)<br>`6265514631ce5e39d84228d1b9cfe4e2064f8a520d436eae3cf8dab78b609916` | `tests/test_run_boundary_filtering.py, evidence/PREPROCESSING_AUDIT.md` | **VERIFIED** |
| **Table 11** | Fold-Isolated Preprocessing Parameter Stability Across Cross-Validation Folds | [`table11_fold_isolated_parameter_stability.csv`](../tables/table11_fold_isolated_parameter_stability.csv)<br>`b29a79c3e1f35c190d65287ae059ce511ea5de45ee6bb5043d1927824a8cb50d` | [`table11_fold_isolated_parameter_stability.md`](../tables/table11_fold_isolated_parameter_stability.md)<br>`897acb2722e457da68c8705a72c8b97aacd7d48d36566eab4aeaeaea002c8c7c` | `benchmark_results/physionet_v1_1/fold_details.json` | **VERIFIED** |
| **Table 12** | Permutation Null Distribution and Signal Noise Burst Robustness | [`table12_permutation_noise_robustness.csv`](../tables/table12_permutation_noise_robustness.csv)<br>`9d392e8607fd7aaea5f35a8fab958777112d05e38bff29e81ec11d222b61a4e6` | [`table12_permutation_noise_robustness.md`](../tables/table12_permutation_noise_robustness.md)<br>`a3626d673e07a0e7f81973e99f9cf3b75995ec40c20fc1a249f3b44872b2372e` | `benchmark_results/physionet_v1_1/subject_info.csv` | **VERIFIED** |
| **Table 13** | Spatial Covariance Matrix Regularization and Decoder Numerical Conditioning | [`table13_decoders_regularization_comparison.csv`](../tables/table13_decoders_regularization_comparison.csv)<br>`6394f9d6b52e33abebe405fe2ddd9c2e5fc8b9592128a9fd8214b52354611b18` | [`table13_decoders_regularization_comparison.md`](../tables/table13_decoders_regularization_comparison.md)<br>`3b81f33e1719908e28d3ee3a4969b7ef1093dbc3f776875b5c329f8294fa3300` | `src/emi/decoders.py, tests/test_signal_utils.py, settings.json` | **VERIFIED** |
| **Table 14** | Participant-Level Decoding Accuracies and Paired Cross-Validation Shifts (N = 105) | [`table14_paired_subject_accuracies_all_105.csv`](../tables/table14_paired_subject_accuracies_all_105.csv)<br>`11e818555f17e4bd418f28e7456544d774f1fba83293a3e653fcdbb13079382f` | [`table14_paired_subject_accuracies_all_105.md`](../tables/table14_paired_subject_accuracies_all_105.md)<br>`88accb85a3d6de56d60b5378f161a1bebb56255404a650818529837e9274787f` | `benchmark_results/physionet_v1_1/inflation_by_subject.csv, subject_info.csv` | **VERIFIED** |
| **Table 15** | Cross-Design Pearson and Spearman Correlation Matrix of Decoding Accuracies | [`table15_cross_design_correlation_matrix.csv`](../tables/table15_cross_design_correlation_matrix.csv)<br>`b0c400db5bf45f0251c02e3d97b67f59f8f924d5a67f2c203e0478d2694fdd44` | [`table15_cross_design_correlation_matrix.md`](../tables/table15_cross_design_correlation_matrix.md)<br>`5b8abaee1037dfe7063ee6863587aba8c154be3be305f276a3ae065040d2cb4e` | `benchmark_results/physionet_v1_1/inflation_by_subject.csv` | **VERIFIED** |
| **Table 16** | Comprehensive Technical Screening and Exclusion Accounting for Rejected Participants | [`table16_bad_channel_artifact_accounting.csv`](../tables/table16_bad_channel_artifact_accounting.csv)<br>`af454ff0814c29be88403949748f270206f3a8a6704177bb399a3962e91885c6` | [`table16_bad_channel_artifact_accounting.md`](../tables/table16_bad_channel_artifact_accounting.md)<br>`3dddf85193254099e111f859cc08a5b21553d691a6ca81912514d42f6d66a070` | `benchmark_results/physionet_v1_1/excluded_or_failed_subjects.csv, participant_flow_manifest.json` | **VERIFIED** |
| **Table 17** | Computational Benchmark Performance and Multi-Core Multiprocessing Scaling | [`table17_computational_performance_scaling.csv`](../tables/table17_computational_performance_scaling.csv)<br>`6ecbc521ee3b10e15e63266b7aea68a96d97d7c3197782699868d049af1dab3d` | [`table17_computational_performance_scaling.md`](../tables/table17_computational_performance_scaling.md)<br>`1ce7b783edf83cb35fa81d778162a6f760f43f38ca6e5297bb1cfcb16ca3b91e` | `benchmark_results/physionet_v1_1/leakcheck_summary.json` | **VERIFIED** |
| **Table 18** | Sprint Capacity Ledger, Daily Active Hours, and Cumulative Milestones | [`table18_sprint_ledger_capacity_utilization.csv`](../tables/table18_sprint_ledger_capacity_utilization.csv)<br>`8a5d437044c885226b502cdf5cf6d1f52300b45568bd5afb73e2b6e287eb4467` | [`table18_sprint_ledger_capacity_utilization.md`](../tables/table18_sprint_ledger_capacity_utilization.md)<br>`cf01741219e8f5107e6c94976a7147189586811edd098511b5087db68ebd2b49` | `progress/AGENT_HOUR_LOG.csv, progress/MASTER_PROGRESS.csv, progress/TEAM_CAPACITY_REPORT.md` | **VERIFIED** |

---

## Detailed Table Specifications & Scientific Findings

### Table 1: Participant Flow, Inclusion/Exclusion Criteria, and Benchmark Demographics
- **Primary CSV Artifact**: [`tables/table01_participant_flow_demographics.csv`](../tables/table01_participant_flow_demographics.csv) (`SHA-256: cff28780f844edfc310762c61597604978c38cd3c19aef2d94d93cb100bb860f`)
- **Markdown Mirror**: [`tables/table01_participant_flow_demographics.md`](../tables/table01_participant_flow_demographics.md) (`SHA-256: c64297ff05c86359919eb70839d55008141aa0fd341431e39bdd133a6420a650`)
- **Short Alias**: `tables/table01.csv` / `tables/table01.md`
- **Source Data**: `benchmark_results/physionet_v1_1/participant_flow_manifest.json, subject_info.csv, excluded_or_failed_subjects.csv`
- **Summary of Scientific Findings**: 109 requested -> 105 analyzed cohort (96.33% retention), 4 exclusions (S044, S069, S086, S091), 4,591 total trials, 102 @ 160Hz, 3 @ 128Hz, refutation of line 95 error.

### Table 2: Primary Benchmark Comparison Matrix Across Validation Schemes
- **Primary CSV Artifact**: [`tables/table02_benchmark_comparison_matrix.csv`](../tables/table02_benchmark_comparison_matrix.csv) (`SHA-256: 38f907e3480abe56d53019f4496c8ad22371b6f70f84113dec7939d5721ea7ad`)
- **Markdown Mirror**: [`tables/table02_benchmark_comparison_matrix.md`](../tables/table02_benchmark_comparison_matrix.md) (`SHA-256: 0a3deabdc99d325942d736abfcf131b1fcd9646d4924f2592370f9457507281e`)
- **Short Alias**: `tables/table02.csv` / `tables/table02.md`
- **Source Data**: `benchmark_results/physionet_v1_1/inflation_table.csv`
- **Summary of Scientific Findings**: Primary paired contrasts (D1s - D3, D1m - D3, P1 - D3) reporting mean, median, Hodges-Lehmann, BCa 95% CIs, Pratt Wilcoxon W, Z, p-values, Holm adjustment, rank-biserial r, Cohen's dz, and TOST.

### Table 3: Comprehensive Taxonomy of EEG Cross-Validation Leakage Mechanisms (P1–P10)
- **Primary CSV Artifact**: [`tables/table03_leakage_mechanisms_taxonomy.csv`](../tables/table03_leakage_mechanisms_taxonomy.csv) (`SHA-256: 652847605b004108f3fd713997b2be1656030fec34f0169bad7c4f4e5c48d8ad`)
- **Markdown Mirror**: [`tables/table03_leakage_mechanisms_taxonomy.md`](../tables/table03_leakage_mechanisms_taxonomy.md) (`SHA-256: 897b3abb7cdec7b4f1adfa649457feef1190bf141e28a53a0893cf22498a8961`)
- **Short Alias**: `tables/table03.csv` / `tables/table03.md`
- **Source Data**: `evidence/SCIENTIFIC_AUDIT.md, src/emi/preprocess.py, src/emi/leakstats.py`
- **Summary of Scientific Findings**: Formal scientific definition, contaminated vs. clean comparators, theoretical bias direction, empirical shifts, and verification status for all 10 leakage mechanisms.

### Table 4: Cohort Sampling Rate Distribution and Covariance Invariance Diagnostics
- **Primary CSV Artifact**: [`tables/table04_sampling_rate_distribution.csv`](../tables/table04_sampling_rate_distribution.csv) (`SHA-256: aa71c506df9ede8358604bea35e10d170c79422b2f43cbd8c05e6c2a9817e5ea`)
- **Markdown Mirror**: [`tables/table04_sampling_rate_distribution.md`](../tables/table04_sampling_rate_distribution.md) (`SHA-256: ab9a7924a111e1b4445aafdc0c8ac57bf840d0ca553c28fee0cc28e24572307b`)
- **Short Alias**: `tables/table04.csv` / `tables/table04.md`
- **Source Data**: `benchmark_results/physionet_v1_1/subject_info.csv`
- **Summary of Scientific Findings**: Complete accounting of 160.0 Hz (n=102) and 128.0 Hz (n=3) participants, trial counts, samples per epoch, covariance matrix dimensionality (64x64), and SVD rank invariance (rank 63).

### Table 5: SVD Numerical Rank and Conditioning Across Preprocessing Transformations
- **Primary CSV Artifact**: [`tables/table05_svd_rank_diagnostics.csv`](../tables/table05_svd_rank_diagnostics.csv) (`SHA-256: 242f56e20dbd826b2f5de6b4d5bebbc27f8d4e6d4d94f552b52b65455af3d149`)
- **Markdown Mirror**: [`tables/table05_svd_rank_diagnostics.md`](../tables/table05_svd_rank_diagnostics.md) (`SHA-256: f673d9d8fe830b4290094fad8167a376dc50534b4cb3f4beecb4c64e14d562e0`)
- **Short Alias**: `tables/table05.csv` / `tables/table05.md`
- **Source Data**: `evidence/DATASET_AUDIT.md, src/emi/diagnostics.py, tests/test_rank_svd.py`
- **Summary of Scientific Findings**: Matrix dimensions, theoretical degrees of freedom, empirical SVD rank, condition numbers, and null space singular values (< 1e-14) pre/post-CAR, bad channel interpolation, and OAS.

### Table 6: Pratt Signed-Rank Test Statistics, Zero-Tie Deductions, and Exact P-Values
- **Primary CSV Artifact**: [`tables/table06_pratt_wilcoxon_statistics.csv`](../tables/table06_pratt_wilcoxon_statistics.csv) (`SHA-256: de8f28718b24566dc3f0e56451167f26591d6dbdfa444c6a9d54bff231c4a494`)
- **Markdown Mirror**: [`tables/table06_pratt_wilcoxon_statistics.md`](../tables/table06_pratt_wilcoxon_statistics.md) (`SHA-256: 0e9cd502254c02cf45eed60121cdbe25cf987494c495c7c2ba6d6d0cff33d578`)
- **Short Alias**: `tables/table06.csv` / `tables/table06.md`
- **Source Data**: `benchmark_results/physionet_v1_1/inflation_table.csv, inflation_by_subject.csv`
- **Summary of Scientific Findings**: Detailed Pratt Wilcoxon breakdown: zero-tie counts, positive/negative ranks, test statistic W, variance correction, standardized Z, asymptotic and Holm-adjusted p-values.

### Table 7: BCa Bootstrap Resampling Parameters, Confidence Intervals, and Convergence
- **Primary CSV Artifact**: [`tables/table07_bca_bootstrap_resampling.csv`](../tables/table07_bca_bootstrap_resampling.csv) (`SHA-256: a322eb7508580862ea91566e8c164b5cd0aec91be6f0ef25d10695e776bd6555`)
- **Markdown Mirror**: [`tables/table07_bca_bootstrap_resampling.md`](../tables/table07_bca_bootstrap_resampling.md) (`SHA-256: 97df93f0b2d0e278f879110549f4b3be7afae370e7e834fc43b6b7b9ae126e83`)
- **Short Alias**: `tables/table07.csv` / `tables/table07.md`
- **Source Data**: `benchmark_results/physionet_v1_1/inflation_table.csv, docs/STATISTICS/bootstrap_resample_indices_b10000_n105.csv`
- **Summary of Scientific Findings**: B=10,000 resamples, deterministic index matrix hash, Hodges-Lehmann location shift point estimates, 95% BCa lower and upper bounds, and confidence interval widths.

### Table 8: Parametric and Nonparametric Effect Size Estimates and Location Shifts
- **Primary CSV Artifact**: [`tables/table08_hodges_lehmann_effect_sizes.csv`](../tables/table08_hodges_lehmann_effect_sizes.csv) (`SHA-256: 424d334ee95ae97d09089abe39fc5ff4d9b594847bb864034321afb56a73cc1f`)
- **Markdown Mirror**: [`tables/table08_hodges_lehmann_effect_sizes.md`](../tables/table08_hodges_lehmann_effect_sizes.md) (`SHA-256: 64a4a8668f4cac5b27ec1ef1fb22305ef038bc5e07647b00f2958803b16c7801`)
- **Short Alias**: `tables/table08.csv` / `tables/table08.md`
- **Source Data**: `benchmark_results/physionet_v1_1/inflation_table.csv, inflation_by_subject.csv`
- **Summary of Scientific Findings**: Side-by-side comparison of parametric (mean, SD, Cohen's dz) and nonparametric (median, IQR, Hodges-Lehmann, rank-biserial r) effect sizes, plus logit-transformed paired t-tests.

### Table 9: Two One-Sided Tests (TOST) Equivalence Bounds and Statistical Decisions
- **Primary CSV Artifact**: [`tables/table09_tost_equivalence_bounds.csv`](../tables/table09_tost_equivalence_bounds.csv) (`SHA-256: 9ca6272c6f5c3cdd870b675c291106c7833418307f0e70f317ee24e16997a39c`)
- **Markdown Mirror**: [`tables/table09_tost_equivalence_bounds.md`](../tables/table09_tost_equivalence_bounds.md) (`SHA-256: c53eaa950c80ff18644df054a8a81283c6fd15777ff3c8ed3573a500b7a0ef9d`)
- **Short Alias**: `tables/table09.csv` / `tables/table09.md`
- **Source Data**: `benchmark_results/physionet_v1_1/inflation_table.csv`
- **Summary of Scientific Findings**: Equivalence bounds [-2.0 pp, +2.0 pp], lower and upper t-tests, overall TOST p-value, 90% confidence intervals, and conclusive rejection of equivalence for random splits vs. LORO.

### Table 10: Run-Independent FIR Filter Boundary Isolation and Cross-Run Bleed Verification
- **Primary CSV Artifact**: [`tables/table10_fir_filter_bleed_comparison.csv`](../tables/table10_fir_filter_bleed_comparison.csv) (`SHA-256: bca2c06991dabb3459fe2a51598a67f9a75bf6afc96b2cca164c92da7231e617`)
- **Markdown Mirror**: [`tables/table10_fir_filter_bleed_comparison.md`](../tables/table10_fir_filter_bleed_comparison.md) (`SHA-256: 6265514631ce5e39d84228d1b9cfe4e2064f8a520d436eae3cf8dab78b609916`)
- **Short Alias**: `tables/table10.csv` / `tables/table10.md`
- **Source Data**: `tests/test_run_boundary_filtering.py, evidence/PREPROCESSING_AUDIT.md`
- **Summary of Scientific Findings**: Empirical verification of 0.000 V impulse bleed in run-independent MNE reflection padding vs. > 1.0 V cross-boundary bleed in legacy concatenated filtering.

### Table 11: Fold-Isolated Preprocessing Parameter Stability Across Cross-Validation Folds
- **Primary CSV Artifact**: [`tables/table11_fold_isolated_parameter_stability.csv`](../tables/table11_fold_isolated_parameter_stability.csv) (`SHA-256: b29a79c3e1f35c190d65287ae059ce511ea5de45ee6bb5043d1927824a8cb50d`)
- **Markdown Mirror**: [`tables/table11_fold_isolated_parameter_stability.md`](../tables/table11_fold_isolated_parameter_stability.md) (`SHA-256: 897acb2722e457da68c8705a72c8b97aacd7d48d36566eab4aeaeaea002c8c7c`)
- **Short Alias**: `tables/table11.csv` / `tables/table11.md`
- **Source Data**: `benchmark_results/physionet_v1_1/fold_details.json`
- **Summary of Scientific Findings**: Training fold parameter stability across 315 fold fits: mean training/test trials, adaptive peak-to-peak rejection threshold tau, bad channel count B_train, ICA components W_train, fold accuracy.

### Table 12: Permutation Null Distribution and Signal Noise Burst Robustness
- **Primary CSV Artifact**: [`tables/table12_permutation_noise_robustness.csv`](../tables/table12_permutation_noise_robustness.csv) (`SHA-256: 9d392e8607fd7aaea5f35a8fab958777112d05e38bff29e81ec11d222b61a4e6`)
- **Markdown Mirror**: [`tables/table12_permutation_noise_robustness.md`](../tables/table12_permutation_noise_robustness.md) (`SHA-256: a3626d673e07a0e7f81973e99f9cf3b75995ec40c20fc1a249f3b44872b2372e`)
- **Short Alias**: `tables/table12.csv` / `tables/table12.md`
- **Source Data**: `benchmark_results/physionet_v1_1/subject_info.csv`
- **Summary of Scientific Findings**: Wald-Wolfowitz runs tests, run decoding accuracy vs. chance, lag-1 autoregressive trial autocorrelation, and simulated noise burst attenuation (50 µV and 200 µV).

### Table 13: Spatial Covariance Matrix Regularization and Decoder Numerical Conditioning
- **Primary CSV Artifact**: [`tables/table13_decoders_regularization_comparison.csv`](../tables/table13_decoders_regularization_comparison.csv) (`SHA-256: 6394f9d6b52e33abebe405fe2ddd9c2e5fc8b9592128a9fd8214b52354611b18`)
- **Markdown Mirror**: [`tables/table13_decoders_regularization_comparison.md`](../tables/table13_decoders_regularization_comparison.md) (`SHA-256: 3b81f33e1719908e28d3ee3a4969b7ef1093dbc3f776875b5c329f8294fa3300`)
- **Short Alias**: `tables/table13.csv` / `tables/table13.md`
- **Source Data**: `src/emi/decoders.py, tests/test_signal_utils.py, settings.json`
- **Summary of Scientific Findings**: Comparison of Empirical Sample Covariance, Ledoit-Wolf Shrinkage, and Oracle Approximating Shrinkage (OAS) condition numbers, invertibility guarantees, and benchmark selection.

### Table 14: Participant-Level Decoding Accuracies and Paired Cross-Validation Shifts (N = 105)
- **Primary CSV Artifact**: [`tables/table14_paired_subject_accuracies_all_105.csv`](../tables/table14_paired_subject_accuracies_all_105.csv) (`SHA-256: 11e818555f17e4bd418f28e7456544d774f1fba83293a3e653fcdbb13079382f`)
- **Markdown Mirror**: [`tables/table14_paired_subject_accuracies_all_105.md`](../tables/table14_paired_subject_accuracies_all_105.md) (`SHA-256: 88accb85a3d6de56d60b5378f161a1bebb56255404a650818529837e9274787f`)
- **Short Alias**: `tables/table14.csv` / `tables/table14.md`
- **Source Data**: `benchmark_results/physionet_v1_1/inflation_by_subject.csv, subject_info.csv`
- **Summary of Scientific Findings**: Complete 105-subject inventory listing native sampling frequency, analyzed trial counts, absolute accuracies for D3, D1s, D1m, P1, and individual paired shifts (ΔD1s, ΔD1m, ΔP1).

### Table 15: Cross-Design Pearson and Spearman Correlation Matrix of Decoding Accuracies
- **Primary CSV Artifact**: [`tables/table15_cross_design_correlation_matrix.csv`](../tables/table15_cross_design_correlation_matrix.csv) (`SHA-256: b0c400db5bf45f0251c02e3d97b67f59f8f924d5a67f2c203e0478d2694fdd44`)
- **Markdown Mirror**: [`tables/table15_cross_design_correlation_matrix.md`](../tables/table15_cross_design_correlation_matrix.md) (`SHA-256: 5b8abaee1037dfe7063ee6863587aba8c154be3be305f276a3ae065040d2cb4e`)
- **Short Alias**: `tables/table15.csv` / `tables/table15.md`
- **Source Data**: `benchmark_results/physionet_v1_1/inflation_by_subject.csv`
- **Summary of Scientific Findings**: Correlation matrix among D3, D1s, D1m, and P1 decoding accuracies across 105 participants, reporting Pearson r, Spearman rho, and two-sided p-values.

### Table 16: Comprehensive Technical Screening and Exclusion Accounting for Rejected Participants
- **Primary CSV Artifact**: [`tables/table16_bad_channel_artifact_accounting.csv`](../tables/table16_bad_channel_artifact_accounting.csv) (`SHA-256: af454ff0814c29be88403949748f270206f3a8a6704177bb399a3962e91885c6`)
- **Markdown Mirror**: [`tables/table16_bad_channel_artifact_accounting.md`](../tables/table16_bad_channel_artifact_accounting.md) (`SHA-256: 3dddf85193254099e111f859cc08a5b21553d691a6ca81912514d42f6d66a070`)
- **Short Alias**: `tables/table16.csv` / `tables/table16.md`
- **Source Data**: `benchmark_results/physionet_v1_1/excluded_or_failed_subjects.csv, participant_flow_manifest.json`
- **Summary of Scientific Findings**: Audit of all 4 excluded participants (S044, S069, S086, S091): flagged channels, bad channel ratio, trial counts, adaptive voltage threshold, exclusion criterion, and rationale.

### Table 17: Computational Benchmark Performance and Multi-Core Multiprocessing Scaling
- **Primary CSV Artifact**: [`tables/table17_computational_performance_scaling.csv`](../tables/table17_computational_performance_scaling.csv) (`SHA-256: 6ecbc521ee3b10e15e63266b7aea68a96d97d7c3197782699868d049af1dab3d`)
- **Markdown Mirror**: [`tables/table17_computational_performance_scaling.md`](../tables/table17_computational_performance_scaling.md) (`SHA-256: 1ce7b783edf83cb35fa81d778162a6f760f43f38ca6e5297bb1cfcb16ca3b91e`)
- **Short Alias**: `tables/table17.csv` / `tables/table17.md`
- **Source Data**: `benchmark_results/physionet_v1_1/leakcheck_summary.json`
- **Summary of Scientific Findings**: Hardware specs, 4-worker multiprocessing throughput, total compute time (1248.24s), mean time per subject (11.89s), peak RAM footprint (1.82 GB), and zero failure rate.

### Table 18: Sprint Capacity Ledger, Daily Active Hours, and Cumulative Milestones
- **Primary CSV Artifact**: [`tables/table18_sprint_ledger_capacity_utilization.csv`](../tables/table18_sprint_ledger_capacity_utilization.csv) (`SHA-256: 8a5d437044c885226b502cdf5cf6d1f52300b45568bd5afb73e2b6e287eb4467`)
- **Markdown Mirror**: [`tables/table18_sprint_ledger_capacity_utilization.md`](../tables/table18_sprint_ledger_capacity_utilization.md) (`SHA-256: cf01741219e8f5107e6c94976a7147189586811edd098511b5087db68ebd2b49`)
- **Short Alias**: `tables/table18.csv` / `tables/table18.md`
- **Source Data**: `progress/AGENT_HOUR_LOG.csv, progress/MASTER_PROGRESS.csv, progress/TEAM_CAPACITY_REPORT.md`
- **Summary of Scientific Findings**: Sprint progress across Days 1 through 6: daily technical objectives, lead agents, active hours, cumulative hours (84.0h / 396.0h ceiling, 21.21%), test suite status (254/254 green).

