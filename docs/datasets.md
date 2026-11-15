# Supported EEG Datasets

LeakCheck V1.1 focuses exclusively on the PhysioNet EEG Motor Movement/Imagery Database (EEGMMIDB) as the authoritative gold standard for benchmarking data leakage and non-stationarity in motor imagery decoders.

---

## 1. Primary Dataset: PhysioNet EEGMMIDB (V1.1 Gold Standard)

The PhysioNet EEG Motor Movement/Imagery Database (Goldberger et al., 2000; Schalk et al., 2004) contains 64-channel EEG recordings acquired at 160 Hz using the BCI2000 system.

| Dataset Attribute | Specification |
|---|---|
| **Full Reference** | Goldberger, A. L. et al. (2000). *PhysioBank, PhysioToolkit, and PhysioNet*. Circulation, 101(23), e215–e220. |
| **Experimental Design** | Schalk, G. et al. (2004). *BCI2000: a general-purpose brain-computer interface system*. IEEE TBME, 51(6), 1034–1043. |
| **Participants** | 109 requested ($N = 105$ analyzed in verified V1.1 cohort) |
| **Electrode Setup** | 64 EEG channels placed according to the international 10–10 system |
| **Sampling Rate** | 160 Hz (106 subjects recorded at 160 Hz; 3 subjects recorded at 128 Hz: S088, S092, S100) |
| **Experimental Task** | Motor Imagery: Left Fist vs. Right Fist |
| **Evaluated Runs** | Runs 4, 8, and 12 (Within-session motor imagery runs) |
| **Trial Count** | ~45 trials per class (~90 trials per participant across 3 runs) |

### Task Selection and Protocol
- **Motor Imagery Runs**: Runs 4, 8, and 12 (Left Fist vs. Right Fist motor imagery).
- **Trial Structure**: Each run contains approximately 15 left-hand and 15 right-hand trials (total ~45 trials per class, 90 trials per participant).
- **Epoch Extraction**: $[-0.5, +4.0]$ s relative to cue onset; baseline correction $[-0.5, 0.0]$ s; active decoding window $[+1.0, +3.0]$ s (320 samples at 160 Hz).
- **Pre-filtering**: Label-blind 5th-order Butterworth bandpass filter ($8.0$–$30.0$ Hz).

### Participant Exclusion Criteria
Of the 109 requested participants, exactly 105 are included and exactly **4 true technical exclusions** occur strictly on technical and eligibility grounds, leaving $N = 105$ analyzable cohorts:
1. `S044`: Missing local cache / 0 channels available in PhysioNet distribution.
2. `S069`: Missing local cache in PhysioNet distribution.
3. `S086`: Insufficient trial count (24 trials < 30 trial minimum eligibility gate).
4. `S091`: Corrupted/truncated recording / all 45 epochs dropped by artifact QC.

*(Note: The refuted earlier draft claim that `S088, S092, S100, S104` were excluded has been corrected; all four are fully retained and evaluated in the verified cohort).*  
*No participant is ever excluded on the basis of classification accuracy.*

### Automated Download and Caching
LeakCheck uses MNE-Python's built-in PhysioNet fetcher:
```python
from mne.datasets import eegbci
# Downloads raw EDF files to ~/mne_data/MNE-eegbci-data/ automatically
```

---

## 2. Epoch Cache Architecture

To enable instantaneous benchmarking and reproducible experiment hashing, LeakCheck caches preprocessed epochs into compressed `.npz` archives under `data/cache/`:

- **Path Schema**: `data/cache/physionet/sub-{subject:03d}_epochs.npz`
- **Stored Arrays**:
  - `X`: `float32` array of shape `(n_trials, n_channels, n_times)`
  - `y`: `int64` array of shape `(n_trials,)`
  - `runs`: `int64` array of shape `(n_trials,)`
  - `times`: `float64` array of shape `(n_times,)`
- **Metadata**: JSON header storing SHA-256 checksum of raw input, filter cutoffs, and preprocessing parameters.

---

## 3. Multi-Dataset Framework Preservation Notice

In accordance with the project release scope boundary mandate (`ORIGINAL_REQUEST.md` lines 503–524), all multi-dataset adapters (BNCI2014-001, Cho et al. 2017, etc.) and cross-dataset benchmarking tools developed for LeakCheck V2 are quarantined in `archive/v2/` and maintained on branch `v2-dev`. Refer to `archive/v2/README.md` for architecture details, adapter interfaces, and V2 replication workflows.
