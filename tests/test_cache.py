
import numpy as np
import pytest

from emi.cache import (
    CACHE_SCHEMA_VERSION,
    load_cache,
    save_cache,
)


def example_data():
    rng = np.random.default_rng(42)
    X = rng.normal(size=(8, 4, 20)).astype(np.float32)
    y = np.array([0, 1] * 4)
    runs = np.repeat([0, 1], 4)
    times = np.arange(20) / 100.0
    sessions = np.zeros(8, dtype=int)
    order = np.arange(8)

    return X, y, runs, times, sessions, order


def save_example(path, **overrides):
    X, y, runs, times, sessions, order = example_data()

    values = {
        "X": X,
        "y": y,
        "runs": runs,
        "times": times,
        "subject": 1,
        "dataset": "test",
        "sessions": sessions,
        "order": order,
    }
    values.update(overrides)

    np.savez_compressed(path, **values)


def test_cache_round_trip_includes_provenance(tmp_path):
    path = tmp_path / "subject.npz"
    X, y, runs, times, sessions, order = example_data()

    save_cache(
        path, X, y, runs, times, subject=1, dataset="test",
        sessions=sessions, order=order, sfreq=100,
        ch_names=["C3", "C4", "Cz", "Pz"],
        extra={"source": "unit_test"},
    )

    result = load_cache(path)

    np.testing.assert_allclose(result["X"], X)
    np.testing.assert_array_equal(result["y"], y)
    np.testing.assert_array_equal(result["runs"], runs)
    np.testing.assert_array_equal(result["sessions"], sessions)
    np.testing.assert_array_equal(result["order"], order)
    np.testing.assert_allclose(result["times"], times)

    assert result["subject"] == 1
    assert result["dataset"] == "test"
    assert result["sfreq"] == 100
    assert result["ch_names"] == ["C3", "C4", "Cz", "Pz"]
    assert result["extra"]["source"] == "unit_test"

    assert result["cache_schema_version"] == CACHE_SCHEMA_VERSION
    assert result["provenance"]["emi_version"]
    assert result["provenance"]["python_version"]
    assert result["provenance"]["numpy_version"]


def test_legacy_cache_without_new_metadata_remains_readable(tmp_path):
    path = tmp_path / "legacy.npz"
    X, y, runs, times, _, _ = example_data()

    np.savez_compressed(
        path,
        X=X,
        y=y,
        runs=runs,
        times=times,
        subject=7,
    )

    result = load_cache(path)

    assert result["subject"] == 7
    assert result["cache_schema_version"] == 1
    assert result["provenance"] == {}
    assert result["dataset"] == "physionet"
    assert result["sessions"].shape == (8,)
    assert result["order"].shape == (8,)


def test_save_rejects_non_binary_labels(tmp_path):
    X, y, runs, times, sessions, order = example_data()
    y[0] = 2

    with pytest.raises(ValueError, match="binary"):
        save_cache(
            tmp_path / "bad.npz", X, y, runs, times,
            subject=1, dataset="test",
            sessions=sessions, order=order,
        )


@pytest.mark.parametrize("bad_label", [256, -256, 1.5])
def test_save_rejects_labels_before_int8_conversion(tmp_path, bad_label):
    X, y, runs, times, sessions, order = example_data()
    y = y.astype(float)
    y[0] = bad_label

    with pytest.raises(ValueError, match="binary"):
        save_cache(
            tmp_path / "bad.npz", X, y, runs, times,
            subject=1, dataset="test",
            sessions=sessions, order=order,
        )


def test_save_rejects_non_finite_eeg(tmp_path):
    X, y, runs, times, sessions, order = example_data()
    X[0, 0, 0] = np.nan

    with pytest.raises(ValueError, match="NaN or infinite"):
        save_cache(
            tmp_path / "bad.npz", X, y, runs, times,
            subject=1, dataset="test",
            sessions=sessions, order=order,
        )


def test_save_rejects_mismatched_sessions(tmp_path):
    X, y, runs, times, _, order = example_data()

    with pytest.raises(ValueError, match="sessions"):
        save_cache(
            tmp_path / "bad.npz", X, y, runs, times,
            subject=1, dataset="test",
            sessions=np.zeros(3), order=order,
        )


def test_save_rejects_non_integer_runs(tmp_path):
    X, y, runs, times, sessions, order = example_data()
    runs = runs.astype(float)
    runs[0] = 0.5

    with pytest.raises(ValueError, match="integer"):
        save_cache(
            tmp_path / "bad.npz", X, y, runs, times,
            subject=1, dataset="test",
            sessions=sessions, order=order,
        )


def test_save_preserves_large_run_identifiers(tmp_path):
    path = tmp_path / "large_runs.npz"
    X, y, runs, times, sessions, order = example_data()
    runs = np.where(runs == 0, 40000, 50000)

    save_cache(
        path, X, y, runs, times,
        subject=1, dataset="test",
        sessions=sessions, order=order,
    )

    result = load_cache(path)
    np.testing.assert_array_equal(result["runs"], runs)


def test_save_rejects_non_integer_sessions(tmp_path):
    X, y, runs, times, sessions, order = example_data()
    sessions = sessions.astype(float)
    sessions[0] = 0.5

    with pytest.raises(ValueError, match="integer"):
        save_cache(
            tmp_path / "bad.npz", X, y, runs, times,
            subject=1, dataset="test",
            sessions=sessions, order=order,
        )


