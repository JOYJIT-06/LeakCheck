"""Preprocessing: filter, bad channels, re-reference, ICA artifact removal, epoching, label-blind trial rejection.

Order (changed in v0.3 after the code review): band-pass -> detect and interpolate bad channels -> average
reference -> ICA. Every rule is LABEL-BLIND and fixed in advance. None of it is 'nested': filtering, interpolation,
ICA and the rejection threshold use all runs of a subject, including the run later held out. That cannot leak
labels, but it is not the same as fitting inside the training folds (the ICA version of the question, P2, is TODO).
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
    raw = raw.copy()
    raw.filter(*cfg.ica_band, fir_design="firwin", verbose="ERROR")

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
    ica = ICA(n_components=n_comp, random_state=cfg.seed, max_iter="auto")
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

    raw_band = raw_clean.copy().filter(*cfg.decode_band, fir_design="firwin", verbose="ERROR")
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
