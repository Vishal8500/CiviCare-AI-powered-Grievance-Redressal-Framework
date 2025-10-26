from telegram import Update
from telegram.ext import ContextTypes
from database import save_grievance, get_status
from genai_helper import extract_issue_and_location, get_gemini_reply
from issue_config import ISSUE_CONFIG

# Dictionary to track multi-step complaint submissions
pending_submissions = {}

# ------------------------------
# Helper: Determine next required data
# ------------------------------
def get_next_step(submission_data):
    issue_config = submission_data['config']

    # 1️⃣ Location missing
    if submission_data.get('location') in (None, 'unknown') or len(submission_data.get('location', '').strip()) < 3:
        return "awaiting_location", "📍 I couldn't detect the location clearly. Please send your location."

    # 2️⃣ Photo requirement
    if issue_config['photo_required'] and submission_data.get('photo_file') is None:
        return "awaiting_photo", "📸 This issue type needs a photo. Please upload one now or skip with /skip_photo."

    # 3️⃣ Additional info
    if issue_config['additional_prompt'] and submission_data.get('additional_data') is None:
        return "awaiting_additional_data", f"📝 {issue_config['additional_prompt']}"

    # ✅ Done
    return "complete", None


# ------------------------------
# /start
# ------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! Use /register <your grievance> to report a civic issue.")


# ------------------------------
# /register
# ------------------------------
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    grievance_text = " ".join(context.args)
    if not grievance_text:
        await update.message.reply_text("Usage: /register <your grievance>")
        return

    user_id = update.message.from_user.id
    username = update.message.from_user.username or "Anonymous"

    # Extract issue + location using Gemini
    extracted = extract_issue_and_location(grievance_text)
    issue = extracted.get("issue", "Other Civic Complaints")
    location = extracted.get("location", "unknown")
    issue_config = ISSUE_CONFIG.get(issue, ISSUE_CONFIG["Other Civic Complaints"])

    # Initialize submission record
    submission_data = {
        "username": username,
        "grievance": grievance_text,
        "issue": issue,
        "config": issue_config,
        "location": location,
        "photo_file": None,
        "additional_data": None
    }

    next_step, prompt = get_next_step(submission_data)
    submission_data["step"] = next_step

    # Case 1: Fully ready to save
    if next_step == "complete":
        ai_reply = get_gemini_reply(grievance_text)
        await save_grievance(user_id, username, grievance_text, issue, location, None, None, ai_reply)


        await update.message.reply_text(
            f"✅ Your grievance has been registered!\n\n"
            f"🧾 Issue: {issue}\n📍 Location: {location}\n\n"
            f"{ai_reply}"
        )

    # Case 2: Ask for next detail
    else:
        pending_submissions[user_id] = submission_data
        await update.message.reply_text(
            f"✅ We classified your issue as: {issue}\n\n"
            f"{prompt}"
        )


# ------------------------------
# /skip_photo
# ------------------------------
async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in pending_submissions:
        await update.message.reply_text("❌ No active grievance to skip a photo for. Please use /register first.")
        return

    submission_data = pending_submissions[user_id]

    if submission_data['step'] == "awaiting_photo":
        submission_data['photo_file'] = None
        next_step, prompt = get_next_step(submission_data)
        submission_data['step'] = next_step

        if next_step == "complete":
            await finalize_submission(update, user_id)
        else:
            await update.message.reply_text(prompt)
    else:
        await update.message.reply_text("You can only use /skip_photo when asked for a photo.")


# ------------------------------
# Finalize submission
# ------------------------------
async def finalize_submission(update: Update, user_id):
    submission_data = pending_submissions.pop(user_id)
    issue = submission_data['issue']
    grievance = submission_data['grievance']
    location = submission_data['location']

    ai_reply = get_gemini_reply(grievance)

    await save_grievance(
        user_id=user_id,
        username=submission_data['username'],
        grievance=grievance,
        issue=issue,
        location=location,
        photo_file=submission_data.get('photo_file'),
        additional_data=submission_data.get('additional_data'),
        ai_reply=ai_reply
    )


    photo_status = "✅ Photo included." if submission_data.get('photo_file') else "❌ No photo."
    additional_status = "✅ Extra detail provided." if submission_data.get('additional_data') else "❌ No extra detail."

    await update.message.reply_text(
        f"🎉 Submission complete!\n\n"
        f"🧾 Issue: {issue}\n📍 Location: {location}\n"
        f"{photo_status}\n{additional_status}\n\n"
        f"{ai_reply}"
    )


# ------------------------------
# Handle messages for step-by-step collection
# ------------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in pending_submissions:
        if update.message.text:
            await update.message.reply_text("💬 Use /register <your grievance> to start reporting.")
        return

    submission_data = pending_submissions[user_id]
    current_step = submission_data['step']
    input_received = False

    # 1️⃣ Location
    if current_step == "awaiting_location" and update.message.text:
        submission_data['location'] = update.message.text.strip()
        input_received = True

    # 2️⃣ Photo
    # Inside handle_message()
    elif current_step == "awaiting_photo" and update.message.photo:
        try:
            # ✅ Always get the largest photo version
            photo = update.message.photo[-1]

            # ✅ Get file info (async)
            file_info = await photo.get_file()

            # ✅ Download bytes (async)
            photo_bytes = await file_info.download_as_bytearray()

            # ✅ Save in memory
            submission_data['photo_file'] = bytes(photo_bytes)
            input_received = True

        except Exception as e:
            await update.message.reply_text(f"⚠️ Failed to download photo: {e}")
            return


    # 3️⃣ Additional Data
    elif current_step == "awaiting_additional_data" and update.message.text:
        submission_data['additional_data'] = update.message.text.strip()
        input_received = True

    # Validation
    if not input_received:
        await update.message.reply_text(f"❌ Please send the expected input for: {current_step.replace('_', ' ')}.")
        return

    next_step, prompt = get_next_step(submission_data)
    submission_data['step'] = next_step

    if next_step == "complete":
        await finalize_submission(update, user_id)
    else:
        await update.message.reply_text(prompt)


# ------------------------------
# /status command
# ------------------------------
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    grievances = get_status(user_id)

    if not grievances:
        await update.message.reply_text("No grievances found.")
        return

    response_lines = ["📋 Your Grievances:"]
    for g in grievances:
        ai_ack = g.get('ai_reply', 'Pending acknowledgment.')
        response_lines.append(
            f"🆔 ID: {g['id']}\n"
            f"Issue: {g['issue']}\n"
            f"Location: {g['location']}\n"
            f"Status: {g['status']}\n"
            f"AI Reply: {ai_ack}\n"
            f"📅 Date: {g['created_at']}\n"
            "----------------------"
        )

    await update.message.reply_text("\n\n".join(response_lines))
