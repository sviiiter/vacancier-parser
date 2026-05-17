from typing import Protocol

from models.message import Message


class MessageFilterProtocol(Protocol):
    def matches(self, message: Message) -> bool:
        ...


class DuplicateCheckerProtocol(Protocol):
    def is_duplicate(self, message: Message) -> bool:
        ...
