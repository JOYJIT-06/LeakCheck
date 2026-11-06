"""Run the full pipeline for one subject.

Example:  python scripts/run_subject.py --subject 1 --outdir results
"""
import argparse
import logging

from emi.config import Config
from emi.pipeline import run_subject


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--subject", type=int, required=True, help="PhysioNet subject number (1-109)")
    ap.add_argument("--outdir", default="results")
    ap.add_argument("--n-perm", type=int, default=200, help="0 skips the permutation test (faster)")
    ap.add_argument("--no-figures", action="store_true")
    ap.add_argument("--csp", choices=["rank_safe", "mne"], default="rank_safe",
                    help="CSP implementation; report it with every number (single subjects can differ by 10-30 points)")
    ap.add_argument("--null-type", choices=["perm", "shift", "both"], default="both")
    ap.add_argument("--no-ica", action="store_true", help="sensitivity run without ICA")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO)
    cfg = Config(n_perm=args.n_perm, null_type=args.null_type, use_ica=not args.no_ica)
    res = run_subject(args.subject, cfg, args.outdir, make_figures=not args.no_figures, csp=args.csp)
    print(f"Subject {res['subject']} [{res['csp_impl']} CSP, {res['validation']}]: accuracy {res['mean_acc']:.3f}, "
          f"null p = {res['perm_p']:.3f} (smallest possible {res['min_possible_p']:.3f}); trials kept "
          f"{res['n_trials_kept']}/{res['n_events']} (threshold {res['threshold_uv']:.0f} uV, {res['reject_mode']}), "
          f"per run {res['trials_per_run_kept']}; bad channels {res['bad_channels']}; ICA removed {res['ica_excluded']}; "
          f"random-split accuracy (optimistic) {res['random_split_acc']:.3f}")


if __name__ == "__main__":
    main()
