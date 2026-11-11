# Feasibility Study & Systems Architecture: Cloud-Based EEG Dataset Acquisition & Remote Storage

**Document Identifier**: `docs/AUDIT/CLOUD_DATASET_ACQUISITION_FEASIBILITY.md`  
**Target Milestone**: LeakCheck V2 Infrastructure & Scaling  
**Date**: November 2026  
**Status**: APPROVED FEASIBILITY STUDY — ZERO EXPENDITURE / ZERO PROVISIONING GATED

---

## 1. Executive Summary & Problem Formulation

The scaling of LeakCheck V2 from a single-cohort framework (PhysioNet $N=105$, 2.6 GB) to a comprehensive multi-dataset validation engine (Group A + B candidates, $>170\text{ GB}$) imposes severe storage, bandwidth, and processing bottlenecks on resource-constrained local workstations:
1. **Local System Constraints**: Windows environment, 8 GB RAM, standard residential broadband (20–50 Mbps downstream), limited local SSD capacity.
2. **Download Latency Bottleneck**: Downloading large institutional datasets (e.g., OpenBMI Session 2: 29.9 GB; Yang2025: 85 GB; Cho2017: 22 GB) over residential internet requires dozens of hours, suffers frequent connection drops, and risks file truncation (as observed in historical OpenBMI files `s1`, `s4`, `s11`, `s40`, `s45`).
3. **Proposed Architectural Solution**: Offload the heavy download and archive verification tasks to a high-speed cloud node (1 Gbps backbone), store the verified master raw files on persistent, low-cost object storage, and securely stream or selectively cache only the necessary participant-level subsets onto the local Windows development machine.

```
+---------------------------------------------------------------------------------------------------------+
|                                    CLOUD ACQUISITION ARCHITECTURE                                       |
+---------------------------------------------------------------------------------------------------------+
  [Original Repositories]            [Cloud Acquisition Node]            [Persistent Cloud Storage]
  (NEMAR / GigaDB / OpenNeuro) -----> (High-Speed Linux VM / Lambda) ---> (Wasabi / AWS S3 / B2)
                                              |                                      |
                                      (Checksum & Unpack)                            |
                                                                             (Rclone / HTTPS Sync)
                                                                                     |
                                                                                     v
                                                                        [Local LeakCheck Machine]
                                                                        (Selective Local Cache:
                                                                         Active Pilot Subjects Only)
```

---

## 2. Comparison of Cloud Storage & Infrastructure Providers

| Provider / Service | Storage Cost ($/GB/mo) | Egress / Download Cost | Network Bandwidth | Persistence Model | Suitability for LeakCheck |
|---|---:|---:|---:|---|---|
| **Wasabi Hot Cloud Storage** | **$0.0069** | **$0.00 (Zero Egress)** | Multi-Gbps | Enterprise S3 Persistent | **HIGHEST (Best Value)**: Zero egress fees eliminate download penalties. |
| **Backblaze B2** | $0.0060 | $0.00 (Free via Cloudflare) | Multi-Gbps | Enterprise S3 Persistent | **HIGH**: Extremely low storage cost, S3-compatible API. |
| **AWS S3 Standard** | $0.0230 | $0.0900 / GB | 10–25 Gbps | Industry Standard | **MODERATE**: High egress fees ($90 / TB) penalize repeated downloads. |
| **Hugging Face Hub** | Free (up to 50GB LFS) | Free | 1 Gbps | Git-LFS Repository | **HIGH for Public Data**: Free tier accommodates open datasets; requires strict privacy for non-redistributable data. |
| **Ephemeral Notebooks (Colab/Kaggle)**| Free / $10/mo | Free | 500–1000 Mbps | **Non-Persistent (Lost on disconnect)**| **UNSUITABLE for Storage**: Disk wiped after session ends; suitable ONLY as transient download relay. |
| **Hetzner / DigitalOcean VPS** | $5.00/mo (incl. 40GB) | 20 TB included | 1 Gbps | Persistent Block Storage | **HIGH for Relay**: Excellent temporary headless download server for aria2/curl scripts. |

---

## 3. Dataset-Specific Storage & Transfer Footprint

```
+---------------------------------------------------------------------------------------------------------+
|                                  MULTI-DATASET CLOUD STORAGE BUDGET                                     |
+--------------------+-----+----------------+------------------+------------------+-----------------------+
| Dataset            |  N  | Archive Format | Raw Source Size  | Extracted Cache  | Cloud Storage Cost/Mo |
+--------------------+-----+----------------+------------------+------------------+-----------------------+
| **OpenBMI (Lee2019)**| 54| MAT (S1 + S2)  | 61.8 GB          | ~45.0 GB         | $0.43 / month (Wasabi)|
| **Cho et al. 2017**|  52 | MAT (GigaDB)   | 11.5 GB (tar.gz) | 22.0 GB          | $0.15 / month         |
| **Yang et al. 2025**| 51 | BIDS (SciDB)   | 45.0 GB (zip)    | 85.0 GB          | $0.59 / month         |
| **PhysioNet**      | 105 | EDF+           | 2.6 GB           | 1.8 GB           | $0.02 / month         |
| **BNCI2014-001/004**| 18 | GDF / MAT      | 1.8 GB           | 3.5 GB           | $0.02 / month         |
| **TOTAL (Group A+B)**| 280| Multi-source   | **122.7 GB**     | **157.3 GB**     | **~$1.21 / month**    |
+--------------------+-----+----------------+------------------+------------------+-----------------------+
```

