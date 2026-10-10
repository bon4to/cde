import sqlite3

from app.utils import cdeapp


class SystemSettings:
    CUSTOMER_OBSERVATION_SHOW_UNTAGGED = "customer_observation_show_untagged"

    @staticmethod
    def show_untagged_customer_observations():
        try:
            with sqlite3.connect(cdeapp.config.get_db_path()) as connection:
                row = connection.execute(
                    """
                    SELECT setting_value
                    FROM tbl_system_settings
                    WHERE setting_key = ?
                    """,
                    (SystemSettings.CUSTOMER_OBSERVATION_SHOW_UNTAGGED,),
                ).fetchone()
        except sqlite3.Error:
            return True

        if not row:
            return True
        return str(row[0]).lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def set_show_untagged_customer_observations(show_all):
        with sqlite3.connect(cdeapp.config.get_db_path()) as connection:
            connection.execute(
                """
                INSERT INTO tbl_system_settings (setting_key, setting_value)
                VALUES (?, ?)
                ON CONFLICT(setting_key) DO UPDATE SET
                    setting_value = excluded.setting_value,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    SystemSettings.CUSTOMER_OBSERVATION_SHOW_UNTAGGED,
                    "1" if show_all else "0",
                ),
            )
            connection.commit()
