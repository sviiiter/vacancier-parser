from datetime import datetime, timezone
from types import TracebackType

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import Message as TgMessage

from models.message import Message


class TelegramChannelFetcher:
    def __init__(self, api_id: int, api_hash: str, session_string: str) -> None:
        self._client = TelegramClient(
            StringSession(session_string), api_id, api_hash
        )

    async def __aenter__(self) -> "TelegramChannelFetcher":
        await self._client.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self._client.disconnect()

    async def fetch_new_messages(
        self, channel: str, since: datetime | None
    ) -> list[Message]:
        channel_name = channel.lstrip("@")
        channel_link = f"https://t.me/{channel_name}"
        entity = await self._client.get_entity(channel)

        aware_since: datetime | None = None
        if since is not None:
            aware_since = since if since.tzinfo is not None else since.replace(tzinfo=timezone.utc)

        messages: list[Message] = []

        # iter_messages returns newest-first by default; break when we pass since
        async for tg_msg in self._client.iter_messages(entity, limit=500):
            if not isinstance(tg_msg, TgMessage) or not tg_msg.text:
                continue

            msg_date = tg_msg.date
            if msg_date.tzinfo is None:
                msg_date = msg_date.replace(tzinfo=timezone.utc)

            if aware_since is not None and msg_date <= aware_since:
                break

            messages.append(
                Message(
                    description=tg_msg.text,
                    tg_channel_link=channel_link,
                    tg_message_link=f"{channel_link}/{tg_msg.id}",
                    created_date=msg_date,
                    source="telegram",
                )
            )

        return messages
