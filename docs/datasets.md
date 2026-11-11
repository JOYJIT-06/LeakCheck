# Supported EEG Datasets and Adapters

LeakCheck is designed around a modular, multi-dataset neuroimaging architecture that unifies raw motor imagery recordings into standardized, epoch-level NumPy arrays with explicit run and temporal metadata.

---

## 1. Supported Dataset Catalog

| Dataset Key | Reference | Participants | Channels | Raw Sampling | Paradigm | Status in LeakCheck |
|---|---|---|---|---|---|---|
| **PhysioNet EEGMMIDB** | Schalk et al. (2004), Goldberger et al. (2000) | 109 ($N=105$ analyzed) | 64 EEG | 160 Hz | Left vs Right Fist MI (Runs 4, 8, 12) | **Tier 1 (Complete V1.1 Baseline)** |
| **OpenBMI** | Lee et al. (2019), GigaScience | 54 ($N=34$ verified intact) | 62 EEG | 1000 Hz $\to$ 160 Hz | Left vs Right Hand MI (Session 1, Runs 0 & 1) | **Tier 1 (Complete V2 Benchmark)** |
| **BNCI2014-001 (BCI IV-2a)** | Tangermann et al. (2012) | 9 | 22 EEG | 250 Hz | 4-class MI (Left/Right/Foot/Tongue) | **Tier 2 (Adapter Implemented & Tested)** |
| **Cho et al. (2017)** | Cho et al. (2017), GigaScience | 52 | 64 EEG | 512 Hz | Left vs Right Hand MI | **Tier 2 (Adapter Implemented & Tested)** |

---

## 2. PhysioNet EEGMMIDB (V1.1 Gold Standard)

The PhysioNet EEG Motor Movement/Imagery Database contains 64-channel recordings acquired at 160 Hz using the BCI2000 system.

### Task Selection and Protocol
- **Motor Imagery Runs**: Runs 4, 8, and 12 (Left Fist vs. Right Fist motor imagery).
- **Trial Structure**: Each run contains approximately 15 left-hand and 15 right-hand trials (total ~45 trials per class, 90 trials per participant).
- **Epoch Extraction**: $[-0.5, +4.0]$ s relative to cue onset; baseline correction $[-0.5, 0.0]$ s; active decoding window $[+1.0, +3.0]$ s (320 samples at 160 Hz).
- **Pre-filtering**: Label-blind 5th-order Butterworth bandpass filter ($8.0$–$30.0$ Hz).

### Participant Exclusion Criteria
Of the 109 enrolled participants, exactly **4 participants are excluded** strictly on technical grounds, leaving $N = 105$ analyzable cohorts:
- `S088`: Missing run annotations.
- `S092`: Discrepant sampling rate and corrupted timing track.
- `S100`: Hardware synchronization failure in Run 8.
- `S104`: Incomplete recording blocks.
*No participant is ever excluded on the basis of low classification accuracy.*

### Automated Download and Caching
LeakCheck uses MNE-Python's built-in PhysioNet fetcher:
```python
from mne.datasets import eegbci
# Downloads raw EDF files to ~/mne_data/MNE-eegbci-data/ automatically
```

---

## 3. OpenBMI Dataset (Lee et al. 2019)

OpenBMI is a large-scale 62-channel BCI dataset recorded at 1000 Hz from 54 healthy participants across two distinct experimental sessions.

### Protocol and Experimental Contrast
- **Session 1 Motor Imagery**:
  - **Run 0 (Offline Screening)**: 100 trials (50 left hand, 50 right hand) performed without visual neurofeedback.
  - **Run 1 (Online Feedback)**: 100 trials (50 left hand, 50 right hand) performed with real-time visual neurofeedback.
- **Total Valid Trials**: 200 trials per intact participant (100 per run, exactly balanced).
- **Preprocessing Pipeline**:
  - Decimated from 1000 Hz to 160 Hz using polyphase FIR anti-aliasing filtering.
  - Sliced into $[1.0, 3.0]$ s post-cue intervals (320 samples at 160 Hz).
  - Common average referenced (CAR) across 62 scalp electrodes.

### File Structure on Disk
OpenBMI session files are provided in MATLAB `.mat` format:
```
data/OpenBMI/
├── sess01_subj01_EEG_MI.mat
├── sess01_subj02_EEG_MI.mat
...
└── sess01_subj54_EEG_MI.mat
```

### Automated Corruption and Integrity Screening
Because remote neuroimaging repositories (NEMAR / GigaScience) occasionally drop truncated files during bulk HTTP downloads, LeakCheck includes an automated integrity checker (`src/emi/datasets_openbmi.py`):
- Verifies MATLAB HDF5 / v7 structure.
- Checks presence of both `EEG_MI_train` (Run 0) and `EEG_MI_test` (Run 1) fields.
- Verifies trial count ($100$ trials per run) and channel matrix dimensions ($62$ electrodes).
- Any truncated or unreadable file is flagged in `participant_eligibility.csv` without crashing the benchmark. In the verified benchmark, **34 participants are completely intact**.

---

## 4. Multi-Dataset Architecture (`BaseEEGDataset`)

All datasets in LeakCheck V2 inherit from the abstract base class `BaseEEGDataset` defined in `src/emi/datasets_base.py`.

### The Base Interface
```python
from emi.datasets_base import BaseEEGDataset, DatasetMetadata, SubjectRecord

class CustomDataset(BaseEEGDataset):
    metadata = DatasetMetadata(
        dataset_id="custom_bci",
        name="Custom Laboratory BCI Dataset",
        n_subjects=20,
        sfreq_raw=250.0,
        channels=32,
        classes=["left_hand", "right_hand"],
        runs_per_subject=4,
    )

    def load_subject(self, subject: int, target_fs: float = 160.0) -> SubjectRecord:
        # Load raw data and return SubjectRecord:
        # SubjectRecord(subject=subject, X=X, y=y, runs=runs, times=times, fs=target_fs)
        pass
```

### Plug-and-Play Adapters
LeakCheck includes plug-and-play adapters for:
- `PhysioNetDatasetAdapter`: Wraps MNE-Python's PhysioNet EEGMMIDB fetcher.
- `OpenBMIDatasetAdapter`: Loads OpenBMI MATLAB session archives.
- `BNCI2014001DatasetAdapter`: Adapts BCI Competition IV-2a 4-class recordings.
- `Cho2017DatasetAdapter`: Adapts Cho et al. 52-subject 64-channel motor imagery.

---

## 5. Schema v2 Epoch Cache

To enable instantaneous benchmarking and reproducible experiment hashing, LeakCheck caches preprocessed epochs into compressed `.npz` archives under `data/cache/`:

- **Path Schema**: `data/cache/{dataset_id}/sub-{subject:03d}_epochs.npz`
- **Stored Arrays**:
  - `X`: `float32` array of shape `(n_trials, n_channels, n_times)`
  - `y`: `int64` array of shape `(n_trials,)`
  - `runs`: `int64` array of shape `(n_trials,)`
  - `times`: `float64` array of shape `(n_times,)`
- **Metadata**: JSON header storing SHA-256 checksum of raw input, filter cutoffs, and preprocessing parameters.
