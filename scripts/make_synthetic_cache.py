"""Write SYNTHETIC subjects in the cache format, to test the whole audit without any real data.

Each subject has a real left/right effect (channel 0 / 1 power) and, optionally, run-specific channel
gains ("run shift", a stand-in for non-stationarity between runs). With run shift, designs that mix
runs should look better than leave-one-run-out; without it they should not.
This is a SOFTWARE VALIDATION tool. Its output must never be reported as an empirical finding.

Example:  python scripts/make_synthetic_cache.py --name synth_shift --run-shift 0.6 --n-subjects 8
"""
import argparse

import numpy as np

from emi.cache import cache_path, save_cache


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--name", default="synthetic")
    ap.add_argument("--cache-dir", default="cache")
    ap.add_argument("--n-subjects", type=int, default=8)
    ap.add_argument("--n-runs", type=int, default=3)
    ap.add_argument("--per-run", type=int, default=16)
    ap.add_argument("--n-channels", type=int, default=16)
    ap.add_argument("--sfreq", type=float, default=80.0)
    ap.add_argument("--effect", type=float, default=1.07, help="amplitude gain of the class-specific channel")
    ap.add_argument("--run-shift", type=float, default=0.0, help="SD of the log run-specific channel gains")
    ap.add_argument("--run-specific-effect", action="store_true",
                    help="the class effect sits on different channels in every run (non-stationary signal)")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    n_t = int(4 * a.sfreq)
    times = np.arange(n_t) / a.sfreq
    for s in range(1, a.n_subjects + 1):
        rng = np.random.default_rng(a.seed + s)
        y, runs = [], []
        for r in range(a.n_runs):
            lab = np.array([0, 1] * (a.per_run // 2))
            rng.shuffle(lab)
            y.extend(lab)
            runs.extend([r] * a.per_run)
        y, runs = np.array(y), np.array(runs)
        X = rng.standard_normal((len(y), a.n_channels, n_t))
        if a.run_specific_effect:
            for r in range(a.n_runs):
                c0, c1 = (2 * r) % a.n_channels, (2 * r + 1) % a.n_channels
                X[(runs == r) & (y == 0), c0, :] *= a.effect
                X[(runs == r) & (y == 1), c1, :] *= a.effect
        else:
            X[y == 0, 0, :] *= a.effect
            X[y == 1, 1, :] *= a.effect
        if a.run_shift > 0:
            gains = np.exp(rng.normal(0, a.run_shift, (a.n_runs, a.n_channels)))
            X *= gains[runs][:, :, None]
        save_cache(cache_path(a.cache_dir, s, a.name), X, y, runs, times, s, a.name, sfreq=a.sfreq,
                   ch_names=[f"ch{i}" for i in range(a.n_channels)], extra={"synthetic": True})
    print(f"wrote {a.n_subjects} synthetic subjects to {a.cache_dir}/{a.name}")


if __name__ == "__main__":
    main()
