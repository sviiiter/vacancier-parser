import logging
import os

import psycopg2
import psycopg2.extras


def get_connection(database_url: str) -> psycopg2.extensions.connection:
    return psycopg2.connect(database_url, cursor_factory=psycopg2.extras.RealDictCursor)


def init_schema(conn: psycopg2.extensions.connection) -> None:
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id              SERIAL PRIMARY KEY,
                description     TEXT NOT NULL,
                tg_channel_link TEXT NOT NULL,
                tg_message_link TEXT NOT NULL UNIQUE,
                created_date    TIMESTAMPTZ NOT NULL,
                source          TEXT NOT NULL DEFAULT 'telegram',
                queue_sent      INTEGER NOT NULL DEFAULT 0,
                read            INTEGER NOT NULL DEFAULT 0
            )
        """)
        # Migrations for databases that predate new columns
        for column, definition in [
            ("queue_sent", "INTEGER NOT NULL DEFAULT 0"),
            ("read",       "INTEGER NOT NULL DEFAULT 0"),
            ("source",     "TEXT NOT NULL DEFAULT 'telegram'"),
            ("fingerprint", "TEXT UNIQUE"),
            ("matched_keywords", "JSONB"),
        ]:
            cur.execute(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_name = 'messages' AND column_name = %s",
                (column,),
            )
            if cur.fetchone() is None:
                cur.execute(f'ALTER TABLE messages ADD COLUMN "{column}" {definition}')

        cur.execute("""
            CREATE TABLE IF NOT EXISTS file (
                id       SERIAL PRIMARY KEY,
                filename TEXT NOT NULL,
                content  TEXT NOT NULL
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS filters (
                id      SERIAL PRIMARY KEY,
                type    TEXT NOT NULL DEFAULT 'json' CHECK (type IN ('file', 'json')),
                extra   TEXT,
                file_id INTEGER REFERENCES file(id) ON DELETE CASCADE
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS message_filters (
                message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
                filter_id  INTEGER NOT NULL REFERENCES filters(id) ON DELETE CASCADE,
                matched_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                PRIMARY KEY (message_id, filter_id)
            )
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_message_filters_filter_id ON message_filters(filter_id)
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_created_date ON messages(created_date)
        """)
    conn.commit()


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    database_url = os.environ["DATABASE_URL"]
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    log = logging.getLogger(__name__)
    log.info("Connecting to: %s", database_url)
    conn = get_connection(database_url)
    with conn.cursor() as cur:
        cur.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'messages'"
        )
        before = {row["column_name"] for row in cur.fetchall()}
    log.info("Columns before: %s", sorted(before))
    init_schema(conn)
    with conn.cursor() as cur:
        cur.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'messages'"
        )
        after = {row["column_name"] for row in cur.fetchall()}
    log.info("Columns after:  %s", sorted(after))
    added = after - before
    log.info("Added: %s", sorted(added) if added else "(none — already up to date)")
    conn.close()
