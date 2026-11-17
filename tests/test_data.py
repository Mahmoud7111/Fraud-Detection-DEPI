"""
Tests for data contracts C1 and C4: load_raw() and the merged dataset.
Owner: Dev C   Reviewer: Dev D

Uses tests/fixtures/sample_transactions.csv (200 rows) — never the full data.

Run:
    pytest tests/test_data.py
"""
import pandas as pd
import pytest
from src.common.io import load_raw
from src.config import SAMPLE_TRANSACTIONS

RAW_COLS = {
    "transaction_id", "user_id", "signup_time", "purchase_time",
    "purchase_value", "device_id", "source", "browser", "sex",
    "age", "ip_address", "class",
}

MERGED_REQUIRED_COLS = {
    "transaction_id", "class",
    "ip_lookup_ok", "cpi_matched",
}


class TestLoadRaw:
    def test_returns_dataframe(self):
        df = load_raw(path=SAMPLE_TRANSACTIONS)
        assert isinstance(df, pd.DataFrame)

    def test_has_transaction_id(self):
        df = load_raw(path=SAMPLE_TRANSACTIONS)
        assert "transaction_id" in df.columns

    def test_transaction_id_is_zero_based(self):
        df = load_raw(path=SAMPLE_TRANSACTIONS)
        assert df["transaction_id"].iloc[0] == 0
        assert df["transaction_id"].iloc[-1] == len(df) - 1

    def test_all_expected_columns_present(self):
        df = load_raw(path=SAMPLE_TRANSACTIONS)
        missing = RAW_COLS - set(df.columns)
        assert not missing, f"Missing columns: {missing}"

    def test_class_binary(self):
        df = load_raw(path=SAMPLE_TRANSACTIONS)
        assert set(df["class"].unique()).issubset({0, 1})

    def test_no_negative_purchase_value(self):
        df = load_raw(path=SAMPLE_TRANSACTIONS)
        assert (df["purchase_value"] >= 0).all()

    def test_row_count_matches_fixture(self):
        df = load_raw(path=SAMPLE_TRANSACTIONS)
        assert len(df) == 200, f"Expected 200 fixture rows, got {len(df)}"


class TestMergedRowCount:
    """The merged dataset must not silently drop rows (Contract C4)."""

    def test_row_count_preserved_after_ip_merge(self):
        """Simulate a left-join and assert no rows are added or removed."""
        df = pd.DataFrame({"transaction_id": range(10), "ip_int": range(10)})
        ip_lookup = pd.DataFrame({
            "ip_int":        [0, 1, 2],   # only 3 of 10 found
            "lookup_status": ["success"] * 3,
            "country":       ["US", "DE", "FR"],
            "country_code":  ["US", "DE", "FR"],
            "proxy":         [False] * 3,
            "hosting":       [False] * 3,
        })
        merged = df.merge(
            ip_lookup[["ip_int", "lookup_status", "country", "country_code", "proxy", "hosting"]],
            on="ip_int",
            how="left",
        )
        assert len(merged) == len(df), (
            "Left-join must preserve all rows. "
            f"Before: {len(df)}, after: {len(merged)}"
        )
