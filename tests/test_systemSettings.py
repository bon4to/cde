import sqlite3

from app.models.systemSettings import SystemSettings
from app.utils import cdeapp


def create_settings_table(db_path):
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE tbl_system_settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def test_missing_setting_defaults_to_show_all(tmp_path, monkeypatch):
    db_path = tmp_path / "settings.db"
    monkeypatch.setattr(cdeapp.config, "db_path", str(db_path))

    assert SystemSettings.show_untagged_customer_observations() is True


def test_setting_can_hide_and_restore_untagged_observations(tmp_path, monkeypatch):
    db_path = tmp_path / "settings.db"
    monkeypatch.setattr(cdeapp.config, "db_path", str(db_path))
    create_settings_table(db_path)

    SystemSettings.set_show_untagged_customer_observations(False)
    assert SystemSettings.show_untagged_customer_observations() is False

    SystemSettings.set_show_untagged_customer_observations(True)
    assert SystemSettings.show_untagged_customer_observations() is True
