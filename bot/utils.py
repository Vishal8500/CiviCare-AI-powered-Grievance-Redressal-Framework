import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

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

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"{system_prompt}\nCitizen complaint: {user_message}"
        )

        return response.text.strip()

    except Exception as e:
        print("Gemini Error:", e)
        return "Thank you for reporting your issue. Our team will look into it soon."
