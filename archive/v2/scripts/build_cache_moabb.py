"""Build LeakCheck caches from MOABB datasets (UNTESTED adapter; see src/emi/datasets_moabb.py).

Example:  python scripts/build_cache_moabb.py --dataset BNCI2014_001 --subjects 1-9 --cache-dir cache
Needs: pip install moabb. Check each dataset's licence and availability first.
"""
import argparse
import logging

import pandas as pd

from emi.datasets_moabb import build_moabb_cache

log = logging.getLogger("build_cache_moabb")


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
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--subjects", default="1-5")
    ap.add_argument("--cache-dir", default="cache")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO)
    rows = []
    for s in parse_subjects(args.subjects):
        try:
            info = build_moabb_cache(args.dataset, s, args.cache_dir)
            rows.append(info)
            log.info("%s", info)
        except Exception as exc:
            log.error("subject %s failed: %s", s, exc)
    if rows:
        pd.DataFrame(rows).to_csv(f"{args.cache_dir}/{args.dataset}_manifest.csv", index=False)


if __name__ == "__main__":
    main()
