import pytest
import tempfile
import os
from datetime import datetime


@pytest.fixture
def frozen_datetime():
    """Return a fixed datetime for deterministic tests."""
    return datetime(2025, 6, 15, 12, 0, 0)


@pytest.fixture
def sample_queries_file(tmp_path):
    """Create a temporary queries file for QueryManager tests."""
    queries_content = """1: SELECT * FROM users WHERE id = {user_id}
2: SELECT name, email FROM contacts
3: SELECT * FROM products
   WHERE category = '{category}'
   AND price < {max_price}
"""
    queries_file = tmp_path / "queries.txt"
    queries_file.write_text(queries_content, encoding="utf-8")
    return str(queries_file)


@pytest.fixture
def sample_csv_data():
    """Sample data for CSV tests."""
    return [
        {"cod_item": "ABC123", "desc_item": "Product A", "qtde": 10},
        {"cod_item": "DEF456", "desc_item": "Product B", "qtde": 20},
        {"cod_item": "GHI789", "desc_item": "Product C", "qtde": 30},
    ]


@pytest.fixture
def empty_csv_data():
    """Empty data for CSV edge case tests."""
    return []


@pytest.fixture
def single_row_csv_data():
    """Single row data for CSV tests."""
    return [{"cod_item": "ABC123", "desc_item": "Product A", "qtde": 10}]


@pytest.fixture
def temp_text_file(tmp_path):
    """Create a temporary text file."""
    text_file = tmp_path / "test.txt"
    text_file.write_text("Test content\nLine 2", encoding="utf-8")
    return str(text_file)
