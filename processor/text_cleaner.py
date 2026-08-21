import html
import re

_BR_RE = re.compile(r'<br\s*/?>', re.IGNORECASE)
_BLOCK_CLOSE_RE = re.compile(r'</(p|div|li|h[1-6]|tr)>', re.IGNORECASE)
_TAG_RE = re.compile(r'<[^>]+>')


def strip_html(text: str) -> str:
    text = _BR_RE.sub('\n', text)
    text = _BLOCK_CLOSE_RE.sub('\n', text)
    text = _TAG_RE.sub(' ', text)
    text = html.unescape(text)
    lines = [' '.join(line.split()) for line in text.splitlines()]
    lines = [line for line in lines if line]
    return '\n'.join(lines)
