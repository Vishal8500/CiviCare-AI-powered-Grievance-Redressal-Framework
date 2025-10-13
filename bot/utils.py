import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize model (you can also use gemini-1.5-flash)
model = genai.GenerativeModel("gemini-2.5-flash")

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

        # Send prompt to Gemini
        response = model.generate_content(
            f"{system_prompt}\nCitizen complaint: {user_message}"
        )

        # Return Gemini's response text
        return response.text.strip()

    except Exception as e:
        print("Gemini Error:", e)
        return "Thank you for reporting your issue. Our team will look into it soon."