def test_save_preserves_large_session_identifiers(tmp_path):
    path = tmp_path / "large_sessions.npz"
    X, y, runs, times, sessions, order = example_data()
    sessions[:] = 40000

    save_cache(
        path, X, y, runs, times,
        subject=1, dataset="test",
        sessions=sessions, order=order,
    )

    result = load_cache(path)
    np.testing.assert_array_equal(result["sessions"], sessions)


def test_save_rejects_non_integer_order(tmp_path):
    X, y, runs, times, sessions, order = example_data()
    order = order.astype(float)
    order[0] = 0.5

    with pytest.raises(ValueError, match="integer"):
        save_cache(
            tmp_path / "bad.npz", X, y, runs, times,
            subject=1, dataset="test",
            sessions=sessions, order=order,
        )


def test_load_rejects_non_integer_order(tmp_path):
    path = tmp_path / "bad_order.npz"
    X, y, runs, times, sessions, order = example_data()
    order = order.astype(float)
    order[0] = 0.5

    save_example(path, order=order)

    with pytest.raises(ValueError, match="integer"):
        load_cache(path)


def test_save_rejects_non_increasing_times(tmp_path):
    X, y, runs, times, sessions, order = example_data()
    times[5] = times[4]

    with pytest.raises(ValueError, match="strictly increasing"):
        save_cache(
            tmp_path / "bad.npz", X, y, runs, times,
            subject=1, dataset="test",
            sessions=sessions, order=order,
        )


def test_load_rejects_non_increasing_times(tmp_path):
    path = tmp_path / "bad_times.npz"
    X, y, runs, times, sessions, order = example_data()
    times[5] = times[4]

    save_example(path, times=times)

    with pytest.raises(ValueError, match="strictly increasing"):
        load_cache(path)


def test_save_rejects_invalid_sampling_frequency(tmp_path):
    X, y, runs, times, sessions, order = example_data()

    with pytest.raises(ValueError, match="sampling frequency"):
        save_cache(
            tmp_path / "bad.npz", X, y, runs, times,
            subject=1, dataset="test",
            sessions=sessions, order=order, sfreq=0,
        )


def test_save_rejects_non_json_serializable_metadata(tmp_path):
    X, y, runs, times, sessions, order = example_data()

    with pytest.raises(ValueError, match="JSON serializable"):
        save_cache(
            tmp_path / "bad.npz", X, y, runs, times,
            subject=1, dataset="test",
            sessions=sessions, order=order,
            extra={"invalid": object()},
        )


def test_load_rejects_unsupported_future_schema(tmp_path):
    path = tmp_path / "future_schema.npz"

    save_example(
        path,
        cache_schema_version=np.array(CACHE_SCHEMA_VERSION + 1),
    )

    with pytest.raises(ValueError, match="Unsupported cache schema"):
        load_cache(path)


def test_load_rejects_non_binary_labels(tmp_path):
    path = tmp_path / "bad_labels.npz"
    X, y, runs, times, sessions, order = example_data()
    y = y.astype(int)
    y[0] = 2

    save_example(path, y=y)

    with pytest.raises(ValueError, match="binary"):
        load_cache(path)

@pytest.mark.parametrize(
    "bad_X",
    [
        np.ones((8, 4, 20), dtype=bool),
        np.full((8, 4, 20), "1.5"),
    ],
)
def test_save_rejects_non_real_eeg_types(tmp_path, bad_X):
    _, y, runs, times, sessions, order = example_data()

    with pytest.raises(ValueError, match="numeric"):
        save_cache(
            tmp_path / "bad.npz", bad_X, y, runs, times,
            subject=1, dataset="test",
            sessions=sessions, order=order,
        )


@pytest.mark.parametrize("field", ["runs", "sessions", "order"])
def test_save_rejects_boolean_identifiers(tmp_path, field):
    X, y, runs, times, sessions, order = example_data()

    values = {
        "runs": runs,
        "sessions": sessions,
        "order": order,
    }
    values[field] = np.zeros(8, dtype=bool)

    with pytest.raises(ValueError):
        save_cache(
            tmp_path / "bad.npz", X, y, times=times,
            runs=values["runs"], subject=1, dataset="test",
            sessions=values["sessions"], order=values["order"],
        )


@pytest.mark.parametrize("bad_extra", [["not", "a", "dictionary"], 42, "text"])
def test_save_rejects_non_dictionary_extra(tmp_path, bad_extra):
    X, y, runs, times, sessions, order = example_data()

    with pytest.raises(ValueError, match="dictionary"):
        save_cache(
            tmp_path / "bad.npz", X, y, runs, times,
            subject=1, dataset="test",
            sessions=sessions, order=order,
            extra=bad_extra,
        )


@pytest.mark.parametrize("bad_subject", [1.5, True])
def test_save_rejects_invalid_subject_id(tmp_path, bad_subject):
    X, y, runs, times, sessions, order = example_data()

    with pytest.raises(ValueError, match="subject"):
        save_cache(
            tmp_path / "bad.npz", X, y, runs, times,
            subject=bad_subject, dataset="test",
            sessions=sessions, order=order,
        )


def test_load_rejects_non_integer_subject_id(tmp_path):
    path = tmp_path / "bad_subject.npz"
    X, y, runs, times, sessions, order = example_data()

    save_example(path, subject=1.5)

    with pytest.raises(ValueError, match="subject"):
        load_cache(path)