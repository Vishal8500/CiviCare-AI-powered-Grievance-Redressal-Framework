from telegram import Update
from telegram.ext import ContextTypes
from database import save_grievance, get_status

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Use /register <your grievance> to submit.")

# /register command
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    grievance_text = " ".join(context.args)
    if not grievance_text:
        await update.message.reply_text("Usage: /register <your grievance>")
        return
    
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "Anonymous"
    save_grievance(user_id, username, grievance_text)
    
    await update.message.reply_text("✅ Your grievance has been registered!")

# /status command
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    grievances = get_status(user_id)
    
    if not grievances:
        await update.message.reply_text("No grievances found.")
        return
    
    response = "📋 Your Grievances:\n\n"
    for g in grievances:
        response += f"ID: {g['id']} | Status: {g['status']}\n{g['grievance']}\n\n"
    
    await update.message.reply_text(response)
