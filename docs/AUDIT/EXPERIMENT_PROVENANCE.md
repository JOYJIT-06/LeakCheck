# Experiment Provenance & Cryptographic Traceability Record

**Project:** LeakCheck V2  
**Document Identifier:** `docs/AUDIT/EXPERIMENT_PROVENANCE.md`  
**Date:** 8 November 2026  
**Host Platform:** Windows-11-10.0.26200-SP0 (AMD64, 8 GB RAM, CPU-only)  
**Python Runtime:** 3.12.16 (Anaconda environment: `D:\anaconda\envs\leakcheck`)  

---

## 1. Study 1: PhysioNet EEGMMIDB Benchmark

- **Dataset:** PhysioNet EEG Motor Movement/Imagery Database (Schalk et al., 2004)
- **Cohort Size:** $N = 105$ completed human participants (4 excluded due to data/annotation corruption: 88, 92, 100, 104)
- **Directory:** `benchmark_results/physionet_v1_1/`
- **Integrity Status:** Strictly preserved, read-only baseline
- **Protocol:**
  - Tasks: Left fist vs right fist motor imagery (runs 4, 8, 12)
  - Channels: 64 channels (standard 10-05 montage)
  - Native Sampling Rate: 160.0 Hz
  - Filter: 8.0–30.0 Hz zero-phase FIR
  - Decoders: OAS Shrinkage CSP-LDA
  - Designs: $D_3$ (LORO), $D_{1s}$ (size-matched random, 20 repeats), $D_{1m}$ ($k$-fold, $k=3$), $P_1$ (CSP on all)
- **Key Output Files & Verification:**
  - `inflation_by_subject.csv`: 315 rows (105 subjects $\times$ 3 designs)
  - `leakcheck_raw.csv`: 420 rows
  - `subject_info.csv`: 105 rows

---

## 2. Study 2: OpenBMI Replication Benchmark

- **Dataset:** OpenBMI (Lee et al., 2019, GigaScience), NEMAR accession `nm000338` (v1.0.5)
- **Cohort Size:** $N = 34$ verified intact human participants (Session 1: runs 0 & 1)
- **Cohort Subject IDs:** `[2, 3, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 42, 43, 44]`
- **Excluded Subjects:**
  - Truncated downloads ($N=5$): `s1` (3.6%), `s4` (53.4%), `s11` (73.3%), `s40` (28.6%), `s45` (76.2%)
  - Unacquired subjects ($N=15$): `s5, s6, s7, s8, s9, s41, s46–s54`
- **Execution Run Metadata:**
  - **Timestamp (UTC):** `2026-11-08T18:27:18.936647+00:00`
  - **Total Elapsed Execution Time:** `2631.55 seconds` (~43.8 minutes)
  - **Runner Invocation:**  
    `python scripts/run_openbmi_benchmark.py --subjects intact --designs D3_loro,D1s_size_matched,P1_csp_on_all --decoders csp_lda,ts_lr --output-dir benchmark_results/openbmi_v2`
  - **Target Frequency:** 250.0 Hz (polyphase decimation from 1000 Hz)
  - **Epoch Window:** $[-0.5, 4.0)\text{ s}$ half-open (1,125 time points)
  - **Bandpass Filter:** 8.0–30.0 Hz run-isolated zero-phase FIR
  - **Baseline Window:** $[-0.5, 0.0)\text{ s}$ mean subtraction
  - **Artifact Threshold:** $150.0\text{ }\mu\text{V}$ peak-to-peak (non-destructive flagging)
  - **Random Seed:** `0` (base seed), `n_repeats_d1s = 20` (seeds 0–19)
- **Cryptographic File Checksums:**
  - `participant_eligibility.csv` (34 rows):  
    `SHA256: a14ff1fe8b632d2852af86931d374b273375a43f5575865a3e56c9427e0bdf0a`
  - `fold_metrics.csv` (2,992 rows):  
    `SHA256: b374086c29ae871de3a9b9d5620b35b94abe81b1360885a9940087c59dc928c6`
  - `participant_metrics.csv` (204 rows):  
    `SHA256: 47eae3f4435b56568cff6583dfd479d8e445e6d21d7aa70f94e23a84365706b0`
  - `design_comparisons.csv` (4 rows):  
    `SHA256: 52d878029c5bd59b424272b89278fffa6290c0e5a78a81d809cf39e002f4017b`
  - `benchmark_manifest.json`: Verified machine-readable manifest recording environment, packages, parameters, and digests.
