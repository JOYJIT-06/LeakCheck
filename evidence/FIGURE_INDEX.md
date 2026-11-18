# LeakCheck V1.1 Evidence Package: Scientific Figure Index

**Benchmark Cohort**: PhysioNet EEGMMIDB Motor Imagery ($N = 105$ analyzed participants, $N = 4$ screened exclusions)  
**Repaired Benchmark Directory**: `benchmark_results/physionet_v1_1_repaired/`  
**Generated Formats**: High-Resolution Raster (`.png` at 300 DPI) and Publication Vector (`.pdf`, `.svg`)  
**Generation Script**: `figures/scripts/generate_figures.py`  
**Figure Standards Compliance**: Colorblind-safe palettes, explicit uncertainty intervals, no truncated axes, full provenance  

---

## Master Figure Inventory

| Figure ID | Title | PNG (300 DPI) & SHA-256 | Vector PDF / SVG | Source Benchmark Data | Status |
|:---|:---|:---|:---|:---|:---:|
| **Figure 1** | LeakCheck Architecture, Preprocessing Pipeline, and Cross-Validation Verification Schemes | [`fig01_workflow_schematic.png`](../figures/fig01_workflow_schematic.png)<br>`9940662ddda4b0ca...` | [`fig01_workflow_schematic.pdf`](../figures/fig01_workflow_schematic.pdf)<br>[`fig01_workflow_schematic.svg`](../figures/fig01_workflow_schematic.svg) | `benchmark_results/physionet_v1_1_repaired/` | **VERIFIED** |
| **Figure 2** | Participant Screening Flowchart and Exclusion Accounting (CONSORT Guideline, N = 105) | [`fig02_participant_flow.png`](../figures/fig02_participant_flow.png)<br>`b70602cfa858cc81...` | [`fig02_participant_flow.pdf`](../figures/fig02_participant_flow.pdf)<br>[`fig02_participant_flow.svg`](../figures/fig02_participant_flow.svg) | `benchmark_results/physionet_v1_1_repaired/` | **VERIFIED** |
| **Figure 3** | Paired Participant-Level Decoding Accuracies Across Cross-Validation Schemes (N = 105) | [`fig03_paired_accuracy_scatter.png`](../figures/fig03_paired_accuracy_scatter.png)<br>`98688e76e1d77502...` | [`fig03_paired_accuracy_scatter.pdf`](../figures/fig03_paired_accuracy_scatter.pdf)<br>[`fig03_paired_accuracy_scatter.svg`](../figures/fig03_paired_accuracy_scatter.svg) | `benchmark_results/physionet_v1_1_repaired/` | **VERIFIED** |
| **Figure 4** | Accuracy Distributions and Paired Cross-Validation Performance Contrasts (N = 105) | [`fig04_inflation_distributions.png`](../figures/fig04_inflation_distributions.png)<br>`9eda3ec8c6f0795e...` | [`fig04_inflation_distributions.pdf`](../figures/fig04_inflation_distributions.pdf)<br>[`fig04_inflation_distributions.svg`](../figures/fig04_inflation_distributions.svg) | `benchmark_results/physionet_v1_1_repaired/` | **VERIFIED** |
| **Figure 5** | Hodges-Lehmann Effect Size Forest Plot Across Primary Cross-Validation Contrasts | [`fig05_effect_size_forest_plot.png`](../figures/fig05_effect_size_forest_plot.png)<br>`5607c539ba37f17b...` | [`fig05_effect_size_forest_plot.pdf`](../figures/fig05_effect_size_forest_plot.pdf)<br>[`fig05_effect_size_forest_plot.svg`](../figures/fig05_effect_size_forest_plot.svg) | `benchmark_results/physionet_v1_1_repaired/` | **VERIFIED** |
| **Figure 6** | FIR Filter Boundary Isolation and Cross-Run Bleed Comparison (Legacy vs. Repaired) | [`fig06_filter_bleed_comparison.png`](../figures/fig06_filter_bleed_comparison.png)<br>`57eb7932fe38d2bb...` | [`fig06_filter_bleed_comparison.pdf`](../figures/fig06_filter_bleed_comparison.pdf)<br>[`fig06_filter_bleed_comparison.svg`](../figures/fig06_filter_bleed_comparison.svg) | `benchmark_results/physionet_v1_1_repaired/` | **VERIFIED** |
| **Figure 7** | SVD Numerical Rank Diagnostics, CAR Null Space, and OAS Covariance Conditioning | [`fig07_svd_rank_spectrum.png`](../figures/fig07_svd_rank_spectrum.png)<br>`ab0241314699f96b...` | [`fig07_svd_rank_spectrum.pdf`](../figures/fig07_svd_rank_spectrum.pdf)<br>[`fig07_svd_rank_spectrum.svg`](../figures/fig07_svd_rank_spectrum.svg) | `benchmark_results/physionet_v1_1_repaired/` | **VERIFIED** |
| **Figure 8** | Pratt Wilcoxon Ranked Participant Differences for Random Partitioning vs. Positive Leakage | [`fig08_pratt_wilcoxon_ranking.png`](../figures/fig08_pratt_wilcoxon_ranking.png)<br>`92024d3d9ff39d12...` | [`fig08_pratt_wilcoxon_ranking.pdf`](../figures/fig08_pratt_wilcoxon_ranking.pdf)<br>[`fig08_pratt_wilcoxon_ranking.svg`](../figures/fig08_pratt_wilcoxon_ranking.svg) | `benchmark_results/physionet_v1_1_repaired/` | **VERIFIED** |
| **Figure 9** | Empirical BCa Bootstrap Distribution Density Curves (B = 10,000 Resamples) | [`fig09_bca_bootstrap_density.png`](../figures/fig09_bca_bootstrap_density.png)<br>`6b21dbab77f85d79...` | [`fig09_bca_bootstrap_density.pdf`](../figures/fig09_bca_bootstrap_density.pdf)<br>[`fig09_bca_bootstrap_density.svg`](../figures/fig09_bca_bootstrap_density.svg) | `benchmark_results/physionet_v1_1_repaired/` | **VERIFIED** |
| **Figure 10** | TOST Equivalence Testing Bounds: Conclusive Rejection of Equivalence for Random Partitions | [`fig10_tost_equivalence_margins.png`](../figures/fig10_tost_equivalence_margins.png)<br>`882449b16a51cfdd...` | [`fig10_tost_equivalence_margins.pdf`](../figures/fig10_tost_equivalence_margins.pdf)<br>[`fig10_tost_equivalence_margins.svg`](../figures/fig10_tost_equivalence_margins.svg) | `benchmark_results/physionet_v1_1_repaired/` | **VERIFIED** |
| **Figure 11** | Leave-One-Run-Out Fold Stability and Parameter Invariance Across Cross-Validation Partitions | [`fig11_cross_validation_fold_stability.png`](../figures/fig11_cross_validation_fold_stability.png)<br>`9b7054d8437618d9...` | [`fig11_cross_validation_fold_stability.pdf`](../figures/fig11_cross_validation_fold_stability.pdf)<br>[`fig11_cross_validation_fold_stability.svg`](../figures/fig11_cross_validation_fold_stability.svg) | `benchmark_results/physionet_v1_1_repaired/` | **VERIFIED** |
| **Figure 12** | Hardware Sampling Rate Invariance: Validating Full Inclusion of S088, S092, and S100 | [`fig12_sampling_rate_invariance.png`](../figures/fig12_sampling_rate_invariance.png)<br>`bc0c3fa712c311ae...` | [`fig12_sampling_rate_invariance.pdf`](../figures/fig12_sampling_rate_invariance.pdf)<br>[`fig12_sampling_rate_invariance.svg`](../figures/fig12_sampling_rate_invariance.svg) | `benchmark_results/physionet_v1_1_repaired/` | **VERIFIED** |
| **Figure 13** | Positive Control (P1) Leakage Dynamics: Universal Optimistic Bias from Global CSP | [`fig13_positive_control_dynamics.png`](../figures/fig13_positive_control_dynamics.png)<br>`dccf62fcfef45d31...` | [`fig13_positive_control_dynamics.pdf`](../figures/fig13_positive_control_dynamics.pdf)<br>[`fig13_positive_control_dynamics.svg`](../figures/fig13_positive_control_dynamics.svg) | `benchmark_results/physionet_v1_1_repaired/` | **VERIFIED** |
| **Figure 14** | Preprocessing Quality-Control Diagnostics and Technical Screening Exclusion Boundaries | [`fig14_preprocessing_qc_distributions.png`](../figures/fig14_preprocessing_qc_distributions.png)<br>`524e6d42d278124f...` | [`fig14_preprocessing_qc_distributions.pdf`](../figures/fig14_preprocessing_qc_distributions.pdf)<br>[`fig14_preprocessing_qc_distributions.svg`](../figures/fig14_preprocessing_qc_distributions.svg) | `benchmark_results/physionet_v1_1_repaired/` | **VERIFIED** |
| **Figure 15** | Computational Performance Scaling and Multiprocessing Execution Profiles | [`fig15_compute_scaling.png`](../figures/fig15_compute_scaling.png)<br>`3d41d10eb4df8af8...` | [`fig15_compute_scaling.pdf`](../figures/fig15_compute_scaling.pdf)<br>[`fig15_compute_scaling.svg`](../figures/fig15_compute_scaling.svg) | `benchmark_results/physionet_v1_1_repaired/` | **VERIFIED** |
| **Figure 16** | LeakCheck V1.1 Comprehensive Multi-Metric Scientific Synthesis Dashboard | [`fig16_multimetric_summary_dashboard.png`](../figures/fig16_multimetric_summary_dashboard.png)<br>`273efad1c7f58527...` | [`fig16_multimetric_summary_dashboard.pdf`](../figures/fig16_multimetric_summary_dashboard.pdf)<br>[`fig16_multimetric_summary_dashboard.svg`](../figures/fig16_multimetric_summary_dashboard.svg) | `benchmark_results/physionet_v1_1_repaired/` | **VERIFIED** |

