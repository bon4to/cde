"""
Migration Manager for CDE
Handles database schema migrations with up/down support.
"""

import os
import sqlite3
import importlib.util
from datetime import datetime

from app.utils.cdeapp import config


class MigrationManager:
    """Manages database migrations."""

    MIGRATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'db', 'migrations')

    @staticmethod
    def _ensure_migrations_table():
        """Create migrations tracking table if it doesn't exist."""
        with sqlite3.connect(config.get_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename VARCHAR(50) UNIQUE,
                    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'success'
                );
            """)
            conn.commit()

    @staticmethod
    def _get_applied_migrations():
        """Get list of successfully applied migrations."""
        MigrationManager._ensure_migrations_table()
        with sqlite3.connect(config.get_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT filename FROM tbl_migrations
                WHERE status = 'success'
                ORDER BY filename
            """)
            return [row[0] for row in cursor.fetchall()]

    @staticmethod
    def _get_migration_files():
        """Get all migration files sorted by name."""
        if not os.path.exists(MigrationManager.MIGRATIONS_DIR):
            os.makedirs(MigrationManager.MIGRATIONS_DIR)
            return []

        files = []
        for f in os.listdir(MigrationManager.MIGRATIONS_DIR):
            if f.endswith('.py') and not f.startswith('__'):
                files.append(f[:-3])  # Remove .py extension
        return sorted(files)

    @staticmethod
    def _load_migration(name):
        """Load a migration module by name."""
        path = os.path.join(MigrationManager.MIGRATIONS_DIR, f"{name}.py")
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    @staticmethod
    def run_pending_migrations():
        """Run all pending migrations. Returns list of results."""
        applied = MigrationManager._get_applied_migrations()
        all_migrations = MigrationManager._get_migration_files()
        pending = [m for m in all_migrations if m not in applied]

        results = []
        for filename in pending:
            result = MigrationManager._run_migration(filename)
            results.append(result)
            if result['status'] == 'failed':
                break  # Stop on first failure

        return results

    @staticmethod
    def _run_migration(name):
        """Run a single migration."""
        MigrationManager._ensure_migrations_table()
        result = {'name': name, 'status': 'success', 'error': None}

        try:
            module = MigrationManager._load_migration(name)
            if hasattr(module, 'up'):
                module.up()

            # Record successful migration
            with sqlite3.connect(config.get_db_path()) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO tbl_migrations (filename, status)
                    VALUES (?, 'success')
                """, (name,))
                conn.commit()

        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)

            # Record failed migration
            with sqlite3.connect(config.get_db_path()) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO tbl_migrations (filename, status)
                    VALUES (?, 'failed')
                """, (name,))
                conn.commit()

        return result

    @staticmethod
    def rollback_migration(name):
        """Rollback a specific migration."""
        result = {'name': name, 'status': 'success', 'error': None}

        try:
            module = MigrationManager._load_migration(name)
            if hasattr(module, 'down'):
                module.down()

            # Remove from migrations table
            with sqlite3.connect(config.get_db_path()) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM tbl_migrations WHERE filename = ?
                """, (name,))
                conn.commit()

        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)

        return result

    @staticmethod
    def get_migrations_status():
        """Get status of all migrations."""
        MigrationManager._ensure_migrations_table()
        all_migrations = MigrationManager._get_migration_files()

        with sqlite3.connect(config.get_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT filename, applied_at, status
                FROM tbl_migrations
            """)
            applied = {row[0]: {'applied_at': row[1], 'status': row[2]} for row in cursor.fetchall()}

        result = []
        for name in all_migrations:
            if name in applied:
                result.append({
                    'name': name,
                    'status': applied[name]['status'],
                    'applied_at': applied[name]['applied_at']
                })
            else:
                result.append({
                    'name': name,
                    'status': 'pending',
                    'applied_at': None
                })

        return result

    @staticmethod
    def run_on_startup():
        """Run pending migrations on application startup."""
        try:
            results = MigrationManager.run_pending_migrations()
            for r in results:
                if r['status'] == 'failed':
                    print(f"[MIGRATION] Failed: {r['name']} - {r['error']}")
                else:
                    print(f"[MIGRATION] Applied: {r['name']}")
        except Exception as e:
            print(f"[MIGRATION] Error running migrations: {e}")
