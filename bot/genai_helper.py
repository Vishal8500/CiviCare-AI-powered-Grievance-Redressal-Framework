# bot/genai_helper.py

import os
import re
import json
import google.generativeai as genai
from issue_config import ISSUE_CONFIG # Import the issue configuration

# Configure Gemini API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Prepare the list of valid issue types for the prompt
VALID_ISSUES = list(ISSUE_CONFIG.keys())
ISSUE_LIST_STRING = ", ".join(VALID_ISSUES)

# --- 1️⃣ Extract issue and location ---
def extract_issue_and_location(grievance_text: str):
    """
    Uses Gemini to extract issue and location from a user's complaint text, 
    classifying the issue against the list of predefined types.
    Returns a dictionary with keys 'issue' (one of the 20 types) and 'location'.
    """
    prompt = f"""
    Analyze this grievance: "{grievance_text}"
    
    Classify the issue into one of these types: {ISSUE_LIST_STRING}.
    If the issue doesn't fit any type, classify it as "Other Civic Complaints".

    Return a short structured JSON with keys:
    - issue: The best matching issue type from the list.
    - location: The location/place mentioned (e.g., "Main Street, near City Hall"), or "unknown" if not found.
    """

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Extract JSON from response
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            
            # Basic validation to ensure issue is one of the types, defaulting to "Other"
            classified_issue = data.get("issue", "Other Civic Complaints")
            if classified_issue not in VALID_ISSUES:
                classified_issue = "Other Civic Complaints"

            return {
                "issue": classified_issue,
                "location": data.get("location", "unknown")
            }

    except Exception as e:
        print("Error in extract_issue_and_location:", e)

    # fallback
    return {"issue": "Other Civic Complaints", "location": "unknown"}


# --- 2️⃣ Generate polite AI reply (Function from original utils.py) ---
def get_gemini_reply(user_message: str) -> str:
    """
    Generate a polite and contextual reply for each complaint using Gemini.
    """
    try:
        system_prompt = (
            "You are a polite and empathetic AI assistant working for the municipal grievance redressal system. "
            "Your task is to reply briefly and professionally to citizens' complaints, "
            "acknowledging the issue and assuring timely action. Keep it under 2 sentences."
        )

        model = genai.GenerativeModel("gemini-2.5-flash")

        # Send prompt to Gemini
        response = model.generate_content(
            f"{system_prompt}\nCitizen complaint: {user_message}"
        )

        # Return Gemini's response text
        return response.text.strip()

    except Exception as e:
        print("Gemini Error:", e)
        return "Thank you for reporting your issue. Our team will look into it soon."