---

## Detailed Figure Descriptions & Scientific Evidence

### Figure 1: LeakCheck Architecture, Preprocessing Pipeline, and Cross-Validation Verification Schemes
- **Raster Image (300 DPI)**: [`figures/fig01_workflow_schematic.png`](../figures/fig01_workflow_schematic.png) (`SHA-256: 9940662ddda4b0ca2faaf4c2bd9fd5454553fe5c7594a23e8e77a99f8442fbde`)
- **Vector PDF**: [`figures/fig01_workflow_schematic.pdf`](../figures/fig01_workflow_schematic.pdf) (`SHA-256: 406d3ac9d7d8803e1fb4a9b81e29aff8b5a8d0fa9ddb7146d31aaae0df4d03a1`)
- **Vector SVG**: [`figures/fig01_workflow_schematic.svg`](../figures/fig01_workflow_schematic.svg) (`SHA-256: 103d3d8d2f95ae73c320fd7f4af1ec0d037fd9c0d96b949e1b16b5d3e6d6bd1a`)
- **Short Aliases**: `figures/fig01.png` / `.pdf` / `.svg`
- **Generation Script**: `figures/scripts/generate_figures.py`
- **Scientific Description & Key Findings**: Architectural schematic showing raw multi-run PhysioNet input, run-independent FIR bandpass filtering [8–30 Hz], artifact thresholding, OAS-regularized CSP spatial filtering, shrinkage LDA classifier, and branchings into D3 (LORO), D1s (Size-Matched), D1m (k-Matched), and P1 (Positive Control Leakage).

