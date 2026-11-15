# LeakCheck: A Leakage-Aware Benchmarking Framework for Evaluating Validation Strategies and Supervised Contamination in Within-Subject Motor-Imagery EEG Decoding

**Repository:** [https://github.com/JOYJIT-06/LeakCheck](https://github.com/JOYJIT-06/LeakCheck) (Commit [2be2821](https://www.google.com/search?q=https://github.com/JOYJIT-06/LeakCheck/tree/2be2821) | Frozen Record `rec_physionet_v1_1_e4a2b05c` | Settings Hash `e4a2b05c`)

**LeakCheck** (`src/emi/`) is a reproducible benchmarking and audit framework designed to evaluate **validation-partitioning choices** (run-held-out vs. trial-level random splitting) separately from **supervised pipeline contamination** (fitting spatial filters using held-out test labels prior to partitioning) in within-subject motor-imagery electroencephalography (MI-EEG) decoding.

## 1. Scope & Methodological Distinction

Published BCI evaluations frequently group two distinct methodological phenomena under the single umbrella term *"data leakage"*:

1. **Validation Design (Partitioning Granularity)**: Choosing how trials are partitioned into training and testing sets while keeping all learned parameters strictly nested inside the training fold—specifically comparing run-held-out validation (`D3_loro`, where entire recording runs are held out) against trial-level random cross-validation across pooled runs (`D1s_size_matched` and `D1m_matched_k`). These protocols evaluate different generalization targets (inter-run transfer vs. within-pool interpolation) without exposing held-out test labels during training.
2. **Supervised Feature-Extraction Contamination**: Fitting supervised spatial filters (Common Spatial Patterns, CSP) on the entire dataset—including held-out test trials and their class labels—prior to cross-validation splitting (`P1_csp_on_all`), and subsequently training a fold-level classifier on the globally projected features.

In the [PhysioNet EEG Motor Movement/Imagery Dataset](https://physionet.org/content/eegmmidb/1.0.0/) (`EEGMMIDB`, $N = 105$ retained participants, frozen artifact record `rec_physionet_v1_1_e4a2b05c`), these two choices act in **opposite empirical directions** relative to run-held-out validation (`D3_loro`):

* Size- and class-matched random trial splitting (`D1s_size_matched`) produced an estimated accuracy **2.68 percentage points (pp) lower** in Hodges–Lehmann location than `D3_loro` ($\hat{\theta}_{\text{HL}} = -2.68\text{ pp}$, 95% BCa CI `[-3.95, -1.47] pp` in `inflation_table.csv` / `[-3.94, -1.46] pp` via `scipy.stats.bootstrap(..., random_state=0)`, $p_{\text{Holm}} = 5.86 \times 10^{-5}$).
* Unconstrained $k$-matched random splitting (`D1m_matched_k`) produced an estimated accuracy **4.47 pp lower** in Hodges–Lehmann location than `D3_loro` ($\hat{\theta}_{\text{HL}} = -4.47\text{ pp}$, 95% BCa CI `[-5.83, -3.14] pp` in `inflation_table.csv` / `[-5.80, -3.11] pp` via `random_state=0`, $p_{\text{Holm}} = 1.08 \times 10^{-8}$).
* Joining participants by ID in `benchmark_results/physionet_v1_1/inflation_by_subject.csv` shows that matching fold sample size and class counts (`D1s_size_matched` vs. `D1m_matched_k`) yielded a direct Hodges–Lehmann location difference of **$+1.86\text{ pp}$** (95% BCa CI `[+1.27, +2.50] pp`, arithmetic mean $+1.89\text{ pp}$, median $+1.79\text{ pp}$, $p_{\text{Holm}} = 4.87 \times 10^{-7}$).
* Deliberate pre-split supervised CSP contamination (`P1_csp_on_all`) produced an estimated accuracy **24.50 pp higher** in Hodges–Lehmann location than `D3_loro` ($\hat{\theta}_{\text{HL}} = +24.50\text{ pp}$, 95% BCa CI `[+22.22, +27.78] pp` in `inflation_table.csv` / `[+21.75, +27.78] pp` via `random_state=0`, $p_{\text{Holm}} = 4.43 \times 10^{-18}$ [`wilcox`] / $2.42 \times 10^{-18}$ [`pratt`]), lifting cohort mean accuracy from **60.15%** (`D3_loro`) to **84.97%** (`P1_csp_on_all`).

> **Scope Note on Mechanisms**: In this dataset and pipeline, random trial splitting produced lower estimated accuracy than leave-one-run-out validation (`D3_loro`), whereas pre-split supervised CSP fitting substantially increased estimated accuracy. Here `D3_loro` serves as the run-held-out reference protocol rather than proven deployment ground truth, and the mechanisms underlying the observed difference between random and run-held-out splitting were not directly tested.

## 2. Protocol & Positive-Control Taxonomy (V1.1 Frozen Record vs. V2 Main-Branch Nomenclature)

To prevent ambiguity between the frozen V1.1 PhysioNet artifact (`benchmark_results/physionet_v1_1/`) and the expanded V2 multi-dataset taxonomy in `src/emi/leakcheck.py`, Table 2.1 maps all protocol identifiers across versions.

### Table 2.1: Cross-Reference Between V1.1 Frozen Artifact Identifiers and V2 Main-Branch Identifiers

| V1.1 Frozen ID (`physionet_v1_1`) | V2 Main-Branch ID | Category | Partitioning & Parameter-Fitting Boundary | Included in Frozen PhysioNet V1.1 CSVs? |
| :--- | :--- | :--- | :--- | :--- |
| **`D3_loro`** | `D3_loro` / `L0_block` | Run-Held-Out Reference | 3-fold Leave-One-Run-Out across Runs 4, 8, 12; OAS-CSP ($m=4$) and shrinkage LDA fitted strictly inside training runs. | **Yes** (`reference` / `ref_design`) |
| **`D1s_size_matched`** | `D1s_size_matched` / `L2_random_size_matched` | Size/Class-Matched Random | 20-repeat random trial split across pooled Runs 4, 8, 12 constrained to match exact `D3_loro` per-fold train/test sample sizes and class counts; fold-nested CSP+LDA. | **Yes** (315-row & summary CSVs) |
| **`D1m_matched_k`** | `D1m_matched_k` / `L2_random_k_matched` | $k$-Matched Stratified Random | 5-repeat 3-fold stratified random trial split (`RepeatedStratifiedKFold`, `seed=0`) across pooled runs without matching run-specific fold sizes; fold-nested CSP+LDA. | **Yes** (315-row & summary CSVs) |
| **`P1_csp_on_all`** | `P7_global_csp` (`P1_csp_on_all` alias) | Positive Contamination Control | Supervised OAS-CSP ($m=4$) fitted once on all trials and labels across all selected runs before `D3_loro` splitting; fold-nested LDA fitted on globally projected features. | **Yes** (315-row & summary CSVs) |
| *(Not in V1.1)* | `P1`–`P6`, `P8`–`P9` | Extended V2 Perturbations | Additional main-branch diagnostic controls (e.g., global standardization, feature selection, hyperparameter tuning, and channel interpolation checks). | **No** (V2 extension only) |

## 3. Repository Structure & Key Files

```text
LeakCheck/
├── benchmark_results/
│   └── physionet_v1_1/
│       ├── inflation_by_subject.csv         # 315 subject-contrast rows (N = 105 subjects × 3 designs)
│       ├── inflation_table.csv              # Frozen 3-row cohort statistical summary table (20 columns)
│       ├── excluded_or_failed_subjects.csv  # Operational exclusion log (S044, S069, S086, S091)
│       ├── subject_info.csv                 # Retained subject trial counts & SHA-256 .npz cache hashes
│       ├── settings.json                    # Frozen execution parameters (hash: e4a2b05c, n_null: 0)
│       └── provenance.json                  # Record rec_physionet_v1_1_e4a2b05c metadata
├── docs/
│   └── AUDIT/
│       └── V1_1_PROVENANCE_RECONCILIATION.md # Historical cache provenance & audit notes
├── src/
│   └── emi/
│       ├── config.py                        # Pipeline & eligibility gate configuration defaults
│       ├── preprocess.py                    # MNE epoching (baseline=None, include_tmax=False) & caching
│       ├── splitters.py                     # D3_loro, D1m_matched_k, and D1s_size_matched splitters
│       ├── decoders.py                      # OAS-CSP (n_components=4, reg='oas') & shrinkage LDA
│       ├── metrics.py                       # Pooled vs. fold-mean accuracy & repeat aggregation
│       ├── leakcheck.py                     # Orchestration of fold-nested & P1 contaminated evaluations
│       └── leakstats.py                     # Hodges-Lehmann, BCa bootstrap, Wilcoxon, dz, & paired TOST
├── recalculate_all_stats.py                 # Standalone statistical verification & reconciliation script
└── README.md
```

## 4. Cohort Accounting & Provenance Reconciliation (`N = 105`)

Of the $109$ volunteers in the [PhysioNet EEG Motor Movement/Imagery Dataset v1.0.0](https://physionet.org/content/eegmmidb/1.0.0/) (`S001`–`S109`), the frozen V1.1 benchmark (`benchmark_results/physionet_v1_1/`) retains **$N = 105$ participants**:

* **Missing Local Cache Files ($n = 3$)**: **`S044`, `S069`, and `S091`** failed with `"no cache file D:\my lab\LeakCheck_Cache\physionet\sub-0{44,69,91}_epochs.npz"` in `excluded_or_failed_subjects.csv`. These represent missing local cache files at execution time rather than verified raw EDF recording defects.
* **Excluded by Trial-Count Eligibility Gate ($n = 1$)**: **`S086`** was excluded with `"EXCLUDED: only 24 trials (< 30)"` under the configured gate (`min_trials >= 30`, `min_per_class >= 10`, `min_runs >= 3`, `min_per_run >= 8`).
* **Erratum Note on `docs/AUDIT/V1_1_PROVENANCE_RECONCILIATION.md`**: An earlier note in `V1_1_PROVENANCE_RECONCILIATION.md` listed `sub-088, sub-092, sub-100, sub-104` as excluded and `sub-086` as retained. Direct inspection of `benchmark_results/physionet_v1_1/inflation_by_subject.csv` and `excluded_or_failed_subjects.csv` confirms that **`S088`, `S092`, `S100`, and `S104` are present and retained in `inflation_by_subject.csv`**, whereas **`S044`, `S069`, `S086`, and `S091` are the exact 4 absent subject IDs**.

## 5. Reconciled Benchmark Results (`benchmark_results/physionet_v1_1/`)

### 5.1 Participant-Level Accuracy Summary Across Protocols ($N = 105$)

Calculated directly from `benchmark_results/physionet_v1_1/inflation_by_subject.csv` (`acc_ref` and `acc_leaky` columns):

| Protocol ID | Role | Mean Accuracy (SD) | Median Accuracy (IQR: Q1–Q3) | Minimum (Subject ID) | Maximum (Subject ID) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`D3_loro`** | Run-Held-Out Reference (3-fold LORO) | **60.15%** (13.29%) | **57.78%** (17.78%: 51.11%–68.89%) | **35.56%** (`S028`) | **100.00%** (`S029`; `S007` = 97.78%) |
| **`D1s_size_matched`** | Size- & Class-Matched Random (20 repeats) | **57.38%** (13.50%) | **52.89%** (16.72%: 47.73%–64.44%) | **40.11%** (`S077`) | **99.67%** (`S029`) |
| **`D1m_matched_k`** | $k=3$ Stratified Random (5 repeats) | **55.48%** (13.51%) | **52.00%** (16.44%: 45.78%–62.22%) | **33.78%** (`S017`) | **99.11%** (`S029`) |
| **`P1_csp_on_all`** | Pre-Split Global Supervised CSP Control | **84.97%** (11.16%) | **86.67%** (15.56%: 77.78%–93.33%) | **56.82%** (`S099`) | **100.00%** (`S005, S007, S009, S029, S061, S062`) |

### 5.2 Paired Contrasts & Reconciliation of `inflation_table.csv` vs. Recomputed SciPy Statistics ($N = 105$)

Why did earlier README tables and `inflation_table.csv` show minor numerical differences in the 95% BCa CI bounds and the `P1_csp_on_all` Wilcoxon $p$-value?

1. **BCa Bootstrap CI Routine**: `src/emi/leakstats.py` uses `scipy.stats.bootstrap((d,), statistic=hodges_lehmann, n_resamples=10000, confidence_level=0.95, method="BCa", random_state=0)`, which yields `[-3.94, -1.46] pp` (`D1s`), `[-5.80, -3.11] pp` (`D1m`), and `[+21.75, +27.78] pp` (`P1`). The frozen file `inflation_table.csv` recorded slightly different BCa endpoints (`[-3.95, -1.47]`, `[-5.83, -3.14]`, `[+22.22, +27.78] pp`) from an earlier bootstrap run.
2. **Wilcoxon Zero-Difference Method & Floating-Point Tie Tolerance**: In `inflation_by_subject.csv`, averaging over 20 or 5 random repeats produces 3 machine-epsilon differences in `D1s_size_matched` (`S024`: $+5.55 \times 10^{-15}\text{ pp}$, `S053`: $+1.11 \times 10^{-14}\text{ pp}$, `S067`: $+5.55 \times 10^{-15}\text{ pp}$) and 1 machine-epsilon difference in `D1m_matched_k` (`S002`: $+1.11 \times 10^{-14}\text{ pp}$, alongside exact tie `S093`: $0.0\text{ pp}$). For `P1_csp_on_all`, `S029` ($100.00\%$ vs. $100.00\%$) and `S054` ($84.09\%$ vs. $84.09\%$) are exact ties ($0.0\text{ pp}$), while `S026` ($-2.22\text{ pp}$) and `S049` ($-2.27\text{ pp}$) are negative. Passing `zero_method="wilcox"` (SciPy default in `leakstats.py`) yields $p_{\text{Holm}} = 4.43 \times 10^{-18}$ for `P1_csp_on_all` (matching `inflation_table.csv`), whereas `zero_method="pratt"` yields $p_{\text{Holm}} = 2.42 \times 10^{-18}$ (matching the earlier README table).

Both sets of values are reported transparently in **Table 5.2** below.

| Contrast ($\Delta = \text{Protocol} - \text{Ref}$) | Directional Counts (Tie Tol. $10^{-9}\text{ pp}$) [Raw Float `== 0`] | Mean $\Delta$ (SD) | Median $\Delta$ | Hodges–Lehmann $\hat{\theta}_{\text{HL}}$ | 95% BCa CI (`inflation_table.csv` / `scipy seed=0`) | Wilcoxon $p_{\text{Holm}}$ (`table` / `wilcox` / `pratt`) | Cohen's $d_z$ ($r_{\text{rb}}$) | Exploratory TOST ($\pm 2.0\text{ pp}$) $p_{\text{TOST}}$ [90% Mean CI] |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`D1s_size_matched` vs. `D3_loro`** | **36 (+), 66 (−), 3 (0)** (`S024, S053, S067`) [Raw: 39+, 66−, 0] | **−2.77 pp** (6.17 pp) | **−2.61 pp** | **−2.68 pp** (`-2.6768`) | **`[-3.95, -1.47]`** / `[-3.94, -1.46]` pp | **`5.86e-05`** / `4.99e-05` / `5.62e-05` | **−0.449** (−0.452) | **0.8985** [`[-3.77, -1.77]` pp] |
| **`D1m_matched_k` vs. `D3_loro`** | **26 (+), 77 (−), 2 (0)** (`S002, S093`) [Raw: 27+, 77−, 1] | **−4.67 pp** (6.81 pp) | **−4.00 pp** | **−4.47 pp** (`-4.4697`) | **`[-5.83, -3.14]`** / `[-5.80, -3.11]` pp | **`1.08e-08`** / `1.05e-08` / `1.06e-08` | **−0.685** (−0.659) | **0.9999** [`[-5.77, -3.56]` pp] |
| **`P1_csp_on_all` vs. `D3_loro`** | **101 (+), 2 (−)** (`S026, S049`), **2 (0)** (`S029, S054`) [Raw: 101+, 2−, 2] | **+24.82 pp** (14.01 pp) | **+23.26 pp** | **+24.50 pp** (`+24.5029`) | **`[+22.22, +27.78]`** / `[+21.75, +27.78]` pp | **`4.43e-18`** / `4.43e-18` / `2.42e-18` | **+1.771** (+0.998) | **1.0000** [`[+22.55, +27.09]` pp] |
| **`D1s_size_matched` vs. `D1m_matched_k`** *(Direct ID-Joined)* | **71 (+), 29 (−), 5 (0)** (`S011, S031, S034, S079, S096`) [Raw: 72+, 30−, 3] | **+1.89 pp** (3.43 pp) | **+1.79 pp** | **+1.86 pp** (`+1.8561`) | *Not in `inflation_table`* / **`[+1.27, +2.50]`** pp | *Not in table* / **`4.87e-07`** / `5.61e-07` ($m=4$) | **+0.552** (+0.595) | **0.3766** [`[+1.34, +2.45]` pp] |

## 6. Note on Secondary Multi-Dataset Benchmarks

In supplementary repository runs across secondary datasets (such as BNCI2014-001 and Lee2019), trial-level vs. run-held-out differences varied in sign and magnitude. **The observed direction differed across the reported benchmarks; the mechanisms responsible require further investigation.** Users should not assume that trial-level random splitting universally increases or universally decreases decoding accuracy across all EEG recording paradigms.

## 7. Reproducing the Statistical Verification from Frozen CSVs

To verify every statistic, directional count, bootstrap interval, Wilcoxon test (`wilcox` and `pratt`), and direct ID-joined contrast directly from `benchmark_results/physionet_v1_1/inflation_by_subject.csv`:

```bash
python3 recalculate_all_stats.py
```

The portable `recalculate_all_stats.py` script automatically locates `inflation_by_subject.csv` whether run from the repository root (`benchmark_results/physionet_v1_1/inflation_by_subject.csv`), from the same directory (`./inflation_by_subject.csv`), or with an explicit file path argument (`python3 recalculate_all_stats.py /path/to/inflation_by_subject.csv`).

## 8. License & Citation

Released under the MIT License. When citing the PhysioNet EEGMMIDB dataset, please cite Schalk et al. (2004) and Goldberger et al. (2000).
