import pytest

from app.models.misc import CSVUtils


class TestIterateCsvData:
    """Tests for CSVUtils.iterate_csv_data method."""

    def test_multiple_rows(self, sample_csv_data):
        """Should format multiple rows correctly."""
        result = CSVUtils.iterate_csv_data(sample_csv_data)
        lines = result.strip().split("\n")
        assert len(lines) == 3
        assert lines[0] == "ABC123;Product A;10"
        assert lines[1] == "DEF456;Product B;20"
        assert lines[2] == "GHI789;Product C;30"

    def test_empty_data(self, empty_csv_data):
        """Should return empty string for empty data."""
        result = CSVUtils.iterate_csv_data(empty_csv_data)
        assert result == ""


class TestIterateCsvDataErp:
    """Tests for CSVUtils.iterate_csv_data_erp method."""

    def test_erp_format_with_quotes(self, sample_csv_data):
        """Should wrap each line in quotes for ERP format."""
        result = CSVUtils.iterate_csv_data_erp(sample_csv_data)
        lines = result.strip().split("\n")
        assert len(lines) == 3
        assert lines[0] == '"ABC123;Product A;10"'
        assert lines[1] == '"DEF456;Product B;20"'
        assert lines[2] == '"GHI789;Product C;30"'


class TestAddHeaders:
    """Tests for CSVUtils.add_headers method."""

    def test_extracts_headers(self, sample_csv_data):
        """Should extract headers from first row keys."""
        result = CSVUtils.add_headers(sample_csv_data)
        assert result == "cod_item;desc_item;qtde\n"

    def test_empty_data_returns_empty(self, empty_csv_data):
        """Should return empty string for empty data."""
        result = CSVUtils.add_headers(empty_csv_data)
        assert result == ""

    def test_single_row(self, single_row_csv_data):
        """Should extract headers from single row."""
        result = CSVUtils.add_headers(single_row_csv_data)
        assert result == "cod_item;desc_item;qtde\n"
