import logging
from telegram.ext import Application, CommandHandler
from handlers import start, register, status
from database import init_db
import os
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from handlers import start, register, status, handle_message
import os

load_dotenv()
init_db()
logging.basicConfig(level=logging.INFO)


def main():
    app = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("register", register))
    app.add_handler(CommandHandler("status", status))

    # Catch all other messages (like when user gives location)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