### Figure 2: Participant Screening Flowchart and Exclusion Accounting (CONSORT Guideline, N = 105)
- **Raster Image (300 DPI)**: [`figures/fig02_participant_flow.png`](../figures/fig02_participant_flow.png) (`SHA-256: b70602cfa858cc81aaff9d155a175b5915ba4dcbafb981adf2264d53bea50d6c`)
- **Vector PDF**: [`figures/fig02_participant_flow.pdf`](../figures/fig02_participant_flow.pdf) (`SHA-256: 2497457d43316d92721b63f35282967f12a16e114d9bd4774c98c377d2417bb8`)
- **Vector SVG**: [`figures/fig02_participant_flow.svg`](../figures/fig02_participant_flow.svg) (`SHA-256: a20adf45d29efb6ba6b59604c3e414d4409a46d2a4944b449279d6d9514aa78a`)
- **Short Aliases**: `figures/fig02.png` / `.pdf` / `.svg`
- **Generation Script**: `figures/scripts/generate_figures.py`
- **Scientific Description & Key Findings**: CONSORT flowchart documenting 109 requested participants -> 106 passed automated QC (3 excluded: S044 bad channels 18.75%, S069 bad channels 18.75%, S091 100% trials dropped) -> 105 passed trial eligibility (1 excluded: S086 with 24 trials < 30) -> 105 analyzed benchmark cohort (96.33% retention). Formal refutation of line 95 error regarding S088, S092, S100, S104.

