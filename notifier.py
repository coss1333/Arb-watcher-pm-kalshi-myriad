import os
import logging
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

_TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = None
if _TELEGRAM_TOKEN and _CHAT_ID:
    bot = Bot(token=_TELEGRAM_TOKEN)

def send_alert(message: str):
    # Send a message to Telegram chat if configured, else print to console.
    if bot is None:
        print("[TELEGRAM NOT CONFIGURED]\n" + message)
        return
    try:
        bot.send_message(chat_id=_CHAT_ID, text=message, disable_web_page_preview=True)
    except Exception as e:
        logging.exception("Failed to send Telegram message: %s", e)
        print("[SEND FAILED]\n" + message)
