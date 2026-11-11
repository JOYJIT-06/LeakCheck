# LeakCheck V1.1 Release Readiness & Independent Audit Report

**Date of Audit**: 2026-11-08  
**Target Release Date**: 2026-11-12  
**Active Working Tree**: `D:\my lab\LeakCheck_remote` (Branch: `fix/v1.1-stabilization`)  
**Package Version**: `1.1.0` (editable installation verified in `leakcheck` conda environment)  
**Evaluated Cohort**: PhysioNet EEGMMIDB ($N=105$ completed participants)

---

## 1. Executive Summary & Audit Classification

An independent, rigorous audit was conducted across the source code, test suite, benchmark artifacts, documentation, and statistical estimators of the LeakCheck repository. 

### Audit Finding Classification:
- **Critical Release Blockers**: **0 Remaining** (Previous syntax error in `preprocess.py` resolved).
- **Major Scientific Issues**: **0 Blockers**; 1 Discrepancy Resolved (Holm-Bonferroni vs. uncorrected Wilcoxon $p$-value clarified with exact mathematics).
- **Moderate Engineering Issues**: **2 Identified** (Untracked patch/zip files in working tree; long console output in multi-core MNE CSP).
- **Minor Documentation Issues**: **1 Identified** (Clarifying raw vs. Holm-corrected $p$-value labeling in table headers).
- **Verified and Acceptable**: Core architecture, D1s implementation, paired statistical analysis, 174 automated tests, OpenBMI real-data adapter, native Riemannian geometry decoders, schema-v2 cache validation, and built release wheels.

**Overall Verdict**: **RECOMMENDED FOR RELEASE (GO FOR V1.1 ON 12 NOVEMBER 2026)**.

---

## 2. Independent Verification of Core Requirements

### 2.1 Automated Test Suite Verification
- **Test Count**: 174 collected, 174 passed, 0 failed in 70.75 seconds.
- **Environment**: Python 3.12.16, MNE 1.13.2, Scikit-Learn 1.9.1, NumPy 2.5.4, SciPy 1.18.1, Pandas 3.1.0.
- **Coverage**:
  - `tests/test_cache.py`: 31 tests covering Schema-v2 round-trip, type checks, provenance metadata, bounds enforcement, and backward compatibility with Schema-v1.
  - `tests/test_preprocess.py`: 5 tests covering `clean_raw`, `_reject` (full vs. analysis window), adaptive artifact thresholds, and bad channel detection.
  - `tests/test_splitters.py`: 21 tests validating non-overlap, coverage, and strict size/class matching.
  - `tests/test_decode.py`: 3 tests including native Riemannian tangent space decoding (`ts_lr`).
  - `tests/test_openbmi.py`: 3 tests verifying real data loading from 62-channel session-1 MAT files.
  - `tests/test_leakcheck.py`, `test_leakstats.py`, `test_diagnostics.py`, `test_summary.py`: Full test coverage of metrics, null generators, BCa intervals, and exact permutation tests.

### 2.2 Mathematical Verification of `D1s_size_matched`
- **Algorithm Verification**: In `src/emi/splitters.py`, `size_matched_random_repeats` stratifies trials by class $c \in \{0, 1\}$, permutes each class pool, and allocates exactly $n_{c, g} = \sum (\text{groups} == g \land y == c)$ trials to test fold $g$.
- **Validation Contract**:
  1. Every test fold has exact class and sample counts matching LORO fold $g$.
  2. Every training fold has exact class and sample counts matching LORO training fold $g$.
  3. Every trial is tested exactly once per repeat (disjoint partition).
  4. Trials are randomly drawn across distinct recording runs, successfully breaking run-boundary isolation while strictly controlling fold geometry.

### 2.3 Preprocessing and Decoder Compatibility between D1s and D3
- **Fairness Guarantee**: Both `D1s_size_matched` and `D3_loro` are evaluated within the exact same `Ctx` object in `lc.audit_subject()`. They operate on identical preprocessed continuous epochs, identical OAS-regularized CSP parameters (`n_components=4`), identical LDA classifiers, and identical random seeds.
- **Fold-Level vs. Participant-Level**: Metrics are pooled across folds per participant, then evaluated using paired non-parametric estimators across participants ($N=105$).

### 2.4 Resolution of the P1 vs D3 Wilcoxon $p$-Value Discrepancy
The audit explicitly investigated the reported discrepancy between $4.43 \times 10^{-18}$ and $1.48 \times 10^{-18}$:
- **Raw Wilcoxon Signed-Rank Test Statistic**: $W = 5565.0$, $p_{\text{raw}} = \mathbf{1.47707 \times 10^{-18}}$.
- **Holm-Bonferroni Family-Wise Adjustment**: In V1.1, the `csp_lda` decoder family evaluates $m = 3$ paired hypotheses (`P1 vs D3`, `D1m vs D3`, `D1s vs D3`). Following Holm's step-down procedure, the smallest $p$-value is multiplied by $m=3$:
  $$p_{\text{Holm}} = 3 \times 1.477073 \times 10^{-18} = \mathbf{4.43122 \times 10^{-18}}$$