### Figure 3: Paired Participant-Level Decoding Accuracies Across Cross-Validation Schemes (N = 105)
- **Raster Image (300 DPI)**: [`figures/fig03_paired_accuracy_scatter.png`](../figures/fig03_paired_accuracy_scatter.png) (`SHA-256: 98688e76e1d77502e0b6f076ed4333539b0f70441cc3b0721edcaab6fc282238`)
- **Vector PDF**: [`figures/fig03_paired_accuracy_scatter.pdf`](../figures/fig03_paired_accuracy_scatter.pdf) (`SHA-256: 8c9ed16edbeb69238ddf38605a1802190caa02104bca86fda4b705e6434588f7`)
- **Vector SVG**: [`figures/fig03_paired_accuracy_scatter.svg`](../figures/fig03_paired_accuracy_scatter.svg) (`SHA-256: 76c05e6b0f202d35af282a61d2c0a6374a6106897b6fc3c68a110fe2136668f6`)
- **Short Aliases**: `figures/fig03.png` / `.pdf` / `.svg`
- **Generation Script**: `figures/scripts/generate_figures.py`
- **Scientific Description & Key Findings**: 3-panel scatter plot comparing reference D3 LORO decoding accuracy against D1s (Size-Matched), D1m (k-Matched), and P1 (Global CSP), with unity lines (y=x), chance levels (50%), linear fits, and color-coded points illustrating random partition deflation vs. massive leakage inflation.

### Figure 4: Accuracy Distributions and Paired Cross-Validation Performance Contrasts (N = 105)
- **Raster Image (300 DPI)**: [`figures/fig04_inflation_distributions.png`](../figures/fig04_inflation_distributions.png) (`SHA-256: 9eda3ec8c6f0795e914d21a3646e965899245b4a96cb2e8e3e7742d2414fc5a5`)
- **Vector PDF**: [`figures/fig04_inflation_distributions.pdf`](../figures/fig04_inflation_distributions.pdf) (`SHA-256: 217ad1bc7195dca71d9d1db72f75c512138553b78e60313056ff0b6f92ecdd98`)
- **Vector SVG**: [`figures/fig04_inflation_distributions.svg`](../figures/fig04_inflation_distributions.svg) (`SHA-256: fbeb688b83875c64f3657c44fb72b3e6f8a580da5151632aee9eeda949147eb8`)
- **Short Aliases**: `figures/fig04.png` / `.pdf` / `.svg`
- **Generation Script**: `figures/scripts/generate_figures.py`
- **Scientific Description & Key Findings**: Panel A: Violin and box plots of absolute decoding accuracies for D3, D1s, D1m, and P1. Panel B: Paired difference distributions (Δ = Leaky - Ref) with Hodges-Lehmann points, 95% BCa confidence intervals, and shaded TOST equivalence band (±2.0 pp).

