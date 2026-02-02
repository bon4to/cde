#!/usr/bin/env python3
"""
Creates a new migration file with the proper naming convention.
Usage: python scripts/create_migration.py description_here
"""

import sys
import os
from datetime import datetime

MIGRATIONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "db", "migrations"
)

TEMPLATE = '''"""
{description}
"""

import sqlite3
from app.utils.cdeapp import config


def up():
    """Apply migration."""
    with sqlite3.connect(config.get_db_path()) as conn:
        cursor = conn.cursor()
        # TODO: Add your migration code here
        # cursor.execute("""
        #     CREATE TABLE IF NOT EXISTS ...
        # """)
        conn.commit()


def down():
    """Rollback migration."""
    with sqlite3.connect(config.get_db_path()) as conn:
        cursor = conn.cursor()
        # TODO: Add your rollback code here
        # cursor.execute("DROP TABLE IF EXISTS ...")
        conn.commit()
'''


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/create_migration.py description_here")
        print("Example: python scripts/create_migration.py add_users_table")
        sys.exit(1)

    description = "_".join(sys.argv[1:])
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}.py"
    filepath = os.path.join(MIGRATIONS_DIR, filename)

    os.makedirs(MIGRATIONS_DIR, exist_ok=True)

    with open(filepath, "w") as f:
        f.write(TEMPLATE.format(description=description.replace("_", " ").title()))

    print(f"Created: {filepath}")


if __name__ == "__main__":
    main()
