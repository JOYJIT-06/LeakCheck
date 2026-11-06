"""All analysis choices live here, so they are visible and fixed in advance.

Do not tune these values on the test results of a subject. If you change a
choice, change it for everyone and say why in your write-up.
"""
from dataclasses import dataclass, asdict

# PhysioNet EEG Motor Movement/Imagery dataset.
# Runs 4, 8, 12 = imagined opening and closing of the left or right fist.
# (Check the dataset documentation if you want other tasks.)
RUNS_LEFT_RIGHT = (4, 8, 12)
ANNOT_TO_ID = {"T1": 2, "T2": 3}  # T1 = left fist cue, T2 = right fist cue
EVENT_ID = {"left": 2, "right": 3}

# Tag written into raw.info["description"] by data.load_raw so that every trial can be
# traced back to the recording run it came from (needed for leave-one-run-out CV).
RUN_TAG = "emi_run_lengths:"


@dataclass(frozen=True)
class Config:
    # data
    runs: tuple = RUNS_LEFT_RIGHT
    data_path: str | None = None  # None = MNE default data folder

    # preprocessing
    ica_band: tuple = (1.0, 40.0)        # band used for ICA and broadband analysis
    n_ica: int = 20
    use_ica: bool = True                 # False = no-ICA sensitivity run
    ica_eog_channels: tuple = ("Fp1", "Fp2")  # frontal EEG used as blink proxy
    max_ica_exclude: int = 2
    # Label-blind quality control. Every rule is fixed in advance and must never be tuned on accuracy.
    bad_channel_z: float = 4.0           # robust log-variance outlier threshold
    bad_channel_corr_z: float = 4.0      # low-correlation robust outlier threshold
    max_bad_fraction: float = 0.15       # more flagged channels than this = the recording is suspect
    reject_mode: str = "adaptive"        # "adaptive" (per subject) or "fixed" (reject_uv for everyone)
    reject_k: float = 6.0                # adaptive: median + k * MAD of the per-trial artifact statistic
    reject_floor_uv: float = 200.0       # the adaptive threshold is never below this ...
    reject_cap_uv: float = 800.0         # ... and never above this
    reject_uv: float = 200.0             # threshold used when reject_mode == "fixed"
    # "analysis": reject on the analysed window only (the decoding window); "full": the whole epoch,
    # including the pre-cue baseline (v0.2 behaviour). Label-blind either way.
    reject_window: str = "analysis"

    # epochs (seconds relative to the cue)
    tmin: float = -1.0
    tmax: float = 4.0

    # time-frequency / ERD
    baseline: tuple = (-0.8, -0.1)
    erd_freqs: tuple = (4.0, 40.0)       # start, stop (1 Hz steps)
    mu_band: tuple = (8.0, 12.0)
    beta_band: tuple = (13.0, 30.0)

    # decoding
    decode_band: tuple = (8.0, 30.0)
    decode_tmin: float = 1.0
    decode_tmax: float = 3.0
    n_csp: int = 4
    n_splits: int = 5
    n_perm: int = 200
    null_type: str = "both"              # "perm", "shift" or "both" (perm_p = the LARGER of the two p-values); see docs/LEAKCHECK.md
    csp_reg: str | float | None = None   # regularisation passed to MNE's CSP (None = unregularised)
    seed: int = 42

    def to_dict(self) -> dict:
        return asdict(self)
