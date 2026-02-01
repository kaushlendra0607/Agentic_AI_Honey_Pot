import os
import re  # <--- ✅ NEW IMPORT
from dotenv import load_dotenv
from app.core.llm import llm
from app.agent.prompts import get_active_system_prompt

load_dotenv()
ACTIVE_PROVIDER = "groq"


def generate_agent_reply(session):
    """
    Generates a reply and CLEANS it of any AI artifacts.
    """
    # 1. Get Context
    intel = session.get("intelligence", {})
    user_message = session.get("last_user_message", "")

    has_upi = len(intel.get("upiIds", [])) > 0
    has_bank = len(intel.get("bankAccounts", [])) > 0
    has_link = len(intel.get("phishingLinks", [])) > 0
    keywords_str = str(intel.get("suspiciousKeywords", []))
    has_crypto = "Crypto" in keywords_str

    # 2. Format History (Truncated)
    recent_messages = session.get("messages", [])[-3:]
    history_text = ""
    for msg in recent_messages:
        role = "SCAMMER" if msg["sender"] == "scammer" else "USER"
        clean_text = str(msg["text"])[:400]
        if len(str(msg["text"])) > 400:
            clean_text += "..."
        history_text += f"{role}: {clean_text}\n"

    # 3. Strategy
    if has_link and not (has_upi or has_bank or has_crypto):
        tactical_directive = (
            "STATUS: They sent a Phishing Link. ACTION: Lie. Say link isn't opening (404 Error) etc, make excuses."
            "Force them to give Bank/UPI."
        )
    elif has_upi or has_bank or has_crypto:
        tactical_directive = (
            "STATUS: We have the Payment Details (Mission Success).\n"
            "ACTION: STALL INDEFINITELY. Invent a new technical failure to explain why you haven't sent money yet. Try to extract more details but must not ask for any detail again which has already been dropped by scammer."
        )
    else:
        tactical_directive = (
            "STATUS: No details. ACTION: Act eager. Ask for UPI/Bank details."
        )

    # 4. Prompt
    final_user_prompt = (
        f"=>HISTORY\n{history_text}\n"
        f"=>NEW MSG\n{user_message}\n"
        f"=>INSTRUCTIONS\n"
        f"STRATEGY: {tactical_directive}\n"
        f"DO NOT include headers like 'User Response:' or '=>REPLY'. Just speak.\n"
        f"REPLY:"
    )

    # 5. System Prompt
    dynamic_system_prompt = get_active_system_prompt(session_context=session)

    # 6. Call LLM
    raw_reply = llm.generate(
        system_prompt=dynamic_system_prompt,
        user_prompt=final_user_prompt,
        provider=ACTIVE_PROVIDER,
    )

    # 🧼 7. CLEAN THE OUTPUT (Crucial Fix)
    # This regex removes "**Arthur's Response**", "=>REPLY", "REPLY:", and quotes.
    clean_reply = re.sub(
        r"^(User Response\b|Arthur's Response\b|Arthur\b|=>REPLY|REPLY:|\*\*REPLY\*\*)[\s:,-]*",
        "",
        raw_reply,
        flags=re.IGNORECASE,
    ).strip()

    # Final cleanup: Remove quotes if the AI wrapped the whole sentence in them
    if clean_reply.startswith('"') and clean_reply.endswith('"'):
        clean_reply = clean_reply[1:-1]

    return clean_reply
