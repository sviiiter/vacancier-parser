import unittest
from datetime import datetime

from models.message import Message
from processor.duplicate_checker import DuplicateChecker
from processor.keyword_filter import KeywordFilter
from processor.message_processor import MessageProcessor


def _msg(text: str, link: str) -> Message:
    return Message(
        description=text,
        tg_channel_link="https://t.me/test",
        tg_message_link=link,
        created_date=datetime(2024, 1, 1),
    )


from processor.keyword_filter import FilterResult


class _AlwaysMatchFilter:
    def matches(self, message: Message) -> FilterResult:
        return FilterResult(True, ["test"])


class _NeverMatchFilter:
    def matches(self, message: Message) -> FilterResult:
        return FilterResult(False, [])


class _NeverDuplicateChecker:
    def is_duplicate(self, message: Message) -> bool:
        return False


class _AlwaysDuplicateChecker:
    def is_duplicate(self, message: Message) -> bool:
        return True


class TestMessageProcessor(unittest.TestCase):
    def test_passes_filter_and_not_duplicate_is_included(self) -> None:
        processor = MessageProcessor(_AlwaysMatchFilter(), _NeverDuplicateChecker())
        result = processor.process([_msg("PHP job", "https://t.me/test/1")])
        self.assertEqual(len(result), 1)

    def test_fails_filter_is_excluded(self) -> None:
        processor = MessageProcessor(_NeverMatchFilter(), _NeverDuplicateChecker())
        result = processor.process([_msg("unrelated text", "https://t.me/test/1")])
        self.assertEqual(len(result), 0)

    def test_duplicate_is_excluded(self) -> None:
        processor = MessageProcessor(_AlwaysMatchFilter(), _AlwaysDuplicateChecker())
        result = processor.process([_msg("PHP job", "https://t.me/test/1")])
        self.assertEqual(len(result), 0)

    def test_empty_input_returns_empty(self) -> None:
        processor = MessageProcessor(_AlwaysMatchFilter(), _NeverDuplicateChecker())
        self.assertEqual(processor.process([]), [])

    def test_mixed_batch_with_real_collaborators(self) -> None:
        processor = MessageProcessor(
            KeywordFilter({"required": ["php"], "any": ["developer", "engineer"], "exclude": []}),
            DuplicateChecker(),
        )
        messages = [
            _msg("PHP developer needed", "https://t.me/test/1"),
            _msg("Frontend React job", "https://t.me/test/2"),       # filtered out
            _msg("PHP developer needed", "https://t.me/test/1"),     # duplicate
            _msg("Senior PHP engineer", "https://t.me/test/3"),
        ]
        result = processor.process(messages)
        self.assertEqual(len(result), 2)
        links = [m.tg_message_link for m in result]
        self.assertIn("https://t.me/test/1", links)
        self.assertIn("https://t.me/test/3", links)
