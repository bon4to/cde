"""Rename the default administrator from Lucas Bonato to Admin."""

import sqlite3

from app.utils.cdeapp import config


def up():
    with sqlite3.connect(config.get_db_path()) as conn:
        conn.execute(
            """
            UPDATE users
            SET nome_user = 'ADMIN', sobrenome_user = ''
            WHERE login_user = 'ADMIN'
              AND nome_user = 'LUCAS'
              AND sobrenome_user = 'BONATO'
            """
        )
        conn.commit()


def down():
    with sqlite3.connect(config.get_db_path()) as conn:
        conn.execute(
            """
            UPDATE users
            SET nome_user = 'LUCAS', sobrenome_user = 'BONATO'
            WHERE login_user = 'ADMIN'
              AND nome_user = 'ADMIN'
              AND sobrenome_user = ''
            """
        )
        conn.commit()
