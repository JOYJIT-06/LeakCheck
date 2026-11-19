"""Preprocessing: filter, bad channels, re-reference, ICA artifact removal, epoching, label-blind trial rejection.

Order (changed in v0.3 after the code review): band-pass -> detect and interpolate bad channels -> average
reference -> ICA. Every rule is LABEL-BLIND and fixed in advance.
Note: clean_raw provides the whole-recording preprocessor baseline, whereas FoldIsolatedPreprocessor
provides strict fold-isolated fitting and transformation (bad channels, FastICA, and rejection thresholds
fitted strictly on training runs and applied to held-out test runs).
"""
import logging

import mne
import numpy as np
from mne.preprocessing import ICA

from .config import ANNOT_TO_ID, EVENT_ID, RUN_TAG, Config
from .signal_utils import (adaptive_reject_mask, detect_bad_channels, parse_run_lengths,  # noqa: F401
                           ptp_reject_indices, trial_artifact_statistic, trial_run_ids)

log = logging.getLogger(__name__)


def clean_raw(raw: mne.io.BaseRaw, cfg: Config):
    """Band-pass, interpolate bad channels, average-reference, remove blink components with ICA.

    Blink components are picked automatically using frontal EEG channels as an EOG proxy (this dataset has no EOG
    channel). The automatic choice can fail, so the returned info lists, for EVERY subject, the bad channels and the
    ICA components that were removed; inspect them for some subjects. `cfg.use_ica=False` gives a no-ICA run.
    Returns (cleaned raw, info dict).
    """
    raw = filter_run_independent(raw, cfg=cfg, band="ica")

    eeg = mne.pick_types(raw.info, eeg=True, exclude=[])
    names = [raw.ch_names[i] for i in eeg]
    bad_idx, reasons = detect_bad_channels(raw.get_data(picks=eeg), z_thresh=cfg.bad_channel_z,
                                           corr_z_thresh=cfg.bad_channel_corr_z, max_bad_fraction=cfg.max_bad_fraction)
    bad_names = [names[i] for i in bad_idx]
    if bad_names:
        raw.info["bads"] = bad_names
        raw.interpolate_bads(reset_bads=True, verbose="ERROR")      # needs channel positions (montage)
    raw.set_eeg_reference("average", projection=False, verbose="ERROR")

    info = {"bad_channels": bad_names, "n_bad_channels": len(bad_names),
            "bad_channel_reasons": {names[i]: r for i, r in reasons.items()},
            "ica_excluded": [], "n_ica_candidates": 0, "use_ica": bool(cfg.use_ica)}
    if not cfg.use_ica:
        return raw, info

    n_comp = min(cfg.n_ica, len(eeg) - len(bad_names) - 1)          # interpolation lowers the rank
    ica = ICA(n_components=n_comp, random_state=cfg.seed, max_iter="auto", fit_params={"tol": 0.001})
    ica.fit(raw, verbose="ERROR")
    candidates = []
    for ch in cfg.ica_eog_channels:
        if ch not in raw.ch_names:
            continue
        try:
            idx, _ = ica.find_bads_eog(raw, ch_name=ch, verbose="ERROR")
        except Exception as exc:  # detection can fail on clean or noisy data
            log.warning("EOG detection failed on %s: %s", ch, exc)
            continue
        for i in idx:
            if i not in candidates:
                candidates.append(int(i))
    exclude = candidates[: cfg.max_ica_exclude]
    ica.exclude = exclude
    raw_clean = ica.apply(raw.copy(), verbose="ERROR")
    info.update({"ica_excluded": exclude, "n_ica_candidates": len(candidates)})
    return raw_clean, info


