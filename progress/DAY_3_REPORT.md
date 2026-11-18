# DAY 3 REPORT — STATISTICAL & NUMERICAL REPAIRS

**Sprint**: LeakCheck V1.1 Seven-Day Scientific Repair, Validation & Release Sprint  
**Stage**: Day 3 / Stage 3 Completed  
**Date**: November 18, 2026  
**Lead Author**: LEAD (Scientific Project Director & Integrator)  
**Contributing Specialists**: AGENT 2 (Statistics), AGENT 4 (Rank/SVD), AGENT 6 (Software Engineering/QA)  

---

## 1. Executive Summary

Day 3 repaired the verified statistical and numerical defects identified during Day 2 audits:
1. **Pratt Wilcoxon Variance Formula Repaired**:
   - Implemented exact Cureton (1967) Pratt signed-rank test in `src/emi/leakstats.py` (`wilcoxon_pratt`).
   - Zero difference tie count $t_0$ is subtracted exactly once via $-t_0(t_0+1)(2t_0+1)$, and non-zero tie corrections iterate strictly over nonzero tie groups ($|d_i| > 10^{-9}\text{ pp}$).
   - Retained `tost_paired` and `paired_summary` public API fields for 100% backward compatibility.
2. **Independent Unit Test Fixtures (`tests/test_pratt_wilcoxon.py`)**:
   - Built and passed 10 exhaustive unit test cases covering zeros, ties, float tolerance thresholds, extreme symmetry, and Hodges-Lehmann Walsh medians. All cases match SciPy approx to 16 decimal places.
3. **Deterministic Shared Bootstrap Index Matrix**:
   - Generated `docs/STATISTICS/bootstrap_resample_indices_b10000_n105.csv` ($10{,}000 \times 105$, `seed=42`).
   - Recorded SHA-256 hash: `2aeb5c4176b5ef7e65447489b4a5bc86f0959be3d9d4106125ce155aea811ce7`.
   - Guarantees bit-level parity between Python and R resampling routines.
4. **Dimension-Aware Numerical SVD Rank Implemented & Tested**:
   - Implemented `numerical_rank_svd` in `src/emi/diagnostics.py` with dimension-aware tolerance $\text{tol} = \sigma_{\max} \max(M, N) \varepsilon$.
   - Added `tests/test_rank_svd.py` (3 passed).
5. **Full Test Suite Status**:
   - Expanded from 192 to **205 passed tests in 38.26 seconds (100% pass rate, exit code 0)**.

---

## 2. Capacity Utilisation Summary (End of Day 3)

- Lead active hours on Day 3: 3.0 h (Cumulative: 9.0 h / 60.0 h ceiling)
- Specialist active hours on Day 3: 11.0 h (Cumulative: 31.5 h / 336.0 h ceiling)
- Total team capacity used: **40.5 active hours** / 396.0 active hours ceiling ($10.23\%$)
- Remaining capacity: **355.5 active hours**
- Blocked hours: **0.0 hours**
- Stage 3 status: **COMPLETED & VERIFIED**
- Ready to transition to **Stage 4 (Day 4 — Preprocessing, Data, and Fold-Isolation Repairs)**.
