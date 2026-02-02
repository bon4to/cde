"""
Example migration file.
Naming convention: YYYYMMDDHHmmss_description.py
"""

import sqlite3
from app.utils.cdeapp import config


def up():
    """Apply migration."""
    # Example: create a table
    # with sqlite3.connect(config.get_db_path()) as conn:
    #     cursor = conn.cursor()
    #     cursor.execute("""
    #         CREATE TABLE IF NOT EXISTS tbl_example (
    #             id INTEGER PRIMARY KEY
    #         )
    #     """)
    #     conn.commit()
    pass


def down():
    """Rollback migration."""
    # Example: drop the table
    # with sqlite3.connect(config.get_db_path()) as conn:
    #     cursor = conn.cursor()
    #     cursor.execute("DROP TABLE IF EXISTS tbl_example")
    #     conn.commit()
    pass
