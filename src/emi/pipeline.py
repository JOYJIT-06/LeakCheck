"""One-subject pipeline used by the command-line scripts."""
import json
import logging
from pathlib import Path

import numpy as np
import sklearn

from . import __version__, data, decode, plotting, preprocess, tfr
from .config import EVENT_ID, Config
from .decoders import get_csp_factory

log = logging.getLogger(__name__)


def run_subject(subject: int, cfg: Config, outdir, make_figures: bool = True, csp: str = "rank_safe") -> dict:
    """Load, clean, analyse and save results for one subject. Returns the result dict.

    Primary accuracy = leave-one-run-out (`mean_acc`, `perm_p`, the larger p of the permutation and the circular-shift
    null). Random-split accuracy is added as a labelled comparison. `csp` names the CSP implementation and is written
    into the result; the report also lists trials lost, bad channels and removed ICA components for this subject.
    """
    import mne

    sub_dir = Path(outdir) / f"sub-{subject:03d}"
    sub_dir.mkdir(parents=True, exist_ok=True)
    factory = get_csp_factory(csp, cfg.csp_reg)

    raw = data.load_raw(subject, cfg)
    raw_clean, prep_info = preprocess.clean_raw(raw, cfg)
    ep_bb, ep_dec, runs, qc = preprocess.build_epochs_full(raw_clean, cfg)

    X = ep_dec.get_data()
    y = (ep_dec.events[:, 2] == EVENT_ID["right"]).astype(int)
    loro = decode.evaluate_loro(X, y, runs, cfg, factory)
    rand = decode.evaluate(X, y, cfg_no_perm(cfg), factory)
    result = {"subject": int(subject), "csp_impl": csp, **prep_info, **qc, **loro,
              "random_split_acc": rand["mean_acc"], "random_split_note": rand["validation"]}
    result["versions"] = {"emi": __version__, "mne": mne.__version__,
                          "scikit-learn": sklearn.__version__, "numpy": np.__version__}
    result["config"] = cfg.to_dict()

    if make_figures and len(ep_bb) >= 10:
        erd, times, freqs, ch_names = tfr.compute_erd(ep_bb, cfg)
        for name, band in (("mu", cfg.mu_band), ("beta", cfg.beta_band)):
            plotting.plot_erd_timecourses(erd, times, freqs, ch_names, band, sub_dir / f"erd_{name}.png",
                                          title=f"Subject {subject}: {name} band ({len(ep_bb)} trials)")
        try:
            fig = decode.csp_patterns_figure(ep_dec, X, y, cfg)
            fig.savefig(sub_dir / "csp_patterns.png", dpi=150)
        except Exception as exc:  # plotting must not stop the analysis
            log.warning("CSP pattern plot failed: %s", exc)

    with open(sub_dir / "result.json", "w") as f:
        json.dump(result, f, indent=2, default=str)
    return result


def cfg_no_perm(cfg: Config) -> Config:
    """Same settings without the (slow) permutation test; used for the labelled random-split comparison."""
    from dataclasses import replace
    return replace(cfg, n_perm=0)