### Figure 5: Hodges-Lehmann Effect Size Forest Plot Across Primary Cross-Validation Contrasts
- **Raster Image (300 DPI)**: [`figures/fig05_effect_size_forest_plot.png`](../figures/fig05_effect_size_forest_plot.png) (`SHA-256: 5607c539ba37f17b7ec2382fe74cb35395ab10e4160d37702efdd1a28cf5db4b`)
- **Vector PDF**: [`figures/fig05_effect_size_forest_plot.pdf`](../figures/fig05_effect_size_forest_plot.pdf) (`SHA-256: 1bd92ac764731c8a88b883f5e29768232fdbea8cf0ee8dc48650e36f172dbcf3`)
- **Vector SVG**: [`figures/fig05_effect_size_forest_plot.svg`](../figures/fig05_effect_size_forest_plot.svg) (`SHA-256: c3dd79eb61386588d0acc559cd644184967cdda44b96293871348df1874c94c5`)
- **Short Aliases**: `figures/fig05.png` / `.pdf` / `.svg`
- **Generation Script**: `figures/scripts/generate_figures.py`
- **Scientific Description & Key Findings**: Publication-grade forest plot showing Hodges-Lehmann median differences and exact 95% BCa confidence intervals for D1s - D3 (-5.71 pp [-7.32, -3.94]), D1m - D3 (-5.91 pp [-7.57, -4.09]), and P1 - D3 (+22.27 pp [+19.24, +25.00]), with rank-biserial correlations and Cohen's dz.

### Figure 6: FIR Filter Boundary Isolation and Cross-Run Bleed Comparison (Legacy vs. Repaired)
- **Raster Image (300 DPI)**: [`figures/fig06_filter_bleed_comparison.png`](../figures/fig06_filter_bleed_comparison.png) (`SHA-256: 57eb7932fe38d2bbc8afabb7dfff5bdec0a03d3a93b08ea8e2d40d1fdb73db3f`)
- **Vector PDF**: [`figures/fig06_filter_bleed_comparison.pdf`](../figures/fig06_filter_bleed_comparison.pdf) (`SHA-256: e024283dd90f35d9f593c2d283c46be6d755377118147e12a341792dc23d05d5`)
- **Vector SVG**: [`figures/fig06_filter_bleed_comparison.svg`](../figures/fig06_filter_bleed_comparison.svg) (`SHA-256: 58876b71922e2e7b5680dba21b828abb49a9698f2d1932f1312ab147ba782e5d`)
- **Short Aliases**: `figures/fig06.png` / `.pdf` / `.svg`
- **Generation Script**: `figures/scripts/generate_figures.py`
- **Scientific Description & Key Findings**: Waveform comparison showing > 1.0 V impulse bleed crossing run boundaries in legacy concatenated filtering vs. strictly zero impulse bleed (Δ = 0.000 V) in repaired run-independent MNE reflection padding buffers.

### Figure 7: SVD Numerical Rank Diagnostics, CAR Null Space, and OAS Covariance Conditioning
- **Raster Image (300 DPI)**: [`figures/fig07_svd_rank_spectrum.png`](../figures/fig07_svd_rank_spectrum.png) (`SHA-256: ab0241314699f96b0efb8d319ad59aab633db0e6f97cbd160c37e0cd498c7cff`)
- **Vector PDF**: [`figures/fig07_svd_rank_spectrum.pdf`](../figures/fig07_svd_rank_spectrum.pdf) (`SHA-256: d1e4f5d2d7dd48f7cae599e65b04747bba361f90e28a2712dd9eee43340bedf7`)
- **Vector SVG**: [`figures/fig07_svd_rank_spectrum.svg`](../figures/fig07_svd_rank_spectrum.svg) (`SHA-256: 5224b51c310a11635d347701d9a8fcfdf7fe4de979a001f6319104749569b2b8`)
- **Short Aliases**: `figures/fig07.png` / `.pdf` / `.svg`
- **Generation Script**: `figures/scripts/generate_figures.py`
- **Scientific Description & Key Findings**: Panel A: Log-scale singular value spectra showing structural rank drop from 64 to 63 under CAR (null singular value < 1e-14) and rank 62 under bad channel interpolation. Panel B: Covariance eigenvalue spectrum comparing ill-conditioned empirical SCM with well-conditioned OAS shrinkage (κ ≈ 118).

