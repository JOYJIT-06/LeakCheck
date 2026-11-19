"""Adversarial stress test suite for filter_run_independent in src/emi/preprocess.py.

Empirical Challenger 1 stress tests:
1. Extreme high-voltage DC offsets (+10,000 V, -10,000 V, +50,000 V).
2. High-frequency noise bursts near run boundaries (Nyquist oscillation, boundary transients).
3. Non-standard sampling rates (128 Hz, 250 Hz, 500 Hz, 1000 Hz) and arbitrary run lengths.
4. Singlet (K=1), doublet (K=2), quintet (K=5), and decet (K=10) multi-run topologies.
5. Exact zero filter bleed verification: max |y_clean - y_corrupt| == 0.0 across independent runs.
6. Numerical stability of reflection padding under extreme magnitudes (no NaNs, no Infs).
7. Legacy unisolated concatenation positive control demonstrating severe leakage.
"""
import warnings
import numpy as np
import mne
import pytest

from emi.config import Config, RUN_TAG
from emi.preprocess import filter_run_independent


def _create_synthetic_run(sfreq=160.0, n_times=3200, n_ch=8, seed=42, ch_prefix="EEG"):
    """Helper to generate a synthetic RawArray."""
    ch_names = ["Fp1", "Fp2", "C3", "Cz", "C4", "P3", "Pz", "P4"][:n_ch]
    if len(ch_names) < n_ch:
        ch_names = [f"{ch_prefix}{i+1}" for i in range(n_ch)]
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types="eeg")
    rng = np.random.default_rng(seed)
    data = rng.standard_normal((n_ch, n_times)) * 1e-5
    raw = mne.io.RawArray(data, info, verbose="ERROR")
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=FutureWarning)
        if all(ch in mne.channels.make_standard_montage("standard_1020").ch_names for ch in ch_names):
            raw.set_montage("standard_1020", verbose="ERROR")
    return raw


def _create_concat_raw(raw_list):
    """Helper to build a concatenated BaseRaw with valid RUN_TAG description."""
    lengths = [r.n_times for r in raw_list]
    raw_concat = mne.concatenate_raws([r.copy() for r in raw_list])
    raw_concat.info["description"] = f"{RUN_TAG}{','.join(str(n) for n in lengths)}"
    return raw_concat


# ============================================================================
# 1. Extreme DC Offset Stress Tests (+10,000 V)
# ============================================================================

@pytest.mark.parametrize("dc_offset", [10000.0, -10000.0, 50000.0])
@pytest.mark.parametrize("band_name", ["ica", "decode"])
def test_extreme_dc_offset_isolation_list(dc_offset, band_name):
    """Verify that an extreme DC offset (+/-10,000V to 50,000V) in Run 12 produces ZERO bleed into Runs 4 and 8."""
    r4 = _create_synthetic_run(seed=1001)
    r8 = _create_synthetic_run(seed=1002)
    r12_clean = _create_synthetic_run(seed=1003)

    # Corrupt entire Run 12 with extreme DC offset
    data_r12_corrupt = r12_clean.get_data().copy()
    data_r12_corrupt += dc_offset
    r12_corrupt = mne.io.RawArray(data_r12_corrupt, r12_clean.info, verbose="ERROR")

    cfg = Config()

    clean_filtered = filter_run_independent([r4, r8, r12_clean], cfg=cfg, band=band_name)
    corrupt_filtered = filter_run_independent([r4, r8, r12_corrupt], cfg=cfg, band=band_name)

    # 1. Run 4 max absolute difference must be strictly 0.0
    diff_r4 = np.max(np.abs(clean_filtered[0].get_data() - corrupt_filtered[0].get_data()))
    assert diff_r4 == 0.0, f"Filter bleed detected in Run 4: max |diff| = {diff_r4}"
    np.testing.assert_array_equal(clean_filtered[0].get_data(), corrupt_filtered[0].get_data())

    # 2. Run 8 max absolute difference must be strictly 0.0
    diff_r8 = np.max(np.abs(clean_filtered[1].get_data() - corrupt_filtered[1].get_data()))
    assert diff_r8 == 0.0, f"Filter bleed detected in Run 8: max |diff| = {diff_r8}"
    np.testing.assert_array_equal(clean_filtered[1].get_data(), corrupt_filtered[1].get_data())

    # 3. Corrupted run must not contain NaNs or Infs
    assert not np.isnan(corrupt_filtered[2].get_data()).any(), "Corrupted run output contains NaN"
    assert not np.isinf(corrupt_filtered[2].get_data()).any(), "Corrupted run output contains Inf"


