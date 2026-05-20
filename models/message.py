from dataclasses import dataclass
from datetime import datetime


@dataclass
class Message:
    description: str
    tg_channel_link: str
    tg_message_link: str
    created_date: datetime
    queue_sent: int = 0
    read: int = 0
