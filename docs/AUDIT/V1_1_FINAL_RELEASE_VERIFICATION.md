# LeakCheck V1.1 Final Release Verification & Audit Report

**Audit Date**: 2026-11-08  
**Target Release Date**: 2026-11-12  
**Active Repository**: `D:\my lab\LeakCheck_remote`  
**Active Git Branch**: `fix/v1.1-stabilization`  
**Package Name**: `emi`  
**Package Version**: `1.1.0`  
**Python / Environment**: Python 3.12.16 (Anaconda `leakcheck` environment)

---

## 1. Git State and Repository Structure Verification

### 1.1 Working Tree Status
- **Current Branch**: `fix/v1.1-stabilization`
- **Tracked Modifications**:
  - `CHANGELOG.md`: Updated with V1.1.0 release notes.
  - `README.md`: Updated with V1.1 benchmark findings and V2 roadmap.
  - `pyproject.toml`: Version bumped to `1.1.0`.
  - `src/emi/__init__.py`: Version bumped to `1.1.0`.
  - `src/emi/preprocess.py`: Indentation blocker in `_reject()` (lines 72–78) resolved.
  - `src/emi/decoders.py`: Native `CovarianceTransformer` and `TangentSpaceTransformer` integrated; MNE CSP log-spam suppressed.
  - `scripts/run_leakcheck.py`: Empty null table handling guarded against `KeyError: 'decoder'`.
  - `docs/METHODS.md`, `docs/PREREGISTRATION.md`, `docs/REQUIREMENTS_STATUS.md`: Scientific documentation updated.
- **Untracked Archives to Preserve**:
  - `leakchckzipremote.zip` (historical backup archive)
  - `V11_current_working.patch` (diff patch file)
  - `CLAUDE_HANDOFF_V11.txt` (historical context notes)
  *Action*: These archives are retained untouched for auditability.

---

## 2. Statistical Verification (PhysioNet EEGMMIDB, $N = 105$)

All statistical values were re-verified from the raw participant-level CSV outputs in `benchmark_results/physionet_v1_1/`:

| Contrast | Contrast Kind | Mean Diff (pp) | Median Diff (pp) | Hodges-Lehmann ($\Delta_{\text{HL}}$) | 95% BCa Bootstrap CI | Wilcoxon $p_{\text{raw}}$ | Wilcoxon $p_{\text{Holm}}$ | Cohen's $d_z$ | TOST ($\pm 2.0$ pp) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| **P1 vs D3** | Supervised Spatial Leakage | $+24.82$ | $+23.26$ | **$+24.50$** | $[+22.22, +27.78]$ | $1.477 \times 10^{-18}$ | $4.431 \times 10^{-18}$ | $+1.771$ | False ($p=1.000$) |
| **D1m vs D3** | $k$-Matched Random ($k=3$) | $-4.67$ | $-4.00$ | **$-4.47$** | $[-5.83, -3.14]$ | $5.413 \times 10^{-9}$ | $1.083 \times 10^{-8}$ | $-0.685$ | False ($p=0.999$) |
| **D1s vs D3** | Headline Size-Matched Random | $-2.77$ | $-2.61$ | **$-2.68$** | $[-3.95, -1.47]$ | $5.859 \times 10^{-5}$ | $5.859 \times 10^{-5}$ | $-0.449$ | False ($p=0.898$) |

### Mathematical Clarification of P1 Wilcoxon $p$-Value:
- **Raw Wilcoxon $p$-value**: $p_{\text{raw}} = \mathbf{1.47707 \times 10^{-18}}$.
- **Holm-Bonferroni Family-Wise Adjustment**: In the `csp_lda` family, $m = 3$ contrasts were tested (`P1`, `D1m`, `D1s`). The smallest $p$-value is multiplied by $m=3$:
  $$p_{\text{Holm}} = 3 \times 1.477073 \times 10^{-18} = \mathbf{4.43122 \times 10^{-18}}$$
- **Verdict**: Verified mathematically consistent.

---

## 3. Test Baseline and Packaging Verification

1. **Test Suite Baseline**:
   - Total tests collected: 174.
   - Total tests passing: **174 passed in 70.75s** (0 failed, 0 errors).
2. **Distribution Artifacts**:
   - Built under `dist/`:
     - `emi-1.1.0-py3-none-any.whl` (55,332 bytes)
     - `emi-1.1.0.tar.gz` (65,996 bytes)
   - Packages build cleanly under `setuptools>=61` with standard build backend.
3. **Release Target**:
   - Software package `emi 1.1.0` is verified and ready for official release tagging on 12 November 2026.
