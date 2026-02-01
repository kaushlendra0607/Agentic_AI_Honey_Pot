import os
import re 
from dotenv import load_dotenv
from app.core.llm import llm
from app.agent.prompts import get_active_system_prompt

load_dotenv()
ACTIVE_PROVIDER = "groq"

def generate_agent_reply(session):
    """
    Generates a reply with RECALL capabilities.
    """
    # 1. Get Context
    intel = session.get("intelligence", {})
    user_message = session.get("last_user_message", "")

    # 2. Format History (Smart Truncation)
    recent_messages = session.get("messages", [])[-5:]
    history_text = ""
    for msg in recent_messages:
        role = "SCAMMER" if msg["sender"] == "scammer" else "USER"
        text = str(msg["text"])
        
        # Only chop AI messages to save space, keep Scammer full text
        if role == "USER":
            if len(text) > 300:
                text = text[:300] + "..."
        
        history_text += f"{role}: {text}\n"

    # --- ✅ NEW: RECALL FEATURE (Build the Memory Block) ---
    recall_data = []
    if intel.get("upiIds"): 
        recall_data.append(f"UPI: {', '.join(intel['upiIds'])}")
    if intel.get("bankAccounts"): 
        recall_data.append(f"BANK ACCOUNTS: {', '.join(intel['bankAccounts'])}")
    if intel.get("phoneNumbers"): 
        recall_data.append(f"PHONES: {', '.join(intel['phoneNumbers'])}")
    
    # Create the string. If empty, it's just "None".
    known_intel_str = " | ".join(recall_data) if recall_data else "None"
    # -------------------------------------------------------

    # 4. Strategy & Prompt
    has_upi = len(intel.get("upiIds", [])) > 0
    has_bank = len(intel.get("bankAccounts", [])) > 0
    has_link = len(intel.get("phishingLinks", [])) > 0
    has_crypto = "Crypto" in str(intel.get("suspiciousKeywords", []))

    if has_link and not (has_upi or has_bank or has_crypto):
        tactical_directive = "STATUS: Phishing Link Found. ACTION: Lie (404 Error). Demand Bank/UPI."
    elif has_upi or has_bank or has_crypto:
        tactical_directive = "STATUS: Success (Details Captured). ACTION: STALL INDEFINITELY. Invent tech failures. Be creative about excuses. You may reference the captured details to sound convincing."
    else:
        tactical_directive = "STATUS: No details. ACTION: Act eager. Ask for UPI/Bank details."

    final_user_prompt = (
        f"KNOWN INTEL (Use this to verify details):\n{known_intel_str}\n\n" # <--- ✅ INJECTED HERE
        f"HISTORY:\n{history_text}\n"
        f"NEW MSG:\n{user_message}\n"
        f"INSTRUCTIONS:\n"
        f"STRATEGY: {tactical_directive}\n"
        f"DO NOT include headers like 'User Response:'. Just speak.\n"
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

    # 7. Clean Output
    clean_reply = re.sub(
        r"^(User Response\b|Arthur's Response\b|Arthur\b|=>REPLY|REPLY:|\*\*REPLY\*\*)[\s:,-]*",
        "",
        raw_reply,
        flags=re.IGNORECASE,
    ).strip()

    if clean_reply.startswith('"') and clean_reply.endswith('"'):
        clean_reply = clean_reply[1:-1]

    return clean_reply