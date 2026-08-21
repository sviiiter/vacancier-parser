from models.message import Message
from processor.interfaces import DuplicateCheckerProtocol, MessageFilterProtocol
from processor.text_cleaner import strip_html


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
            message.description = strip_html(message.description)
            filter_result = self._filter.matches(message)
            if filter_result.matches and not self._checker.is_duplicate(message):
                message.matched_keywords = filter_result.matched_keywords
                result.append(message)
        return result
