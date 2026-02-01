"""
Migration Manager for CDE
Handles database schema migrations with up/down support.
Auto-rollback when migration files are removed.
"""

import os
import sqlite3
import importlib.util
import inspect

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
                    status VARCHAR(20) DEFAULT 'success',
                    down_code TEXT
                );
            """)
            # Add down_code column if missing (for existing tables)
            cursor.execute("PRAGMA table_info(tbl_migrations)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'down_code' not in columns:
                cursor.execute("ALTER TABLE tbl_migrations ADD COLUMN down_code TEXT")
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
    def _extract_down_code(module):
        """Extract the down() function source code from a module."""
        if hasattr(module, 'down'):
            try:
                return inspect.getsource(module.down)
            except (OSError, TypeError):
                return None
        return None

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
            down_code = MigrationManager._extract_down_code(module)

            if hasattr(module, 'up'):
                module.up()

            # Record successful migration with down code
            with sqlite3.connect(config.get_db_path()) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO tbl_migrations (filename, status, down_code)
                    VALUES (?, 'success', ?)
                """, (name, down_code))
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
        """Rollback a specific migration using file or stored code."""
        result = {'name': name, 'status': 'success', 'error': None}

        try:
            # Try to load from file first
            path = os.path.join(MigrationManager.MIGRATIONS_DIR, f"{name}.py")
            if os.path.exists(path):
                module = MigrationManager._load_migration(name)
                if hasattr(module, 'down'):
                    module.down()
            else:
                # File missing, use stored down_code
                MigrationManager._run_stored_down(name)

            # Remove from migrations table
            with sqlite3.connect(config.get_db_path()) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tbl_migrations WHERE filename = ?", (name,))
                conn.commit()

        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)

        return result

    @staticmethod
    def _run_stored_down(name):
        """Run the stored down() code for a migration."""
        with sqlite3.connect(config.get_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT down_code FROM tbl_migrations WHERE filename = ?", (name,))
            row = cursor.fetchone()

        if not row or not row[0]:
            raise Exception(f"No stored down() code for migration {name}")

        down_code = row[0]
        # Execute the stored down function
        exec_globals = {'sqlite3': sqlite3, 'config': config}
        exec(down_code, exec_globals)
        if 'down' in exec_globals:
            exec_globals['down']()

    @staticmethod
    def rollback_orphaned_migrations():
        """Rollback migrations that are applied but file no longer exists."""
        MigrationManager._ensure_migrations_table()
        applied = MigrationManager._get_applied_migrations()
        existing_files = MigrationManager._get_migration_files()

        orphaned = [m for m in applied if m not in existing_files]
        results = []

        # Rollback in reverse order (newest first)
        for name in reversed(orphaned):
            result = MigrationManager.rollback_migration(name)
            results.append(result)
            if result['status'] == 'success':
                print(f"[MIGRATION] Rolled back orphaned: {name}")
            else:
                print(f"[MIGRATION] Failed to rollback orphaned: {name} - {result['error']}")

        return results

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

        # First, show orphaned (applied but file missing)
        for name in applied:
            if name not in all_migrations:
                result.append({
                    'name': name,
                    'status': 'orphaned',
                    'applied_at': applied[name]['applied_at']
                })

        # Then show existing files
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
        """Run migrations on application startup: rollback orphaned, then apply pending."""
        try:
            # First, rollback any orphaned migrations
            orphaned_results = MigrationManager.rollback_orphaned_migrations()

            # Then run pending migrations
            results = MigrationManager.run_pending_migrations()
            for r in results:
                if r['status'] == 'failed':
                    print(f"[MIGRATION] Failed: {r['name']} - {r['error']}")
                else:
                    print(f"[MIGRATION] Applied: {r['name']}")
        except Exception as e:
            print(f"[MIGRATION] Error running migrations: {e}")