@pytest.mark.parametrize("dc_offset", [10000.0, -10000.0])
@pytest.mark.parametrize("band_name", ["ica", "decode"])
def test_extreme_dc_offset_isolation_concatenated(dc_offset, band_name):
    """Verify that extreme DC offset in concatenated Raw with RUN_TAG produces ZERO bleed into adjacent runs."""
    r4 = _create_synthetic_run(seed=1101)
    r8 = _create_synthetic_run(seed=1102)
    r12_clean = _create_synthetic_run(seed=1103)

    data_r12_corrupt = r12_clean.get_data().copy()
    data_r12_corrupt += dc_offset
    r12_corrupt = mne.io.RawArray(data_r12_corrupt, r12_clean.info, verbose="ERROR")

    concat_clean = _create_concat_raw([r4, r8, r12_clean])
    concat_corrupt = _create_concat_raw([r4, r8, r12_corrupt])

    cfg = Config()

    clean_filt = filter_run_independent(concat_clean, cfg=cfg, band=band_name)
    corrupt_filt = filter_run_independent(concat_corrupt, cfg=cfg, band=band_name)

    d_clean = clean_filt.get_data()
    d_corrupt = corrupt_filt.get_data()

    len_r4 = r4.n_times
    len_r8 = r8.n_times

    # Verify Run 4 segment
    diff_r4 = np.max(np.abs(d_clean[:, :len_r4] - d_corrupt[:, :len_r4]))
    assert diff_r4 == 0.0, f"Bleed in Run 4 segment of concatenated Raw: {diff_r4}"

    # Verify Run 8 segment (directly adjacent to corrupted Run 12)
    diff_r8 = np.max(np.abs(d_clean[:, len_r4:len_r4 + len_r8] - d_corrupt[:, len_r4:len_r4 + len_r8]))
    assert diff_r8 == 0.0, f"Bleed in Run 8 segment of concatenated Raw: {diff_r8}"


# ============================================================================
# 2. High-Frequency Boundary Noise Burst Stress Tests
# ============================================================================

