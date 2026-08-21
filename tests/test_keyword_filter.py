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
        self.filter = KeywordFilter({
            "required": ["php"],
            "any": ["developer", "engineer"],
            "exclude": ["wordpress"],
        })

    def test_matches_all_required_and_any(self) -> None:
        result = self.filter.matches(_msg("Looking for a PHP developer"))
        self.assertTrue(result.matches)
        self.assertIn("php", result.matched_keywords)
        self.assertIn("developer", result.matched_keywords)

    def test_matches_required_and_any_engineer(self) -> None:
        result = self.filter.matches(_msg("Senior PHP engineer needed"))
        self.assertTrue(result.matches)
        self.assertIn("php", result.matched_keywords)
        self.assertIn("engineer", result.matched_keywords)

    def test_matches_case_insensitive(self) -> None:
        result = self.filter.matches(_msg("PHP DEVELOPER position open"))
        self.assertTrue(result.matches)

    def test_no_match_missing_required_keyword(self) -> None:
        result = self.filter.matches(_msg("Java developer wanted"))
        self.assertFalse(result.matches)

    def test_no_match_missing_any_keyword(self) -> None:
        result = self.filter.matches(_msg("PHP position open"))
        self.assertFalse(result.matches)

    def test_no_match_exclude_keyword_present(self) -> None:
        result = self.filter.matches(_msg("PHP WordPress developer needed"))
        self.assertFalse(result.matches)

    def test_no_match_empty_description(self) -> None:
        result = self.filter.matches(_msg(""))
        self.assertFalse(result.matches)
