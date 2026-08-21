import logging
import pika

from models.message import Message

log = logging.getLogger(__name__)


class JobPublisher:
    def __init__(self, rabbitmq_url: str) -> None:
        self._url = rabbitmq_url
        self._connection = None
        self._channel = None
        self._connect()

    def _connect(self) -> None:
        self._connection = pika.BlockingConnection(pika.URLParameters(self._url))
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

    def publish(self, message: Message) -> None:
        try:
            self._channel.basic_publish(
                exchange="",
                routing_key="jobs.raw",
                body=message.to_json(),
                properties=pika.BasicProperties(delivery_mode=2),
            )
            log.debug("Published message: %s", message.tg_message_link)
        except Exception as e:
            log.error("Failed to publish message: %s", e)
            self._reconnect()

    def _reconnect(self) -> None:
        try:
            if self._connection:
                self._connection.close()
        except Exception:
            pass
        self._connect()

    def close(self) -> None:
        if self._connection:
            self._connection.close()
