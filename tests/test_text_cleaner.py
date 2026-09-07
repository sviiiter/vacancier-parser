import pytest

from processor.text_cleaner import strip_html


def test_strip_html_removes_tags():
    """Test that HTML tags are removed."""
    html = "<p>Hello <b>World</b></p>"
    result = strip_html(html)
    assert result == "Hello World"


def test_strip_html_removes_nested_tags():
    """Test removal of nested HTML tags."""
    html = "<div><p>Nested <span>content</span></p></div>"
    result = strip_html(html)
    assert result == "Nested content"


def test_strip_html_preserves_text():
    """Test that text without tags is unchanged."""
    text = "Plain text without HTML"
    result = strip_html(text)
    assert result == "Plain text without HTML"


def test_strip_html_empty_string():
    """Test with empty string."""
    result = strip_html("")
    assert result == ""


def test_strip_html_none_value():
    """Test with None value."""
    result = strip_html(None)
    assert result is None


def test_strip_html_with_attributes():
    """Test removal of tags with attributes."""
    html = '<a href="http://example.com" class="link">Click here</a>'
    result = strip_html(html)
    assert result == "Click here"


def test_strip_html_multiple_lines():
    """Test multiline HTML."""
    html = """
    <div>
        <p>First paragraph</p>
        <p>Second paragraph</p>
    </div>
    """
    result = strip_html(html)
    assert "First paragraph" in result
    assert "Second paragraph" in result
    assert "<" not in result
    assert ">" not in result


def test_strip_html_with_special_chars():
    """Test HTML with special characters."""
    html = "<p>Salary: $50,000 &amp; benefits</p>"
    result = strip_html(html)
    assert "Salary: $50,000 &amp; benefits" in result
