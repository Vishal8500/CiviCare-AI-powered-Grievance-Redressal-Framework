# bot/genai_helper.py

import os
import re
import json
import google.generativeai as genai

# Configure Gemini API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


# --- 1️⃣ Extract issue and location ---
def extract_issue_and_location(grievance_text: str):
    """
    Uses Gemini to extract issue and location from a user's complaint text.
    Returns a dictionary with keys 'issue' and 'location'.
    """
    prompt = f"""
    Analyze this grievance: "{grievance_text}"

    Return a short structured JSON with keys:
    - issue: describe the issue in 3-5 words
    - location: location/place mentioned, or "unknown" if not found
    """

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Extract JSON from response
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            return {
                "issue": data.get("issue", "unknown"),
                "location": data.get("location", "unknown")
            }

    except Exception as e:
        print("Error in extract_issue_and_location:", e)

    # fallback
    return {"issue": "unknown", "location": "unknown"}


# --- 2️⃣ Generate polite AI reply ---
def get_gemini_reply(user_message: str) -> str:
    """
    Generate a short, polite, and contextual reply for the user’s grievance.
    """
    try:
        system_prompt = (
            "You are a polite and empathetic municipal assistant. "
            "Reply briefly (max 2 sentences) to acknowledge the user's complaint "
            "and assure that the issue will be handled soon."
        )

        model = genai.GenerativeModel("gemini-2.5-flash")

        response = model.generate_content(f"{system_prompt}\nCitizen complaint: {user_message}")
        return response.text.strip()

    except Exception as e:
        print("Gemini Error:", e)
        return "Thank you for reporting this issue. Our team will look into it soon."
