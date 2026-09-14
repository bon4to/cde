import os
import sqlite3
import pytest
from app.services import NotificationManager as nm
from app.utils.cdeapp import config


class TestNotificationManagerSecurity:
    """Tests for SQL injection resistance in NotificationManager."""

    @pytest.fixture
    def setup_db(self, tmp_path, monkeypatch):
        db_file = tmp_path / "test_notifications.db"
        monkeypatch.setattr(config, "db_path", str(db_file))

        nm.createNotificationsTable()

        with sqlite3.connect(str(db_file)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "CREATE TABLE users (id_user INTEGER PRIMARY KEY, nome_user TEXT);"
            )
            cursor.execute("INSERT INTO users VALUES (1, 'User1');")
            cursor.execute("INSERT INTO users VALUES (2, 'User2');")
            conn.commit()

        return str(db_file)

    def test_set_notification_with_quotes_and_sql_injection(self, setup_db):
        """Should safely insert notifications containing SQL injection payloads and quotes."""
        malicious_title = '"; DROP TABLE users; --'
        malicious_msg = 'He said "Hello" and it\'s safe!'

        _, err = nm.setNotification(1, malicious_title, malicious_msg)
        assert err == ""

        # Ensure users table was not dropped
        with sqlite3.connect(setup_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users;")
            assert cursor.fetchone()[0] == 2

        # Verify notification was saved properly
        notifications, err = nm.getNotifications(1)
        assert err is None
        assert len(notifications) == 1
        assert notifications[0]["title"] == malicious_title.strip().upper()
        assert notifications[0]["flag_read"] is False

    def test_broadcast_notification_with_quotes(self, setup_db):
        """Broadcast (userid=0) should safely insert for all users."""
        _, err = nm.setNotification(0, 'ALERT "SYSTEM"', 'Message with "quotes"')
        assert err == ""

        notifs_user1, _ = nm.getNotifications(1)
        notifs_user2, _ = nm.getNotifications(2)
        assert len(notifs_user1) == 1
        assert len(notifs_user2) == 1

    def test_clear_and_unclear_notification(self, setup_db):
        """Should update read flag correctly without SQL errors."""
        nm.setNotification(1, "TEST", "MSG")
        notifications, _ = nm.getNotifications(1)
        notif_id = notifications[0]["id"]

        nm.clearNotification(1, notif_id)
        notifications, _ = nm.getNotifications(1)
        assert notifications[0]["flag_read"] is True

        nm.unclearNotification(1, notif_id)
        notifications, _ = nm.getNotifications(1)
        assert notifications[0]["flag_read"] is False


@pytest.fixture(scope="module")
def app_client():
    os.environ["DEFAULT_DIR"] = os.getcwd()
    from cde import app
    return app.test_client()


class TestSecurityHeadersAndAuth:
    """Tests for HTTP Security Headers and UserUtils.get_username hardening."""

    def test_http_security_headers_present(self, app_client):
        """Responses should include standard hardening headers."""
        response = app_client.get("/login/")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_get_username_rejects_sql_injection(self):
        """UserUtils.get_username should safely return None for non-integer / SQLi input."""
        from cde import UserUtils
        result = UserUtils.get_username("1 UNION SELECT 'admin'")
        assert result is None

    def test_get_username_route_enforces_auth_and_int(self, app_client):
        """Endpoint /get/username/<int:id_user> requires login and valid int."""
        res = app_client.get("/get/username/1")
        assert res.status_code in (302, 403)

        res_invalid = app_client.get("/get/username/invalid_id")
        assert res_invalid.status_code == 404
