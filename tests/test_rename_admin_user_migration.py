import importlib.util
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = ROOT / "db" / "migrations" / "20261009010000_rename_admin_user.py"


def load_migration():
    spec = importlib.util.spec_from_file_location(
        "rename_admin_user_migration", MIGRATION_PATH
    )
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def test_migration_renames_only_default_admin(tmp_path, monkeypatch):
    db_path = tmp_path / "migration.db"
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE users (
                id_user INTEGER PRIMARY KEY,
                login_user TEXT UNIQUE,
                nome_user TEXT,
                sobrenome_user TEXT
            )
            """
        )
        connection.executemany(
            "INSERT INTO users VALUES (?, ?, ?, ?)",
            [
                (1, "ADMIN", "LUCAS", "BONATO"),
                (2, "LUCAS", "LUCAS", "BONATO"),
            ],
        )

    migration = load_migration()
    monkeypatch.setattr(migration.config, "get_db_path", lambda: str(db_path))

    migration.up()
    migration.up()

    with sqlite3.connect(db_path) as connection:
        users = connection.execute(
            "SELECT login_user, nome_user, sobrenome_user FROM users ORDER BY id_user"
        ).fetchall()

    assert users == [("ADMIN", "ADMIN", ""), ("LUCAS", "LUCAS", "BONATO")]

    migration.down()

    with sqlite3.connect(db_path) as connection:
        admin = connection.execute(
            "SELECT nome_user, sobrenome_user FROM users WHERE login_user = 'ADMIN'"
        ).fetchone()

    assert admin == ("LUCAS", "BONATO")
