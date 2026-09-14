import sqlite3
from app.utils import cdeapp
from app.models import dbUtils as db


# cria a tabela de notificações caso ela não exista
def createNotificationsTable() -> tuple[None, str]:
    try:
        query = """
            CREATE TABLE IF NOT EXISTS tbl_notifications (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                id_user    INTEGER(10),
                title      VARCHAR(20),
                message    VARCHAR(200),
                date       DATETIME,
                flag_read  BOOLEAN DEFAULT FALSE
            );
        """
        dsn = "LOCAL"
        db.query(query, dsn)
    except Exception as e:
        return None, str(e)
    return None, ""


# cria uma entrada de notificação para o usuário
def setNotification(userid: int, title: str, message: str) -> tuple[None, str]:
    try:
        title = title.strip().upper()
        message = message.strip().capitalize()
    except Exception as e:
        return None, str(e)

    # pega todos os usuários e cria um registro para cada um caso o id_user seja 0
    users = []
    try:
        userid = int(userid)
    except (ValueError, TypeError):
        return None, "Invalid userid"

    if userid != 0:
        users.append(userid)
    else:
        try:
            query = """
                SELECT id_user
                FROM users
                ORDER BY id_user ASC;
            """
            dsn = "LOCAL"
            result, _ = db.query(query, dsn)

            for row in result:
                users.append(row[0])
        except Exception as e:
            return None, str(e)

    try:
        db_path = cdeapp.config.get_db_path()
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            for user in users:
                cursor.execute(
                    """
                    INSERT INTO tbl_notifications (
                        id_user, title, message, date
                    ) VALUES (
                        ?, ?, ?, datetime('now', '-3 hours')
                    );
                    """,
                    (int(user), title, message),
                )
            conn.commit()
    except Exception as e:
        return None, str(e)
    return None, ""


# pega todas as notificações do usuário
def getNotifications(userid: int, id_notification: int = 0) -> tuple[list | None, str]:
    try:
        db_path = cdeapp.config.get_db_path()
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            if id_notification != 0:
                cursor.execute(
                    """
                    SELECT id, title, message, date, flag_read
                    FROM tbl_notifications
                    WHERE id_user = ?
                    AND id = ?;
                    """,
                    (int(userid), int(id_notification)),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, title, message, date, flag_read
                    FROM tbl_notifications
                    WHERE id_user = ?
                    ORDER BY date DESC;
                    """,
                    (int(userid),),
                )
            result = cursor.fetchall()

        notifications = []
        for row in result:
            notifications.append(
                {
                    "id": row[0],
                    "title": row[1],
                    "message": row[2],
                    "date": row[3],
                    "flag_read": bool(row[4]),
                }
            )
        return notifications, None
    except Exception as e:
        return None, str(e)


# limpa/ marca como lida uma notificação do usuário
def clearNotification(userid: int, id: int):
    try:
        db_path = cdeapp.config.get_db_path()
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE tbl_notifications
                SET flag_read = 1
                WHERE id_user = ?
                AND id = ?;
                """,
                (int(userid), int(id)),
            )
            conn.commit()
        return None, None
    except Exception as e:
        return None, str(e)


# marca como não lida uma notificação do usuário
def unclearNotification(userid: int, id: int):
    try:
        db_path = cdeapp.config.get_db_path()
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE tbl_notifications
                SET flag_read = 0
                WHERE id_user = ?
                AND id = ?;
                """,
                (int(userid), int(id)),
            )
            conn.commit()
        return None, None
    except Exception as e:
        return None, str(e)


def clearAllNotifications(userid: int):
    pass
