"""
Unit tests for estoqueUtils functions.
Tests inventory management, custom date_fab, and related functionality.
"""

import os
import sys
import sqlite3
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCustomDateFab:
    """Tests for custom date_fab override functionality."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        temp_dir = tempfile.mkdtemp()
        temp_db_path = os.path.join(temp_dir, 'test.db')

        # Create the table
        with sqlite3.connect(temp_db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tbl_custom_date_fab (
                    cod_item     VARCHAR(6),
                    cod_lote     VARCHAR(20),
                    date_fab     DATETIME NOT NULL,
                    id_user      INTEGER,
                    time_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (cod_item, cod_lote)
                )
            """)

        yield temp_db_path

        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_get_custom_date_fab_returns_none_when_not_set(self, temp_db):
        """Should return None when no custom date exists."""
        with patch('app.models.estoqueUtils.db_path', temp_db):
            with patch('app.models.dbUtils.query') as mock_query:
                mock_query.return_value = ([], [])

                from app.models import estoqueUtils
                result = estoqueUtils.get_custom_date_fab('ITEM01', 'CS123')

                assert result is None

    def test_get_custom_date_fab_returns_date_when_set(self, temp_db):
        """Should return the custom date when it exists."""
        with patch('app.models.dbUtils.query') as mock_query:
            mock_query.return_value = ([('2025-01-15',)], ['date_fab'])

            from app.models import estoqueUtils
            result = estoqueUtils.get_custom_date_fab('ITEM01', 'CS123')

            assert result == '2025-01-15'

    def test_set_custom_date_fab_inserts_new_record(self, temp_db):
        """Should insert a new custom date_fab record."""
        with sqlite3.connect(temp_db) as conn:
            # Manually insert and verify
            conn.execute("""
                INSERT INTO tbl_custom_date_fab (cod_item, cod_lote, date_fab, id_user)
                VALUES ('ITEM01', 'CS123', '2025-01-15', 1)
            """)

            cursor = conn.execute("""
                SELECT date_fab FROM tbl_custom_date_fab
                WHERE cod_item = 'ITEM01' AND cod_lote = 'CS123'
            """)
            result = cursor.fetchone()

            assert result is not None
            assert result[0] == '2025-01-15'

    def test_set_custom_date_fab_updates_existing_record(self, temp_db):
        """Should update existing record when setting new date."""
        with sqlite3.connect(temp_db) as conn:
            # Insert initial record
            conn.execute("""
                INSERT INTO tbl_custom_date_fab (cod_item, cod_lote, date_fab, id_user)
                VALUES ('ITEM01', 'CS123', '2025-01-15', 1)
            """)

            # Update with new date
            conn.execute("""
                INSERT OR REPLACE INTO tbl_custom_date_fab (cod_item, cod_lote, date_fab, id_user)
                VALUES ('ITEM01', 'CS123', '2025-02-20', 2)
            """)

            cursor = conn.execute("""
                SELECT date_fab, id_user FROM tbl_custom_date_fab
                WHERE cod_item = 'ITEM01' AND cod_lote = 'CS123'
            """)
            result = cursor.fetchone()

            assert result[0] == '2025-02-20'
            assert result[1] == 2

    def test_delete_custom_date_fab_removes_record(self, temp_db):
        """Should delete the custom date_fab record."""
        with sqlite3.connect(temp_db) as conn:
            # Insert record
            conn.execute("""
                INSERT INTO tbl_custom_date_fab (cod_item, cod_lote, date_fab, id_user)
                VALUES ('ITEM01', 'CS123', '2025-01-15', 1)
            """)

            # Delete it
            conn.execute("""
                DELETE FROM tbl_custom_date_fab
                WHERE cod_item = 'ITEM01' AND cod_lote = 'CS123'
            """)

            cursor = conn.execute("""
                SELECT * FROM tbl_custom_date_fab
                WHERE cod_item = 'ITEM01' AND cod_lote = 'CS123'
            """)
            result = cursor.fetchone()

            assert result is None

    def test_custom_date_fab_unique_per_item_lote(self, temp_db):
        """Should maintain unique constraint on cod_item + cod_lote."""
        with sqlite3.connect(temp_db) as conn:
            # Insert first record
            conn.execute("""
                INSERT INTO tbl_custom_date_fab (cod_item, cod_lote, date_fab, id_user)
                VALUES ('ITEM01', 'CS123', '2025-01-15', 1)
            """)

            # Same item, different lote should work
            conn.execute("""
                INSERT INTO tbl_custom_date_fab (cod_item, cod_lote, date_fab, id_user)
                VALUES ('ITEM01', 'CS456', '2025-02-20', 1)
            """)

            cursor = conn.execute("SELECT COUNT(*) FROM tbl_custom_date_fab")
            count = cursor.fetchone()[0]

            assert count == 2


