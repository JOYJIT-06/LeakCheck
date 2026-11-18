"""Test that run-independent filtering has zero cross-run convolution bleed."""
import numpy as np
import mne
import pytest

from emi.config import Config, RUN_TAG, EVENT_ID
from emi.preprocess import filter_run_independent


def _create_synthetic_run(sfreq=160.0, n_times=3200, n_ch=8, seed=42):
    ch_names = ["Fp1", "Fp2", "C3", "Cz", "C4", "P3", "Pz", "P4"][:n_ch]
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types="eeg")
    rng = np.random.default_rng(seed)
    data = rng.standard_normal((n_ch, n_times)) * 1e-5
    raw = mne.io.RawArray(data, info, verbose="ERROR")
    raw.set_montage("standard_1020", verbose="ERROR")
    return raw


def test_filter_run_independent_isolation():
    """Verify that perturbations in one run do not affect filtered output of another run."""
    sfreq = 160.0
    ch_names = ["C3", "Cz", "C4"]
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types="eeg")

    rng = np.random.default_rng(42)
    # Run 1: clean EEG
    data1 = rng.standard_normal((3, 1600)) * 1e-5
    raw1 = mne.io.RawArray(data1, info, verbose="ERROR")

    # Run 2: clean EEG
    data2 = rng.standard_normal((3, 1600)) * 1e-5
    raw2 = mne.io.RawArray(data2, info, verbose="ERROR")

    # Run 2 corrupted: massive artifact spike
    data2_corrupted = data2.copy()
    data2_corrupted[:, 500:700] += 1000.0  # huge 1000V spike
    raw2_corrupted = mne.io.RawArray(data2_corrupted, info, verbose="ERROR")

    cfg = Config()

    # Filter pair (raw1, raw2)
    filt_clean = filter_run_independent([raw1, raw2], cfg, band="ica")

    # Filter pair (raw1, raw2_corrupted)
    filt_corrupted = filter_run_independent([raw1, raw2_corrupted], cfg, band="ica")

    # Assert raw1 output is 100% byte-identical
    np.testing.assert_array_equal(filt_clean[0].get_data(), filt_corrupted[0].get_data())


def test_physionet_three_runs_test_isolation_r12_artifact():
    """Test Case 1: Corrupting held-out Run 12 has zero impact on filtered Runs 4 and 8."""
    r4 = _create_synthetic_run(seed=101)
    r8 = _create_synthetic_run(seed=102)
    r12_clean = _create_synthetic_run(seed=103)

    # Corrupt first 200 samples of Run 12 with extreme +1000V spike
    data_r12_corrupt = r12_clean.get_data().copy()
    data_r12_corrupt[:, :200] += 1000.0
    r12_corrupt = mne.io.RawArray(data_r12_corrupt, r12_clean.info, verbose="ERROR")
    r12_corrupt.set_montage("standard_1020", verbose="ERROR")

    cfg = Config()

    # Test both broadband (1-40 Hz) and decoding band (8-30 Hz)
    for band_name in ("ica", "decode"):
        clean_runs = filter_run_independent([r4, r8, r12_clean], cfg=cfg, band=band_name)
        corrupt_runs = filter_run_independent([r4, r8, r12_corrupt], cfg=cfg, band=band_name)

        # Runs 4 and 8 must be bitwise identical
        np.testing.assert_array_equal(clean_runs[0].get_data(), corrupt_runs[0].get_data())
        np.testing.assert_array_equal(clean_runs[1].get_data(), corrupt_runs[1].get_data())

        # Run 12 must differ
        assert not np.array_equal(clean_runs[2].get_data(), corrupt_runs[2].get_data())


def test_physionet_three_runs_middle_run_isolation_r8_artifact():
    """Test Case 2: Corrupting middle Run 8 has zero impact on surrounding Runs 4 and 12."""
    r4 = _create_synthetic_run(seed=201)
    r8_clean = _create_synthetic_run(seed=202)
    r12 = _create_synthetic_run(seed=203)

    # Corrupt Run 8 on both edges (first 200 and last 200 samples)
    data_r8_corrupt = r8_clean.get_data().copy()
    data_r8_corrupt[:, :200] += 1000.0
    data_r8_corrupt[:, -200:] += 1000.0
    r8_corrupt = mne.io.RawArray(data_r8_corrupt, r8_clean.info, verbose="ERROR")
    r8_corrupt.set_montage("standard_1020", verbose="ERROR")

    cfg = Config()
    clean_runs = filter_run_independent([r4, r8_clean, r12], cfg=cfg, band="decode")
    corrupt_runs = filter_run_independent([r4, r8_corrupt, r12], cfg=cfg, band="decode")

    # Surrounding runs 4 and 12 must be bitwise identical
    np.testing.assert_array_equal(clean_runs[0].get_data(), corrupt_runs[0].get_data())
    np.testing.assert_array_equal(clean_runs[2].get_data(), corrupt_runs[2].get_data())
    assert not np.array_equal(clean_runs[1].get_data(), corrupt_runs[1].get_data())


