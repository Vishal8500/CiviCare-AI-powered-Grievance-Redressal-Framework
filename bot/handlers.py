
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from database import save_grievance, get_status
from genai_helper import extract_issue_and_location, get_gemini_reply
from issue_config import ISSUE_CONFIG # Import the config

# Dictionary to hold the state of ongoing submissions (multi-step process)
# user_id → {step: str, config: dict, grievance: str, ..., additional_data: str/None}
pending_submissions = {} 

# Helper function to get the next required step
def get_next_step(submission_data):
    """Determines the next required piece of data to collect."""
    issue_config = submission_data['config']
    
    # 1. Check Location
    if submission_data.get('location') in (None, 'unknown') or len(submission_data.get('location', '').strip()) < 3:
        return "awaiting_location", "📍 I couldn't find a clear location. Could you please send me the location of this issue now?"
    
    # 2. Check Photo Requirement
    if issue_config['photo_required'] and submission_data.get('photo_file_id') is None:
        return "awaiting_photo", "📸 This issue type often requires a photo. Are you willing to upload one now? (Send photo or skip with /skip_photo)"

    # 3. Check Additional Data Requirement
    if issue_config['additional_prompt'] and submission_data.get('additional_data') is None:
        return "awaiting_additional_data", f"📝 We need a little more detail. {issue_config['additional_prompt']}"

    # 4. Completion
    return "complete", None

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
    issue = extracted.get("issue", "Other Civic Complaints")
    location = extracted.get("location", "unknown")
    issue_config = ISSUE_CONFIG.get(issue)

    # Initialize submission data
    submission_data = {
        "username": username,
        "grievance": grievance_text,
        "issue": issue,
        "config": issue_config,
        "location": location,
        "photo_file_id": None,
        "additional_data": None
    }
    
    # Determine next step
    next_step, prompt = get_next_step(submission_data)
    submission_data['step'] = next_step
    
    if next_step == "complete":
        # Case 1: All required info gathered in the initial command
        
        # Generate AI reply and save
        ai_reply = get_gemini_reply(grievance_text)
        save_grievance(user_id, username, grievance_text, issue, location, 
                       submission_data['photo_file_id'], submission_data['additional_data'], ai_reply)

        await update.message.reply_text(
            f"✅ Your grievance has been registered immediately!\n\n"
            f"🧾 Issue: {issue}\n📍 Location: {location}\n\n"
            f"{ai_reply}"
        )
    else:
        # Case 2: Start multi-step collection process
        pending_submissions[user_id] = submission_data
        await update.message.reply_text(
            f"✅ We classified your issue as: **{issue}**\n\n"
            f"Next, we need more information:\n"
            f"{prompt}",
            parse_mode='Markdown'
        )

# Command to skip photo upload
async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    if user_id not in pending_submissions:
        await update.message.reply_text("There is no active grievance waiting for a photo. Please use /register first.")
        return

    submission_data = pending_submissions[user_id]

    if submission_data['step'] == "awaiting_photo":
        # Mark photo as skipped (None) and move to the next step
        submission_data['photo_file_id'] = "skipped" # Mark as intentionally skipped
        next_step, prompt = get_next_step(submission_data)
        submission_data['step'] = next_step
        
        if next_step == "complete":
            # Save final submission
            await finalize_submission(update, user_id)
        else:
            await update.message.reply_text(prompt)
    else:
        await update.message.reply_text("You can only use /skip_photo when prompted to upload a photo.")

# Finalize submission (save to DB and send final confirmation)
async def finalize_submission(update: Update, user_id):
    submission_data = pending_submissions.pop(user_id)
    
    issue = submission_data['issue']
    grievance = submission_data['grievance']
    location = submission_data['location']
    
    # Generate AI reply
    ai_reply = get_gemini_reply(grievance) 
    
    # Save grievance with all collected data
    photo_id_to_save = submission_data['photo_file_id']
    # Ensure 'skipped' is saved as NULL/None in the DB
    if photo_id_to_save == 'skipped':
        photo_id_to_save = None

    save_grievance(
        user_id=user_id, 
        username=submission_data['username'], 
        grievance=grievance, 
        issue=issue, 
        location=location,
        photo_file_id=photo_id_to_save,
        additional_data=submission_data['additional_data'],
        ai_reply=ai_reply
    )
    
    # Final confirmation message
    photo_status = "✅ Photo included." if submission_data['photo_file_id'] not in (None, 'skipped') else "❌ No photo."
    additional_status = "✅ Extra detail provided." if submission_data['additional_data'] else "❌ N/A"
    
    await update.message.reply_text(
        f"🎉 **Submission Complete!** 🎉\n\n"
        f"🧾 Issue: {issue}\n"
        f"📍 Location: {location}\n"
        f"{photo_status}\n"
        f"{additional_status}\n\n"
        f"{ai_reply}",
        parse_mode='Markdown'
    )


# Handler for all messages (Location, Photo, or Additional Data text)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in pending_submissions:
        # Not in a submission flow, reply normally
        if update.message.text:
            await update.message.reply_text("💬 Please use /register <your grievance> to report an issue.")
        # Ignore random photos/other media if not in a flow
        return

    submission_data = pending_submissions[user_id]
    current_step = submission_data['step']
    input_received = False
    
    # --- AWAITING LOCATION ---
    if current_step == "awaiting_location" and update.message.text:
        submission_data['location'] = update.message.text.strip()
        input_received = True
        
    # --- AWAITING PHOTO ---
    elif current_step == "awaiting_photo" and update.message.photo:
        # Get the largest photo file ID
        photo_file_id = update.message.photo[-1].file_id
        submission_data['photo_file_id'] = photo_file_id
        input_received = True

    # --- AWAITING ADDITIONAL DATA (TEXT RESPONSE) ---
    elif current_step == "awaiting_additional_data" and update.message.text:
        submission_data['additional_data'] = update.message.text.strip()
        input_received = True
        
    if not input_received:
        # Invalid input for the current step (e.g., sent text when expecting photo)
        await update.message.reply_text(f"❌ Input mismatch! We are currently waiting for your **{current_step.replace('awaiting_', '').replace('_', ' ')}**. Please try again.")
        return

    # After receiving valid input, transition to the next step
    next_step, prompt = get_next_step(submission_data)
    submission_data['step'] = next_step
    
    if next_step == "complete":
        await finalize_submission(update, user_id)
    else:
        await update.message.reply_text(prompt)


# /status command (Minor update to include new fields)
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    grievances = get_status(user_id)

    if not grievances:
        await update.message.reply_text("No grievances found.")
        return

    response = "📋 Your Grievances (Newest first):\n\n"
    for g in grievances:
        ai_acknowledgement = g.get('ai_reply', 'Acknowledgment pending.')
        photo_status = "🖼️ Yes" if g.get('photo_file_id') and g.get('photo_file_id') != 'skipped' else "❌ No"
        data_status = f"✅ Provided: *{g.get('additional_data', 'N/A')[:40]}...*" if g.get('additional_data') else "❌ N/A"
        
        response += (
            f"--- [ID: {g['id']}] ---\n"
            f"**Issue:** {g['issue']}\n"
            f"**Location:** {g['location']}\n"
            f"**Status:** {g['status']}\n"
            f"**Photo:** {photo_status}\n"
            f"**Extra Detail:** {data_status}\n"
            f"**Your Message:** *{g['grievance']}*\n"
            f"**AI Reply:** *{ai_acknowledgement}*\n"
            f"**Reported:** {g['created_at'].strftime('%Y-%m-%d %H:%M')}\n\n"
        )
    
    await update.message.reply_text(response, parse_mode='Markdown')



