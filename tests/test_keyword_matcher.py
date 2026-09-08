import pytest

from processor.keyword_matcher import KeywordMatcher


class MockConnection:
    """Mock database connection for testing."""
    pass


def test_required_keywords_all_present():
    """Test that all required keywords must be present."""
    conn = MockConnection()
    matcher = KeywordMatcher(conn)

    filters = [
        {
            "id": 1,
            "type": "json",
            "extra": '{"required": ["python", "developer"]}',
        },
    ]

    description = "Looking for a Python Developer with 5 years experience"
    matched_ids = matcher.match_message(1, description, filters)

    assert matched_ids == [1]


def test_required_keywords_missing():
    """Test that filter doesn't match if required keyword is missing."""
    conn = MockConnection()
    matcher = KeywordMatcher(conn)

    filters = [
        {
            "id": 1,
            "type": "json",
            "extra": '{"required": ["python", "senior"]}',
        },
    ]

    description = "Looking for a Python Developer"
    matched_ids = matcher.match_message(1, description, filters)

    assert matched_ids == []


def test_any_keywords_one_present():
    """Test that at least one 'any' keyword must be present."""
    conn = MockConnection()
    matcher = KeywordMatcher(conn)

    filters = [
        {
            "id": 1,
            "type": "json",
            "extra": '{"any": ["senior", "junior", "mid-level"]}',
        },
    ]

    description = "Looking for a junior Python Developer"
    matched_ids = matcher.match_message(1, description, filters)

    assert matched_ids == [1]


def test_any_keywords_none_present():
    """Test that filter doesn't match if no 'any' keyword is present."""
    conn = MockConnection()
    matcher = KeywordMatcher(conn)

    filters = [
        {
            "id": 1,
            "type": "json",
            "extra": '{"any": ["senior", "manager"]}',
        },
    ]

    description = "Looking for a Python Developer"
    matched_ids = matcher.match_message(1, description, filters)

    assert matched_ids == []


def test_exclude_keywords_none_present():
    """Test that filter matches when excluded keywords are not present."""
    conn = MockConnection()
    matcher = KeywordMatcher(conn)

    filters = [
        {
            "id": 1,
            "type": "json",
            "extra": '{"any": ["python"], "exclude": ["wordpress"]}',
        },
    ]

    description = "Looking for a Python Developer"
    matched_ids = matcher.match_message(1, description, filters)

    assert matched_ids == [1]


def test_exclude_keywords_present():
    """Test that filter doesn't match if excluded keyword is present."""
    conn = MockConnection()
    matcher = KeywordMatcher(conn)

    filters = [
        {
            "id": 1,
            "type": "json",
            "extra": '{"any": ["python"], "exclude": ["wordpress"]}',
        },
    ]

    description = "Looking for a Python Developer with WordPress experience"
    matched_ids = matcher.match_message(1, description, filters)

    assert matched_ids == []


def test_combined_rules():
    """Test combination of required, any, and exclude rules."""
    conn = MockConnection()
    matcher = KeywordMatcher(conn)

    filters = [
        {
            "id": 1,
            "type": "json",
            "extra": '{"required": ["python"], "any": ["senior", "lead"], "exclude": ["wordpress"]}',
        },
    ]

    # Match: has required, has any, no exclude
    description = "Senior Python Developer needed"
    matched_ids = matcher.match_message(1, description, filters)
    assert matched_ids == [1]

    # No match: has required and any but has exclude
    description = "Senior Python Developer with WordPress"
    matched_ids = matcher.match_message(1, description, filters)
    assert matched_ids == []

    # No match: missing required keyword
    description = "Senior Java Developer"
    matched_ids = matcher.match_message(1, description, filters)
    assert matched_ids == []


def test_case_insensitive():
    """Test that matching is case-insensitive."""
    conn = MockConnection()
    matcher = KeywordMatcher(conn)

    filters = [
        {"id": 1, "type": "json", "extra": '{"required": ["PYTHON"]}'},
    ]

    description = "Looking for python developer"
    matched_ids = matcher.match_message(1, description, filters)

    assert matched_ids == [1]


def test_empty_description():
    """Test with empty description."""
    conn = MockConnection()
    matcher = KeywordMatcher(conn)

    filters = [
        {"id": 1, "type": "json", "extra": '{"required": ["python"]}'},
    ]

    matched_ids = matcher.match_message(1, "", filters)

    assert matched_ids == []


def test_invalid_json():
    """Test handling of invalid JSON in filter."""
    conn = MockConnection()
    matcher = KeywordMatcher(conn)

    filters = [
        {"id": 1, "type": "json", "extra": 'invalid json'},
    ]

    description = "Looking for a Python Developer"
    matched_ids = matcher.match_message(1, description, filters)

    assert matched_ids == []


def test_no_rules():
    """Test that filter with no rules doesn't match."""
    conn = MockConnection()
    matcher = KeywordMatcher(conn)

    filters = [
        {"id": 1, "type": "json", "extra": '{}'},
    ]

    description = "Looking for a Python Developer"
    matched_ids = matcher.match_message(1, description, filters)

    assert matched_ids == []