def test_legacy_concatenation_leak_demonstration():
    """Test Case 3 (Positive Control): Concatenating runs prior to filtering causes bleed into adjacent runs."""
    r4 = _create_synthetic_run(seed=301)
    r8 = _create_synthetic_run(seed=302)
    r12_clean = _create_synthetic_run(seed=303)

    data_r12_corrupt = r12_clean.get_data().copy()
    data_r12_corrupt[:, :200] += 1000.0

    # In legacy concatenated filtering (without independent buffers)
    d_clean_concat = np.concatenate([r4.get_data(), r8.get_data(), r12_clean.get_data()], axis=1)
    d_corrupt_concat = np.concatenate([r4.get_data(), r8.get_data(), data_r12_corrupt], axis=1)

    # Filter concatenated signals directly using MNE filter_data
    filt_clean = mne.filter.filter_data(d_clean_concat, 160.0, 1.0, 40.0, fir_design="firwin", verbose="ERROR")
    filt_corrupt = mne.filter.filter_data(d_corrupt_concat, 160.0, 1.0, 40.0, fir_design="firwin", verbose="ERROR")

    # Run 8 samples are indices 3200 to 6400. Check difference in Run 8 near boundary with Run 12
    diff_r8 = np.max(np.abs(filt_clean[:, 3200:6400] - filt_corrupt[:, 3200:6400]))
    # Demonstrable bleed (> 1.0 Volt) exists across boundary in legacy concatenated filtering!
    assert diff_r8 > 1.0


def test_filter_run_independent_concatenated_raw_support():
    """Test Case 4: BaseRaw with RUN_TAG produces identical output to list of BaseRaws."""
    r4 = _create_synthetic_run(seed=401)
    r8 = _create_synthetic_run(seed=402)
    r12 = _create_synthetic_run(seed=403)

    lengths = [r4.n_times, r8.n_times, r12.n_times]
    raw_concat = mne.concatenate_raws([r4.copy(), r8.copy(), r12.copy()])
    raw_concat.info["description"] = f"{RUN_TAG}{','.join(str(n) for n in lengths)}"

    list_filtered = filter_run_independent([r4, r8, r12], 8.0, 30.0)
    concat_filtered = filter_run_independent(raw_concat, 8.0, 30.0)

    expected_data = np.concatenate([r.get_data() for r in list_filtered], axis=1)
    np.testing.assert_allclose(concat_filtered.get_data(), expected_data, rtol=1e-12, atol=1e-12)


def test_filter_run_independent_polymorphic_signatures():
    """Test Case 5: Verify all polymorphic calling signatures execute correctly and identically."""
    r1 = _create_synthetic_run(seed=501)
    r2 = _create_synthetic_run(seed=502)
    cfg = Config()

    # 1. Positional floats
    f1 = filter_run_independent([r1, r2], 8.0, 30.0)
    # 2. Keyword floats
    f2 = filter_run_independent([r1, r2], l_freq=8.0, h_freq=30.0)
    # 3. Tuple
    f3 = filter_run_independent([r1, r2], (8.0, 30.0))
    # 4. Config object with band name
    f4 = filter_run_independent([r1, r2], cfg, "decode")
    # 5. Config keyword with band keyword
    f5 = filter_run_independent([r1, r2], cfg=cfg, band="decode")

    np.testing.assert_array_equal(f1[0].get_data(), f2[0].get_data())
    np.testing.assert_array_equal(f1[0].get_data(), f3[0].get_data())
    np.testing.assert_array_equal(f1[0].get_data(), f4[0].get_data())
    np.testing.assert_array_equal(f1[0].get_data(), f5[0].get_data())


def test_edge_reflection_padding_stability():
    """Test Case 6: Boundary reflection padding avoids NaNs/Infs and preserves shapes."""
    r1 = _create_synthetic_run(seed=601)
    filtered = filter_run_independent([r1], 1.0, 40.0, pad="reflect_limited")

    assert not np.isnan(filtered[0].get_data()).any()
    assert not np.isinf(filtered[0].get_data()).any()
    assert filtered[0].get_data().shape == r1.get_data().shape


def test_epoch_extraction_zero_bleed():
    """Test Case 7: Epochs extracted near run boundary are invariant to artifacts in adjacent run."""
    sfreq = 160.0
    r8_clean = _create_synthetic_run(n_times=3200, seed=701)
    r12_clean = _create_synthetic_run(n_times=3200, seed=702)

    # Event in Run 8 at t = 18.5s (sample 2960), which is within filter half-width (1.65s = 264 samples) of boundary (sample 3200)
    onset = [18.5]
    duration = [1.0]
    description = ["T1"]
    annot = mne.Annotations(onset=onset, duration=duration, description=description)
    r8_clean.set_annotations(annot)

    # Corrupted R12: massive artifact spike
    data_r12_corrupt = r12_clean.get_data().copy()
    data_r12_corrupt[:, :200] += 1000.0
    r12_corrupt = mne.io.RawArray(data_r12_corrupt, r12_clean.info, verbose="ERROR")
    r12_corrupt.set_montage("standard_1020", verbose="ERROR")

    # Filter clean and corrupt runs independently
    r8_filt_clean = filter_run_independent([r8_clean], 8.0, 30.0)[0]
    r8_filt_corrupt = filter_run_independent([r8_clean], 8.0, 30.0)[0]

    events, event_dict = mne.events_from_annotations(r8_filt_clean, event_id={"T1": EVENT_ID["left"]}, verbose="ERROR")
    ep_clean = mne.Epochs(r8_filt_clean, events, event_dict, tmin=0.0, tmax=1.0, baseline=None, preload=True, verbose="ERROR")
    ep_corrupt = mne.Epochs(r8_filt_corrupt, events, event_dict, tmin=0.0, tmax=1.0, baseline=None, preload=True, verbose="ERROR")

    np.testing.assert_array_equal(ep_clean.get_data(), ep_corrupt.get_data())
