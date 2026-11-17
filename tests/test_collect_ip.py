"""
Tests for src/collect/ip_lookup.py and src/common/ips.py.
Owner: Dev A   Reviewer: Dev C

Run:
    pytest tests/test_collect_ip.py
"""
import pandas as pd
import pytest
from src.common.ips import float_to_ip_int, ip_int_to_str, series_to_ip_int, series_to_ip_str


class TestIpConversion:
    def test_float_to_int_round_trip(self):
        """Integer cast of a whole float must be exact."""
        assert float_to_ip_int(732758369.0) == 732758369

    def test_ip_int_to_str_known(self):
        """Known IP integer → dotted-quad mapping."""
        # 2130706433 = 127.0.0.1
        assert ip_int_to_str(2130706433) == "127.0.0.1"

    def test_ip_int_to_str_loopback(self):
        assert ip_int_to_str(16777343) == "1.0.0.127"  # 0x0100007F

    def test_series_to_ip_int_dtype(self):
        s = pd.Series([732758369.0, 2130706433.0])
        result = series_to_ip_int(s)
        assert result.dtype.name == "int64"
        assert list(result) == [732758369, 2130706433]

    def test_series_to_ip_str(self):
        s = pd.Series([2130706433.0])
        result = series_to_ip_str(s)
        assert result.iloc[0] == "127.0.0.1"

    def test_zero_ip_converts(self):
        """Zero is technically invalid but should not raise."""
        assert float_to_ip_int(0.0) == 0

    def test_max_ipv4(self):
        """Max IPv4 (255.255.255.255 = 4294967295) must round-trip."""
        assert ip_int_to_str(4294967295) == "255.255.255.255"