def _reject(data_v, times, cfg: Config, window):
    """Label-blind trial rejection. Returns (keep mask, threshold in microvolts)."""
    if cfg.reject_window == "full":
        # Include every sample in the full epoch.
        mask = np.ones(times.shape, dtype=bool)
    else:
        win = window
        # Preserve the existing analysis-window behaviour.
        mask = (times >= win[0] - 1e-9) & (times < win[1] - 1e-9)

    if cfg.reject_mode == "fixed":
        bad = ptp_reject_indices(data_v[:, :, mask], cfg.reject_uv)
        keep = np.ones(len(data_v), bool)
        keep[bad] = False
        return keep, float(cfg.reject_uv)
    stat = trial_artifact_statistic(data_v[:, :, mask] * 1e6)
    return adaptive_reject_mask(stat, cfg.reject_k, cfg.reject_floor_uv, cfg.reject_cap_uv)


def build_epochs_full(raw_clean: mne.io.BaseRaw, cfg: Config, decode_window=None):
    """Epoch, reject trials label-blind, and return (broadband epochs, decoding epochs, run ids, quality report).

    Bad trials are rejected once, on the ANALYSED window (cfg.reject_window='analysis') or on the whole epoch
    ('full', v0.2 behaviour); the decoding epochs use exactly the same trials. `decode_window` (seconds after
    the cue) defaults to the window in the config; LeakCheck uses a wider one (0 to 4 s) to compare several windows.
    """
    window = decode_window or (cfg.decode_tmin, cfg.decode_tmax)
    events, _ = mne.events_from_annotations(raw_clean, event_id=ANNOT_TO_ID, verbose="ERROR")
    lengths = parse_run_lengths(raw_clean.info.get("description"), RUN_TAG)
    if sum(lengths) != raw_clean.n_times:
        raise ValueError(f"Run lengths {lengths} add up to {sum(lengths)} samples but the recording has "
                         f"{raw_clean.n_times}; run assignment would be wrong.")
    run_all = trial_run_ids(events[:, 0], lengths, raw_clean.first_samp)
    picks = mne.pick_types(raw_clean.info, eeg=True, exclude="bads")

    ep_bb = mne.Epochs(raw_clean, events, EVENT_ID, cfg.tmin, cfg.tmax, picks=picks, baseline=None,
                       preload=True, reject=None, verbose="ERROR")
    n_available = len(ep_bb)
    keep, thr = _reject(ep_bb.get_data(), ep_bb.times, cfg, window)
    if (~keep).any():
        ep_bb.drop(np.where(~keep)[0], reason="PTP_REJECT", verbose="ERROR")
    if len(ep_bb) == 0:
        raise ValueError(
            f"All {len(events)} epochs were rejected (mode={cfg.reject_mode!r}, threshold {thr:.0f} uV, "
            f"reject_window={cfg.reject_window!r}). Check the recording for bad channels, or use a label-blind "
            "rule fixed in advance for everyone.")

    raw_band = filter_run_independent(raw_clean, cfg=cfg, band="decode")
    ep_dec = mne.Epochs(raw_band, events[ep_bb.selection], EVENT_ID, cfg.tmin, cfg.tmax, picks=picks,
                        baseline=None, preload=True, verbose="ERROR")
    ep_dec.crop(window[0], window[1], include_tmax=False)
    runs = run_all[ep_bb.selection][ep_dec.selection]
    qc = {"n_events": int(len(events)), "n_epochs_available": int(n_available), "n_trials_kept": int(len(ep_dec)),
          "reject_mode": cfg.reject_mode, "threshold_uv": float(thr),
          "trials_per_run_kept": np.bincount(runs, minlength=len(lengths)).tolist()}
    return ep_bb, ep_dec, runs, qc


def build_epochs_with_runs(raw_clean: mne.io.BaseRaw, cfg: Config, decode_window=None):
    """(broadband epochs, band-passed decoding epochs, run id of every kept decoding trial)."""
    ep_bb, ep_dec, runs, _ = build_epochs_full(raw_clean, cfg, decode_window)
    return ep_bb, ep_dec, runs


def build_epochs(raw_clean: mne.io.BaseRaw, cfg: Config):
    """Same as build_epochs_with_runs but without the run ids (kept for the basic pipeline)."""
    ep_bb, ep_dec, _ = build_epochs_with_runs(raw_clean, cfg)
    return ep_bb, ep_dec


