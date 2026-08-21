import unittest

from processor.text_cleaner import strip_html


class TestStripHtml(unittest.TestCase):
    def test_strip_simple_tags(self) -> None:
        self.assertEqual(strip_html("<b>Senior PHP</b>"), "Senior PHP")

    def test_strip_paragraph_tags(self) -> None:
        self.assertEqual(strip_html("<p>Full Stack Developer</p>"), "Full Stack Developer")

    def test_strip_nested_tags(self) -> None:
        self.assertEqual(strip_html("<div><b>Senior</b> <i>PHP</i></div>"), "Senior PHP")

    def test_decode_html_entities(self) -> None:
        self.assertEqual(strip_html("Full &amp; Remote"), "Full & Remote")

    def test_decode_multiple_entities(self) -> None:
        self.assertEqual(strip_html("&lt;b&gt;PHP&lt;/b&gt; &quot;5+ years&quot;"), '<b>PHP</b> "5+ years"')

    def test_strip_tags_and_decode_entities(self) -> None:
        self.assertEqual(strip_html("<p>Senior &amp; Remote</p>"), "Senior & Remote")

    def test_plain_text_passthrough(self) -> None:
        self.assertEqual(strip_html("Senior PHP Developer"), "Senior PHP Developer")

    def test_preserve_line_breaks_between_paragraphs(self) -> None:
        self.assertEqual(strip_html("<p>A</p><p>B</p>"), "A\nB")

    def test_empty_string(self) -> None:
        self.assertEqual(strip_html(""), "")

    def test_whitespace_trimming(self) -> None:
        self.assertEqual(strip_html("  <b>Senior</b>  "), "Senior")

    def test_nbsp_entity_decoded(self) -> None:
        result = strip_html("Remote&nbsp;Work")
        self.assertIn("Remote", result)
        self.assertIn("Work", result)

    def test_br_tags_to_newlines(self) -> None:
        self.assertEqual(strip_html("Line1<br>Line2"), "Line1\nLine2")
        self.assertEqual(strip_html("Line1<br/>Line2"), "Line1\nLine2")
        self.assertEqual(strip_html("Line1<BR>Line2"), "Line1\nLine2")

    def test_list_items_to_newlines(self) -> None:
        self.assertEqual(strip_html("<li>One</li><li>Two</li><li>Three</li>"), "One\nTwo\nThree")

    def test_nested_block_elements(self) -> None:
        self.assertEqual(strip_html("<div><p>Senior</p><p>PHP</p></div>"), "Senior\nPHP")

    def test_mixed_inline_and_block(self) -> None:
        self.assertEqual(strip_html("<p><b>Senior</b> <i>PHP</i></p><p>Developer</p>"), "Senior PHP\nDeveloper")

    def test_multiple_consecutive_blocks_no_blank_lines(self) -> None:
        self.assertEqual(strip_html("<p>A</p><p></p><p>B</p>"), "A\nB")
