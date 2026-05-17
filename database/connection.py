import os
import sqlite3


def get_connection(db_path: str) -> sqlite3.Connection:
    directory = os.path.dirname(os.path.abspath(db_path))
    os.makedirs(directory, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            description     TEXT NOT NULL,
            tg_channel_link TEXT NOT NULL,
            tg_message_link TEXT NOT NULL UNIQUE,
            created_date    TEXT NOT NULL
        )
    """)
    conn.commit()