- **Conclusion**: There is no computational or data error. $1.48 \times 10^{-18}$ is the uncorrected $p$-value, while $4.43 \times 10^{-18}$ is the Holm-adjusted $p$-value. Both are mathematically exact and must be reported with explicit column distinctions (`wilcoxon_p` vs. `wilcoxon_p_holm`).

---

## 3. Empirical Benchmark Verification ($N = 105$)

Results archived in `benchmark_results/physionet_v1_1/` without modifying historical V1 outputs in `benchmark_results/physionet_v1/`:

| Contrast | Description | $N$ | Mean Diff | Median Diff | Hodges-Lehmann ($\Delta_{\text{HL}}$) | 95% BCa Bootstrap CI | Wilcoxon $p_{\text{raw}}$ | Wilcoxon $p_{\text{Holm}}$ | Cohen's $d_z$ | TOST Equivalent? |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| **P1 vs D3** | Spatial Leakage (CSP on all) | 105 | $+24.82$ pp | $+23.26$ pp | **$+24.50$ pp** | $[+22.22, +27.78]$ pp | $1.48 \times 10^{-18}$ | $4.43 \times 10^{-18}$ | $+1.771$ | False ($p=1.00$) |
| **D1m vs D3** | $k$-Matched Random ($k=3$) | 105 | $-4.67$ pp | $-4.00$ pp | **$-4.47$ pp** | $[-5.83, -3.14]$ pp | $5.41 \times 10^{-9}$ | $1.08 \times 10^{-8}$ | $-0.685$ | False ($p=0.999$) |
| **D1s vs D3** | Size-Matched Random | 105 | $-2.77$ pp | $-2.61$ pp | **$-2.68$ pp** | $[-3.95, -1.47]$ pp | $5.86 \times 10^{-5}$ | $5.86 \times 10^{-5}$ | $-0.449$ | False ($p=0.898$) |

### Scientific Audit Insights:
1. **Confirmation of H1/H2**: Naive trial shuffling does not produce positive optimism in this multi-run motor imagery benchmark. Random partitioning deflates accuracy by $-2.68$ pp ($p = 5.86 \times 10^{-5}$) because training folds must bridge inter-run non-stationarity.
2. **Geometric Recovery**: Strictly matching fold geometry (`D1s` vs `D1m`) recovers $+1.79$ pp, demonstrating that unconstrained $k$-fold cross-validation imposes artificial degradation through class imbalance artifacts.
3. **Leakage Dominance**: Supervised spatial filter leakage (`P1`) inflates performance by $+24.50$ pp ($d_z = 1.771$), confirming that feature contamination dwarfs validation protocol differences.

---

## 4. Software Engineering & Packaging Audit

1. **Package Metadata & Consistency**:
   - `pyproject.toml`: `version = "1.1.0"`, build backend `setuptools.build_meta`.
   - `src/emi/__init__.py`: `__version__ = "1.1.0"`.
   - `dist/`: Cleanly built wheels `emi-1.1.0-py3-none-any.whl` (55.3 KB) and `emi-1.1.0.tar.gz` (66.0 KB).
2. **Multi-Dataset OpenBMI Adapter**:
   - Ingests Lee et al. 2019 session-1 MAT files.
   - Automatically excludes 5 known truncated downloads ({1, 4, 11, 40, 41}).
   - Verified on real subject 2 (`test_load_openbmi_subject_2`).
3. **Riemannian Geometry Decoders**:
   - Standalone `CovarianceTransformer` and `TangentSpaceTransformer` implemented using pure NumPy/SciPy matrix logarithms, eliminating mandatory C-dependencies.
4. **EEG Benchmark Registry**:
   - 5 formal JSON Schemas created under `registry/schemas/` with example records in `registry/records/`.

---

## 5. Potential Risks & Release Recommendations

| Item | Risk Level | Description | Recommendation |
|---|---|---|---|
| Working tree cleanliness | Low | Untracked zip and patch files in repository root (`leakchckzipremote.zip`, `V11_current_working.patch`). | Archive or add to `.gitignore` prior to release tag. |
| MNE Deprecation Notice | Low | `standard_1020` montage emits warning in MNE 1.13.2 (deprecated in favor of `colin27_1020`). | Remap synthetic tests to `colin27_1020` (already applied in `test_preprocess.py`). |
| Release Tagging | Low | Git branch `fix/v1.1-stabilization` needs release tag `v1.1.0`. | Tag upon final user sign-off. |

**Final Recommendation**: The LeakCheck V1.1 package is scientifically sound, fully tested, reproducible, and ready for release.
