from models.message import Message


class FilterResult:
    def __init__(self, matches: bool, matched_keywords: list[str]):
        self.matches = matches
        self.matched_keywords = matched_keywords


class KeywordFilter:
    def __init__(self, rules: dict) -> None:
        self._required = [kw.lower() for kw in rules.get("required", [])]
        self._any = [kw.lower() for kw in rules.get("any", [])]
        self._exclude = [kw.lower() for kw in rules.get("exclude", [])]

    def matches(self, message: Message) -> FilterResult:
        text = message.description.lower()
        matched = []

        if self._required:
            for kw in self._required:
                if kw not in text:
                    return FilterResult(False, [])
                matched.append(kw)

        if self._any:
            any_match = False
            for kw in self._any:
                if kw in text:
                    matched.append(kw)
                    any_match = True
            if not any_match:
                return FilterResult(False, [])

        for kw in self._exclude:
            if kw in text:
                return FilterResult(False, [])

        return FilterResult(True, list(set(matched)))
