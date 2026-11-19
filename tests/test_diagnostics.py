"""
Tests for src/diagnostics.py (data-quality flags — NOT model features).

Owner: Dev A

Run:
    pytest tests/test_diagnostics.py
"""
import datetime

import pandas as pd
import pytest

from src.diagnostics import cohort_flags, cohort_report, instant_purchase_flag
from src.features import build_features
from tests.test_features import _make_merged_df


def _make_df(rows):
    """rows = list of (device_id, ip_int, gap_seconds, class)."""
    base = datetime.datetime(2015, 1, 1)
    out = []
    for i, (device, ip, gap, label) in enumerate(rows):
        signup = pd.Timestamp(base + datetime.timedelta(hours=i), tz="UTC")
        out.append({
            "transaction_id": i,
            "signup_time": signup,
            "purchase_time": signup + pd.Timedelta(seconds=gap),
            "device_id": device,
            "ip_int": ip,
            "class": label,
        })
    return pd.DataFrame(out)


class TestInstantPurchaseFlag:
    def test_flags_exactly_one_second(self):
        df = _make_df([
            ("d1", 1, 1, 1),
            ("d2", 2, 2, 0),
            ("d3", 3, 0, 0),
            ("d4", 4, 3600, 0),
        ])
        assert instant_purchase_flag(df).tolist() == [True, False, False, False]

    def test_returns_boolean_series(self):
        df = _make_df([("d1", 1, 1, 1)])
        flag = instant_purchase_flag(df)
        assert str(flag.dtype) == "bool"
        assert flag.index.equals(df.index)

    def test_unparseable_timestamps_are_false_not_error(self):
        df = _make_df([("d1", 1, 1, 1), ("d2", 2, 5, 0)])
        df["signup_time"] = df["signup_time"].astype(object)
        df.loc[1, "signup_time"] = "not-a-date"
        assert instant_purchase_flag(df).tolist() == [True, False]

    def test_works_on_unsorted_input(self):
        df = _make_df([("d1", 1, 1, 1), ("d2", 2, 9, 0), ("d3", 3, 1, 1)])
        df = df.iloc[[2, 0, 1]]
        assert instant_purchase_flag(df).tolist() == [True, True, False]

    def test_mixed_timezone_input_is_handled(self):
        """One naive + one aware timestamp must not raise."""
        df = _make_df([("d1", 1, 1, 1)])
        df["signup_time"] = df["signup_time"].dt.tz_localize(None)
        assert instant_purchase_flag(df).tolist() == [True]


class TestCohortFlags:
    def test_burst_rows_are_exclusive(self):
        """A burst row must not also be labelled as an echo row."""
        df = _make_df([
            ("d1", 1, 1, 1),      # burst
            ("d1", 1, 1, 1),      # burst, same device
            ("d1", 1, 500, 0),    # non-burst, shares the burst device -> echo
            ("d9", 9, 500, 0),    # unrelated
        ])
        flags = cohort_flags(df)
        assert flags["is_instant_purchase"].tolist() == [1, 1, 0, 0]
        assert flags["device_in_burst"].tolist() == [0, 0, 1, 0]
        assert flags["ip_in_burst"].tolist() == [0, 0, 1, 0]

    def test_flags_are_binary(self):
        df = _make_df([("d1", 1, 1, 1), ("d2", 2, 42, 0)])
        flags = cohort_flags(df)
        for col in flags.columns:
            assert set(flags[col].unique()).issubset({0, 1})

    def test_missing_key_columns_raise(self):
        df = _make_df([("d1", 1, 1, 1)]).drop(columns=["ip_int"])
        with pytest.raises(KeyError, match="ip_int"):
            cohort_flags(df)


class TestCohortReport:
    def test_rows_partition_the_dataset(self):
        df = _make_df([
            ("d1", 1, 1, 1),
            ("d1", 1, 500, 0),
            ("d2", 2, 600, 0),
        ])
        report = cohort_report(df)
        cohorts = report.drop(index="all")
        assert cohorts["n"].sum() == len(df)
        assert int(report.loc["all", "n"]) == len(df)
        assert int(report.loc["all", "positives"]) == int(df["class"].sum())

    def test_reports_fraud_rate_per_cohort(self):
        df = _make_df([
            ("d1", 1, 1, 1),
            ("d1", 1, 1, 1),
            ("d1", 1, 900, 0),
            ("d2", 2, 900, 0),
        ])
        report = cohort_report(df)
        assert report.loc["burst", "positives"] == 2
        assert report.loc["burst", "rate_pct"] == 100.0
        assert report.loc["burst_echo", "n"] == 1
        assert report.loc["unaffected", "n"] == 1

    def test_missing_target_raises(self):
        df = _make_df([("d1", 1, 1, 1)]).drop(columns=["class"])
        with pytest.raises(KeyError, match="class"):
            cohort_report(df)


class TestContractBoundary:
    def test_build_features_does_not_emit_diagnostic_columns(self):
        """The diagnostic flags must never leak into the C5 feature table."""
        out = build_features(_make_merged_df(10))
        forbidden = {"is_instant_purchase", "device_in_burst", "ip_in_burst"}
        assert not (forbidden & set(out.columns))
        assert out.shape[1] - 3 == 19, "features.csv must stay at 19 features"
