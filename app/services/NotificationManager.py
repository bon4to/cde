from app.models import dbUtils as db

def createNotificationsTable() -> tuple[None, str]:
    try:
        query = '''
            CREATE TABLE IF NOT EXISTS tbl_notifications (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                id_user    INTEGER(10),
                title      VARCHAR(20),
                message    VARCHAR(200),
                date       DATETIME,
                flag_read  BOOLEAN DEFAULT FALSE
            );
        '''
        dsn = 'LOCAL'
        db.query(query, dsn)
    except Exception as e:
        return None, str(e)
    return None, ""


def setNotification(userid: int, title: str, message: str) -> tuple[None, str]:
    try:
        query = f'''
            INSERT INTO tbl_notifications (
                id_user, title, message, date
            ) VALUES (
                {userid}, "{title}", "{message}", datetime('now', '-3 hours')
            );
        '''
        dsn = 'LOCAL'
        db.query(query, dsn)
    except Exception as e:
        return None, str(e)
    return None, None


def getNotifications(userid: int) -> tuple[list | None, str]:
    try:
        query = f'''
            SELECT id, title, message, date, flag_read
            FROM tbl_notifications
            WHERE id_user = {userid}
            ORDER BY date DESC
        '''
        dsn = 'LOCAL'
        result, _ = db.query(query, dsn)
        notifications = []
        for row in result:
            notifications.append({
                'id': row[0],
                'title': row[1],
                'message': row[2],
                'date': row[3],
                'flag_read': row[4]
            })
        return notifications, None
    except Exception as e:
        return None, str(e)


def clearNotification(userid: int, id: int):
    pass


def clearAllNotifications(userid: int):
    pass