
import logging
import os
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters
# Updated handlers import to include the new skip_photo function
from handlers import start, register, status, handle_message, skip_photo 
from database import init_db

# Load environment variables (like TELEGRAM_BOT_TOKEN)
load_dotenv()

# Initialize the database (create DB and table if they don't exist)
init_db()

# Set up logging for better error visibility
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def main():
    """Start the bot."""
    # Ensure the token is available
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logging.error("TELEGRAM_BOT_TOKEN not found in environment variables. Cannot start bot.")
        return

    app = Application.builder().token(bot_token).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("register", register))
    app.add_handler(CommandHandler("status", status))
    # New handler for skipping photo upload
    app.add_handler(CommandHandler("skip_photo", skip_photo)) 

    # Catch all other messages (used for multi-step data collection, accepting PHOTOS and TEXT)
    # The filter ensures we handle messages that are either photos OR text that isn't a command.
    app.add_handler(MessageHandler(filters.PHOTO | filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("🤖 Bot is running...")
    # Start the bot, which blocks until the user presses Ctrl-C
    app.run_polling(poll_interval=1.0)

if __name__ == "__main__":
    main()





