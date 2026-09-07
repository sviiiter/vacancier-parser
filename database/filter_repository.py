import psycopg2.extensions


class FilterRepository:
    def __init__(self, conn: psycopg2.extensions.connection) -> None:
        self._conn = conn

    def list_filters(self) -> list[dict]:
        with self._conn.cursor() as cur:
            cur.execute(
                """SELECT filters.id, filters.type, filters.extra, file.content
                   FROM filters
                   LEFT JOIN file ON file.id = filters.file_id"""
            )
            return [dict(row) for row in cur.fetchall()]

    def save_message_filters(self, message_id: int, filter_ids: list[int]) -> None:
        if not filter_ids:
            return
        with self._conn.cursor() as cur:
            cur.executemany(
                """INSERT INTO message_filters (message_id, filter_id)
                   VALUES (%s, %s)
                   ON CONFLICT DO NOTHING""",
                [(message_id, fid) for fid in filter_ids],
            )
        self._conn.commit()
