"""Tests for utility functions."""

import pytest

from provisioner.utils import (
    detect_vendor,
    format_mac,
    get_mac_oui,
    model_to_vendor,
    normalize_mac,
)


class TestNormalizeMac:
    """Tests for MAC address normalization."""
    
    def test_no_separators(self):
        assert normalize_mac("001565123456") == "001565123456"
    
    def test_colons(self):
        assert normalize_mac("00:15:65:12:34:56") == "001565123456"
    
    def test_dashes(self):
        assert normalize_mac("00-15-65-12-34-56") == "001565123456"
    
    def test_dots(self):
        assert normalize_mac("0015.6512.3456") == "001565123456"
    
    def test_uppercase(self):
        assert normalize_mac("00:15:65:AB:CD:EF") == "001565abcdef"
    
    def test_mixed_case(self):
        assert normalize_mac("00:15:65:aB:cD:eF") == "001565abcdef"
    
    def test_whitespace(self):
        assert normalize_mac("  00:15:65:12:34:56  ") == "001565123456"
    
    def test_invalid_length(self):
        with pytest.raises(ValueError):
            normalize_mac("00:15:65:12:34")
    
    def test_invalid_characters(self):
        with pytest.raises(ValueError):
            normalize_mac("00:15:65:GH:IJ:KL")


class TestFormatMac:
    """Tests for MAC address formatting."""
    
    def test_colons(self):
        assert format_mac("001565123456", ":") == "00:15:65:12:34:56"
    
    def test_dashes(self):
        assert format_mac("001565123456", "-") == "00-15-65-12-34-56"
    
    def test_dots(self):
        assert format_mac("001565123456", ".") == "0015.6512.3456"
    
    def test_no_separator(self):
        assert format_mac("00:15:65:12:34:56", "") == "001565123456"
    
    def test_uppercase(self):
        assert format_mac("001565abcdef", ":", True) == "00:15:65:AB:CD:EF"


class TestGetMacOui:
    """Tests for OUI extraction."""
    
    def test_basic(self):
        assert get_mac_oui("001565123456") == "001565"
    
    def test_with_separators(self):
        assert get_mac_oui("00:15:65:12:34:56") == "001565"
    
    def test_uppercase_output(self):
        assert get_mac_oui("0c383eabcdef") == "0C383E"


class TestDetectVendor:
    """Tests for vendor detection from MAC OUI."""
    
    @pytest.fixture
    def oui_map(self):
        return {
            "yealink": ["001565", "805E0C"],
            "fanvil": ["0C383E"],
        }
    
    def test_yealink(self, oui_map):
        assert detect_vendor("00:15:65:12:34:56", oui_map) == "yealink"
    
    def test_fanvil(self, oui_map):
        assert detect_vendor("0C:38:3E:AB:CD:EF", oui_map) == "fanvil"
    
    def test_unknown(self, oui_map):
        assert detect_vendor("AA:BB:CC:DD:EE:FF", oui_map) is None


class TestModelToVendor:
    """Tests for vendor extraction from model name."""
    
    def test_yealink(self):
        assert model_to_vendor("yealink_t23g") == "yealink"
        assert model_to_vendor("YEALINK_T46S") == "yealink"
    
    def test_fanvil(self):
        assert model_to_vendor("fanvil_v64") == "fanvil"
        assert model_to_vendor("FANVIL_X6U") == "fanvil"
    
    def test_unknown(self):
        assert model_to_vendor("cisco_7940") is None
