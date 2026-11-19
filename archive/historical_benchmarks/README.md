# Historical Benchmark Archives & Scientific Provenance Ledger

This directory contains archived, historical benchmark result directories from earlier iterations of the LeakCheck V1.1 validation and remediation pipeline. These runs are frozen and preserved for permanent scientific auditability, forensic verification, and methodological transparency.

All historical benchmark iterations in this directory are **SUPERSEDED** by the single authoritative benchmark result set at:
`benchmark_results/physionet_v1_1/`

---

## 1. Directory Inventory and Provenance Ledger

| Archived Directory | Execution Date | Git Commit / Tag | Python / Software Environment | Cohort Size | Status | Primary Purpose / Historical Context |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `physionet_v1_1_final/` | 2026-11-15T07:18:00Z | `4c63b27` / `2774aa9` | Python 3.11, MNE 1.13.2, Scipy 1.18.1, Sklearn 1.9.1 | $N=105$ included ($N=109$ screened) | **SUPERSEDED** | Historical baseline run prior to surgical remediation |
| `physionet_v1_1_repaired/` | 2026-11-18T16:45:00Z | Milestone 1 Remediation | Python 3.11, MNE 1.13.2, Scipy 1.18.1, Sklearn 1.9.1 | $N=105$ included ($N=109$ screened) | **SUPERSEDED** | Intermediate remediation run validating D1s disjointness and SciPy underflow fixes |

---

## 2. Identified Defects & Scientific Analysis of Superseded Runs

### 2.1 `physionet_v1_1_final/` (Historical Baseline Run)
- **Provenance**: Generated during the initial V1.1 audit phase on 2026-11-15.
- **Settings Manifest** (`settings.json`):
  ```json
  {
    "dataset": "physionet",
    "designs": "D3_loro,D1m_matched_k,D1s_size_matched,P1_csp_on_all",
    "decoders": "csp_lda",
    "n_null": 0,
    "null_types": "perm,shift",
    "n_repeats": 5,
    "n_repeats_matched": 20,
    "min_trials": 30,
    "min_per_class": 10,
    "min_per_run": 8,
    "csp": "mne",
    "csp_reg": "oas",
    "seed": 0
  }
  ```
- **Identified Methodological & Statistical Defects**:
  1. **$D_{1s}$ Trial Partitioning Defect (Repeats Overlap)**:
     - In `physionet_v1_1_final`, the $D_{1s}$ size-matched partition loop sliced random permutations of class trials (`perm0[:n_test_0]` and `perm0[n_test_0 : n_test_0 + n_train_0]`) independently per fold.
     - While train and test were disjoint within each individual fold, test partitions across the 3 folds of a repeat were *not* constrained to be mutually disjoint. Trials were evaluated multiple times within a single repeat, violating the exact complete-coverage partitioning invariant of $K$-fold cross-validation.
     - This produced an artificially attenuated headline deflation estimate ($\Delta_{\text{HL}} = -2.68$ pp vs. true $\Delta_{\text{HL}} = -5.71$ pp).
  2. **Statistical Underflow Defect ($p = 0.00\text{e}+00$)**:
     - Large-$Z$ Wilcoxon signed-rank and normal tail probabilities were computed via naive subtraction: $p = 2 \times (1 - \Phi(|Z|))$.
     - For large $Z > 8.2$ (such as $Z = 8.845$ in $P_1$ vs. $D_3$), floating-point IEEE-754 precision underflowed to exact zero (`0.00e+00`), failing strict statistical reporting standards.
  3. **Unpopulated Null Distribution Tables**:
     - Executed with `--n-null 0`. Consequently, `null_table.csv`, `paired_delta_vs_null.csv`, and `subject_empirical_p.csv` were left as empty 2-byte placeholder files containing only newline characters.

### 2.2 `physionet_v1_1_repaired/` (Intermediate Remediation Run)
- **Provenance**: Generated on 2026-11-18 during Milestone 1 surgical remediation.
- **Settings Manifest** (`settings.json`):
  ```json
  {
    "dataset": "physionet",
    "designs": "D3_loro,D1m_matched_k,D1s_size_matched,P1_csp_on_all",
    "decoders": "csp_lda",
    "n_null": 0,
    "null_types": "perm,shift",
    "n_repeats": 5,
    "n_repeats_matched": 20,
    "min_trials": 30,
    "min_per_class": 10,
    "min_per_run": 8,
    "csp": "mne",
    "csp_reg": "oas",
    "seed": 42
  }
  ```
- **Remediations Validated**:
  - Integrated `sp.size_matched_random_repeats` ensuring 100% mutually disjoint test folds with exact LORO fold-size and class-balance matching (100% trial coverage per repeat).
  - Replaced naive CDF subtractions with `scipy.stats.norm.sf` / `scipy.stats.t.sf`, resolving numerical underflow ($P_1$ Pratt $p = 9.076\times 10^{-19}$).
  - Populated Holm-Bonferroni multiplicity adjustments across Pratt Wilcoxon p-values.
- **Remaining Limitations**:
  - Executed with non-standard random seed (`seed: 42` instead of standard `seed: 0`).
  - Executed with `n_null: 0`, leaving empirical null distributions uncomputed.

---

## 3. Authoritative Single Source of Truth: `benchmark_results/physionet_v1_1/`

The definitive, authoritative benchmark result set for all manuscript tables, figures, statistical audits, and release artifacts is housed strictly in:
`benchmark_results/physionet_v1_1/`

### Authoritative Run Specifications:
- **Dataset**: PhysioNet EEG Motor Movement/Imagery Database (EEGMMIDB)
- **Cohort**: $N = 105$ included participants ($S001$–$S109$, strictly excluding technical failures $S044, S069, S086, S091$)
- **Decoder**: OAS-regularized Common Spatial Patterns + Shrinkage Linear Discriminant Analysis (`csp_lda`, `mne_oas`)
- **Designs**:
  - $D_3$: Leave-one-run-out (3 folds, fold-isolated preprocessing and decoding, 100% leak-free reference)
  - $D_{1m}$: 3-fold Stratified K-Fold (5 repeats = 15 folds)
  - $D_{1s}$: Size-matched random split (20 repeats = 60 folds) via `sp.size_matched_random_repeats`
  - $P_1$: Positive control global supervised CSP fit on all trials + 3 LORO LDA folds
- **Random Seed**: `seed = 0`
- **Null Distribution Controls**: `--n-null 10` with within-run permutation (`perm`) and circular shift (`shift`) models.
- **Outputs Populated**:
  - `leakcheck_raw.csv`: Complete fold-level and trial-level raw predictions across real and null label sets
  - `subject_info.csv`: Complete participant demographics, native sampling rates (102 @ 160Hz, 3 @ 128Hz), and temporal autocorrelation metrics
  - `inflation_by_subject.csv`: Paired participant-level accuracy differences across all contrasts
  - `inflation_table.csv`: Population-level effect sizes, Hodges-Lehmann shifts, exact BCa CIs, Pratt Wilcoxon tests, and TOST statistics
  - `null_table.csv`: Empirical false-positive rates and optimism metrics under permuted and shifted null models
  - `paired_delta_vs_null.csv`: Paired empirical difference tests against null distributions
  - `subject_empirical_p.csv`: Participant-level empirical p-values against null distributions
  - `participant_flow_manifest.json`: Machine-readable participant flow accounting and formal refutation of draft line 95
  - `fold_details.json`: Exact fold boundaries, trial counts, and parameter stability records
  - `leakcheck_summary.json`: Software environment, platform specs, and compute execution hashes
