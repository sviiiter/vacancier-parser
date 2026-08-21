from typing import Protocol, TYPE_CHECKING

from models.message import Message

if TYPE_CHECKING:
    from processor.keyword_filter import FilterResult


class MessageFilterProtocol(Protocol):
    def matches(self, message: Message) -> 'FilterResult':
        ...


class DuplicateCheckerProtocol(Protocol):
    def is_duplicate(self, message: Message) -> bool:
        ...
