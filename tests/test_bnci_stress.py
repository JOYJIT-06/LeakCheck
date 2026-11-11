"""Empirical Stress & Fuzzing Harness for BNCI Event Parsing and Run Boundary Logic.

Tested by: teamwork_challenger (Agent: challenger_m1_1)
Target: parse_bnci_events_and_runs in src/emi/datasets_adapters.py
"""

import sys
import numpy as np
import mne
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from emi.datasets_adapters import parse_bnci_events_and_runs


def _create_mock_epochs(event_array: np.ndarray, event_id_dict: dict) -> mne.Epochs:
    """Helper to create minimal Epochs object from event array."""
    raw_info = mne.create_info(ch_names=["C3", "Cz", "C4"], sfreq=250.0, ch_types="eeg")
    max_sample = int(np.max(event_array[:, 0])) + 500 if len(event_array) > 0 else 1000
    raw_data = np.zeros((3, max(max_sample, 1000)))
    raw = mne.io.RawArray(raw_data, raw_info, verbose="ERROR")
    return mne.Epochs(
        raw,
        event_array,
        event_id=event_id_dict,
        tmin=0.0,
        tmax=0.5,
        baseline=None,
        preload=True,
        verbose="ERROR",
        on_missing="ignore",
        event_repeated="drop",
    )


def test_stress_direct_integer_triggers():
    """Stress-test direct integer trigger codes [769, 770]."""
    for n_trials in [2, 10, 50, 144, 200]:
        events = np.zeros((n_trials, 3), dtype=int)
        events[:, 0] = np.arange(100, 100 + n_trials * 100, 100)
        # Alternate 769 and 770
        events[:, 2] = [769 if i % 2 == 0 else 770 for i in range(n_trials)]
        target_ids = {"769": 769, "770": 770}
        epochs = _create_mock_epochs(events, target_ids)

        y, runs = parse_bnci_events_and_runs(epochs, events, target_ids, target_ids, default_n_runs=6)
        assert len(y) == n_trials
        assert len(runs) == n_trials
        assert set(np.unique(y)).issubset({0, 1})
        assert np.all(runs >= 0)
        assert np.array_equal(y, [0 if i % 2 == 0 else 1 for i in range(n_trials)])


def test_stress_mne_mapped_event_ids():
    """Stress-test MNE-mapped event IDs with various annotation string keys."""
    key_combos = [
        ({"769": 1, "770": 2}, 1, 2),
        ({"Cue/769": 10, "Cue/770": 20}, 10, 20),
        ({"OVTK_GDF_769": 100, "OVTK_GDF_770": 200}, 100, 200),
        ({"Event_769_LeftHand": 5, "Event_770_RightHand": 6}, 5, 6),
    ]
    for target_ids, code_left, code_right in key_combos:
        n_trials = 24
        events = np.zeros((n_trials, 3), dtype=int)
        events[:, 0] = np.arange(100, 100 + n_trials * 100, 100)
        events[:, 2] = [code_left if i % 2 == 0 else code_right for i in range(n_trials)]
        epochs = _create_mock_epochs(events, target_ids)

        y, runs = parse_bnci_events_and_runs(epochs, events, target_ids, target_ids, default_n_runs=4)
        assert len(y) == n_trials
        assert np.array_equal(y, [0 if i % 2 == 0 else 1 for i in range(n_trials)])
        assert set(np.unique(runs)) == {0, 1, 2, 3}


def test_stress_uneven_trial_numbers():
    """Stress-test uneven trial counts without run markers."""
    uneven_counts = [1, 2, 3, 5, 7, 11, 13, 23, 71, 97, 143, 145, 251]
    target_ids = {"769": 1, "770": 2}

    for n_trials in uneven_counts:
        for default_runs in [2, 3, 6, 8]:
            events = np.zeros((n_trials, 3), dtype=int)
            events[:, 0] = np.arange(100, 100 + n_trials * 100, 100)
            events[:, 2] = [1 if i % 2 == 0 else 2 for i in range(n_trials)]
            epochs = _create_mock_epochs(events, target_ids)

            y, runs = parse_bnci_events_and_runs(epochs, events, target_ids, target_ids, default_n_runs=default_runs)
            assert len(y) == n_trials
            assert len(runs) == n_trials
            assert set(np.unique(y)).issubset({0, 1})
            assert np.all(runs >= 0)
            expected_n_runs = min(default_runs, n_trials) if n_trials > 1 else 1
            assert len(np.unique(runs)) == expected_n_runs
            assert np.min(runs) == 0
            assert np.max(runs) == expected_n_runs - 1


