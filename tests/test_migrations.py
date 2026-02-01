"""
Unit tests for MigrationManager.
Uses a temporary database to avoid residues.
"""

import os
import sys
import sqlite3
import tempfile
import shutil
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.migrationManager import MigrationManager


class TestMigrationManager(unittest.TestCase):
    """Test cases for MigrationManager."""

    def setUp(self):
        """Set up test fixtures with temporary database and migrations dir."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = os.path.join(self.temp_dir, 'test.db')
        self.temp_migrations = os.path.join(self.temp_dir, 'migrations')
        os.makedirs(self.temp_migrations)

        # Patch config.get_db_path to use temp db
        self.db_patcher = patch('app.models.migrationManager.config.get_db_path',
                                return_value=self.temp_db)
        self.db_patcher.start()

        # Patch MIGRATIONS_DIR to use temp dir
        self.original_migrations_dir = MigrationManager.MIGRATIONS_DIR
        MigrationManager.MIGRATIONS_DIR = self.temp_migrations

    def tearDown(self):
        """Clean up temp files."""
        self.db_patcher.stop()
        MigrationManager.MIGRATIONS_DIR = self.original_migrations_dir
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_migration(self, name, up_code="pass", down_code="pass"):
        """Helper to create a migration file."""
        content = f'''
import sqlite3

def up():
    {up_code}

def down():
    {down_code}
'''
        path = os.path.join(self.temp_migrations, f"{name}.py")
        with open(path, 'w') as f:
            f.write(content)
        return path

    def test_ensure_migrations_table(self):
        """Test that migrations table is created."""
        MigrationManager._ensure_migrations_table()

        with sqlite3.connect(self.temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tbl_migrations'")
            result = cursor.fetchone()

        self.assertIsNotNone(result)
        self.assertEqual(result[0], 'tbl_migrations')

    def test_get_migration_files_empty(self):
        """Test getting migration files when directory is empty."""
        files = MigrationManager._get_migration_files()
        self.assertEqual(files, [])

    def test_get_migration_files_sorted(self):
        """Test that migration files are returned sorted."""
        self._create_migration('20250102000000_second')
        self._create_migration('20250101000000_first')
        self._create_migration('20250103000000_third')

        files = MigrationManager._get_migration_files()

        self.assertEqual(files, [
            '20250101000000_first',
            '20250102000000_second',
            '20250103000000_third'
        ])

    def test_run_pending_migrations(self):
        """Test running pending migrations."""
        self._create_migration(
            '20250101000000_test',
            up_code=f"sqlite3.connect('{self.temp_db}').execute('CREATE TABLE test_table (id INTEGER)')"
        )

        results = MigrationManager.run_pending_migrations()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['status'], 'success')

        # Verify table was created
        with sqlite3.connect(self.temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'")
            self.assertIsNotNone(cursor.fetchone())

    def test_run_pending_skips_applied(self):
        """Test that already applied migrations are skipped."""
        self._create_migration('20250101000000_applied')

        # Run once
        MigrationManager.run_pending_migrations()

        # Run again
        results = MigrationManager.run_pending_migrations()

        self.assertEqual(len(results), 0)

    def test_migration_failure_recorded(self):
        """Test that failed migrations are recorded."""
        self._create_migration(
            '20250101000000_fail',
            up_code="raise Exception('Test error')"
        )

        results = MigrationManager.run_pending_migrations()

        self.assertEqual(results[0]['status'], 'failed')
        self.assertIn('Test error', results[0]['error'])

        # Check recorded status
        status = MigrationManager.get_migrations_status()
        self.assertEqual(status[0]['status'], 'failed')

    def test_rollback_migration(self):
        """Test rolling back a migration."""
        self._create_migration(
            '20250101000000_rollback',
            up_code=f"sqlite3.connect('{self.temp_db}').execute('CREATE TABLE rollback_test (id INTEGER)')",
            down_code=f"sqlite3.connect('{self.temp_db}').execute('DROP TABLE rollback_test')"
        )

        # Apply
        MigrationManager.run_pending_migrations()

        # Verify table exists
        with sqlite3.connect(self.temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rollback_test'")
            self.assertIsNotNone(cursor.fetchone())

        # Rollback
        result = MigrationManager.rollback_migration('20250101000000_rollback')

        self.assertEqual(result['status'], 'success')

        # Verify table removed
        with sqlite3.connect(self.temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rollback_test'")
            self.assertIsNone(cursor.fetchone())

        # Verify removed from tracking
        status = MigrationManager.get_migrations_status()
        self.assertEqual(status[0]['status'], 'pending')

    def test_get_migrations_status(self):
        """Test getting status of all migrations."""
        self._create_migration('20250101000000_one')
        self._create_migration('20250102000000_two')

        # Apply first one only
        MigrationManager._run_migration('20250101000000_one')

        status = MigrationManager.get_migrations_status()

        self.assertEqual(len(status), 2)
        self.assertEqual(status[0]['name'], '20250101000000_one')
        self.assertEqual(status[0]['status'], 'success')
        self.assertEqual(status[1]['name'], '20250102000000_two')
        self.assertEqual(status[1]['status'], 'pending')

    def test_stops_on_first_failure(self):
        """Test that migration stops on first failure."""
        self._create_migration('20250101000000_fail', up_code="raise Exception('fail')")
        self._create_migration('20250102000000_never_runs')

        results = MigrationManager.run_pending_migrations()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['status'], 'failed')

        # Second migration should still be pending
        status = MigrationManager.get_migrations_status()
        self.assertEqual(status[1]['status'], 'pending')

    def test_down_code_stored(self):
        """Test that down() code is stored when migration is applied."""
        self._create_migration('20250101000000_store', down_code="pass  # stored")

        MigrationManager.run_pending_migrations()

        with sqlite3.connect(self.temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT down_code FROM tbl_migrations WHERE filename = ?",
                          ('20250101000000_store',))
            row = cursor.fetchone()

        self.assertIsNotNone(row[0])
        self.assertIn('stored', row[0])

    def test_rollback_orphaned_migration(self):
        """Test rollback of migration when file is deleted (orphaned)."""
        # Create and apply migration
        self._create_migration(
            '20250101000000_orphan',
            up_code=f"sqlite3.connect('{self.temp_db}').execute('CREATE TABLE orphan_test (id INTEGER)')",
            down_code=f"sqlite3.connect('{self.temp_db}').execute('DROP TABLE orphan_test')"
        )
        MigrationManager.run_pending_migrations()

        # Verify table exists
        with sqlite3.connect(self.temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orphan_test'")
            self.assertIsNotNone(cursor.fetchone())

        # Delete migration file (simulating branch switch)
        os.remove(os.path.join(self.temp_migrations, '20250101000000_orphan.py'))

        # Run orphaned rollback
        results = MigrationManager.rollback_orphaned_migrations()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['status'], 'success')

        # Verify table was dropped using stored down code
        with sqlite3.connect(self.temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orphan_test'")
            self.assertIsNone(cursor.fetchone())

    def test_orphaned_shown_in_status(self):
        """Test that orphaned migrations are shown in status."""
        self._create_migration('20250101000000_will_orphan')
        MigrationManager.run_pending_migrations()

        # Delete file
        os.remove(os.path.join(self.temp_migrations, '20250101000000_will_orphan.py'))

        status = MigrationManager.get_migrations_status()

        self.assertEqual(len(status), 1)
        self.assertEqual(status[0]['status'], 'orphaned')

    def test_run_on_startup_handles_orphaned(self):
        """Test that run_on_startup rolls back orphaned and applies pending."""
        # Create and apply first migration
        self._create_migration(
            '20250101000000_old',
            up_code=f"sqlite3.connect('{self.temp_db}').execute('CREATE TABLE old_table (id INTEGER)')",
            down_code=f"sqlite3.connect('{self.temp_db}').execute('DROP TABLE old_table')"
        )
        MigrationManager.run_pending_migrations()

        # Delete old, create new (simulating branch switch)
        os.remove(os.path.join(self.temp_migrations, '20250101000000_old.py'))
        self._create_migration(
            '20250102000000_new',
            up_code=f"sqlite3.connect('{self.temp_db}').execute('CREATE TABLE new_table (id INTEGER)')"
        )

        # Run on startup
        MigrationManager.run_on_startup()

        # Old table should be gone, new table should exist
        with sqlite3.connect(self.temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='old_table'")
            self.assertIsNone(cursor.fetchone())
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='new_table'")
            self.assertIsNotNone(cursor.fetchone())


if __name__ == '__main__':
    unittest.main()
