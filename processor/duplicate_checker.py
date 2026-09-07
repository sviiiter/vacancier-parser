import hashlib
import psycopg2.extensions


class DuplicateChecker:
    """Check if a message already exists in the database."""

    def __init__(self, conn: psycopg2.extensions.connection) -> None:
        self._conn = conn

    def exists(self, tg_message_link: str) -> bool:
        """Check if a message with the given link already exists."""
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM messages WHERE tg_message_link = %s",
                (tg_message_link,),
            )
            return cur.fetchone() is not None

    def exists_by_fingerprint(self, fingerprint: str) -> bool:
        """Check if a message with the given fingerprint already exists."""
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM messages WHERE fingerprint = %s",
                (fingerprint,),
            )
            return cur.fetchone() is not None

    @staticmethod
    def generate_fingerprint(description: str) -> str:
        """Generate a fingerprint from message description."""
        if not description:
            return ""
        text = description.lower()
        normalized = " ".join(text.split())
        return hashlib.sha256(normalized.encode()).hexdigest()