def filter_run_independent(
    raw_runs,
    l_freq=None,
    h_freq=None,
    *,
    cfg: Config | None = None,
    band: str = "ica",
    fir_design: str = "firwin",
    pad: str = "reflect_limited",
    verbose: str = "ERROR",
):
    """Filter each recording run independently to eliminate cross-run filter convolution bleed.

    Guarantees that FIR filter impulse response tails cannot convolve samples across
    recording run boundaries. Operates on independent memory buffers with reflection padding.

    Parameters
    ----------
    raw_runs : list of mne.io.BaseRaw or single mne.io.BaseRaw
        If a list of Raw objects, each run is filtered in its own memory buffer.
        If a single Raw object with RUN_TAG metadata in info['description'],
        it is partitioned and filtered run-by-run with reflection padding.
    l_freq : float, Config, tuple, list, or None
        Lower passband edge (Hz). If an instance of Config is passed, configuration
        parameters are extracted automatically for backward compatibility.
    h_freq : float, str, or None
        Upper passband edge (Hz). If l_freq is a Config, h_freq can specify band name ('ica' or 'decode').
    cfg : Config, optional
        Configuration object containing band definitions.
    band : str, default "ica"
        Band selector if freqs not provided ('ica' for cfg.ica_band, 'decode' for cfg.decode_band).
    fir_design : str, default "firwin"
        FIR filter design method ('firwin').
    pad : str, default "reflect_limited"
        Padding method applied at run boundaries ('reflect_limited' or 'reflect').
    verbose : str, default "ERROR"
        Verbosity level.

    Returns
    -------
    list of mne.io.BaseRaw or mne.io.BaseRaw
        Independently filtered raw objects with zero cross-run convolution.
    """
    if isinstance(l_freq, Config):
        cfg = l_freq
        band = h_freq if isinstance(h_freq, str) else band
        l_freq = None
        h_freq = None
    elif isinstance(l_freq, (tuple, list)) and len(l_freq) == 2:
        low, high = float(l_freq[0]), float(l_freq[1])
        l_freq, h_freq = low, high

    if l_freq is None and h_freq is None:
        if cfg is None:
            cfg = Config()
        band_freqs = cfg.ica_band if band == "ica" else cfg.decode_band
        low, high = band_freqs
    else:
        low, high = float(l_freq), float(h_freq)

    # Branch 1: List or tuple of separate Raw objects
    if isinstance(raw_runs, (list, tuple)):
        filtered = []
        for r in raw_runs:
            r_filt = r.copy()
            r_filt.filter(low, high, fir_design=fir_design, pad=pad, verbose=verbose)
            filtered.append(r_filt)
        return filtered

    # Branch 2: Single concatenated Raw object with RUN_TAG
    elif isinstance(raw_runs, mne.io.BaseRaw):
        desc = raw_runs.info.get("description") or ""
        if desc.startswith(RUN_TAG):
            lengths = parse_run_lengths(desc, RUN_TAG)
            if sum(lengths) == raw_runs.n_times:
                raw_filt = raw_runs.copy()
                if not raw_filt.preload:
                    raw_filt.load_data()
                data = raw_filt.get_data().copy()
                start = 0
                for l in lengths:
                    stop = start + l
                    data[:, start:stop] = mne.filter.filter_data(
                        data[:, start:stop],
                        raw_filt.info["sfreq"],
                        low,
                        high,
                        fir_design=fir_design,
                        pad=pad,
                        verbose=verbose,
                    )
                    start = stop
                raw_filt._data = data
                return raw_filt

        # Fallback for single BaseRaw without RUN_TAG or length mismatch
        raw_filt = raw_runs.copy()
        raw_filt.filter(low, high, fir_design=fir_design, pad=pad, verbose=verbose)
        return raw_filt
    else:
        raise TypeError(f"Unsupported raw_runs type: {type(raw_runs)}")


