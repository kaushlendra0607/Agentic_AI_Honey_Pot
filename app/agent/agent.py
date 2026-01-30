import os
from dotenv import load_dotenv
from app.core.llm import llm

# ✅ CHANGE: Import the function, not the variable
from app.agent.prompts import get_active_system_prompt

load_dotenv()

# TOGGLE THIS TO SWITCH REPLY MODEL
ACTIVE_PROVIDER = "groq"  # Options: "groq", "gemini"

def generate_agent_reply(session):
    """
    Generates a reply by analyzing the ENTIRE history to prevent repeating ANY past excuses.
    """
    # 1. Get Context & Intel
    intel = session.get("intelligence", {})
    user_message = session.get("last_user_message", "")
    
    has_upi = len(intel.get("upiIds", [])) > 0
    has_bank = len(intel.get("bankAccounts", [])) > 0
    has_link = len(intel.get("phishingLinks", [])) > 0
    keywords_str = str(intel.get("suspiciousKeywords", []))
    has_crypto = "Crypto" in keywords_str
    
    # 2. Format History (Last 10 messages)
    recent_messages = session.get("messages", [])[-10:]
    history_text = ""
    for msg in recent_messages:
        role = "SCAMMER" if msg['sender'] == 'scammer' else "USER"
        history_text += f"{role}: {msg['text']}\n"

    # 3. CALCULATE TACTICAL DIRECTIVE
    if has_link and not (has_upi or has_bank or has_crypto):
        tactical_directive = (
            "STATUS: They sent a Phishing Link.\n"
            "ACTION: Lie. Say the link isn't opening (e.g., 'Server Not Found', '404 Error' etc. Make excuses creatively, these are just some examples). "
            "Force them to give a Bank Account or UPI instead."
        )
    elif has_upi or has_bank or has_crypto:
        tactical_directive = (
            "STATUS: We have the Payment Details (Mission Success).\n"
            "ACTION: STALL INDEFINITELY. Invent a new technical failure to explain why you haven't sent money yet. Try to extract more details but must not ask for any detail again which has already been dropped by scammer."
        )
    else:
        tactical_directive = (
            "STATUS: No payment details yet.\n"
            "ACTION: Act eager to pay. Ask for UPI ID or Bank Details."
        )

    # 4. The "Global History" User Prompt
    final_user_prompt = (
        f"--- CONVERSATION HISTORY ---\n{history_text}\n"
        f"----------------------------\n"
        f"CURRENT SCAMMER MESSAGE: {user_message}\n\n"
        f"--- INSTRUCTIONS ---\n"
        f"1. STRATEGY: {tactical_directive}\n"
        f"2. GLOBAL ANTI-REPETITION: Read the 'USER' messages in the history above. "
        f"List the excuses USER has ALREADY used. DO NOT use them again.\n"
        f"DO NOT use those specific excuses again. Invent a NEW problem as conversation demands.\n"
        f"3. PERSONA: Keep it short, confused, and polite.\n\n"
        f"OUTPUT RULES: \n"
        f"1. Reply ONLY with the spoken text.\n"
        f"2. DO NOT include headers like 'User Response:' or '**Reasoning**'.\n"
        f"3. DO NOT use quotes around the message.\n\n"
        f"4. Chat as normal humans chat with each other, you are not reporting giving a presentation or something."
        f"REPLY:"
    )

    # 5. GENERATE SYSTEM PROMPT (The "Time Cost" Step)
    # This runs every time. If Strategy is "AI_GENERATED", this takes ~1.5s.
    dynamic_system_prompt = get_active_system_prompt(session_context=session)

    # 6. Call the LLM for the final reply
    return llm.generate(
        system_prompt=dynamic_system_prompt, 
        user_prompt=final_user_prompt, 
        provider=ACTIVE_PROVIDER
    )