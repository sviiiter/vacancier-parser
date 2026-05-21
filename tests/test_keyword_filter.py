import unittest
from datetime import datetime

from models.message import Message
from processor.keyword_filter import KeywordFilter


def _msg(text: str) -> Message:
    return Message(
        description=text,
        tg_channel_link="https://t.me/test",
        tg_message_link="https://t.me/test/1",
        created_date=datetime(2024, 1, 1),
    )


class TestKeywordFilter(unittest.TestCase):
    def setUp(self) -> None:
        self.filter = KeywordFilter([["PHP", "Senior"], ["backend", "senior"]])

    def test_matches_php_and_senior(self) -> None:
        self.assertTrue(self.filter.matches(_msg("Looking for a Senior PHP developer")))

    def test_matches_backend_and_senior(self) -> None:
        self.assertTrue(self.filter.matches(_msg("Senior backend engineer needed")))

    def test_matches_case_insensitive(self) -> None:
        self.assertTrue(self.filter.matches(_msg("senior backend position open")))

    def test_no_match_php_without_senior(self) -> None:
        self.assertFalse(self.filter.matches(_msg("PHP developer wanted")))

    def test_no_match_senior_alone(self) -> None:
        self.assertFalse(self.filter.matches(_msg("senior frontend engineer")))

    def test_no_match_unrelated_text(self) -> None:
        self.assertFalse(self.filter.matches(_msg("Frontend JavaScript React developer")))

    def test_no_match_empty_description(self) -> None:
        self.assertFalse(self.filter.matches(_msg("")))
