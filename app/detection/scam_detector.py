import os
from google import genai  # <--- NEW IMPORT
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# 1. Initialize Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
client1 = Groq(api_key=os.getenv("GROQ_API_KEY"))


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

    # STEP 2: AI Analysis (New SDK)
    # try:
    #     response = client.models.generate_content(
    #         model='gemini-2.5-flash-lite',
    #         contents=f"""
    #         Analyze this message for scam intent.
    #         Message: "{text}"

    #         Rules:
    #         - Look for urgency, requests for money, or personal info.
    #         - Reply with ONLY "TRUE" if it is a scam, or "FALSE" if it is safe.
    #         - Do not explain.
    #         """
    #     )

    #     safe_text = (response.text or "").strip().upper()
    #     is_ai_flagged = "TRUE" in safe_text

    #     if is_ai_flagged:
    #         return True, ["AI_Context_Analysis"]
    try:
        chat_completion = client1.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a scam detector. Reply ONLY with TRUE or FALSE.",
                },
                {"role": "user", "content": f"Analyze this for scam intent: '{text}'"},
            ],
            model="llama-3.1-8b-instant",  # Use the smaller model for detection (It's faster)
        )

        response_text = (
            (chat_completion.choices[0].message.content or "").strip().upper()
        )

        if "TRUE" in response_text:
            return True, ["AI_Context_Analysis"]

    except Exception as e:
        print(f"AI Detection Error: {e}")

    # Default to Safe
    return False, []
