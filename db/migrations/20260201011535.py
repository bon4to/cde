"""
Import Filtro Cargas
Imports carga IDs from filtro_1.txt into tbl_carga_status as 'excluida'.
"""

import os
import sqlite3
from app.utils.cdeapp import config


FILTRO_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "report",
    "cargas_preset",
    "filtro_1.txt",
)


def up():
    """Apply migration - import cargas from filtro_1.txt."""
    if not os.path.exists(FILTRO_PATH):
        raise Exception(f"File not found: {FILTRO_PATH}")

    with open(FILTRO_PATH, "r") as f:
        content = f.read().strip()

    ids = [int(x.strip()) for x in content.split(",") if x.strip()]

    with sqlite3.connect(config.get_db_path()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tbl_carga_status (
                id_log        INTEGER PRIMARY KEY AUTOINCREMENT,
                id_carga      INTEGER(6),
                status        VARCHAR(20),
                justificativa TEXT,
                id_user       INTEGER,
                timestamp     DATETIME DEFAULT CURRENT_TIMESTAMP,
                flag_ativo    BOOLEAN DEFAULT TRUE
            )
        """
        )
        for id_carga in ids:
            cursor.execute(
                """
                INSERT INTO tbl_carga_status (id_carga, status, justificativa, id_user)
                VALUES (?, 'excluida', 'Importado automaticamente', 0)
            """,
                (id_carga,),
            )
        conn.commit()


def down():
    """Rollback migration - remove imported cargas."""
    with sqlite3.connect(config.get_db_path()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM tbl_carga_status
            WHERE justificativa = 'Importado automaticamente'
        """
        )
        conn.commit()
