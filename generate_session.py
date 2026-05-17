"""
One-time script to generate a Telegram session string.

Run this locally before deploying:
    python generate_session.py

Then copy the printed string into your .env file as TELEGRAM_SESSION_STRING.
The session string encodes your login credentials so subsequent runs
(including inside Docker) authenticate without an interactive prompt.
"""
import os

from dotenv import load_dotenv
from telethon.sessions import StringSession
from telethon.sync import TelegramClient

load_dotenv()

api_id = int(os.environ["TELEGRAM_API_ID"])
api_hash = os.environ["TELEGRAM_API_HASH"]

print("Connecting to Telegram — you will be asked for your phone number and the SMS code.\n")

with TelegramClient(StringSession(), api_id, api_hash) as client:
    session_string = client.session.save()

print("\nSession string generated. Add this to your .env file:")
print(f"\nTELEGRAM_SESSION_STRING={session_string}\n")
