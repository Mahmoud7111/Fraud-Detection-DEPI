"""
Tests for src/features.py (Contract C5).
Owner: Dev C   Reviewer: Dev D

Run:
    pytest tests/test_features.py
"""
import pandas as pd
import numpy as np
import pytest

RAW_ID_COLS = {"user_id", "device_id", "ip_address", "ip_int"}
REQUIRED_FEATURE_COLS = {
    "transaction_id", "class", "split",
    "seconds_since_signup", "hour_of_day", "day_of_week",
    "purchase_value", "age", "sex_male",
    "ip_lookup_ok", "cpi_matched",
}


def _make_merged_df(n=20):
    """Create a minimal merged DataFrame for feature tests."""
    import datetime
    base = datetime.datetime(2015, 1, 1)
    rows = []
    for i in range(n):
        signup   = base + datetime.timedelta(hours=i * 10)
        purchase = signup + datetime.timedelta(hours=i + 1)
        rows.append({
            "transaction_id": i,
            "user_id":        i % 5,
            "signup_time":    pd.Timestamp(signup, tz="UTC"),
            "purchase_time":  pd.Timestamp(purchase, tz="UTC"),
            "purchase_value": float(10 + i),
            "device_id":      f"dev_{i % 3}",
            "source":         "Ads",
            "browser":        "Chrome",
            "sex":            "M",
            "age":            25 + (i % 20),
            "ip_address":     float(16777216 + i),
            "ip_int":         16777216 + i,
            "class":          i % 7 == 0,
            "split":          "train",
            "lookup_status":  "success",
            "country":        "United States",
            "country_code":   "US",
            "proxy":          False,
            "hosting":        False,
            "ip_lookup_ok":   True,
            "cpi_score":      55.0,
            "cpi_year":       2015,
            "cpi_matched":    True,
        })
    return pd.DataFrame(rows)


class TestBuildFeatures:
    def test_no_raw_id_columns(self):
        """Feature output must not contain raw ID columns."""
        from src.features import build_features
        df = _make_merged_df()
        out = build_features(df)
        leaked = RAW_ID_COLS & set(out.columns)
        assert not leaked, f"Raw ID columns leaked into features: {leaked}"

    def test_required_columns_present(self):
        from src.features import build_features
        df = _make_merged_df()
        out = build_features(df)
        missing = REQUIRED_FEATURE_COLS - set(out.columns)
        assert not missing, f"Missing feature columns: {missing}"

    def test_row_count_preserved(self):
        from src.features import build_features
        df = _make_merged_df(30)
        out = build_features(df)
        assert len(out) == 30

    def test_seconds_since_signup_non_negative(self):
        from src.features import build_features
        df = _make_merged_df()
        out = build_features(df)
        assert (out["seconds_since_signup"] >= 0).all()

    def test_binary_columns_are_0_or_1(self):
        from src.features import build_features
        df = _make_merged_df()
        out = build_features(df)
        for col in ["sex_male", "ip_lookup_ok", "cpi_matched", "is_proxy", "is_hosting"]:
            assert set(out[col].unique()).issubset({0, 1}), \
                f"Column {col!r} has non-binary values: {out[col].unique()}"

    def test_hour_of_day_range(self):
        from src.features import build_features
        df = _make_merged_df()
        out = build_features(df)
        assert out["hour_of_day"].between(0, 23).all()

    def test_day_of_week_range(self):
        from src.features import build_features
        df = _make_merged_df()
        out = build_features(df)
        assert out["day_of_week"].between(0, 6).all()


class TestPointInTimeCounts:
    def test_counts_use_only_prior_users(self):
        """A row must never count users who appear at a later purchase_time."""
        from src.features import build_features
        # device = dev_{i%3}, user = i%5, purchase_time increases with i
        df = _make_merged_df(6)
        out = build_features(df)
        # i=0..2: first user on each device -> 1
        # i=3..5: second user on dev_0/dev_1/dev_2 -> 2
        assert out["users_per_device"].tolist() == [1, 1, 1, 2, 2, 2]

    def test_counts_do_not_depend_on_split_labels(self):
        """Counts are a function of arrival order only, not of the split column."""
        from src.features import build_features
        df = _make_merged_df(9)
        as_is = build_features(df)["users_per_device"].tolist()

        flipped = _make_merged_df(9)
        flipped["split"] = "test"
        assert build_features(flipped)["users_per_device"].tolist() == as_is

    def test_unique_ip_counts_stay_at_one(self):
        from src.features import build_features
        df = _make_merged_df(10)   # every ip_int is distinct
        out = build_features(df)
        assert (out["users_per_ip"] == 1).all()


class TestCategoryGuard:
    def test_unknown_source_raises(self):
        from src.features import build_features
        df = _make_merged_df(3)
        df.loc[0, "source"] = "SEO"          # wrong casing
        with pytest.raises(ValueError, match="source"):
            build_features(df)

    def test_unknown_browser_raises(self):
        from src.features import build_features
        df = _make_merged_df(3)
        df.loc[0, "browser"] = "Edge"
        with pytest.raises(ValueError, match="browser"):
            build_features(df)
