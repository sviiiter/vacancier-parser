import pytest

from processor.keyword_matcher import KeywordMatcher


class MockConnection:
    """Mock database connection for testing."""
    pass


def test_match_message_with_matching_keywords():
    """Test that KeywordMatcher finds matching keywords in message."""
    conn = MockConnection()
    matcher = KeywordMatcher(conn)

    filters = [
        {
            "id": 1,
            "type": "json",
            "extra": '["python", "developer"]',
        },
        {
            "id": 2,
            "type": "json",
            "extra": '["php", "senior"]',
        },
    ]

    description = "Looking for a Python Developer with 5 years experience"
    matched_ids = matcher.match_message(1, description, filters)

    assert matched_ids == [1]


def test_match_message_with_multiple_matches():
    """Test matching against multiple filters."""
    conn = MockConnection()
    matcher = KeywordMatcher(conn)

    filters = [
        {"id": 1, "type": "json", "extra": '["python", "developer"]'},
        {"id": 2, "type": "json", "extra": '["senior"]'},
    ]

    description = "Senior Python Developer needed"
    matched_ids = matcher.match_message(1, description, filters)

    assert set(matched_ids) == {1, 2}


def test_match_message_case_insensitive():
    """Test that matching is case-insensitive."""
    conn = MockConnection()
    matcher = KeywordMatcher(conn)

    filters = [
        {"id": 1, "type": "json", "extra": '["Python"]'},
    ]

    description = "Looking for a python developer"
    matched_ids = matcher.match_message(1, description, filters)

    assert matched_ids == [1]


def test_match_message_no_matches():
    """Test when no keywords match."""
    conn = MockConnection()
    matcher = KeywordMatcher(conn)

    filters = [
        {"id": 1, "type": "json", "extra": '["java", "rust"]'},
    ]

    description = "Looking for a Python Developer"
    matched_ids = matcher.match_message(1, description, filters)

    assert matched_ids == []


def test_match_message_empty_description():
    """Test with empty description."""
    conn = MockConnection()
    matcher = KeywordMatcher(conn)

    filters = [
        {"id": 1, "type": "json", "extra": '["python"]'},
    ]

    matched_ids = matcher.match_message(1, "", filters)

    assert matched_ids == []


def test_match_message_invalid_json():
    """Test handling of invalid JSON in filter."""
    conn = MockConnection()
    matcher = KeywordMatcher(conn)

    filters = [
        {"id": 1, "type": "json", "extra": 'invalid json'},
    ]

    description = "Looking for a Python Developer"
    matched_ids = matcher.match_message(1, description, filters)

    assert matched_ids == []


def test_match_message_substring_matching():
    """Test substring matching of keywords."""
    conn = MockConnection()
    matcher = KeywordMatcher(conn)

    filters = [
        {"id": 1, "type": "json", "extra": '["dev"]'},
    ]

    description = "Looking for a Developer"
    matched_ids = matcher.match_message(1, description, filters)

    assert matched_ids == [1]
