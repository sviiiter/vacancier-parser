import unittest
from datetime import datetime

from models.message import Message
from processor.duplicate_checker import DuplicateChecker


def _msg(link: str) -> Message:
    return Message(
        description="PHP developer",
        tg_channel_link="https://t.me/test",
        tg_message_link=link,
        created_date=datetime(2024, 1, 1),
    )


class TestDuplicateChecker(unittest.TestCase):
    def test_first_occurrence_not_duplicate(self) -> None:
        checker = DuplicateChecker()
        self.assertFalse(checker.is_duplicate(_msg("https://t.me/test/1")))

    def test_second_occurrence_is_duplicate(self) -> None:
        checker = DuplicateChecker()
        msg = _msg("https://t.me/test/1")
        checker.is_duplicate(msg)
        self.assertTrue(checker.is_duplicate(msg))

    def test_different_links_not_duplicate(self) -> None:
        checker = DuplicateChecker()
        checker.is_duplicate(_msg("https://t.me/test/1"))
        self.assertFalse(checker.is_duplicate(_msg("https://t.me/test/2")))

    def test_preseeded_link_is_duplicate(self) -> None:
        checker = DuplicateChecker(seen_links={"https://t.me/test/99"})
        self.assertTrue(checker.is_duplicate(_msg("https://t.me/test/99")))

    def test_unseen_link_with_seed_not_duplicate(self) -> None:
        checker = DuplicateChecker(seen_links={"https://t.me/test/99"})
        self.assertFalse(checker.is_duplicate(_msg("https://t.me/test/100")))

    def test_empty_seed_not_duplicate(self) -> None:
        checker = DuplicateChecker(seen_links=set())
        self.assertFalse(checker.is_duplicate(_msg("https://t.me/test/1")))
