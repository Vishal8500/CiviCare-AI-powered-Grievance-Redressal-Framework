import logging
from telegram.ext import Application, CommandHandler
from handlers import start, register, status
from database import init_db
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

def main():
    init_db()  # ensure DB table exists

    app = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("register", register))
    app.add_handler(CommandHandler("status", status))

    app.run_polling()

if __name__ == "__main__":
    main()
