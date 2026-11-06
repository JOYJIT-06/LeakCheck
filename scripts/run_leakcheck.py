
"""Run the LeakCheck audit on cached subjects and write tables and figures.

Example (quick check):
  python scripts/run_leakcheck.py --subjects 1-3 --designs quick --n-null 5 --outdir results_leakcheck

Example (core audit, 4 workers):
  python scripts/run_leakcheck.py --subjects 1-20 --designs core --decoders csp_lda,csp_lr --n-null 20 --n-jobs 4

Each subject is saved separately, inside a folder named after a hash of the settings.
Runs with different settings are kept separate.
"""

import argparse
import hashlib
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
import sklearn
from joblib import Parallel, delayed

from emi import __version__
from emi import diagnostics as dg
from emi import leakcheck as lc
from emi.cache import cache_path, load_cache
from emi.plotting import (
    plot_leakcheck_inflation,
    plot_leakcheck_null,
    plot_paired_accuracy,
)
from emi.decoders import get_csp_factory


log = logging.getLogger("leakcheck")


def parse_subjects(text):
    out = []

    for part in text.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))

    return out


def file_sha256(path, chunk_size=1024 * 1024):
    """Return SHA256 fingerprint of a cache file."""
    h = hashlib.sha256()

    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)

    return h.hexdigest()


def technical_exclusion(d, min_trials, min_class, min_run):
    """Exclusion by technical criteria only. Never by accuracy."""
    y, runs = d["y"], d["runs"]

    if len(y) < min_trials:
        return f"only {len(y)} trials (< {min_trials})"

    if min(int((y == 0).sum()), int((y == 1).sum())) < min_class:
        return f"fewer than {min_class} trials in a class"

    counts = np.bincount(runs)
    counts = counts[counts > 0]

    if len(counts) == 0:
        return "no valid runs"

    if counts.min() < min_run:
        return f"a run has fewer than {min_run} trials: {counts.tolist()}"

    if len(counts) < 3:
        return f"only {len(counts)} runs (need 3)"

    return None


def run_one(subject, a, folder):

    out = folder / f"{a.dataset}_sub-{subject:03d}.csv"
    info_path = folder / f"{a.dataset}_sub-{subject:03d}_info.json"

    path = cache_path(a.cache_dir, subject, a.dataset)

    if not path.exists():
        return subject, None, None, f"no cache file {path}"

    try:
        # Identify the exact cache file used for this subject.
        cache_hash = file_sha256(path)

        # Reuse previous results only when the cache is unchanged.
        if out.exists() and info_path.exists() and not a.force:
            try:
                old_info = json.loads(info_path.read_text())

                if old_info.get("cache_sha256") == cache_hash:
                    return (
                        subject,
                        pd.read_csv(out),
                        old_info,
                        None,
                    )

            except (OSError, ValueError, json.JSONDecodeError):
                pass

        d = load_cache(path)

        why = technical_exclusion(
            d,
            a.min_trials,
            a.min_per_class,
            a.min_per_run,
        )

        if why:
            return subject, None, None, "EXCLUDED: " + why

        info = {
            "dataset": a.dataset,
            "subject": subject,
            "cache_file": str(path),
            "cache_sha256": cache_hash,
            "n_trials": int(len(d["y"])),
            "n_sessions": int(len(np.unique(d["sessions"]))),
            "sfreq": d.get("sfreq"),
            **dg.label_sequence_stats(d["y"], d["runs"]),
            **dg.run_decodability(d["X"], d["y"], d["runs"]),
            **dg.trial_dependence(d["X"], d["runs"], y=d["y"]),
        }

        # CSP regularisation.
        reg = None if a.csp_reg == "none" else a.csp_reg

        if a.csp != "mne" and reg is not None:
            raise ValueError(
                "--csp-reg can only be used with --csp mne"
            )

        factory = get_csp_factory(a.csp, reg=reg)

        csp_name = (
            a.csp
            if reg is None
            else f"{a.csp}_{a.csp_reg}"
        )

        df = lc.audit_subject(
            d["X"],
            d["y"],
            d["runs"],
            d["times"],
            subject,
            csp_factory=factory,
            csp_name=csp_name,
            dataset=a.dataset,
            sessions=d["sessions"],
            order=d["order"],
            decoders=tuple(a.decoders.split(",")),
            designs=a.designs,
            n_null=a.n_null,
            null_types=tuple(a.null_types.split(",")),
            n_repeats=a.n_repeats,
            n_repeats_matched=a.n_repeats_matched,
            seed=a.seed,
        )

        df.to_csv(out, index=False)

        info_path.write_text(
            json.dumps(info, indent=2)
        )

        return subject, df, info, None

    except Exception as exc:

        if a.debug:
            raise

        import traceback

        log.error(
            "subject %s failed:\n%s",
            subject,
            traceback.format_exc(),
        )

        return subject, None, None, f"FAILED: {exc!r}"