### Figure 8: Pratt Wilcoxon Ranked Participant Differences for Random Partitioning vs. Positive Leakage
- **Raster Image (300 DPI)**: [`figures/fig08_pratt_wilcoxon_ranking.png`](../figures/fig08_pratt_wilcoxon_ranking.png) (`SHA-256: 92024d3d9ff39d12ded438a3281b5555fe5df5b64ca5f4182a93bd2816ca010e`)
- **Vector PDF**: [`figures/fig08_pratt_wilcoxon_ranking.pdf`](../figures/fig08_pratt_wilcoxon_ranking.pdf) (`SHA-256: 0d5735b7594bc4c55ced19b3b646eded4a1efb9ce0b52b99bc271e7d1e6c385d`)
- **Vector SVG**: [`figures/fig08_pratt_wilcoxon_ranking.svg`](../figures/fig08_pratt_wilcoxon_ranking.svg) (`SHA-256: eca74eb42f0f03b9c15ea2ca1ee31bbf970fcf4410c2300292eaad808263edea`)
- **Short Aliases**: `figures/fig08.png` / `.pdf` / `.svg`
- **Generation Script**: `figures/scripts/generate_figures.py`
- **Scientific Description & Key Findings**: Ordered participant difference bar plots highlighting 80/105 negative ranks in D1s - D3 (deflation from breaking run autocorrelation) vs. 104/105 positive ranks in P1 - D3 (universal optimistic bias from global CSP).

### Figure 9: Empirical BCa Bootstrap Distribution Density Curves (B = 10,000 Resamples)
- **Raster Image (300 DPI)**: [`figures/fig09_bca_bootstrap_density.png`](../figures/fig09_bca_bootstrap_density.png) (`SHA-256: 6b21dbab77f85d792b2eb7bf5b4b2514219c8f2249b2b016e7d864078c519fc7`)
- **Vector PDF**: [`figures/fig09_bca_bootstrap_density.pdf`](../figures/fig09_bca_bootstrap_density.pdf) (`SHA-256: fc3235f2dc26425e34709b8a7ca4ece8515db5dbcbb1eeac93eeddf7a3f1b8a3`)
- **Vector SVG**: [`figures/fig09_bca_bootstrap_density.svg`](../figures/fig09_bca_bootstrap_density.svg) (`SHA-256: cd4f420b39b09c3be76c8a1a37732b2a9eda0e9faf2d493d3b307b117dde4496`)
- **Short Aliases**: `figures/fig09.png` / `.pdf` / `.svg`
- **Generation Script**: `figures/scripts/generate_figures.py`
- **Scientific Description & Key Findings**: Histograms and kernel density estimates of 10,000 bootstrap resamples for Hodges-Lehmann location estimates of D1s - D3, D1m - D3, and P1 - D3, highlighting 95% BCa confidence interval limits and point estimates.

### Figure 10: TOST Equivalence Testing Bounds: Conclusive Rejection of Equivalence for Random Partitions
- **Raster Image (300 DPI)**: [`figures/fig10_tost_equivalence_margins.png`](../figures/fig10_tost_equivalence_margins.png) (`SHA-256: 882449b16a51cfdd8f8ee686ddb55da25ed53f13403c5e7528f6cf245683a3f0`)
- **Vector PDF**: [`figures/fig10_tost_equivalence_margins.pdf`](../figures/fig10_tost_equivalence_margins.pdf) (`SHA-256: 0dab5ca343f2271fe882e77f9b51ac54493145ab896ffe5f12a3303ff2a00746`)
- **Vector SVG**: [`figures/fig10_tost_equivalence_margins.svg`](../figures/fig10_tost_equivalence_margins.svg) (`SHA-256: e36d3afa0fcbfdac82cd18201d28b879e8cdd944935c5b0ce6bc1fcafa077dfa`)
- **Short Aliases**: `figures/fig10.png` / `.pdf` / `.svg`
- **Generation Script**: `figures/scripts/generate_figures.py`
- **Scientific Description & Key Findings**: Two One-Sided Tests (TOST) equivalence region [±2.0 pp] and 90% confidence intervals for mean paired differences, conclusively rejecting equivalence (p > 0.05) between random splits and LORO.

