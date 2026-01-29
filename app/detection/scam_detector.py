from google import genai  # <--- NEW IMPORT
from dotenv import load_dotenv
from groq import Groq
from app.core.llm import llm



# 2. Hardcoded Patterns
SCAM_KEYWORDS = [
    "blocked",
    "suspended",
    "verify",
    "urgent",
    "account",
    "upi",
    "otp",
    "freeze",
    "immediately",
    "bank",
    "kyc",
    "refund",
    "won",
    "lottery",
    "expired",
    "click here",
    "link",
    "password",
    "pin",
]


def detect_scam(text: str):
    """
    Returns: (is_scam: bool, keywords_found: list[str])
    """
    text_lower = text.lower()

    # STEP 1: Fast Keyword Match
    hits = [kw for kw in SCAM_KEYWORDS if kw in text_lower]
    if len(hits) >= 1:
        return True, hits

    try:
        response_text = llm.generate(
            system_prompt="You are a scam detector. Reply ONLY with 'TRUE' or 'FALSE'.",
            user_prompt=f"Analyze this message for scam intent: '{text}'",
            provider="groq" # You can use "gemini" here explicitly if you want specific efficiency
        ).strip().upper()

        if "TRUE" in response_text:
            return True, ["AI_Context_Analysis"]
            
    except Exception as e:
        print(f"Detector Error: {e}")

    # Default to Safe
    return False, []
