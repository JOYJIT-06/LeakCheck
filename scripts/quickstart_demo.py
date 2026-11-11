#!/usr/bin/env python3
"""LeakCheck Quick-Start Demonstration.

Runs a self-contained leakage-auditing demonstration on synthetic 3-run motor imagery EEG
without requiring any external dataset downloads or network access.

Usage:
    python scripts/quickstart_demo.py
"""

from __future__ import annotations

import sys
import time
import mne
import numpy as np
import pandas as pd

import emi
from emi.leakcheck import audit_subject

# Suppress verbose MNE covariance estimation logs during demo
mne.set_log_level("WARNING")


def generate_synthetic_mi_session(
    n_trials: int = 60,
    n_channels: int = 16,
    n_times: int = 640,
    sfreq: float = 160.0,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Generate synthetic 3-run EEG motor imagery data.

    Creates left-hand vs. right-hand motor imagery with run-specific non-stationarity
    and differential sensorimotor rhythm power.
    """
    rng = np.random.default_rng(seed)
    
    # Balance classes (0 = Left, 1 = Right)
    y = np.tile([0, 1], n_trials // 2)
    
    # 3 distinct recording runs
    runs = np.repeat([0, 1, 2], n_trials // 3)
    
    # Base background EEG noise
    X = rng.standard_normal((n_trials, n_channels, n_times)) * 15.0
    
    # Time vector (0 to 4.0 seconds)
    times = np.linspace(0.0, n_times / sfreq, n_times, endpoint=False)
    
    # Inject mu/beta rhythm modulations in sensorimotor channels (Ch 0 = C3, Ch 1 = C4)
    # Left hand (y=0): contralateral C4 desynchronization / C3 synchronization
    # Right hand (y=1): contralateral C3 desynchronization / C4 synchronization
    for r in (0, 1, 2):
        mask = runs == r
        # Add baseline run drift
        drift = rng.standard_normal((n_channels, 1)) * 5.0
        X[mask] += drift
        
        # SMR burst
        t_active = (times >= 1.0) & (times <= 3.0)
        osc = np.sin(2 * np.pi * 12.0 * times[t_active])
        for idx in np.where(mask & (y == 0))[0]:
            X[idx, 0, t_active] += 12.0 * osc
        for idx in np.where(mask & (y == 1))[0]:
            X[idx, 1, t_active] += 12.0 * osc

    return X, y, runs, times


def main():
    print("================================================================================")
    print("                    LeakCheck v1.1 Quick-Start Demonstration                     ")
    print("================================================================================")
    print(f"Package: emi v{emi.__version__}")
    print("Generating synthetic 3-run motor imagery dataset (60 trials, 16 channels, 160 Hz)...")
    
    t0 = time.time()
    X, y, runs, times = generate_synthetic_mi_session(seed=42)
    print(f"Dataset generated in {time.time() - t0:.2f} s. No external downloads required.")
    print("\nAuditing validation designs and leakage mechanisms:")
    print("  1. D3_loro          : Clean Leave-One-Run-Out (operational benchmark)")
    print("  2. D1s_size_matched : Size- and class-matched pooled random partition")
    print("  3. P1_csp_on_all    : Supervised spatial filtering leakage (CSP on all trials)")
    print("\nEvaluating decoders: Shrinkage CSP-LDA and Riemannian TS-LR...")

    # Run audit
    results_df = audit_subject(
        X=X,
        y=y,
        runs=runs,
        times=times,
        subject=1,
        decoders=["csp_lda", "ts_lr"],
        designs=["D3_loro", "D1s_size_matched", "P1_csp_on_all"],
        n_null=0,
        n_repeats=5,
        n_repeats_matched=5,
        seed=0,
    )

    print("\n-------------------------------- AUDIT RESULTS --------------------------------")
    summary = []
    for dec in ["csp_lda", "ts_lr"]:
        sub = results_df[results_df["decoder"] == dec].set_index("design")
        d3_acc = sub.loc["D3_loro", "acc_pooled"] * 100.0 if "D3_loro" in sub.index else float("nan")
        d1s_acc = sub.loc["D1s_size_matched", "acc_pooled"] * 100.0 if "D1s_size_matched" in sub.index else float("nan")
        
        has_p1 = "P1_csp_on_all" in sub.index
        p1_acc_str = f"{sub.loc['P1_csp_on_all', 'acc_pooled'] * 100.0:.1f}%" if has_p1 else "N/A"
        p1_diff_str = f"{sub.loc['P1_csp_on_all', 'acc_pooled'] * 100.0 - d3_acc:+.1f} pp" if has_p1 else "N/A (No CSP)"

        summary.append({
            "Decoder": "Shrinkage CSP-LDA" if dec == "csp_lda" else "Riemannian TS-LR",
            "D3 (LORO, %)": f"{d3_acc:.1f}%",
            "D1s (Random, %)": f"{d1s_acc:.1f}%",
            "D1s Bias (pp)": f"{d1s_acc - d3_acc:+.1f} pp",
            "P1 (Leaky, %)": p1_acc_str,
            "P1 Inflation (pp)": p1_diff_str,
        })

    sum_df = pd.DataFrame(summary)
    print(sum_df.to_string(index=False))
    print("--------------------------------------------------------------------------------")
    print("\nKey Scientific Takeaways:")
    print("  * P1 Inflation : Supervised spatial filters fit on all trials encode test-set labels.")
    print("  * D1s vs D3    : Random trial pooling alters cross-run non-stationarity exposure.")
    print("  * Decoder Diff : Riemannian TS-LR is less vulnerable to global CSP-style contamination.")
    print("\nDemo completed successfully in {:.2f} seconds!".format(time.time() - t0))
    print("To run on real empirical benchmarks (PhysioNet/OpenBMI), see docs/quickstart.md.")
    print("================================================================================")


if __name__ == "__main__":
    main()
