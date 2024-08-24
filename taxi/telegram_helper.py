import os

import telebot
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = telebot.TeleBot(BOT_TOKEN)


def send_message(message: str) -> dict:
    try:
        bot.send_message(CHAT_ID, message)
        return {"success": True, "message": "Message sent successfully"}
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to send message: {str(e)}",
        }