def test_stress_single_class_only():
    """Stress-test when recording contains only left hand or only right hand trials."""
    target_ids = {"769": 1, "770": 2}
    n_trials = 30

    # Only left hand
    events_left = np.zeros((n_trials, 3), dtype=int)
    events_left[:, 0] = np.arange(100, 100 + n_trials * 100, 100)
    events_left[:, 2] = 1
    epochs_left = _create_mock_epochs(events_left, {"769": 1})
    y_l, runs_l = parse_bnci_events_and_runs(epochs_left, events_left, {"769": 1}, target_ids, default_n_runs=3)
    assert np.all(y_l == 0)
    assert set(np.unique(runs_l)) == {0, 1, 2}

    # Only right hand
    events_right = np.zeros((n_trials, 3), dtype=int)
    events_right[:, 0] = np.arange(100, 100 + n_trials * 100, 100)
    events_right[:, 2] = 2
    epochs_right = _create_mock_epochs(events_right, {"770": 2})
    y_r, runs_r = parse_bnci_events_and_runs(epochs_right, events_right, {"770": 2}, target_ids, default_n_runs=3)
    assert np.all(y_r == 1)
    assert set(np.unique(runs_r)) == {0, 1, 2}


def test_stress_gdf_marker_variations():
    """Stress-test different GDF run marker representations and case sensitivity."""
    marker_keys = [
        "32766",
        "0x7ffe",
        "0x7FFE",
        "start of a new run",
        "Start of a new run",
        "START OF A NEW RUN",
    ]
    target_ids = {"769": 1, "770": 2}

    for key in marker_keys:
        full_event_id = {"769": 1, "770": 2, key: 99}
        # 3 runs: markers at 100, 1000, 2000
        # trials at 200, 300 (run 0), 1200, 1300 (run 1), 2200, 2300 (run 2)
        raw_events = np.array([
            [100, 0, 99],
            [200, 0, 1],
            [300, 0, 2],
            [1000, 0, 99],
            [1200, 0, 1],
            [1300, 0, 2],
            [2000, 0, 99],
            [2200, 0, 1],
            [2300, 0, 2],
        ])
        epochs = _create_mock_epochs(raw_events[raw_events[:, 2] != 99], target_ids)
        y, runs = parse_bnci_events_and_runs(epochs, raw_events, full_event_id, target_ids, default_n_runs=6)

        assert np.array_equal(y, [0, 1, 0, 1, 0, 1]), f"Failed for key {key}"
        assert np.array_equal(runs, [0, 0, 1, 1, 2, 2]), f"Failed run assignment for key {key}"


def test_stress_boundary_marker_edge_cases():
    """Stress-test trials before first marker, exactly at marker, and after last marker."""
    full_event_id = {"769": 1, "770": 2, "32766": 99}
    target_ids = {"769": 1, "770": 2}

    # Case A: Trials occurring BEFORE first run marker (e.g. pre-run baseline/cues)
    raw_events_early = np.array([
        [50, 0, 1],     # Pre-marker trial (sample 50 < 200)
        [200, 0, 99],   # Run 0 marker
        [300, 0, 2],    # Trial in run 0
        [1000, 0, 99],  # Run 1 marker
        [1200, 0, 1],   # Trial in run 1
    ])
    epochs_early = _create_mock_epochs(raw_events_early[raw_events_early[:, 2] != 99], target_ids)
    y_e, runs_e = parse_bnci_events_and_runs(epochs_early, raw_events_early, full_event_id, target_ids, default_n_runs=2)
    assert np.all(runs_e >= 0), "Runs must be non-negative even for pre-marker trials"
    assert runs_e[0] == 0, "Pre-marker trial must clip to run 0"
    assert np.array_equal(runs_e, [0, 0, 1])

    # Case B: Trial occurring EXACTLY at marker timestamp
    raw_events_exact = np.array([
        [200, 0, 99],   # Run 0 marker
        [200, 0, 1],    # Trial at exact same sample 200
        [1000, 0, 99],  # Run 1 marker
        [1000, 0, 2],   # Trial at exact same sample 1000
    ])
    epochs_exact = _create_mock_epochs(raw_events_exact[raw_events_exact[:, 2] != 99], target_ids)
    y_x, runs_x = parse_bnci_events_and_runs(epochs_exact, raw_events_exact, full_event_id, target_ids, default_n_runs=2)
    assert np.all(runs_x >= 0)
    assert np.array_equal(runs_x, [0, 1])

    # Case C: Trials long after last marker
    raw_events_late = np.array([
        [200, 0, 99],   # Run 0 marker
        [300, 0, 1],    # Trial
        [1000, 0, 99],  # Run 1 marker
        [5000, 0, 2],   # Late trial
        [9000, 0, 1],   # Very late trial
    ])
    epochs_late = _create_mock_epochs(raw_events_late[raw_events_late[:, 2] != 99], target_ids)
    y_l, runs_l = parse_bnci_events_and_runs(epochs_late, raw_events_late, full_event_id, target_ids, default_n_runs=2)
    assert np.array_equal(runs_l, [0, 1, 1])