### Figure 11: Leave-One-Run-Out Fold Stability and Parameter Invariance Across Cross-Validation Partitions
- **Raster Image (300 DPI)**: [`figures/fig11_cross_validation_fold_stability.png`](../figures/fig11_cross_validation_fold_stability.png) (`SHA-256: 9b7054d8437618d9be71b3d96d93e1f63585875c51d80a18da97ec286327ea2f`)
- **Vector PDF**: [`figures/fig11_cross_validation_fold_stability.pdf`](../figures/fig11_cross_validation_fold_stability.pdf) (`SHA-256: e98fdd2c9b401e166db911c4fe711d7a313ac791a1732418e8ca3ee4e56f29d8`)
- **Vector SVG**: [`figures/fig11_cross_validation_fold_stability.svg`](../figures/fig11_cross_validation_fold_stability.svg) (`SHA-256: 2f9bea9e29c1cb9da0eb7b2a4fa6b89c91f5e35321e92d20f4988a91c85b87fa`)
- **Short Aliases**: `figures/fig11.png` / `.pdf` / `.svg`
- **Generation Script**: `figures/scripts/generate_figures.py`
- **Scientific Description & Key Findings**: Parallel coordinate trajectories showing participant accuracy consistency across LORO Folds 0, 1, and 2, alongside preprocessor adaptive artifact threshold tau stability across folds.

### Figure 12: Hardware Sampling Rate Invariance: Validating Full Inclusion of S088, S092, and S100
- **Raster Image (300 DPI)**: [`figures/fig12_sampling_rate_invariance.png`](../figures/fig12_sampling_rate_invariance.png) (`SHA-256: bc0c3fa712c311ae8d08c831d58ecb4d5a8a1fbd46fb3e3a8865e1bb7e0a300d`)
- **Vector PDF**: [`figures/fig12_sampling_rate_invariance.pdf`](../figures/fig12_sampling_rate_invariance.pdf) (`SHA-256: 51317f360d255fb1643f6560a4e3e644a59c3b60a34da329f5cbeabf5d5faabc`)
- **Vector SVG**: [`figures/fig12_sampling_rate_invariance.svg`](../figures/fig12_sampling_rate_invariance.svg) (`SHA-256: cb9c51599351ec00695b3e8ac289b92a30581a905a2ef21711c7b2d83c9719a0`)
- **Short Aliases**: `figures/fig12.png` / `.pdf` / `.svg`
- **Generation Script**: `figures/scripts/generate_figures.py`
- **Scientific Description & Key Findings**: Decoding accuracy distributions and spatial covariance dimension (64x64) and rank (63) invariance between native 160.0 Hz participants (n=102) and native 128.0 Hz participants (n=3: S088, S092, S100).

### Figure 13: Positive Control (P1) Leakage Dynamics: Universal Optimistic Bias from Global CSP
- **Raster Image (300 DPI)**: [`figures/fig13_positive_control_dynamics.png`](../figures/fig13_positive_control_dynamics.png) (`SHA-256: dccf62fcfef45d3187a506cb9d263413f661f0062cf4e9d83a96d37059dc169e`)
- **Vector PDF**: [`figures/fig13_positive_control_dynamics.pdf`](../figures/fig13_positive_control_dynamics.pdf) (`SHA-256: 96a1c9a82c3b0cbcb6a43df9821e94dc0c2795c91bc4c39550f9b4d48a6b21c6`)
- **Vector SVG**: [`figures/fig13_positive_control_dynamics.svg`](../figures/fig13_positive_control_dynamics.svg) (`SHA-256: b7b0d1d04bd637c7df07b766edbb2c8a9384677f557985aea235375ddca74196`)
- **Short Aliases**: `figures/fig13.png` / `.pdf` / `.svg`
- **Generation Script**: `figures/scripts/generate_figures.py`
- **Scientific Description & Key Findings**: Sorted waterfall plot of P1 - D3 shift across all 105 participants (104 positive, mean +22.31 pp, max +47.78 pp) and scatter plot illustrating massive optimistic inflation.