def main():

    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    ap.add_argument("--dataset", default="physionet")
    ap.add_argument("--subjects", default="1-5")
    ap.add_argument("--cache-dir", default="cache")
    ap.add_argument("--outdir", default="results_leakcheck")

    ap.add_argument(
        "--designs",
        default="core",
        help="quick | core | full | comma-separated design ids",
    )

    ap.add_argument(
        "--decoders",
        default="csp_lda",
        help="csp_lda,csp_lr,ts_lr",
    )

    ap.add_argument(
        "--n-null",
        type=int,
        default=20,
        help="null label sets per subject and null type",
    )

    ap.add_argument(
        "--null-types",
        default="perm,shift",
        help="perm (within-run permutation) and/or shift (circular shift)",
    )

    ap.add_argument(
        "--n-repeats",
        type=int,
        default=5,
        help="repeats for random k-fold designs",
    )

    ap.add_argument("--n-repeats-matched", type=int, default=20)
    ap.add_argument("--min-trials", type=int, default=30)
    ap.add_argument("--min-per-class", type=int, default=10)
    ap.add_argument("--min-per-run", type=int, default=8)

    ap.add_argument(
        "--csp",
        choices=["rank_safe", "mne", "numpy"],
        default="rank_safe",
        help=(
            "rank_safe (= numpy) is the built-in CSP that works inside "
            "the data subspace; mne = mne.decoding.CSP."
        ),
    )

    ap.add_argument(
        "--csp-reg",
        choices=["none", "oas", "ledoit_wolf", "shrunk"],
        default="none",
        help="MNE CSP covariance regularisation. Use oas for rank-deficient EEG.",
    )

    ap.add_argument(
        "--debug",
        action="store_true",
        help="stop at the first error and show the traceback",
    )

    ap.add_argument("--n-jobs", type=int, default=1)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--force", action="store_true")

    a = ap.parse_args()

    if a.csp_reg != "none" and a.csp != "mne":
        ap.error("--csp-reg can only be used with --csp mne")

    if a.n_null < 0:
        ap.error("--n-null cannot be negative")

    if a.n_null < 20:
        log.warning(
            "n_null=%d: the smallest possible empirical p is %.3f, "
            "so subject-level significance (p < 0.05) is impossible. "
            "Use --n-null 20 or more for confirmatory runs.",
            a.n_null,
            1 / (a.n_null + 1),
        )

    logging.basicConfig(level=logging.INFO)

    designs = lc.resolve_designs(a.designs)

    settings = {
        k: getattr(a, k)
        for k in (
            "dataset",
            "designs",
            "decoders",
            "n_null",
            "null_types",
            "n_repeats",
            "n_repeats_matched",
            "min_trials",
            "min_per_class",
            "min_per_run",
            "csp",
            "csp_reg",
            "seed",
        )
    }

    tag = hashlib.md5(
        json.dumps(settings, sort_keys=True).encode()
    ).hexdigest()[:8]

    out = Path(a.outdir)

    # All combined outputs are isolated by settings hash.
    run_out = out / "runs" / tag
    run_out.mkdir(parents=True, exist_ok=True)

    # Individual subject results remain separately stored.
    folder = out / "per_subject" / tag
    folder.mkdir(parents=True, exist_ok=True)

    settings_data = {
        **settings,
        "designs_resolved": designs,
    }

    (folder / "settings.json").write_text(
        json.dumps(settings_data, indent=2)
    )

    (run_out / "settings.json").write_text(
        json.dumps(settings_data, indent=2)
    )

    subjects = parse_subjects(a.subjects)

    results = Parallel(n_jobs=a.n_jobs)(
        delayed(run_one)(s, a, folder)
        for s in subjects
    )

    frames, infos, problems = [], [], []

    for s, df, info, err in results:

        if df is not None:
            frames.append(df)
            infos.append(info)

        else:
            log.error("subject %s: %s", s, err)

            problems.append({
                "dataset": a.dataset,
                "subject": s,
                "reason": err,
            })

    if problems:
        pd.DataFrame(problems).to_csv(
            run_out / "excluded_or_failed_subjects.csv",
            index=False,
        )

    if not frames:
        raise SystemExit(
            "No subject finished. See the log above."
        )

    df = pd.concat(frames, ignore_index=True)

    df.to_csv(
        run_out / "leakcheck_raw.csv",
        index=False,
    )

    pd.DataFrame(infos).to_csv(
        run_out / "subject_info.csv",
        index=False,
    )

    by = lc.inflation_by_subject(df)

    by.to_csv(
        run_out / "inflation_by_subject.csv",
        index=False,
    )

    infl = lc.inflation_table(by)

    infl.to_csv(
        run_out / "inflation_table.csv",
        index=False,
    )

    nul = lc.null_table(df)

    nul.to_csv(
        run_out / "null_table.csv",
        index=False,
    )

    lc.subject_empirical_p(df).to_csv(
        run_out / "subject_empirical_p.csv",
        index=False,
    )

    lc.paired_delta_vs_null(df).to_csv(
        run_out / "paired_delta_vs_null.csv",
        index=False,
    )

    dropped = by.attrs.get("dropped_subjects", [])

    if dropped:
        pd.DataFrame(dropped).to_csv(
            run_out / "dropped_pairs.csv",
            index=False,
        )

        log.warning(
            "%d subject/contrast pairs were dropped for missing "
            "accuracies; see dropped_pairs.csv",
            len(dropped),
        )

    shift = df[df["label_type"] == "shift"]

    if len(shift):
        agree = shift.drop_duplicates(
            ["subject", "perm"]
        )["label_agreement"]

        log.info(
            "shift-null label agreement with the real labels: "
            "mean %.2f, share above 0.8: %.1f%%",
            agree.mean(),
            100 * (agree > 0.8).mean(),
        )

    for (dec, nt), g in nul.groupby(
        ["decoder", "null_type"]
    ):
        plot_leakcheck_null(
            g,
            run_out / f"null_fpr_{dec}_{nt}.png",
            title=f"{a.dataset} | {dec} | null: {nt}",
        )

    for dec, g in by.groupby("decoder"):

        plot_leakcheck_inflation(
            g,
            run_out / f"inflation_{dec}.png",
            title=f"{a.dataset} | {dec}",
        )

        if "D1s_size_matched" in set(g["design"]):
            plot_paired_accuracy(
                g,
                "D1s_size_matched",
                run_out / f"paired_{dec}_size_matched.png",
            )

    summary = {
        "settings": settings,
        "designs": designs,
        "settings_hash": tag,
        "n_subjects_finished": int(
            df["subject"].nunique()
        ),
        "n_subjects_requested": len(subjects),
        "versions": {
            "emi": __version__,
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "scikit-learn": sklearn.__version__,
        },
        "total_compute_seconds": float(
            df["seconds"].sum()
        ),
    }

    try:
        import mne
        summary["versions"]["mne"] = mne.__version__
    except ImportError:
        pass

    (run_out / "leakcheck_summary.json").write_text(
        json.dumps(summary, indent=2)
    )

    pd.set_option(
        "display.width",
        220,
        "display.max_columns",
        30,
    )

    print(
        "\n=== Null labels "
        "(negative control: accuracy near 0.5 and "
        "false positives near 5%) ==="
    )

    print(
        nul[
            [
                "decoder",
                "null_type",
                "design",
                "n_subjects",
                "null_mean_acc",
                "false_positive_rate",
            ]
        ].round(3).to_string(index=False)
    )

    print(
        "\n=== Real labels: inflation in percentage points "
        "(leaky minus reference) ==="
    )

    cols = [
        c
        for c in (
            "decoder",
            "design",
            "reference",
            "n_subjects",
            "hl_pp",
            "hl_ci_low_pp",
            "hl_ci_high_pp",
            "wilcoxon_p_holm",
        )
        if c in infl.columns
    ]

    print(
        infl[cols].round(3).to_string(index=False)
    )

    print(f"\nResults saved in: {run_out}")


if __name__ == "__main__":
    main()
