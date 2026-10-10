import importlib.util
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = (
    ROOT / "db" / "migrations" / "20261009000000_customer_observation_policy.py"
)


def load_migration():
    spec = importlib.util.spec_from_file_location(
        "customer_observation_policy_migration", MIGRATION_PATH
    )
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def test_migration_defaults_to_show_all(tmp_path, monkeypatch):
    db_path = tmp_path / "migration.db"
    migration = load_migration()
    monkeypatch.setattr(migration.config, "get_db_path", lambda: str(db_path))

    migration.up()
    migration.up()

    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(
            "SELECT setting_key, setting_value FROM tbl_system_settings"
        ).fetchall()

    assert rows == [("customer_observation_show_untagged", "1")]

    migration.down()

    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(
            "SELECT setting_key, setting_value FROM tbl_system_settings"
        ).fetchall()

    assert rows == []