---

## 4. Evaluation of Four Acquisition Workflows

### Workflow A: Direct Local Download (Status Quo)
- **Mechanism**: Browser or PowerShell script downloading files directly to `D:\my lab\LeakCheck\data\`.
- **Pros**: Zero third-party cloud setup; zero monthly recurring costs.
- **Cons**: High latency (~15–20 hours per 50 GB); frequent network timeouts causing file corruption (demonstrated by the 5 truncated OpenBMI files); consumes local disk headroom.
- **Suitability**: Suitable for small benchmarks ($N \le 10$) or single-subject recovery; unviable for 100+ GB cohorts.

### Workflow B: Pure Cloud Ingestion & Persistent Remote Storage
- **Mechanism**: A lightweight cloud VPS (e.g., $5 Hetzner cloud node) downloads files from institutional mirrors at 1 Gbps directly into a private Wasabi/B2 S3 bucket, validates SHA256 checksums, and leaves the files in cloud storage.
- **Pros**: Lightning-fast transfer (OpenBMI 11 GB recovers in <3 minutes); zero bandwidth load on residential line; central immutable master archive.
- **Cons**: Requires configuring cloud credentials and S3 bucket.
- **Suitability**: Recommended for repository master curation.

### Workflow C: Remote Cloud Storage Direct Mount
- **Mechanism**: The Wasabi/B2 cloud bucket is mounted as a local Windows drive letter (e.g., `Z:\`) using `Rclone mount` with VFS caching.
- **Pros**: Zero local disk used for unaccessed subjects; appears as a native folder to `emi.datasets`.
- **Cons**: Severe latency penalty during EEG processing: reading 600 MB MATLAB arrays over WebDAV/FUSE causes repeated multi-second stalls during cross-validation fold splitting.
- **Suitability**: Not recommended for active benchmark execution.

### Workflow D: Cloud Download with Selective Local Caching (RECOMMENDED HYBRID)
- **Mechanism**:
  1. Heavy dataset ingestion is executed in the cloud directly to S3 persistent storage.
  2. For a specific benchmark run (e.g., OpenBMI $N=34$ pilot), a dedicated sync command downloads only the active participant files into the local cache (`D:\my lab\LeakCheck_remote\data\cache\`).
  3. Preprocessing converts raw files into compact `.npz` epoch caches ($~15\text{ MB}$ per participant), after which raw files can be safely offloaded.
- **Pros**: Combines 1 Gbps cloud download speeds with zero-latency local disk execution; minimizes local disk footprint to only active cohorts.
- **Cons**: Requires one-time setup of Rclone or AWS CLI on Windows.
- **Suitability**: **OPTIMAL ARCHITECTURE FOR LEAKCHECK V2**.

---

## 5. Security, Licensing & Governance Rules

1. **Strict Prohibition on Public Redistribution**:
   - Datasets governed by institutional user agreements (e.g., PhysioNet Credentialed Access, certain BNCI accessions) must NEVER be uploaded to public buckets or public Hugging Face spaces.
   - All cloud buckets must be configured as **Private** with restricted IAM access tokens.
2. **Credential Safety**:
   - Cloud access keys (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `HF_TOKEN`) must be stored in local environment variables or Windows Credential Manager (`%USERPROFILE%\.aws\credentials`), never committed to the git repository.
3. **No Automatic Financial Expenditure**:
   - Zero paid cloud accounts, subscriptions, or credit card charges may be initiated without prior explicit authorization from the user.

---

## 6. Implementation Prerequisites & Phased Pilot Plan

### Phase 1: Small Cloud Pilot (Post-Approval)
- Test the remote ingestion pipeline on a single 600 MB missing OpenBMI subject (`s5`):
  1. Spin up a free ephemeral GitHub Actions workflow or free-tier cloud node.
  2. Download `s5` directly from NEMAR HTTPS endpoint.
  3. Verify MD5 checksum against `manifest.json`.
  4. Securely transfer verified file to local test directory.
  5. Validate that `emi.datasets_openbmi` loads `s5` without error.

### Phase 2: Full Cohort Staging
- Upon validation of Phase 1, evaluate whether to expand to full Session 1 recovery (11.30 GB) or defer until the local $N=34$ pilot completes.
