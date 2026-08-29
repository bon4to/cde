import importlib.util
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = ROOT / "db" / "migrations" / "20260815000000.py"


def _load_migration():
    spec = importlib.util.spec_from_file_location("paid_feature_migration", MIGRATION_PATH)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def test_paid_feature_migration_marks_contracted_modules(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE aux_permissions (
                id_perm VARCHAR(6) PRIMARY KEY,
                desc_perm VARCHAR(100)
            )
            """
        )
        conn.executemany(
            "INSERT INTO aux_permissions (id_perm, desc_perm) VALUES (?, ?)",
            [
                ("MOV008", "MAPA"),
                ("PRC010", "PROCESSAMENTO"),
                ("MOV004", "ESTOQUE"),
            ],
        )

    migration = _load_migration()
    monkeypatch.setattr(migration.config, "get_db_path", lambda: str(db_path))

    migration.up()

    with sqlite3.connect(db_path) as conn:
        rows = dict(
            conn.execute("SELECT id_perm, paid_feature FROM aux_permissions").fetchall()
        )

    assert rows["MOV008"] == 1
    assert rows["PRC010"] == 1
    assert rows["ENV006"] == 1
    assert rows["MOV004"] == 0

    migration.down()

    with sqlite3.connect(db_path) as conn:
        rows = dict(
            conn.execute("SELECT id_perm, paid_feature FROM aux_permissions").fetchall()
        )

    assert rows["MOV008"] == 0
    assert rows["PRC010"] == 0
    assert rows["ENV006"] == 0
