import pytest

from processor.openai_matcher import OpenAIMatcher


class MockConnection:
    """Mock database connection for testing."""
    pass


def test_openai_matcher_returns_empty():
    """Test that OpenAIMatcher returns empty list (placeholder implementation)."""
    conn = MockConnection()
    matcher = OpenAIMatcher(conn)

    filters = [
        {
            "id": 1,
            "type": "file",
            "content": "Some OpenAI prompt content",
        },
    ]

    description = "Job description to match"
    matched_ids = matcher.match_message(1, description, filters)

    assert matched_ids == []


def test_openai_matcher_with_multiple_filters():
    """Test OpenAIMatcher with multiple filters."""
    conn = MockConnection()
    matcher = OpenAIMatcher(conn)

    filters = [
        {"id": 1, "type": "file", "content": "Prompt 1"},
        {"id": 2, "type": "file", "content": "Prompt 2"},
        {"id": 3, "type": "file", "content": "Prompt 3"},
    ]

    description = "Job description"
    matched_ids = matcher.match_message(1, description, filters)

    assert matched_ids == []


def test_openai_matcher_empty_description():
    """Test OpenAIMatcher with empty description."""
    conn = MockConnection()
    matcher = OpenAIMatcher(conn)

    filters = [
        {"id": 1, "type": "file", "content": "Some prompt"},
    ]

    matched_ids = matcher.match_message(1, "", filters)

    assert matched_ids == []
