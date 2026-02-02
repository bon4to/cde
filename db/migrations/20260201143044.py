"""
Create tbl_custom_date_fab
Allows users to set custom fabrication dates for item+batch combinations,
overriding the auto-calculated first movement date.
"""

import sqlite3
from app.utils.cdeapp import config


def up():
    """Apply migration - create tbl_custom_date_fab table."""
    with sqlite3.connect(config.get_db_path()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tbl_custom_date_fab (
                cod_item     VARCHAR(6),
                cod_lote     VARCHAR(20),
                date_fab     DATETIME NOT NULL,
                id_user      INTEGER,
                time_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (cod_item, cod_lote)
            )
        """
        )
        conn.commit()


def down():
    """Rollback migration - drop tbl_custom_date_fab table."""
    with sqlite3.connect(config.get_db_path()) as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS tbl_custom_date_fab")
        conn.commit()
