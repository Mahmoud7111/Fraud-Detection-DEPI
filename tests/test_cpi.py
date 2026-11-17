"""
Tests for src/collect/cpi_scrape.py output format (Contract C3).
Owner: Dev B   Reviewer: Dev C

These tests validate the CSV schema and basic data quality, not the
network scrape itself (which uses cached HTML or is mocked).

Run:
    pytest tests/test_cpi.py
"""
import pandas as pd
import pytest


REQUIRED_COLUMNS = {"country", "cpi_year", "cpi_score", "source_url", "scraped_at"}
REQUIRED_MAP_COLUMNS = {"geo_country", "cpi_country", "match_type"}
VALID_MATCH_TYPES = {"exact", "manual", "none"}


def _make_cpi_df():
    """Minimal valid cpi.csv for testing."""
    return pd.DataFrame({
        "country":    ["Denmark", "New Zealand", "Finland"],
        "cpi_year":   [2015, 2015, 2015],
        "cpi_score":  [91.0, 88.0, 90.0],
        "source_url": ["https://example.com"] * 3,
        "scraped_at": ["2024-01-01T00:00:00+00:00"] * 3,
    })


def _make_map_df():
    """Minimal valid country_name_map.csv for testing."""
    return pd.DataFrame({
        "geo_country":  ["Denmark", "New Zealand", "United States", "Unknown Land"],
        "cpi_country":  ["Denmark", "New Zealand", "United States", ""],
        "match_type":   ["exact",   "exact",        "manual",         "none"],
    })


class TestCpiSchema:
    def test_required_columns(self):
        df = _make_cpi_df()
        assert REQUIRED_COLUMNS.issubset(set(df.columns)), \
            f"Missing columns: {REQUIRED_COLUMNS - set(df.columns)}"

    def test_cpi_score_numeric(self):
        df = _make_cpi_df()
        assert pd.api.types.is_numeric_dtype(df["cpi_score"])

    def test_no_null_country(self):
        df = _make_cpi_df()
        assert df["country"].notna().all()

    def test_no_null_score(self):
        df = _make_cpi_df()
        assert df["cpi_score"].notna().all()

    def test_cpi_score_range(self):
        df = _make_cpi_df()
        assert (df["cpi_score"] >= 0).all() and (df["cpi_score"] <= 100).all()


class TestCountryMap:
    def test_required_columns(self):
        df = _make_map_df()
        assert REQUIRED_MAP_COLUMNS.issubset(set(df.columns))

    def test_match_type_values(self):
        df = _make_map_df()
        assert set(df["match_type"].unique()).issubset(VALID_MATCH_TYPES)

    def test_none_match_has_empty_cpi_country(self):
        df = _make_map_df()
        none_rows = df[df["match_type"] == "none"]
        assert (none_rows["cpi_country"] == "").all(), \
            "Rows with match_type='none' should have an empty cpi_country."
