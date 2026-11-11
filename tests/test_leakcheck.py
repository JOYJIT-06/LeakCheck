"""LeakCheck logic tests. They use a numpy CSP stand-in, so they run without MNE."""
import numpy as np
import pandas as pd

from emi import leakcheck as lc
from emi.decoders import ChannelSelector, DECODERS
from emi.signal_utils import parse_run_lengths, trial_run_ids
from tests.helpers import csp_factory, make_data


def _scores(designs, **kw):
    X, y, runs, times = make_data(**kw)
    df = lc.audit_subject(X, y, runs, times, subject=1, csp_factory=csp_factory, designs=designs,
                          n_null=0, n_repeats=2, n_repeats_matched=3)
    return df.set_index("design")["acc_pooled"].to_dict(), df


def test_channel_selector_finds_informative_channels():
    X, y, runs, times = make_data(n_ch=16)
    sel = ChannelSelector(n_keep=4).fit(X, y)
    assert 0 in sel.idx_ and 1 in sel.idx_
    assert sel.transform(X).shape == (X.shape[0], 4, X.shape[2])


def test_every_design_runs_and_informative_data_is_decoded():
    designs = [d for d in lc.PRESETS["full"] if not d.startswith("D6")]
    s, df = _scores(designs, informative=True, per_run=16)
    assert set(s) == set(designs)
    for d, acc in s.items():
        assert 0.0 <= acc <= 1.0, d
    assert s["D3_loro"] > 0.8 and s["P4_select_inside@0"] > 0.8


def test_session_design_is_skipped_without_two_sessions():
    s, df = _scores(["D3_loro", "D6_loso_session"])
    assert "D6_loso_session" not in s and "D3_loro" in s


def test_p1_is_skipped_for_decoders_without_csp():
    X, y, runs, times = make_data()
    spec = DECODERS["ts_lr"]
    try:
        import pyriemann  # noqa: F401
    except ImportError:
        # the design must still be reported as not applicable before the decoder is even built
        df = lc.audit_subject(X, y, runs, times, 1, csp_factory, designs=["P1_csp_on_all"],
                              decoders=("ts_lr",), n_null=0)
        assert df.empty
        return
    assert not spec.uses_csp


def test_clean_designs_are_near_chance_on_pure_noise_negative_control():
    accs = []
    for seed in range(6):
        X, y, runs, times = make_data(informative=False, seed=seed)
        for kind in ("perm", "shift"):
            df = lc.audit_subject(X, y, runs, times, seed, csp_factory, designs=["D3_loro", "D1m_matched_k"],
                                  n_null=2, null_types=(kind,), n_repeats=2)
            accs.extend(df[df["label_type"] != "real"]["acc_pooled"].tolist())
    assert abs(np.mean(accs) - 0.5) < 0.05


def test_injected_leaks_raise_accuracy_on_pure_noise():
    """Positive control. With no signal at all, a leaky design must beat its clean comparator."""
    gaps = {"P1_csp_on_all": [], "P4_select_on_all@64": [], "P5_tune_on_test": []}
    refs = {"P1_csp_on_all": "D3_loro", "P4_select_on_all@64": "P4_select_inside@64", "P5_tune_on_test": "P5_tune_nested"}
    for seed in range(4):
        X, y, runs, times = make_data(informative=False, seed=10 + seed, n_ch=24)
        s, _ = _scores(list(gaps) + list(set(refs.values())), informative=False, seed=10 + seed, n_ch=24)
        for k in gaps:
            gaps[k].append(s[k] - s[refs[k]])
    for k, v in gaps.items():
        assert np.mean(v) > 0.02, (k, v)


def test_audit_output_columns_and_row_counts():
    X, y, runs, times = make_data()
    df = lc.audit_subject(X, y, runs, times, 7, csp_factory, designs=["D3_loro", "D1m_matched_k"],
                          n_null=2, null_types=("perm", "shift"), n_repeats=2)
    for col in ("dataset", "subject", "decoder", "design", "label_type", "perm", "n_trials",
                "acc_pooled", "acc_fold_mean", "bal_acc", "auc", "kappa", "recall_left", "recall_right",
                "n_folds", "n_test_mean", "seconds"):
        assert col in df.columns, col
    assert len(df) == (1 + 2 * 2) * 2                 # (real + 2 perm + 2 shift) x 2 designs
    assert set(df["label_type"]) == {"real", "perm", "shift"}


def test_audit_requires_three_runs_and_both_classes_per_run():
    X, y, runs, times = make_data(n_runs=2)
    for bad in (lambda: lc.audit_subject(X, y, runs, times, 1, csp_factory, designs="quick", n_null=0),):
        try:
            bad()
        except ValueError:
            continue
        raise AssertionError("expected ValueError")


