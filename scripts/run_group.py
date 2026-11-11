"""Run several subjects, then write a group summary and figure.

Example:  python scripts/run_group.py --subjects 1-10 --outdir results
"""
import argparse
import json
import logging
from pathlib import Path

import pandas as pd

from emi.config import Config
from emi.pipeline import run_subject
from emi.plotting import plot_group_accuracy
from emi.summary import summarize_group

log = logging.getLogger("run_group")


def parse_subjects(text: str):
    """'1-10' -> 1..10, '1,5,7' -> [1, 5, 7], mixed forms allowed."""
    out = []
    for part in text.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--subjects", default="1-10")
    ap.add_argument("--outdir", default="results")
    ap.add_argument("--n-perm", type=int, default=200)
    ap.add_argument("--csp", choices=["rank_safe", "mne"], default="rank_safe")
    ap.add_argument("--null-type", choices=["perm", "shift", "both"], default="both")
    ap.add_argument("--debug", action="store_true", help="stop and show the traceback on the first error")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO)
    cfg = Config(n_perm=args.n_perm, null_type=args.null_type)
    rows, failed = [], []
    for s in parse_subjects(args.subjects):
        try:
            res = run_subject(s, cfg, args.outdir, csp=args.csp)
            rows.append({k: res[k] for k in ("subject", "csp_impl", "n_events", "n_trials_kept", "mean_acc", "perm_p",
                                             "random_split_acc", "n_bad_channels")})
            rows[-1]["n_trials"] = res["n_trials_kept"]
            log.info("subject %s done: acc=%.3f", s, res["mean_acc"])
        except Exception as exc:  # keep going; some subjects have known irregularities
            if args.debug:
                raise
            import traceback
            log.error("subject %s failed: %s", s, exc)
            failed.append({"subject": s, "error": str(exc), "traceback": traceback.format_exc()})

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    if failed:
        pd.DataFrame(failed).to_csv(out / "failed_subjects.csv", index=False)
    if not rows:
        raise SystemExit("No subject finished. See the log above.")
    df = pd.DataFrame(rows)
    df.to_csv(out / "group_results.csv", index=False)
    summary = summarize_group(df)
    with open(out / "group_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    plot_group_accuracy(df, out / "group_accuracy.png")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
