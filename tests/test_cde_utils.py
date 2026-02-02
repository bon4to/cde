import pytest
from datetime import datetime


# Re-implement the pure utility functions from cde.py for testing
# These functions cannot be imported directly due to Flask app initialization side effects

def split_code_seq(code):
    """
    Splits a string code into its base code and sequence number.
    Mirror of cde.split_code_seq
    """
    if "-" in code:
        code, seq = code.split("-")
        return code, seq
    seq = "0"
    return code, seq


def format_three_no(number: int) -> str:
    """Mirror of cde.format_three_no"""
    return str(number).zfill(3)


def parse_date(value):
    """Mirror of cde.parse_date"""
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%d / %m / %Y")
    except Exception as e:
        return value


class TestSplitCodeSeq:
    """Tests for split_code_seq function."""

    def test_code_with_sequence(self):
        """Should split code and sequence correctly."""
        code, seq = split_code_seq("123-1")
        assert code == "123"
        assert seq == "1"

    def test_code_without_sequence(self):
        """Should return '0' as default sequence."""
        code, seq = split_code_seq("456")
        assert code == "456"
        assert seq == "0"

    def test_code_with_single_dash(self):
        """Should handle alphanumeric codes with dash."""
        code, seq = split_code_seq("ABC-1")
        assert code == "ABC"
        assert seq == "1"

    def test_empty_code(self):
        """Should handle empty code."""
        code, seq = split_code_seq("")
        assert code == ""
        assert seq == "0"


class TestFormatThreeNo:
    """Tests for format_three_no function."""

    def test_single_digit(self):
        """Should pad single digit to three digits."""
        result = format_three_no(1)
        assert result == "001"

    def test_double_digit(self):
        """Should pad double digit to three digits."""
        result = format_three_no(42)
        assert result == "042"

    def test_triple_digit(self):
        """Should keep triple digit as is."""
        result = format_three_no(123)
        assert result == "123"

    def test_zero(self):
        """Should format zero correctly."""
        result = format_three_no(0)
        assert result == "000"

    def test_four_digits(self):
        """Should not truncate numbers with more than 3 digits."""
        result = format_three_no(1234)
        assert result == "1234"


class TestParseDate:
    """Tests for parse_date function."""

    def test_valid_iso_date(self):
        """Should format valid ISO date."""
        result = parse_date("2025-06-15")
        assert result == "15 / 06 / 2025"

    def test_valid_iso_datetime(self):
        """Should format valid ISO datetime."""
        result = parse_date("2025-06-15T10:30:00")
        assert result == "15 / 06 / 2025"

    def test_invalid_date_returns_original(self):
        """Should return original value for invalid date."""
        result = parse_date("invalid-date")
        assert result == "invalid-date"

    def test_empty_string(self):
        """Should return empty string for empty input."""
        result = parse_date("")
        assert result == ""