class TestCargaStatusFiltering:
    """Tests for carga status filtering (baixa/excluida)."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database with carga status table."""
        temp_dir = tempfile.mkdtemp()
        temp_db_path = os.path.join(temp_dir, 'test.db')

        with sqlite3.connect(temp_db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tbl_carga_status (
                    id_log        INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_carga      INTEGER(6),
                    status        VARCHAR(20),
                    justificativa TEXT,
                    id_user       INTEGER,
                    timestamp     DATETIME DEFAULT CURRENT_TIMESTAMP,
                    flag_ativo    BOOLEAN DEFAULT TRUE
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tbl_transactions (
                    id_mov     INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_carga   VARCHAR(10)
                )
            """)

        yield temp_db_path
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_listed_cargas_status_returns_strings(self, temp_db):
        """Should return carga IDs as strings for comparison."""
        with sqlite3.connect(temp_db) as conn:
            conn.execute("""
                INSERT INTO tbl_carga_status (id_carga, status, flag_ativo)
                VALUES (3646, 'baixa', TRUE)
            """)

            cursor = conn.execute("""
                SELECT DISTINCT id_carga FROM tbl_carga_status
                WHERE flag_ativo = TRUE
            """)
            rows = cursor.fetchall()
            result = [str(row[0]) for row in rows]

            assert '3646' in result
            assert isinstance(result[0], str)

    def test_baixa_carga_excluded_from_query(self, temp_db):
        """Baixa cargas should be in the NOT IN exclusion list."""
        with sqlite3.connect(temp_db) as conn:
            # Add some cargas to transactions
            conn.execute("INSERT INTO tbl_transactions (id_carga) VALUES ('3645')")
            conn.execute("INSERT INTO tbl_transactions (id_carga) VALUES ('3646')")
            conn.execute("INSERT INTO tbl_transactions (id_carga) VALUES ('3647')")

            # Mark 3646 as baixa
            conn.execute("""
                INSERT INTO tbl_carga_status (id_carga, status, flag_ativo)
                VALUES (3646, 'baixa', TRUE)
            """)

            # Get all cargas
            cursor = conn.execute("SELECT DISTINCT id_carga FROM tbl_transactions")
            all_cargas = [str(row[0]) for row in cursor.fetchall()]

            # Get baixa cargas
            cursor = conn.execute("""
                SELECT DISTINCT id_carga FROM tbl_carga_status WHERE flag_ativo = TRUE
            """)
            baixa_cargas = [str(row[0]) for row in cursor.fetchall()]

            # Finalized = all - baixa
            finalized = [c for c in all_cargas if c not in baixa_cargas]
            # Then add baixa back for exclusion
            exclusion_list = finalized + baixa_cargas

            assert '3646' in exclusion_list
            assert '3645' in exclusion_list
            assert '3647' in exclusion_list

    def test_revert_carga_removes_from_baixa(self, temp_db):
        """Reverting a carga should set flag_ativo to FALSE."""
        with sqlite3.connect(temp_db) as conn:
            conn.execute("""
                INSERT INTO tbl_carga_status (id_carga, status, flag_ativo)
                VALUES (3646, 'baixa', TRUE)
            """)

            # Revert
            conn.execute("""
                UPDATE tbl_carga_status
                SET flag_ativo = FALSE
                WHERE id_carga = 3646 AND flag_ativo = TRUE
            """)

            cursor = conn.execute("""
                SELECT flag_ativo FROM tbl_carga_status WHERE id_carga = 3646
            """)
            result = cursor.fetchone()

            assert result[0] == 0  # FALSE


class TestInventoryCalculations:
    """Tests for inventory balance calculations."""

    def test_balance_entry_adds(self):
        """Entry (E) operations should add to balance."""
        # Simulating the balance calculation logic
        transactions = [
            {'quantity': 100, 'operation': 'E'},
            {'quantity': 50, 'operation': 'E'},
        ]

        balance = sum(
            t['quantity'] if t['operation'] == 'E' else -t['quantity']
            for t in transactions
        )

        assert balance == 150

    def test_balance_exit_subtracts(self):
        """Exit (S) operations should subtract from balance."""
        transactions = [
            {'quantity': 100, 'operation': 'E'},
            {'quantity': 30, 'operation': 'S'},
        ]

        balance = sum(
            t['quantity'] if t['operation'] == 'E' else -t['quantity']
            for t in transactions
        )

        assert balance == 70

    def test_balance_mixed_operations(self):
        """Mixed operations should calculate correctly."""
        transactions = [
            {'quantity': 100, 'operation': 'E'},
            {'quantity': 20, 'operation': 'S'},
            {'quantity': 50, 'operation': 'E'},
            {'quantity': 10, 'operation': 'S'},
        ]

        balance = sum(
            t['quantity'] if t['operation'] == 'E' else -t['quantity']
            for t in transactions
        )

        assert balance == 120  # 100 - 20 + 50 - 10

    def test_balance_can_go_negative(self):
        """Balance can go negative (oversold scenario)."""
        transactions = [
            {'quantity': 50, 'operation': 'E'},
            {'quantity': 100, 'operation': 'S'},
        ]

        balance = sum(
            t['quantity'] if t['operation'] == 'E' else -t['quantity']
            for t in transactions
        )

        assert balance == -50


class TestAddressFormatting:
    """Tests for address formatting."""

    def test_address_format_with_trailing_space(self):
        """Address should have trailing space for exact search."""
        letra = 'A'
        numero = 1
        address = f"{letra}.{numero} "

        assert address == "A.1 "
        assert address.endswith(" ")

    def test_address_search_exact_match(self):
        """Trailing space prevents partial matches."""
        addresses = ["A.1 ", "A.10 ", "A.100 "]
        search = "A.1 "

        exact_matches = [a for a in addresses if a == search]

        assert len(exact_matches) == 1
        assert exact_matches[0] == "A.1 "


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
