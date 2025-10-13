from telegram import Update
from telegram.ext import ContextTypes
from database import save_grievance, get_status
from genai_helper import extract_issue_and_location, get_gemini_reply

# To temporarily store users waiting to provide location
pending_locations = {}  # user_id → {username, grievance, issue}

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! Use /register <your grievance> to submit an issue.")

# /register command
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    grievance_text = " ".join(context.args)
    if not grievance_text:
        await update.message.reply_text("Usage: /register <your grievance>")
        return

    user_id = update.message.from_user.id
    username = update.message.from_user.username or "Anonymous"

    # --- Step 1: Extract issue and location using Gemini ---
    extracted = extract_issue_and_location(grievance_text)
    issue = extracted.get("issue", "General complaint")
    location = extracted.get("location", "unknown")

    # --- Step 2: Ask for location if not found ---
    if location.lower() == "unknown" or not location.strip():
        pending_locations[user_id] = {
            "username": username,
            "grievance": grievance_text,
            "issue": issue
        }
        await update.message.reply_text("📍 Could you please tell me the location of this issue?")
        return

    # --- Step 3: Save grievance and generate AI reply ---
    save_grievance(user_id, username, grievance_text, issue, location)
    ai_reply = get_gemini_reply(grievance_text)

    await update.message.reply_text(
        f"✅ Your grievance has been registered!\n\n"
        f"🧾 Issue: {issue}\n📍 Location: {location}\n\n"
        f"{ai_reply}"
    )

# Handle location replies
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    if user_id in pending_locations:
        data = pending_locations.pop(user_id)
        username = data["username"]
        grievance = data["grievance"]
        issue = data["issue"]

        # Save grievance once location is received
        save_grievance(user_id, username, grievance, issue, text)

        # Get a smart AI reply for confirmation
        ai_reply = get_gemini_reply(grievance)

        await update.message.reply_text(
            f"✅ Thanks! Your grievance has been registered.\n\n"
            f"🧾 Issue: {issue}\n📍 Location: {text}\n\n"
            f"{ai_reply}"
        )
    else:
        await update.message.reply_text("💬 Please use /register <your grievance> to report an issue.")

# /status command
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    grievances = get_status(user_id)

    if not grievances:
        await update.message.reply_text("No grievances found.")
        return

    response = "📋 Your Grievances:\n\n"
    for g in grievances:
        response += (
            f"🆔 ID: {g['id']} | 🧾 {g['issue']} | 📍 {g['location']}\n"
            f"Status: {g['status']}\n"
            f"Message: {g['grievance']}\n\n"
        )

    await update.message.reply_text(response)
