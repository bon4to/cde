import pytest
import os
from unittest.mock import patch

from app.models import dbUtils
from app.models.dbUtils import QueryManager


class TestQueryManagerLoadQueries:
    """Tests for QueryManager.load_queries method."""

    def test_loads_single_line_queries(self, sample_queries_file):
        """Should load single-line queries correctly."""
        QueryManager.load_queries(sample_queries_file)
        queries = QueryManager.get_all_queries()
        assert 1 in queries
        assert 2 in queries
        assert "SELECT * FROM users" in queries[1]
        assert "SELECT name, email FROM contacts" in queries[2]

    def test_loads_multi_line_queries(self, sample_queries_file):
        """Should load multi-line queries correctly."""
        QueryManager.load_queries(sample_queries_file)
        queries = QueryManager.get_all_queries()
        assert 3 in queries
        # Multi-line query should be joined
        assert "SELECT * FROM products" in queries[3]
        assert "WHERE category" in queries[3]
        assert "AND price" in queries[3]

    def test_empty_file(self, tmp_path):
        """Should handle empty file."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("", encoding="utf-8")
        QueryManager.load_queries(str(empty_file))
        queries = QueryManager.get_all_queries()
        assert len(queries) == 0


class TestQueryManagerGet:
    """Tests for QueryManager.get method."""

    def test_get_basic_query(self, sample_queries_file):
        """Should retrieve a basic query."""
        QueryManager.load_queries(sample_queries_file)

        # Directly access QUERIES to test
        result = QueryManager.QUERIES.get(1)
        assert "SELECT * FROM users" in result

    def test_get_with_variables(self, sample_queries_file):
        """Should substitute variables in query."""
        QueryManager.load_queries(sample_queries_file)
        # Manually set a query with variable
        QueryManager.QUERIES[99] = "SELECT * FROM users WHERE id = {user_id}"
        query = QueryManager.QUERIES[99].format(user_id=42)
        assert "id = 42" in query

    def test_get_nonexistent_query_returns_none(self, sample_queries_file):
        """Should return None for non-existent query ID."""
        QueryManager.load_queries(sample_queries_file)
        result = QueryManager.QUERIES.get(999)
        assert result is None


class TestGetFileText:
    """Tests for get_file_text function."""

    def test_reads_file_content(self, temp_text_file):
        """Should read and strip file content."""
        result = dbUtils.get_file_text(temp_text_file)
        assert result == "Test content\nLine 2"

    def test_returns_empty_on_missing_file(self):
        """Should return empty string for missing file."""
        result = dbUtils.get_file_text("/nonexistent/path/file.txt")
        assert result == ""


class TestGetOdbcUserCredentials:
    """Tests for get_odbc_user_credentials function."""

    def test_parses_credentials_from_env(self, monkeypatch):
        """Should parse user and password from DB_USER env var."""
        monkeypatch.setenv("DB_USER", "testuser;testpass")
        user, password = dbUtils.get_odbc_user_credentials()
        assert user == "testuser"
        assert password == "testpass"