class FoldIsolatedPreprocessor:
    """Fold-isolated EEG preprocessor guaranteeing zero cross-partition leakage.

    Estimates bad-channel sets, FastICA unmixing matrices, and adaptive artifact thresholds
    strictly on training data (R_train), freezing parameters before linear application
    to held-out test data (R_test).
    """

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.bad_channels_: list[str] = []
        self.bad_channel_reasons_: dict[str, str] = {}
        self.ica_: mne.preprocessing.ICA | None = None
        self.ica_excluded_: list[int] = []
        self.reject_threshold_uv_: float | None = None
        self.fitted_: bool = False
        self.qc_: dict = {}

    def fit(self, raw_train_runs, events_train=None, window=None):
        """Fit bad channels, FastICA unmixing, and artifact threshold strictly on train runs."""
        runs = [raw_train_runs] if isinstance(raw_train_runs, mne.io.BaseRaw) else list(raw_train_runs)
        if len(runs) == 0:
            raise ValueError("raw_train_runs must not be empty")

        rej_window = window or (self.cfg.decode_tmin, self.cfg.decode_tmax)

        # 1. Run-independent 1-40 Hz filtering
        filt_ica_runs = filter_run_independent(runs, self.cfg, band="ica")

        # 2. Bad channel detection strictly on training runs
        eeg_picks = mne.pick_types(filt_ica_runs[0].info, eeg=True, exclude=[])
        ch_names = [filt_ica_runs[0].ch_names[i] for i in eeg_picks]
        concat_train_data = np.concatenate([r.get_data(picks=eeg_picks) for r in filt_ica_runs], axis=1)

        bad_idx, reasons = detect_bad_channels(
            concat_train_data,
            z_thresh=self.cfg.bad_channel_z,
            corr_z_thresh=self.cfg.bad_channel_corr_z,
            max_bad_fraction=self.cfg.max_bad_fraction,
        )
        self.bad_channels_ = [ch_names[i] for i in bad_idx]
        self.bad_channel_reasons_ = {ch_names[i]: r for i, r in reasons.items()}

        # 3. Interpolation and average reference on training runs
        interp_train_runs = []
        for r in filt_ica_runs:
            r_cp = r.copy()
            if self.bad_channels_:
                r_cp.info["bads"] = list(self.bad_channels_)
                r_cp.interpolate_bads(reset_bads=True, verbose="ERROR")
            r_cp.set_eeg_reference("average", projection=False, verbose="ERROR")
            interp_train_runs.append(r_cp)

        # 4. FastICA unmixing strictly on training runs
        clean_train_runs = []
        if self.cfg.use_ica:
            train_concat = mne.concatenate_raws([r.copy() for r in interp_train_runs])
            n_comp = min(self.cfg.n_ica, len(eeg_picks) - len(self.bad_channels_) - 1)
            self.ica_ = ICA(n_components=n_comp, random_state=self.cfg.seed, max_iter="auto", fit_params={"tol": 0.001})
            self.ica_.fit(train_concat, verbose="ERROR")

            candidates = []
            for ch in self.cfg.ica_eog_channels:
                if ch in train_concat.ch_names:
                    try:
                        idx, _ = self.ica_.find_bads_eog(train_concat, ch_name=ch, verbose="ERROR")
                        for i in idx:
                            if int(i) not in candidates:
                                candidates.append(int(i))
                    except Exception:
                        continue
            self.ica_excluded_ = candidates[: self.cfg.max_ica_exclude]
            self.ica_.exclude = list(self.ica_excluded_)

            for r in interp_train_runs:
                clean_train_runs.append(self.ica_.apply(r.copy(), verbose="ERROR"))
        else:
            self.ica_ = None
            self.ica_excluded_ = []
            clean_train_runs = interp_train_runs

        # 5. Extract broadband epochs and estimate tau_train strictly on training epochs
        train_clean_concat = mne.concatenate_raws([r.copy() for r in clean_train_runs])
        if events_train is not None:
            ev = events_train
        else:
            try:
                ev, _ = mne.events_from_annotations(train_clean_concat, event_id=ANNOT_TO_ID, verbose="ERROR")
            except Exception:
                ev = np.empty((0, 3), dtype=int)

        if len(ev) == 0:
            self.reject_threshold_uv_ = float(self.cfg.reject_uv)
        elif self.cfg.reject_mode == "fixed":
            self.reject_threshold_uv_ = float(self.cfg.reject_uv)
        else:
            picks = mne.pick_types(train_clean_concat.info, eeg=True, exclude="bads")
            ep_bb = mne.Epochs(
                train_clean_concat, ev, EVENT_ID, self.cfg.tmin, self.cfg.tmax,
                picks=picks, baseline=None, preload=True, reject=None, verbose="ERROR",
            )
            if len(ep_bb) == 0:
                self.reject_threshold_uv_ = float(self.cfg.reject_uv)
            else:
                if self.cfg.reject_window == "full":
                    mask = np.ones(ep_bb.times.shape, dtype=bool)
                else:
                    mask = (ep_bb.times >= rej_window[0] - 1e-9) & (ep_bb.times < rej_window[1] - 1e-9)
                stat_train = trial_artifact_statistic(ep_bb.get_data()[:, :, mask] * 1e6)
                med = np.median(stat_train)
                mad = 1.4826 * np.median(np.abs(stat_train - med))
                thr = med + self.cfg.reject_k * mad
                thr = max(thr, self.cfg.reject_floor_uv)
                thr = min(thr, self.cfg.reject_cap_uv)
                self.reject_threshold_uv_ = float(thr)

        self.fitted_ = True
        return self

    def fit_training(self, raw_train: mne.io.BaseRaw):
        """Compatibility alias for fitting on training raw."""
        return self.fit(raw_train)

    def transform_raw(self, raw: mne.io.BaseRaw | list[mne.io.BaseRaw]):
        """Apply frozen training transformations to continuous Raw object(s) without epoching."""
        if not self.fitted_:
            raise RuntimeError("FoldIsolatedPreprocessor must be fitted before calling transform_raw()")
        is_list = isinstance(raw, (list, tuple))
        runs = list(raw) if is_list else [raw]
        filt_runs = filter_run_independent(runs, self.cfg, band="ica")
        clean_runs = []
        for r in filt_runs:
            r_cp = r.copy()
            if self.bad_channels_:
                r_cp.info["bads"] = list(self.bad_channels_)
                r_cp.interpolate_bads(reset_bads=True, verbose="ERROR")
            r_cp.set_eeg_reference("average", projection=False, verbose="ERROR")
            if self.cfg.use_ica and self.ica_ is not None:
                self.ica_.exclude = list(self.ica_excluded_)
                r_cp = self.ica_.apply(r_cp, verbose="ERROR")
            clean_runs.append(r_cp)
        return clean_runs if is_list else clean_runs[0]

    def transform(self, raw_test_runs, events_test=None, window=None, return_epochs=None, return_qc=False):
        """Apply frozen transformations to test runs, extracting epochs (X_test, y_test).

        If raw_test_runs is a single BaseRaw and events_test is None and return_epochs is not True,
        and no motor imagery annotations are present (or return_epochs is False),
        returns a cleaned BaseRaw for backward compatibility.
        """
        if not self.fitted_:
            raise RuntimeError("FoldIsolatedPreprocessor must be fitted before calling transform()")

        if isinstance(raw_test_runs, mne.io.BaseRaw) and events_test is None and return_epochs is not True:
            has_annots = False
            try:
                ev_check, _ = mne.events_from_annotations(raw_test_runs, event_id=ANNOT_TO_ID, verbose="ERROR")
                has_annots = len(ev_check) > 0
            except Exception:
                has_annots = False

            if not has_annots or return_epochs is False:
                return self.transform_raw(raw_test_runs)

        runs = [raw_test_runs] if isinstance(raw_test_runs, mne.io.BaseRaw) else list(raw_test_runs)
        rej_window = window or (self.cfg.decode_tmin, self.cfg.decode_tmax)

        # 1. Run-independent 1-40 Hz filtering
        filt_ica_runs = filter_run_independent(runs, self.cfg, band="ica")

        # 2. Spherical spline interpolation using FROZEN bad_channels_
        interp_test_runs = []
        for r in filt_ica_runs:
            r_cp = r.copy()
            if self.bad_channels_:
                r_cp.info["bads"] = list(self.bad_channels_)
                r_cp.interpolate_bads(reset_bads=True, verbose="ERROR")
            r_cp.set_eeg_reference("average", projection=False, verbose="ERROR")
            interp_test_runs.append(r_cp)

        # 3. Linear application of FROZEN ICA unmixing and components
        clean_test_runs = []
        if self.cfg.use_ica and self.ica_ is not None:
            for r in interp_test_runs:
                self.ica_.exclude = list(self.ica_excluded_)
                clean_test_runs.append(self.ica_.apply(r.copy(), verbose="ERROR"))
        else:
            clean_test_runs = interp_test_runs

        # 4. Extract broadband epochs & apply FROZEN threshold reject_threshold_uv_
        test_clean_concat = mne.concatenate_raws([r.copy() for r in clean_test_runs])
        if events_test is not None:
            ev = events_test
        else:
            ev, _ = mne.events_from_annotations(test_clean_concat, event_id=ANNOT_TO_ID, verbose="ERROR")

        picks = mne.pick_types(test_clean_concat.info, eeg=True, exclude="bads")
        ep_bb = mne.Epochs(
            test_clean_concat, ev, EVENT_ID, self.cfg.tmin, self.cfg.tmax,
            picks=picks, baseline=None, preload=True, reject=None, verbose="ERROR",
        )

        if self.cfg.reject_window == "full":
            mask = np.ones(ep_bb.times.shape, dtype=bool)
        else:
            mask = (ep_bb.times >= rej_window[0] - 1e-9) & (ep_bb.times < rej_window[1] - 1e-9)

        stat_test = trial_artifact_statistic(ep_bb.get_data()[:, :, mask] * 1e6)
        thr = self.reject_threshold_uv_ if self.reject_threshold_uv_ is not None else float(self.cfg.reject_cap_uv)
        keep = stat_test <= thr
        n_avail = len(ep_bb)
        if (~keep).any():
            ep_bb.drop(np.where(~keep)[0], reason="PTP_REJECT", verbose="ERROR")

        # 5. Run-independent 8-30 Hz decoding band filtering & epoching
        band_runs = filter_run_independent(clean_test_runs, self.cfg, band="decode")
        test_band_concat = mne.concatenate_raws([r.copy() for r in band_runs])
        ep_dec = mne.Epochs(
            test_band_concat, ev[ep_bb.selection], EVENT_ID, self.cfg.tmin, self.cfg.tmax,
            picks=picks, baseline=None, preload=True, verbose="ERROR",
        )
        ep_dec.crop(rej_window[0], rej_window[1], include_tmax=False)

        X = ep_dec.get_data()
        y = (ep_dec.events[:, 2] == EVENT_ID["right"]).astype(int)
        self.qc_ = {
            "n_events": int(len(ev)),
            "n_epochs_available": int(n_avail),
            "n_trials_kept": int(len(ep_dec)),
            "reject_threshold_uv": float(thr),
            "bad_channels": list(self.bad_channels_),
            "ica_excluded": list(self.ica_excluded_),
        }
        if return_qc:
            return X, y, self.qc_
        return X, y

    def fit_transform(self, raw_train_runs, events_train=None, window=None, return_qc=False):
        """Fit preprocessor strictly on train runs, then extract training epochs (X_tr, y_tr)."""
        self.fit(raw_train_runs, events_train=events_train, window=window)
        return self.transform(
            raw_train_runs, events_test=events_train, window=window, return_epochs=True, return_qc=return_qc
        )
