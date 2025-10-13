from telegram import Update
from telegram.ext import ContextTypes
from database import save_grievance, get_status
from utils import get_gemini_reply  # 👈 Import the LLM function

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to the Smart Grievance Redressal System!\n"
        "Use /register <your grievance> to submit a complaint.\n"
        "You can also use /status to check your registered grievances."
    )

# /register command
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    grievance_text = " ".join(context.args)
    if not grievance_text:
        await update.message.reply_text("⚠️ Usage: /register <your grievance>")
        return
    
    user = update.message.from_user
    user_id = user.id
    username = user.username or "Anonymous"

    # Save grievance in DB
    save_grievance(user_id, username, grievance_text)

    # Generate Gemini AI-based reply
    ai_reply = get_gemini_reply(grievance_text)

    await update.message.reply_text(
        f"✅ Your grievance has been registered successfully!\n\n"
        f"{ai_reply}",
        parse_mode="Markdown"
    )

# /status command
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    grievances = get_status(user_id)
    
    if not grievances:
        await update.message.reply_text("📭 You have no registered grievances yet.")
        return
    
    response = "📋 *Your Grievances:*\n\n"
    for g in grievances:
        response += f"🆔 ID: {g['id']} | 🏷️ Status: {g['status']}\n📝 {g['grievance']}\n\n"
    
    await update.message.reply_text(response, parse_mode="Markdown")
