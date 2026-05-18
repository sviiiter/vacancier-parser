from models.message import Message


class KeywordFilter:
    def __init__(self, keywords: list[str]) -> None:
        self._keywords = [kw.lower() for kw in keywords]

    def matches(self, message: Message) -> bool:
        text = message.description.lower()
        return all(kw in text for kw in self._keywords)
