# ==========================================
# 🤖 bot/priority_index.py — AI-based Priority Scoring (No DB Import)
# ==========================================
from transformers import pipeline
import re

# ---------------------------
# 1️⃣ Initialize Sentiment Model
# ---------------------------
# Uses lightweight BERT-based model (multilingual safe)
sentiment_analyzer = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")

# ---------------------------
# 2️⃣ Keyword Severity Mapping
# ---------------------------
KEYWORD_WEIGHTS = {
    "fire": 0.95,
    "accident": 0.9,
    "flood": 0.85,
    "earthquake": 1.0,
    "injury": 0.8,
    "hazard": 0.9,
    "emergency": 1.0,
    "crime": 0.85,
    "theft": 0.7,
    "power": 0.6,
    "sewage": 0.4,
    "garbage": 0.5,
    "pollution": 0.4,
    "noise": 0.3,
    "road": 0.4,
    "water": 0.5,
    "corruption": 0.7,
    "malpractice": 0.8,
}


# ---------------------------
# 3️⃣ Sentiment Analysis
# ---------------------------
def get_sentiment_score(text: str) -> float:
    """
    Converts sentiment (1–5 stars) to polarity (0–1 scale).
    """
    try:
        result = sentiment_analyzer(text[:512])[0]  # limit length
        label = result["label"]  # e.g., "4 stars"
        stars = int(re.findall(r"\d+", label)[0])
        return (stars - 1) / 4.0  # normalize to 0–1
    except Exception:
        return 0.5


# ---------------------------
# 4️⃣ Keyword Severity
# ---------------------------
def get_keyword_severity(text: str) -> float:
    text = text.lower()
    max_score = 0.0
    for word, weight in KEYWORD_WEIGHTS.items():
        if word in text:
            max_score = max(max_score, weight)
    return max_score


# ---------------------------
# 5️⃣ Frequency Weight (Simple Placeholder)
# ---------------------------
# You can enhance this later with actual DB counts.
def get_frequency_score(issue: str) -> float:
    freq_lookup = {
        "Fire Hazards": 0.9,
        "Crime / Anti-Social Activity": 0.8,
        "Electricity / Power": 0.6,
        "Sewage & Drainage": 0.5,
        "Garbage & Waste Management": 0.4,
    }
    return freq_lookup.get(issue, 0.3)


# ---------------------------
# 6️⃣ Final Priority Index Calculation
# ---------------------------
def calculate_priority_index(text: str, issue: str):
    """
    Calculates weighted priority index:
    P = w1*S + w2*K + w3*F
    """
    S = get_sentiment_score(text)
    K = get_keyword_severity(text)
    F = get_frequency_score(issue)

    # Normalize weights
    w1, w2, w3 = 0.3, 0.5, 0.2
    P = (w1 * S) + (w2 * K) + (w3 * F)
    P = round(P, 3)

    return S, K, F, P
