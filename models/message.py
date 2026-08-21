import json
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class Message:
    description: str
    tg_channel_link: str
    tg_message_link: str
    created_date: datetime
    source: str = "telegram"
    queue_sent: int = 0
    read: int = 0
    matched_keywords: list[str] = field(default_factory=list)
    fingerprint: str = ""

    def to_json(self) -> str:
        data = asdict(self)
        data['created_date'] = self.created_date.isoformat()
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        data = json.loads(json_str)
        data['created_date'] = datetime.fromisoformat(data['created_date'])
        return cls(**data)
