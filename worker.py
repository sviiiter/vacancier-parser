import json
import logging
import os
import signal
import sys
from typing import Optional

import pika

from config import RABBITMQ_URL
from database.connection import get_connection, init_schema
from database.repository import MessageRepository
from models.message import Message
from processor.duplicate_checker import DuplicateChecker
from processor.text_cleaner import strip_html

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)


class MessageWorker:
    def __init__(self, rabbitmq_url: str, database_url: str) -> None:
        self._rabbitmq_url = rabbitmq_url
        self._database_url = database_url
        self._connection: Optional[pika.BlockingConnection] = None
        self._channel: Optional[pika.adapters.blocking_connection.BlockingChannel] = None
        self._repo: Optional[MessageRepository] = None
        self._checker: Optional[DuplicateChecker] = None

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, sig, frame):
        log.info("Received signal, shutting down gracefully...")
        self.shutdown()

    def start(self) -> None:
        try:
            self._setup_db()
            self._setup_rabbitmq()
            log.info("Worker started, listening on jobs.raw queue")
            self._channel.basic_qos(prefetch_count=1)
            self._channel.basic_consume(
                queue="jobs.raw",
                on_message_callback=self._process_message,
            )
            self._channel.start_consuming()
        except KeyboardInterrupt:
            self.shutdown()
        except Exception as e:
            log.error("Fatal error: %s", e)
            self.shutdown()

    def _setup_db(self) -> None:
        conn = get_connection(self._database_url)
        init_schema(conn)
        self._repo = MessageRepository(conn)
        self._checker = DuplicateChecker(conn)
        log.info("Database connection established")

    def _setup_rabbitmq(self) -> None:
        self._connection = pika.BlockingConnection(
            pika.URLParameters(self._rabbitmq_url)
        )
        self._channel = self._connection.channel()

        self._channel.queue_declare(
            queue="jobs.raw",
            durable=True,
            arguments={
                "x-dead-letter-exchange": "",
                "x-dead-letter-routing-key": "jobs.raw.dlq",
            },
        )

        self._channel.queue_declare(
            queue="jobs.raw.dlq",
            durable=True,
        )
        log.info("RabbitMQ connection established")

    def _process_message(self, ch, method, properties, body: bytes) -> None:
        try:
            message = Message.from_json(body.decode('utf-8'))

            # Check for duplicates by link
            if self._checker.exists(message.tg_message_link):
                log.info("Duplicate [%s]: %s", message.source, message.tg_message_link)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            message.description = strip_html(message.description)

            # Generate and check fingerprint
            fingerprint = DuplicateChecker.generate_fingerprint(message.description)
            if fingerprint and self._checker.exists_by_fingerprint(fingerprint):
                log.info("Duplicate by fingerprint [%s]: %s", message.source, message.tg_message_link)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            message.fingerprint = fingerprint
            self._repo.save(message)
            log.info("Saved [%s]: %s", message.source, message.tg_message_link)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except json.JSONDecodeError as e:
            log.error("Failed to decode message: %s", e)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            log.error("Error processing message: %s", e)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def shutdown(self) -> None:
        log.info("Shutting down...")
        if self._channel:
            try:
                self._channel.stop_consuming()
            except Exception:
                pass
        if self._connection:
            try:
                self._connection.close()
            except Exception:
                pass
        sys.exit(0)


if __name__ == "__main__":
    database_url = os.environ["DATABASE_URL"]
    rabbitmq_url = os.environ.get("RABBITMQ_URL", RABBITMQ_URL)

    worker = MessageWorker(rabbitmq_url, database_url)
    worker.start()
# @todo add processor/duplicate_checker.py