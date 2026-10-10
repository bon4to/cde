"""Add persisted system settings and default customer observation policy."""

import sqlite3

from app.utils.cdeapp import config


SETTING_KEY = "customer_observation_show_untagged"


def up():
    with sqlite3.connect(config.get_db_path()) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tbl_system_settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO tbl_system_settings (setting_key, setting_value)
            VALUES (?, '1')
            """,
            (SETTING_KEY,),
        )
        conn.commit()


def down():
    with sqlite3.connect(config.get_db_path()) as conn:
        conn.execute(
            "DELETE FROM tbl_system_settings WHERE setting_key = ?",
            (SETTING_KEY,),
        )
        conn.commit()
