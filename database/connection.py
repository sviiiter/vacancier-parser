import logging
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
            created_date    TEXT NOT NULL,
            queue_sent      INTEGER NOT NULL DEFAULT 0,
            read            INTEGER NOT NULL DEFAULT 0
        )
    """)
    # Migrations for existing databases that predate these columns
    existing = {row[1] for row in conn.execute("PRAGMA table_info(messages)").fetchall()}
    for column, definition in [
        ("queue_sent", "INTEGER NOT NULL DEFAULT 0"),
        ("read",       "INTEGER NOT NULL DEFAULT 0"),
    ]:
        if column not in existing:
            conn.execute(f'ALTER TABLE messages ADD COLUMN "{column}" {definition}')
    conn.commit()


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    db_path = os.getenv("DB_PATH", "data/vacancier.db")
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    log = logging.getLogger(__name__)
    log.info("DB path: %s", os.path.abspath(db_path))
    conn = get_connection(db_path)
    before = {row[1] for row in conn.execute("PRAGMA table_info(messages)").fetchall()}
    log.info("Columns before: %s", sorted(before))
    init_schema(conn)
    after = {row[1] for row in conn.execute("PRAGMA table_info(messages)").fetchall()}
    log.info("Columns after:  %s", sorted(after))
    added = after - before
    log.info("Added: %s", sorted(added) if added else "(none — already up to date)")
    conn.close()
