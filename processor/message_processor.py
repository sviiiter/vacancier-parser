from models.message import Message
from processor.interfaces import DuplicateCheckerProtocol, MessageFilterProtocol


class MessageProcessor:
    def __init__(
        self,
        filter: MessageFilterProtocol,
        checker: DuplicateCheckerProtocol,
    ) -> None:
        self._filter = filter
        self._checker = checker

    def process(self, messages: list[Message]) -> list[Message]:
        result = []
        for message in messages:
            if self._filter.matches(message) and not self._checker.is_duplicate(message):
                result.append(message)
        return result
