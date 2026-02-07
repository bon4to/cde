import pytest
from datetime import datetime
from freezegun import freeze_time

from app.models import misc


class TestDaysToExpire:
    """Tests for days_to_expire function."""

    @freeze_time("2025-06-15")
    def test_valid_date_with_cs_lote(self):
        """Should calculate remaining days correctly."""
        # Fabrication date: Jan 1, 2025, 6 months validity
        # Expiration: Jul 1, 2025
        # Today: Jun 15, 2025 -> 16 days remaining
        remaining, error = misc.days_to_expire("2025-01-01 10:00:00", 6, "CS12345")
        assert error is None
        assert remaining == 16

    def test_no_cs_in_lote(self):
        """Should return 0 and 'N/A' when lote doesn't contain 'CS'."""
        remaining, error = misc.days_to_expire("2025-01-01 10:00:00", 6, "AB12345")
        assert remaining == 0
        assert error == "N/A"

    def test_no_months_provided(self):
        """Should return 0 and 'N/A' when months is 0 or None."""
        remaining, error = misc.days_to_expire("2025-01-01 10:00:00", 0, "CS12345")
        assert remaining == 0
        assert error == "N/A"

        remaining, error = misc.days_to_expire("2025-01-01 10:00:00", None, "CS12345")
        assert remaining == 0
        assert error == "N/A"

    def test_no_cod_lote(self):
        """Should return 0 and 'N/A' when cod_lote is empty or None."""
        remaining, error = misc.days_to_expire("2025-01-01 10:00:00", 6, "")
        assert remaining == 0
        assert error == "N/A"

        remaining, error = misc.days_to_expire("2025-01-01 10:00:00", 6, None)
        assert remaining == 0
        assert error == "N/A"

    @freeze_time("2025-06-15")
    def test_month_overflow_to_next_year(self):
        """Should handle month overflow to next year correctly."""
        # Fabrication date: Aug 1, 2025, 6 months validity
        # Expiration: Feb 1, 2026
        remaining, error = misc.days_to_expire("2025-08-01 10:00:00", 6, "CS12345")
        assert error is None
        assert remaining > 200  # Approximately 231 days

    @freeze_time("2024-02-28")
    def test_leap_year_handling(self):
        """Should handle leap year correctly for end-of-month dates."""
        # 2024 is a leap year
        # Fabrication: Jan 31, 2024, 1 month validity
        # Expiration should be Feb 29, 2024 (last day of Feb in leap year)
        remaining, error = misc.days_to_expire("2024-01-31 10:00:00", 1, "CS12345")
        assert error is None
        assert remaining == 1  # Feb 29 - Feb 28 = 1 day

    @freeze_time("2025-06-15")
    def test_date_format_with_slashes(self):
        """Should handle date format with slashes."""
        remaining, error = misc.days_to_expire("2025/01/01 10:00:00", 6, "CS12345")
        assert error is None
        assert remaining == 16


class TestParseDateToHtmlInput:
    """Tests for parse_date_to_html_input function."""

    def test_standard_date_format(self):
        """Should convert standard date format."""
        result = misc.parse_date_to_html_input("2025/06/15 10:30:00")
        assert result == "2025-06-15"

    def test_date_with_dashes(self):
        """Should handle date already with dashes."""
        result = misc.parse_date_to_html_input("2025-06-15 10:30:00")
        assert result == "2025-06-15"


class TestParseDbDatetime:
    """Tests for parse_db_datetime function."""

    def test_none_timestamp_returns_current_time(self):
        """Should return current time when timestamp is None."""
        result = misc.parse_db_datetime(None)
        # Result should be in format YYYY/MM/DD HH:MM:SS
        assert len(result) == 19
        assert "/" in result
        assert ":" in result

    def test_string_timestamp(self):
        """Should parse string timestamp correctly."""
        result = misc.parse_db_datetime("2025-06-15")
        assert result == "2025/06/15 00:00:00"

    def test_datetime_object(self):
        """Should format datetime object correctly."""
        from datetime import timezone, timedelta

        dt = datetime(2025, 6, 15, 10, 30, 45, tzinfo=timezone(timedelta(hours=-3)))
        result = misc.parse_db_datetime(dt)
        assert result == "2025/06/15 10:30:45"


class TestAddDaysToDatetimeStr:
    """Tests for add_days_to_datetime_str function."""

    def test_add_positive_days(self):
        """Should add positive days correctly."""
        result = misc.add_days_to_datetime_str("2025-06-15", 10)
        assert result == "2025-06-25"

    def test_add_negative_days(self):
        """Should subtract days when negative."""
        result = misc.add_days_to_datetime_str("2025-06-15", -10)
        assert result == "2025-06-05"

    def test_cross_month_boundary(self):
        """Should handle crossing month boundary."""
        result = misc.add_days_to_datetime_str("2025-06-28", 5)
        assert result == "2025-07-03"

    def test_cross_year_boundary(self):
        """Should handle crossing year boundary."""
        result = misc.add_days_to_datetime_str("2025-12-28", 10)
        assert result == "2026-01-07"


class TestParseFloat:
    """Tests for parse_float function."""

    def test_comma_decimal_separator(self):
        """Should handle comma as decimal separator."""
        result = misc.parse_float("123,45")
        assert result == 123.45

    def test_dot_decimal_separator(self):
        """Should handle dot as decimal separator."""
        result = misc.parse_float("123.45")
        assert result == 123.45

    def test_integer_string(self):
        """Should handle integer string."""
        result = misc.parse_float("123")
        assert result == 123.0

    def test_invalid_value(self):
        """Should return 0.0 for invalid values."""
        result = misc.parse_float("abc")
        assert result == 0.0

    def test_empty_string(self):
        """Should return 0.0 for empty string."""
        result = misc.parse_float("")
        assert result == 0.0
