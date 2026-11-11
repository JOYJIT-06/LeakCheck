"""Preprocess subjects once and save their epochs, so LeakCheck runs fast.

Example:  python scripts/build_cache.py --subjects 1-10 --cache-dir cache
Needs MNE. Existing cache files are skipped unless --force is given.
"""
import argparse
import logging

import pandas as pd

from emi.cache import build_subject_cache, cache_path
from emi.config import Config

log = logging.getLogger("build_cache")


def parse_subjects(text):
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
    ap.add_argument("--cache-dir", default="cache")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO)
    cfg = Config()
    rows, failed = [], []
    for s in parse_subjects(args.subjects):
        if cache_path(args.cache_dir, s).exists() and not args.force:
            log.info("subject %s already cached, skipping", s)
            continue
        try:
            info = build_subject_cache(s, cfg, args.cache_dir)
            rows.append(info)
            # CHECK THIS: each run should hold roughly the same number of trials (about 15).
            log.info("subject %s: kept %s of %s trials (threshold %s uV, %s), per run %s, bad channels [%s], ICA removed %s",
                     s, info["n_trials"], info["n_events"], info["reject_threshold_uv"], info["reject_mode"],
                     info["trials_per_run"], info["bad_channels"], info["n_ica_removed"])
        except Exception as exc:
            log.error("subject %s failed: %s", s, exc)
            failed.append({"subject": s, "error": str(exc)})
    if rows:
        pd.DataFrame(rows).to_csv(f"{args.cache_dir}/cache_manifest_new.csv", index=False)
    if failed:
        pd.DataFrame(failed).to_csv(f"{args.cache_dir}/cache_failed.csv", index=False)


if __name__ == "__main__":
    main()
