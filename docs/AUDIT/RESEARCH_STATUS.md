# LeakCheck Research Status & Scientific Evidence Audit

**Date of Audit:** November 8, 2026  
**Auditor:** Google Antigravity Research Engineering & Scientific Software Audit  
**Status:** VERIFIED via `benchmark_results/physionet_v1/` Historical Evidence & Codebase Verification

---

## 1. Central Research Statement & Questions

### Central Research Statement
> "LeakCheck investigates how validation design, preprocessing contamination, feature-selection decisions, temporal dependence and other forms of information leakage influence the reliability of EEG decoding performance estimates. Through controlled comparisons between clean and deliberately contaminated evaluation pipelines, the framework aims to quantify mechanism-specific performance inflation, examine its variation across participants, datasets and decoder families, and translate the resulting evidence into a reproducible software system for auditing EEG machine-learning experiments."

### Status of Supporting Research Questions (RQ1–RQ10)
- **RQ1 (Random vs Run-Held-Out Evaluation):** **PARTIALLY VERIFIED**. Evaluated via D1m vs D3 ($N=105$). D1m yielded a Hodges-Lehmann difference of $-3.17$ pp (95% CI: $[-4.46, -1.79]$, $p = 8.62 \times 10^{-6}$).
- **RQ2 (Sample-Size and Class-Matched Validation):** **UNTESTED / MISSING EMPIRICALLY**. D1s (`SizeMatchedRandomSplit`) is implemented in code but was omitted from the 105-subject V1 benchmark. Required for V1.1.
- **RQ3 (Global CSP Contamination Inflation):** **VERIFIED**. Evaluated via P1 vs D3 ($N=105$). Massive performance inflation confirmed: Hodges-Lehmann median difference $= +24.50$ percentage points (95% BCa CI: $[+22.22, +27.78]$, $p = 1.48 \times 10^{-18}$, Cohen's $d_z = 1.771$).
- **RQ4 (Global Scaling, Feature Selection, Tuning):** **PARTIALLY VERIFIED (Code Implemented)**. Synthetic positive control tests pass in `tests/test_leakcheck.py`, but full 105-subject empirical benchmark data not yet executed.
- **RQ5 (Temporal Dependence & Epoch Overlap):** **PARTIALLY VERIFIED (Code Implemented)**. Diagnostic functions (`lag1_label_autocorr`, `runs_test_p`, `run_decodability`) verified in `tests/test_diagnostics.py`.
- **RQ6 (ICA & Channel Interpolation):** **PROPOSED / PARTIALLY IMPLEMENTED**. Stubbed in `leakcheck.py::p2_ica_on_all`.
- **RQ7 (Decoder Family Dependence):** **PROPOSED**. Historical benchmark evaluated only CSP-LDA.
- **RQ8 (Independent Multi-Dataset Replication):** **PARTIALLY VERIFIED**. PhysioNet complete (105 subjects). OpenBMI partially downloaded (39 session-1 subjects). Other datasets proposed.
- **RQ9 (Negative Controls & Permutation Testing):** **VERIFIED**. LORO clean pipeline showed $49.99\%$ mean null accuracy and $3.23\%$ false positive rate at $\alpha=0.05$. P1 leak detected in $91.3\%$ of subjects under permutation.
- **RQ10 (Automated Audits):** **VERIFIED**. Command-line pipeline `run_leakcheck.py` and diagnostic reporting operational.

---

## 2. Hypothesis Testing Status Matrix

| Hypothesis ID | Scientific Hypothesis | Empirical Status | Current Evidence |
|---|---|---|---|
| **H1** | Random validation yields optimistic estimates when trials share run structure | **REVISED / MIXED** | D1m was slightly lower than D3 ($-3.17$ pp, $p < 10^{-5}$) on PhysioNet; requires D1s resolution |
| **H2** | Sample-size and class matching explains D1m vs D3 difference | **UNTESTED** | D1s implementation verified; empirical evaluation pending |
| **H3** | Global CSP contamination produces massive optimistic inflation | **CONFIRMED** | $+24.50$ pp inflation, $p = 1.48 \times 10^{-18}$, $d_z = 1.771$ ($N=105$) |
| **H4** | Global scaling alters held-out performance | **CODE READY** | Unit test positive controls pass; benchmark pending |
| **H5** | Global feature/channel selection inflates performance | **CODE READY** | Unit test positive controls pass; benchmark pending |
| **H6** | Test-set hyperparameter tuning inflates performance | **CODE READY** | Unit test positive controls pass; benchmark pending |
| **H7** | Overlapping windows create artificial optimism | **CODE READY** | Unit test positive controls pass; benchmark pending |
| **H8** | Leakage effects are decoder-dependent | **PROPOSED** | Framework extensibility ready; multi-decoder run pending |
| **H9** | Leakage effects vary across dataset acquisition structures | **PROPOSED** | OpenBMI integration in progress |
| **H10** | Clean pipelines preserve nominal false-positive rates; audits detect leaks | **CONFIRMED** | Clean LORO FPR $= 3.2\%$ ($< 5\%$); P1 leak detection rate $= 91.3\%$ |

---

## 3. Verified Historical V1 Empirical Benchmark Evidence (Run `091e47dc`)

- **Dataset:** PhysioNet EEGMMIDB (64 channels, 160 Hz, Left Fist vs Right Fist Motor Imagery).
- **Participants:** 106 requested, 105 completed (Subject 86 excluded: only 24 valid trials after artifact rejection, below 30-trial cutoff).
- **Decoder:** MNE CSP (6 components, OAS covariance shrinkage) + Scikit-Learn LDA (`lsqr`, auto shrinkage).
- **Decoding Band & Window:** 8–30 Hz, 1.0–3.0 s relative to cue.
- **Compute Time:** 81,280.628 seconds (~22.58 hours).
- **Environment:** `emi` v0.1.0, NumPy 2.5.4, SciPy 1.18.1, Scikit-Learn 1.9.1, MNE 1.13.2.

### Historical Metric Results Table ($N=105$)

| Comparison | Contrast | Mean $\Delta$ (pp) | Median $\Delta$ (pp) | Hodges-Lehmann (pp) | 95% BCa CI (pp) | Wilcoxon $p$ | Cohen's $d_z$ | TOST Equivalent ($ \pm 2$ pp)? |
|---|---|---|---|---|---|---|---|---|
| **D1m vs D3** | Matched Random vs LORO | $-3.21$ | $-2.67$ | $-3.17$ | $[-4.46, -1.79]$ | $8.62 \times 10^{-6}$ | $-0.486$ | FALSE ($p=0.968$) |
| **P1 vs D3** | Global CSP vs LORO | $+24.82$ | $+23.26$ | $+24.50$ | $[+22.22, +27.78]$ | $1.48 \times 10^{-18}$ | $+1.771$ | FALSE ($p=1.000$) |

### Null Model & False Positive Rate Table ($N=105$, 199 repeats/type)

| Design | Null Type | Mean Null Acc | Null Optimism | False Positive Rate | 95% FPR CI | Nominal $\alpha$ | Interpretation |
|---|---|---|---|---|---|---|---|
| **D3 (LORO)** | Permutation | $49.99\%$ | $-0.01$ pp | $0.0323$ ($3.2\%$) | $[0.029, 0.036]$ | $0.05$ | Clean null control valid |
| **D3 (LORO)** | Circular Shift | $50.00\%$ | $+0.00$ pp | $0.0323$ ($3.2\%$) | $[0.028, 0.036]$ | $0.05$ | Clean shift control valid |
| **P1 (Global CSP)** | Permutation | $81.32\%$ | $+31.32$ pp | $0.9134$ ($91.3\%$) | $[0.880, 0.942]$ | $0.05$ | Leak detected in $91\%$ subjects |
| **P1 (Global CSP)** | Circular Shift | $82.02\%$ | $+32.02$ pp | $0.9227$ ($92.3\%$) | $[0.888, 0.952]$ | $0.05$ | Leak detected in $92\%$ subjects |
| **D1m (Matched k)** | Permutation | $46.72\%$ | $-3.28$ pp | $0.0043$ ($0.4\%$) | $[0.003, 0.005]$ | $0.05$ | Fold-size suppression detected |

---

## 4. Literature Comparison & Novelty Matrix

| Related Framework / Work | Domain Focus | Multi-Mechanism Audit? | Size/Class Matched Splits? | Participant-Level Stats Engine? | Automated Leak Diagnostics? | Full-Pipeline Permutation Nulls? |
|---|---|---|---|---|---|---|
| **MOABB** (Jayaram et al. 2018) | Standardized BCI Benchmarking | No (assumes clean pipelines) | No (standard k-fold / within-session) | Group Wilcoxon | No | Post-hoc label shuffling |
| **MNE-Python** (Gramfort et al. 2013) | General Neuroimaging Processing | No | No | Basic stats | No | Post-hoc perm |
| **Braindecode** (Schirrmeister 2017) | Deep Learning BCI Architectures | No | No | Trial-pooled metrics | No | No |
| **Yger et al. (2017)** | Riemannian BCI Classification | No | No | Cross-subject Wilcoxon | No | No |
| **Lemm et al. (2011)** | EEG ML Guide & Validation Pitfalls | Conceptual guidelines only | Conceptual discussion | None (Review paper) | No | Conceptual |
| **LeakCheck (This Work)** | Systematic EEG Leakage Auditing | **YES (P1–P9)** | **YES (D1s vs D3)** | **YES (HL, BCa, TOST, Holm)** | **YES (Autocorr, Runs)** | **YES (Within-run fold-nested)** |