### Figure 14: Preprocessing Quality-Control Diagnostics and Technical Screening Exclusion Boundaries
- **Raster Image (300 DPI)**: [`figures/fig14_preprocessing_qc_distributions.png`](../figures/fig14_preprocessing_qc_distributions.png) (`SHA-256: 524e6d42d278124fcfcf34ec8f320717ae62b99cfc30a5bae1f9ca449ff4ece9`)
- **Vector PDF**: [`figures/fig14_preprocessing_qc_distributions.pdf`](../figures/fig14_preprocessing_qc_distributions.pdf) (`SHA-256: 0c1104ba4c0fd54a8eccfb2e8e6a26ff7adae8c4e56114dcf97df286d188c7f2`)
- **Vector SVG**: [`figures/fig14_preprocessing_qc_distributions.svg`](../figures/fig14_preprocessing_qc_distributions.svg) (`SHA-256: f6d57333913b4b2f14a5447d0d0c5d7a021e879aff4e46a1f72d3a9a367130fe`)
- **Short Aliases**: `figures/fig14.png` / `.pdf` / `.svg`
- **Generation Script**: `figures/scripts/generate_figures.py`
- **Scientific Description & Key Findings**: Distribution of bad channel counts highlighting excluded subjects S044 and S069 (> 15% threshold) and retained trial counts highlighting S086 (< 30 trials) and S091 (100% thresholding rejection).

### Figure 15: Computational Performance Scaling and Multiprocessing Execution Profiles
- **Raster Image (300 DPI)**: [`figures/fig15_compute_scaling.png`](../figures/fig15_compute_scaling.png) (`SHA-256: 3d41d10eb4df8af822807e2c90a9ec20a7f00ebaa8b7b914d694f3070d1dc19e`)
- **Vector PDF**: [`figures/fig15_compute_scaling.pdf`](../figures/fig15_compute_scaling.pdf) (`SHA-256: f07d75ce4aeee5e22028925406773d7e7505d7b156660692ca4ea79ad63edcea`)
- **Vector SVG**: [`figures/fig15_compute_scaling.svg`](../figures/fig15_compute_scaling.svg) (`SHA-256: 5b51e58e1b7cb377f211061bd5d9c728d0d1b88640f8a9db7cf9227c8f4a1d23`)
- **Short Aliases**: `figures/fig15.png` / `.pdf` / `.svg`
- **Generation Script**: `figures/scripts/generate_figures.py`
- **Scientific Description & Key Findings**: Histogram of wall-clock processing time per participant (mean = 11.89s) and cumulative execution scaling curve across the 105 participants (1248.24s across 4 workers).

### Figure 16: LeakCheck V1.1 Comprehensive Multi-Metric Scientific Synthesis Dashboard
- **Raster Image (300 DPI)**: [`figures/fig16_multimetric_summary_dashboard.png`](../figures/fig16_multimetric_summary_dashboard.png) (`SHA-256: 273efad1c7f585274dd594c4d5482debdb82c4c777fafe94a396f1722f9d2a1c`)
- **Vector PDF**: [`figures/fig16_multimetric_summary_dashboard.pdf`](../figures/fig16_multimetric_summary_dashboard.pdf) (`SHA-256: 4330786aaacc047219dcedbde3575693b0d47d528c2a9bd7a943c1c67ffa2ae6`)
- **Vector SVG**: [`figures/fig16_multimetric_summary_dashboard.svg`](../figures/fig16_multimetric_summary_dashboard.svg) (`SHA-256: 9d1e6d08a9fe4c63fdd68d1e36081e6fb473e68ac146ea838edda934eb879514`)
- **Short Aliases**: `figures/fig16.png` / `.pdf` / `.svg`
- **Generation Script**: `figures/scripts/generate_figures.py`
- **Scientific Description & Key Findings**: Comprehensive 4-panel publication dashboard integrating paired performance shifts, effect size forest plot, deflation waterfall, and 5-dimensional methodological rigor radar.

