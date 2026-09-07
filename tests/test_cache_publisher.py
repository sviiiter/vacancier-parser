from unittest.mock import MagicMock, call, patch
import sys

import pytest

# Mock redis module if not available
if 'redis' not in sys.modules:
    sys.modules['redis'] = MagicMock()

from cache.publisher import CachePublisher


class MockCursor:
    """Mock database cursor."""
    def __init__(self, results):
        self.results = results

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def execute(self, query, params=None):
        pass

    def fetchall(self):
        return self.results


def test_publish_for_subscribers_publishes_to_redis():
    """Test that messages are published to Redis with correct keys."""
    # Mock database connection
    mock_conn = MagicMock()
    
    # Mock Redis client
    mock_redis = MagicMock()

    # Mock subscriber query results
    subscriber_results = [
        {
            "id": 1,
            "chat_id": "123456",
            "message_sent_last_date": None,
            "filter_ids": [1, 2],
        },
    ]

    # Mock message query results
    message_results = [
        [101],
        [102],
        [103],
    ]

    # Setup mock connection to return different results for each cursor call
    cursor_calls = [
        MockCursor(subscriber_results),
        MockCursor(message_results),
    ]
    mock_conn.cursor = MagicMock(side_effect=lambda: cursor_calls.pop(0))

    publisher = CachePublisher(mock_conn, mock_redis)
    publisher.publish_for_subscribers()

    # Verify Redis operations
    mock_redis.sadd.assert_any_call("pending:123456", 101, 102, 103)
    mock_redis.sadd.assert_any_call("pending:index", "123456")


def test_publish_for_subscribers_skips_inactive():
    """Test that inactive subscribers are skipped."""
    mock_conn = MagicMock()
    mock_redis = MagicMock()

    # Subscriber with no filter_ids
    subscriber_results = [
        {
            "id": 1,
            "chat_id": "123456",
            "message_sent_last_date": None,
            "filter_ids": [],
        },
    ]

    cursor_calls = [
        MockCursor(subscriber_results),
    ]
    mock_conn.cursor = MagicMock(side_effect=lambda: cursor_calls.pop(0))

    publisher = CachePublisher(mock_conn, mock_redis)
    publisher.publish_for_subscribers()

    # Verify Redis was not called for empty filter_ids
    mock_redis.sadd.assert_not_called()


def test_publish_for_subscribers_multiple_subscribers():
    """Test publishing for multiple subscribers."""
    mock_conn = MagicMock()
    mock_redis = MagicMock()

    subscriber_results = [
        {
            "id": 1,
            "chat_id": "chat1",
            "message_sent_last_date": None,
            "filter_ids": [1],
        },
        {
            "id": 2,
            "chat_id": "chat2",
            "message_sent_last_date": None,
            "filter_ids": [2],
        },
    ]

    message_results_1 = [[101], [102]]
    message_results_2 = [[201], [202]]

    cursor_calls = [
        MockCursor(subscriber_results),
        MockCursor(message_results_1),
        MockCursor(message_results_2),
    ]
    mock_conn.cursor = MagicMock(side_effect=lambda: cursor_calls.pop(0))

    publisher = CachePublisher(mock_conn, mock_redis)
    publisher.publish_for_subscribers()

    # Verify both subscribers got their messages
    mock_redis.sadd.assert_any_call("pending:chat1", 101, 102)
    mock_redis.sadd.assert_any_call("pending:chat2", 201, 202)
    assert mock_redis.sadd.call_count >= 4  # At least 4 calls (2 per subscriber)