def test_unknown_design_name_is_rejected():
    try:
        lc.resolve_designs("D3_loro,not_a_design")
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_tables_have_expected_structure():
    X, y, runs, times = make_data(per_run=16)
    frames = []
    for s in range(4):
        X, y, runs, times = make_data(seed=s)
        frames.append(lc.audit_subject(X, y, runs, times, s, csp_factory,
                                       designs=["D1s_size_matched", "D3_loro", "P1_csp_on_all"],
                                       n_null=3, n_repeats=2, n_repeats_matched=3))
    df = pd.concat(frames)
    by = lc.inflation_by_subject(df)
    assert set(by["design"]) == {"D1s_size_matched", "P1_csp_on_all"}
    assert by["subject"].nunique() == 4
    tab = lc.inflation_table(by, n_boot=100)
    assert {"hl_pp", "wilcoxon_p", "rank_biserial", "wilcoxon_p_holm", "equivalent"} <= set(tab.columns)
    nt = lc.null_table(df, n_boot=100)
    assert ((nt["false_positive_rate"] >= 0) & (nt["false_positive_rate"] <= 1)).all()
    ep = lc.subject_empirical_p(df)
    assert (ep["empirical_p"] > 0).all() and (ep["empirical_p"] <= 1).all()
    assert ep["n_null"].eq(3).all()


def test_trial_run_ids_from_sample_positions():
    lengths = parse_run_lengths("emi_run_lengths:100,100,100", "emi_run_lengths:")
    assert trial_run_ids([10, 99, 100, 150, 299], lengths, 0).tolist() == [0, 0, 1, 1, 2]
    assert trial_run_ids([510, 600, 700], [100, 100, 100], 500).tolist() == [0, 1, 2]


def test_trial_run_ids_rejects_event_past_the_end_and_missing_tag():
    for fn in (lambda: trial_run_ids([500], [100, 100], 0), lambda: parse_run_lengths("x", "emi_run_lengths:")):
        try:
            fn()
        except ValueError:
            continue
        raise AssertionError("expected ValueError")


# ---- v0.3: table honesty -------------------------------------------------------------------------
def _two_subject_frame(n_null=2, designs=("D1s_size_matched", "D3_loro")):
    parts = []
    for s in (1, 2):
        X, y, runs, times = make_data(seed=s)
        parts.append(lc.audit_subject(X, y, runs, times, subject=s, csp_factory=csp_factory, designs=list(designs),
                                      n_null=n_null, n_repeats=2, n_repeats_matched=2))
    return pd.concat(parts, ignore_index=True)


def test_inflation_by_subject_reports_dropped_subjects(caplog):
    df = _two_subject_frame(n_null=0)
    df.loc[(df["subject"] == 2) & (df["design"] == "D3_loro") & (df["label_type"] == "real"), "acc_pooled"] = np.nan
    with caplog.at_level("WARNING"):
        out = lc.inflation_by_subject(df)
    assert set(out["subject"]) == {1}
    assert out.attrs["dropped_subjects"] and out.attrs["dropped_subjects"][0]["subjects"] == [2]
    assert any("dropped" in r.message for r in caplog.records)


def test_null_table_says_what_the_rate_means():
    tab = lc.null_table(_two_subject_frame(n_null=2), n_boot=50)
    kinds = dict(zip(tab["design"], tab["rate_meaning"]))
    assert kinds["D3_loro"] == "false_positive_rate"
    assert kinds["D1s_size_matched"] == "detection_of_leak"


def test_empirical_p_warns_when_too_few_nulls_for_p05(caplog):
    df = _two_subject_frame(n_null=3)
    with caplog.at_level("WARNING"):
        ep = lc.subject_empirical_p(df)
    assert (ep["min_possible_p"] == 0.25).all()
    assert any("smallest possible p" in r.message for r in caplog.records)


def test_paired_delta_vs_null_has_the_right_shape_and_range():
    import pandas as pd
    frames = []
    for s in range(3):
        X, y, runs, times = make_data(seed=s)
        frames.append(lc.audit_subject(X, y, runs, times, s, csp_factory,
                                       designs=["D1s_size_matched", "D3_loro"], n_null=4,
                                       null_types=("perm", "shift"), n_repeats=2, n_repeats_matched=3))
    out = lc.paired_delta_vs_null(pd.concat(frames))
    assert set(out["null_type"]) == {"perm", "shift"} and out["subject"].nunique() == 3
    assert (out["n_null"] == 4).all() and ((out["empirical_p"] >= 1 / 5) & (out["empirical_p"] <= 1)).all()


def test_audit_records_provenance_columns_and_pairs_fold_seeds():
    X, y, runs, times = make_data()
    df = lc.audit_subject(X, y, runs, times, 1, csp_factory, designs=["D1m_matched_k"], n_null=2,
                          null_types=("perm",), n_repeats=2, csp_name="rank_safe")
    assert (df["csp_impl"] == "rank_safe").all() and (df["n_channels"] == X.shape[1]).all()
    assert df.loc[df.label_type == "real", "label_agreement"].eq(1.0).all()
    assert df["label_hash"].nunique() == 3 and df["base_window"].iloc[0] == "1-3"