def test_stress_single_or_zero_markers():
    """Verify fallback behavior when 0 or only 1 run marker exists."""
    full_event_id = {"769": 1, "770": 2, "32766": 99}
    target_ids = {"769": 1, "770": 2}

    # Only 1 marker present
    raw_events_one = np.array([
        [100, 0, 99],
        [200, 0, 1],
        [300, 0, 2],
        [400, 0, 1],
        [500, 0, 2],
    ])
    epochs_one = _create_mock_epochs(raw_events_one[raw_events_one[:, 2] != 99], target_ids)
    y_1, runs_1 = parse_bnci_events_and_runs(epochs_one, raw_events_one, full_event_id, target_ids, default_n_runs=2)
    assert len(y_1) == 4
    assert np.all(runs_1 >= 0)
    assert set(np.unique(runs_1)) == {0, 1}


def test_stress_fuzzing_random_scenarios():
    """Randomized fuzzing test across 100 arbitrary configurations."""
    rng = np.random.default_rng(42)
    target_ids = {"769": 1, "770": 2}

    for trial_idx in range(100):
        n_trials = rng.integers(1, 150)
        has_markers = rng.choice([True, False])
        n_markers = rng.integers(0, 8) if has_markers else 0

        trial_samples = np.sort(rng.choice(np.arange(100, 200000), size=n_trials, replace=False))
        trial_codes = rng.choice([1, 2], size=n_trials)

        trial_events = np.column_stack([trial_samples, np.zeros(n_trials, dtype=int), trial_codes])

        if n_markers >= 2:
            marker_samples = np.sort(rng.choice(np.arange(50, 200000), size=n_markers, replace=False))
            marker_events = np.column_stack([marker_samples, np.zeros(n_markers, dtype=int), np.full(n_markers, 99)])
            all_events = np.vstack([trial_events, marker_events])
            # Sort chronologically as MNE does
            all_events = all_events[np.argsort(all_events[:, 0])]
            event_id = {"769": 1, "770": 2, "32766": 99}
        else:
            all_events = trial_events
            event_id = {"769": 1, "770": 2}

        epochs = _create_mock_epochs(trial_events, target_ids)
        default_runs = rng.integers(1, 7)

        y, runs = parse_bnci_events_and_runs(epochs, all_events, event_id, target_ids, default_n_runs=default_runs)

        assert len(y) == len(epochs.events)
        assert len(runs) == len(epochs.events)
        assert set(np.unique(y)).issubset({0, 1}), f"Fuzz iteration {trial_idx}: invalid y {y}"
        assert np.all(runs >= 0), f"Fuzz iteration {trial_idx}: negative run ID found {runs}"
        assert issubclass(y.dtype.type, (np.integer, int))
        assert issubclass(runs.dtype.type, (np.integer, int))


def test_stress_empty_events():
    """Stress-test zero trials / empty event array."""
    import types
    target_ids = {"769": 1, "770": 2}
    empty_events = np.zeros((0, 3), dtype=int)
    mock_epochs = types.SimpleNamespace(events=empty_events)

    y, runs = parse_bnci_events_and_runs(mock_epochs, empty_events, target_ids, target_ids, default_n_runs=6)
    assert len(y) == 0
    assert len(runs) == 0
    assert issubclass(y.dtype.type, (np.integer, int))
    assert issubclass(runs.dtype.type, (np.integer, int))


def test_stress_large_recording():
    """Stress-test large recording with 10,000 trials."""
    n_trials = 10000
    events = np.zeros((n_trials, 3), dtype=int)
    events[:, 0] = np.arange(10, 10 + n_trials * 10, 10)
    events[:, 2] = [1 if i % 2 == 0 else 2 for i in range(n_trials)]
    target_ids = {"769": 1, "770": 2}
    epochs = _create_mock_epochs(events, target_ids)

    y, runs = parse_bnci_events_and_runs(epochs, events, target_ids, target_ids, default_n_runs=6)
    assert len(y) == n_trials
    assert len(runs) == n_trials
    assert set(np.unique(runs)) == {0, 1, 2, 3, 4, 5}
    assert np.all(runs >= 0)


if __name__ == "__main__":
    print("Running BNCI Stress & Fuzzing Harness...")
    test_stress_direct_integer_triggers()
    print("  [PASS] Direct integer triggers")
    test_stress_mne_mapped_event_ids()
    print("  [PASS] MNE mapped event IDs")
    test_stress_uneven_trial_numbers()
    print("  [PASS] Uneven trial counts")
    test_stress_single_class_only()
    print("  [PASS] Single-class only recordings")
    test_stress_gdf_marker_variations()
    print("  [PASS] GDF marker variations & case insensitivity")
    test_stress_boundary_marker_edge_cases()
    print("  [PASS] Boundary marker edge cases (early/exact/late)")
    test_stress_single_or_zero_markers()
    print("  [PASS] Single / zero run markers fallback")
    test_stress_empty_events()
    print("  [PASS] Empty events (zero trials)")
    test_stress_large_recording()
    print("  [PASS] Large recording (10,000 trials)")
    test_stress_fuzzing_random_scenarios()
    print("  [PASS] 100 randomized fuzzing iterations")
    print("ALL EMPIRICAL TESTS PASSED SUCCESSFULLY!")
