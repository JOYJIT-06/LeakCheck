# Table 17: Computational Benchmark Performance and Multi-Core Multiprocessing Scaling

| System / Benchmark Parameter      | Value / Metric                                                 |
| --------------------------------- | -------------------------------------------------------------- |
| Host Operating System             | Microsoft Windows 11 Enterprise (10.0.26100)                   |
| Processor Architecture            | AMD64 Family 25 Model 68 Stepping 1, AuthenticAMD (Multi-Core) |
| Parallel Multiprocessing Workers  | 4 Worker Processes (joblib.Parallel(n_jobs=4))                 |
| Total Evaluated Participants      | 105 Evaluated Cohort + 4 Screened Exclusions (109 Total)       |
| Total Wall-Clock Execution Time   | 3388.32 seconds (20 min 48 sec)                                |
| Mean Wall-Clock Time per Subject  | 32.270 seconds/subject                                         |
| Benchmark Throughput Rate         | 1.86 participants/minute                                       |
| Total CV Model Fits Executed      | 420 Full Pipeline Fits (105 subjects × 4 designs)              |
| Peak RAM Memory Consumption       | 1.82 GB RAM across 4 worker processes                          |
| Pipeline Failure / Exception Rate | 0.00% (Zero unhandled exceptions, zero NaNs)                   |

