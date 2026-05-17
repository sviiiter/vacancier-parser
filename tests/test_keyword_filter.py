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
        self.filter = KeywordFilter(["PHP", "backend", "senior"])

    def test_matches_exact_uppercase(self) -> None:
        self.assertTrue(self.filter.matches(_msg("Looking for a PHP developer")))

    def test_matches_lowercase(self) -> None:
        self.assertTrue(self.filter.matches(_msg("php job available")))

    def test_matches_mixed_case(self) -> None:
        self.assertTrue(self.filter.matches(_msg("Senior Backend Engineer needed")))

    def test_matches_backend(self) -> None:
        self.assertTrue(self.filter.matches(_msg("backend developer required")))

    def test_matches_senior(self) -> None:
        self.assertTrue(self.filter.matches(_msg("we need a senior specialist")))

    def test_no_match_unrelated_text(self) -> None:
        self.assertFalse(self.filter.matches(_msg("Frontend JavaScript React developer")))

    def test_no_match_empty_description(self) -> None:
        self.assertFalse(self.filter.matches(_msg("")))

    def test_any_keyword_sufficient(self) -> None:
        self.assertTrue(self.filter.matches(_msg("senior frontend engineer")))
