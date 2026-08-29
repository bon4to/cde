"""
Add paid feature flag to permission contracts.

Paid modules require an external license entry before they can be opened.
"""

import sqlite3
from app.utils.cdeapp import config


PAID_FEATURES = (
    ("MOV008", "MAPA (ENDEREÇOS)"),
    ("PRC010", "PROCESSAMENTO"),
    ("ENV006", "ENVASE"),
)


def _column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return any(row[1] == column_name for row in cursor.fetchall())


def up():
    """Apply migration - mark paid permission contracts."""
    with sqlite3.connect(config.get_db_path()) as conn:
        cursor = conn.cursor()

        if not _column_exists(cursor, "aux_permissions", "paid_feature"):
            cursor.execute(
                """
                ALTER TABLE aux_permissions
                ADD COLUMN paid_feature INTEGER NOT NULL DEFAULT 0
                """
            )

        cursor.executemany(
            """
            INSERT OR IGNORE INTO aux_permissions (
                id_perm, desc_perm, paid_feature
            ) VALUES (
                ?, ?, 1
            )
            """,
            PAID_FEATURES,
        )

        cursor.executemany(
            """
            UPDATE aux_permissions
            SET paid_feature = 1
            WHERE id_perm = ?
            """,
            [(id_perm,) for id_perm, _ in PAID_FEATURES],
        )
        conn.commit()


def down():
    """Rollback migration - remove paid markers while keeping the column."""
    with sqlite3.connect(config.get_db_path()) as conn:
        cursor = conn.cursor()
        if _column_exists(cursor, "aux_permissions", "paid_feature"):
            cursor.execute(
                """
                UPDATE aux_permissions
                SET paid_feature = 0
                WHERE id_perm IN (?, ?, ?)
                """,
                [id_perm for id_perm, _ in PAID_FEATURES],
            )
        conn.commit()
