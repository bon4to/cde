import pytest
from io import StringIO
import sys
from unittest.mock import patch

from app.models import logTexts


class TestTags:
    """Tests for TAGS dictionary."""

    def test_tags_contains_expected_keys(self):
        """Should contain all expected tag keys."""
        assert 1 in logTexts.TAGS
        assert 2 in logTexts.TAGS
        assert 3 in logTexts.TAGS
        assert 4 in logTexts.TAGS

    def test_tags_have_correct_values(self):
        """Should have correct tag values."""
        assert logTexts.TAGS[1] == "[CDE]"
        assert logTexts.TAGS[2] == "[INF]"
        assert logTexts.TAGS[3] == "[ERR]"
        assert logTexts.TAGS[4] == "[STATUS]"


class TestStartHeader:
    """Tests for start_header function."""

    def test_start_header_format(self):
        """Should format header with version and date."""
        result = logTexts.start_header("1.0.0", "2025-06-15")
        assert "[CDE] CDE Version: 1.0.0 (beta) - 2025-06-15" in result
        assert "[INF] Python Version:" in result
        assert "[INF] Starting in:" in result


class TestLog:
    """Tests for log function."""

    def test_log_basic_output(self, capsys):
        """Should print formatted log message."""
        logTexts.log(1, "Test message")
        captured = capsys.readouterr()
        assert "[CDE]" in captured.out
        assert "Test message" in captured.out
        assert "|" in captured.out

    def test_log_with_tag2(self, capsys):
        """Should include secondary tag when provided."""
        logTexts.log(2, "Test message", "[EXTRA]")
        captured = capsys.readouterr()
        assert "[INF]" in captured.out
        assert "[EXTRA]" in captured.out
        assert "Test message" in captured.out

    def test_log_with_invalid_tag(self, capsys):
        """Should default to [CDE] for invalid tag index."""
        logTexts.log(999, "Test message")
        captured = capsys.readouterr()
        assert "[CDE]" in captured.out
        assert "Test message" in captured.out