def test_high_frequency_boundary_noise_burst():
    """Verify that an alternating Nyquist high-voltage noise burst at run boundaries produces zero bleed."""
    r1 = _create_synthetic_run(seed=2001)
    r2_clean = _create_synthetic_run(seed=2002)
    r3 = _create_synthetic_run(seed=2003)

    # In Run 2, corrupt first 250 samples and last 250 samples with +/- 5000 V alternating spikes
    data_r2_corrupt = r2_clean.get_data().copy()
    burst_len = 250
    nyquist_pattern = np.tile([5000.0, -5000.0], burst_len // 2)
    data_r2_corrupt[:, :burst_len] += nyquist_pattern
    data_r2_corrupt[:, -burst_len:] += nyquist_pattern

    r2_corrupt = mne.io.RawArray(data_r2_corrupt, r2_clean.info, verbose="ERROR")

    # 1. Test List mode
    clean_list = filter_run_independent([r1, r2_clean, r3], 1.0, 40.0)
    corrupt_list = filter_run_independent([r1, r2_corrupt, r3], 1.0, 40.0)

    diff_r1 = np.max(np.abs(clean_list[0].get_data() - corrupt_list[0].get_data()))
    diff_r3 = np.max(np.abs(clean_list[2].get_data() - corrupt_list[2].get_data()))

    assert diff_r1 == 0.0, f"Run 1 suffered bleed from Run 2 boundary burst: {diff_r1}"
    assert diff_r3 == 0.0, f"Run 3 suffered bleed from Run 2 boundary burst: {diff_r3}"

    # 2. Test Concatenated mode
    concat_clean = _create_concat_raw([r1, r2_clean, r3])
    concat_corrupt = _create_concat_raw([r1, r2_corrupt, r3])

    filt_concat_clean = filter_run_independent(concat_clean, 1.0, 40.0)
    filt_concat_corrupt = filter_run_independent(concat_corrupt, 1.0, 40.0)

    d_cc = filt_concat_clean.get_data()
    d_cp = filt_concat_corrupt.get_data()

    l1, l2, l3 = r1.n_times, r2_clean.n_times, r3.n_times
    diff_c_r1 = np.max(np.abs(d_cc[:, :l1] - d_cp[:, :l1]))
    diff_c_r3 = np.max(np.abs(d_cc[:, l1+l2:l1+l2+l3] - d_cp[:, l1+l2:l1+l2+l3]))

    assert diff_c_r1 == 0.0, f"Concat mode Run 1 suffered bleed: {diff_c_r1}"
    assert diff_c_r3 == 0.0, f"Concat mode Run 3 suffered bleed: {diff_c_r3}"


# ============================================================================
# 3. Non-Standard Sampling Rates and Arbitrary Run Lengths
# ============================================================================

@pytest.mark.parametrize("sfreq", [128.0, 250.0, 500.0])
def test_non_standard_sampling_rate_and_arbitrary_lengths(sfreq):
    """Verify isolation under non-standard sampling rates (128Hz, 250Hz, 500Hz) and arbitrary asymmetric run lengths."""
    # Asymmetric, non-round lengths
    lengths = [1357, 2891, 1923]
    runs_clean = []
    for i, length in enumerate(lengths):
        runs_clean.append(_create_synthetic_run(sfreq=sfreq, n_times=length, seed=3000 + i))

    # Corrupt Run 2 (middle) with extreme voltage
    runs_corrupt = [r.copy() for r in runs_clean]
    data_r2 = runs_corrupt[1].get_data().copy()
    data_r2 += 10000.0
    runs_corrupt[1] = mne.io.RawArray(data_r2, runs_clean[1].info, verbose="ERROR")

    # Filter with decoding band (e.g. 8-30 Hz)
    clean_out = filter_run_independent(runs_clean, 8.0, 30.0)
    corrupt_out = filter_run_independent(runs_corrupt, 8.0, 30.0)

    # Check isolation for Run 1 and Run 3
    diff_r1 = np.max(np.abs(clean_out[0].get_data() - corrupt_out[0].get_data()))
    diff_r3 = np.max(np.abs(clean_out[2].get_data() - corrupt_out[2].get_data()))

    assert diff_r1 == 0.0, f"sfreq={sfreq} Run 1 bleed: {diff_r1}"
    assert diff_r3 == 0.0, f"sfreq={sfreq} Run 3 bleed: {diff_r3}"

    # Also test concatenated mode with arbitrary lengths
    concat_clean = _create_concat_raw(runs_clean)
    concat_corrupt = _create_concat_raw(runs_corrupt)

    filt_cc = filter_run_independent(concat_clean, 8.0, 30.0)
    filt_cp = filter_run_independent(concat_corrupt, 8.0, 30.0)

    d_cc = filt_cc.get_data()
    d_cp = filt_cp.get_data()

    l1, l2, l3 = lengths
    diff_cc_r1 = np.max(np.abs(d_cc[:, :l1] - d_cp[:, :l1]))
    diff_cc_r3 = np.max(np.abs(d_cc[:, l1+l2:l1+l2+l3] - d_cp[:, l1+l2:l1+l2+l3]))

    assert diff_cc_r1 == 0.0, f"Concat sfreq={sfreq} Run 1 bleed: {diff_cc_r1}"
    assert diff_cc_r3 == 0.0, f"Concat sfreq={sfreq} Run 3 bleed: {diff_cc_r3}"


# ============================================================================
# 4. Multi-Run Topologies: Singlet, Doublet, Quintet (5-run), Decet (10-run)
# ============================================================================

def test_singlet_run_topology():
    """Verify singlet run (K=1) execution without errors in list and single BaseRaw modes."""
    r1 = _create_synthetic_run(seed=4001)

    # 1. As list
    filt_list = filter_run_independent([r1], 1.0, 40.0)
    assert len(filt_list) == 1
    assert filt_list[0].get_data().shape == r1.get_data().shape
    assert not np.isnan(filt_list[0].get_data()).any()

    # 2. As single BaseRaw with RUN_TAG
    raw_single = r1.copy()
    raw_single.info["description"] = f"{RUN_TAG}{r1.n_times}"
    filt_single = filter_run_independent(raw_single, 1.0, 40.0)
    assert filt_single.get_data().shape == r1.get_data().shape
    np.testing.assert_array_equal(filt_list[0].get_data(), filt_single.get_data())


def test_doublet_run_topology():
    """Verify doublet run (K=2) isolation when Run 2 has +10,000 V artifact."""
    r1 = _create_synthetic_run(seed=4101)
    r2_clean = _create_synthetic_run(seed=4102)

    data_r2_corrupt = r2_clean.get_data().copy() + 10000.0
    r2_corrupt = mne.io.RawArray(data_r2_corrupt, r2_clean.info, verbose="ERROR")

    clean_out = filter_run_independent([r1, r2_clean], 8.0, 30.0)
    corrupt_out = filter_run_independent([r1, r2_corrupt], 8.0, 30.0)

    diff_r1 = np.max(np.abs(clean_out[0].get_data() - corrupt_out[0].get_data()))
    assert diff_r1 == 0.0
    np.testing.assert_array_equal(clean_out[0].get_data(), corrupt_out[0].get_data())


def test_quintet_five_runs_topology():
    """Verify quintet session (K=5) isolation when middle Run 3 is violently corrupted."""
    lengths = [1600, 2000, 2400, 1800, 2200]
    runs_clean = [_create_synthetic_run(n_times=l, seed=4200 + i) for i, l in enumerate(lengths)]

    # Corrupt Run 3 (index 2)
    runs_corrupt = [r.copy() for r in runs_clean]
    data_r3_corrupt = runs_corrupt[2].get_data().copy() + 10000.0
    runs_corrupt[2] = mne.io.RawArray(data_r3_corrupt, runs_clean[2].info, verbose="ERROR")

    # Filter list
    clean_out = filter_run_independent(runs_clean, 1.0, 40.0)
    corrupt_out = filter_run_independent(runs_corrupt, 1.0, 40.0)

    # All runs except Run 3 must have diff == 0.0
    for idx in [0, 1, 3, 4]:
        diff = np.max(np.abs(clean_out[idx].get_data() - corrupt_out[idx].get_data()))
        assert diff == 0.0, f"Run {idx+1} suffered bleed: {diff}"
        np.testing.assert_array_equal(clean_out[idx].get_data(), corrupt_out[idx].get_data())

    # Check concatenated mode
    concat_clean = _create_concat_raw(runs_clean)
    concat_corrupt = _create_concat_raw(runs_corrupt)

    filt_cc = filter_run_independent(concat_clean, 1.0, 40.0)
    filt_cp = filter_run_independent(concat_corrupt, 1.0, 40.0)

    d_cc = filt_cc.get_data()
    d_cp = filt_cp.get_data()

    start = 0
    for idx, l in enumerate(lengths):
        stop = start + l
        if idx != 2:
            diff = np.max(np.abs(d_cc[:, start:stop] - d_cp[:, start:stop]))
            assert diff == 0.0, f"Concat Run {idx+1} suffered bleed: {diff}"
        start = stop


def test_decet_ten_runs_topology():
    """Verify decet session (K=10) where alternating odd runs are corrupted with +10,000 V."""
    n_runs = 10
    runs_clean = [_create_synthetic_run(n_times=1200, seed=4300 + i) for i in range(n_runs)]

    runs_corrupt = [r.copy() for r in runs_clean]
    for i in range(0, n_runs, 2):  # Corrupt runs 1, 3, 5, 7, 9
        data_c = runs_corrupt[i].get_data().copy() + 10000.0
        runs_corrupt[i] = mne.io.RawArray(data_c, runs_clean[i].info, verbose="ERROR")

    clean_out = filter_run_independent(runs_clean, 8.0, 30.0)
    corrupt_out = filter_run_independent(runs_corrupt, 8.0, 30.0)

    # Even runs (index 1, 3, 5, 7, 9 -> 2nd, 4th, 6th, 8th, 10th runs) must be bitwise identical
    for i in range(1, n_runs, 2):
        diff = np.max(np.abs(clean_out[i].get_data() - corrupt_out[i].get_data()))
        assert diff == 0.0, f"Even run {i+1} suffered bleed: {diff}"
        np.testing.assert_array_equal(clean_out[i].get_data(), corrupt_out[i].get_data())


# ============================================================================
# 5. Reflection Padding Extreme Values & Numerical Stability
# ============================================================================

@pytest.mark.parametrize("extreme_val", [1e6, -1e6, 1e-25, 0.0, 42.0])
def test_reflection_padding_extreme_values_stability(extreme_val):
    """Verify that reflection padding does not produce NaNs or Infs under extreme value scales."""
    info = mne.create_info(ch_names=["C3", "Cz", "C4"], sfreq=160.0, ch_types="eeg")
    if extreme_val == 0.0:
        data = np.zeros((3, 1600))
    elif extreme_val == 42.0:
        data = np.full((3, 1600), 42.0)
    else:
        rng = np.random.default_rng(5001)
        data = rng.standard_normal((3, 1600)) * extreme_val

    raw = mne.io.RawArray(data, info, verbose="ERROR")

    for pad_mode in ["reflect_limited", "reflect"]:
        filtered = filter_run_independent([raw], 1.0, 40.0, pad=pad_mode)
        out_data = filtered[0].get_data()

        assert not np.isnan(out_data).any(), f"NaN found with extreme_val={extreme_val}, pad={pad_mode}"
        assert not np.isinf(out_data).any(), f"Inf found with extreme_val={extreme_val}, pad={pad_mode}"


# ============================================================================
# 6. Legacy Unisolated Concatenation Positive Control
# ============================================================================

def test_legacy_unisolated_concatenation_severe_bleed():
    """Positive Control: Demonstrate that unisolated filtering leaks massive voltage across run boundaries."""
    r4 = _create_synthetic_run(seed=6001)
    r8 = _create_synthetic_run(seed=6002)
    r12_clean = _create_synthetic_run(seed=6003)

    data_r12_corrupt = r12_clean.get_data().copy() + 10000.0  # +10,000 V in Run 12

    # Unisolated concatenation
    d_clean_concat = np.concatenate([r4.get_data(), r8.get_data(), r12_clean.get_data()], axis=1)
    d_corrupt_concat = np.concatenate([r4.get_data(), r8.get_data(), data_r12_corrupt], axis=1)

    filt_clean = mne.filter.filter_data(d_clean_concat, 160.0, 1.0, 40.0, fir_design="firwin", verbose="ERROR")
    filt_corrupt = mne.filter.filter_data(d_corrupt_concat, 160.0, 1.0, 40.0, fir_design="firwin", verbose="ERROR")

    len_r4 = r4.n_times
    len_r8 = r8.n_times
    # Run 8 is index len_r4 to len_r4 + len_r8
    diff_r8 = np.max(np.abs(filt_clean[:, len_r4:len_r4 + len_r8] - filt_corrupt[:, len_r4:len_r4 + len_r8]))

    # Filter bleed in legacy filtering is massive (> 10 Volts)
    assert diff_r8 > 10.0, f"Expected massive bleed in legacy filtering, got {diff_r8}"

    # Meanwhile, filter_run_independent has strictly 0.0 bleed:
    clean_indep = filter_run_independent([r4, r8, r12_clean], 1.0, 40.0)
    corrupt_indep = filter_run_independent([r4, r8, mne.io.RawArray(data_r12_corrupt, r12_clean.info, verbose="ERROR")], 1.0, 40.0)
    diff_r8_indep = np.max(np.abs(clean_indep[1].get_data() - corrupt_indep[1].get_data()))
    assert diff_r8_indep == 0.0
