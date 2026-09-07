import re


def strip_html(text: str) -> str:
    if not text:
        return text
    return re.sub(r'<[^>]+>', '', text)
