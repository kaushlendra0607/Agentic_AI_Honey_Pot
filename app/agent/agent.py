import os
from dotenv import load_dotenv
from app.core.llm import llm
from app.agent.prompts import HONEYPOT_SYSTEM_PROMPT

load_dotenv()

# TOGGLE THIS TO SWITCH MODELS INSTANTLY
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
    
    # 2. Format History (Last 10 messages)
    # This block provides the "Global Memory" to the AI
    recent_messages = session.get("messages", [])[-10:]
    history_text = ""
    
    for msg in recent_messages:
        role = "SCAMMER" if msg['sender'] == 'scammer' else "ARTHUR"
        history_text += f"{role}: {msg['text']}\n"

    # 3. CALCULATE TACTICAL DIRECTIVE
    if has_link and not (has_upi or has_bank):
        tactical_directive = (
            "STATUS: They sent a Phishing Link.\n"
            "ACTION: Lie. Say the link isn't opening (e.g., 'Server Not Found', '404 Error'). "
            "Force them to give a Bank Account or UPI instead."
        )
    elif has_upi or has_bank:
        tactical_directive = (
            "STATUS: We have the Payment Details (Mission Success).\n"
            "ACTION: STALL INDEFINITELY. Invent a new technical failure to explain why you haven't sent money yet."
        )
    else:
        tactical_directive = (
            "STATUS: No payment details yet.\n"
            "ACTION: Act eager to pay. Ask for UPI ID or Bank Details."
        )

    # 4. The "Global History" Prompt
    # We force the model to look at the history_text block itself.
    final_user_prompt = (
        f"--- CONVERSATION HISTORY ---\n{history_text}\n"
        f"----------------------------\n"
        f"CURRENT SCAMMER MESSAGE: {user_message}\n\n"
        f"--- INSTRUCTIONS ---\n"
        f"1. STRATEGY: {tactical_directive}\n"
        f"2. GLOBAL ANTI-REPETITION: Read the 'ARTHUR' messages in the history above. "
        f"List the excuses or technical issues Arthur has ALREADY used. "
        f"DO NOT use those specific excuses again. Invent a NEW problem.\n"
        f"3. PERSONA: Keep it short, confused, and polite.\n\n"
        f"ARTHUR'S RESPONSE:"
    )

    # 5. Call the LLM
    return llm.generate(
        system_prompt=HONEYPOT_SYSTEM_PROMPT, 
        user_prompt=final_user_prompt, 
        provider=ACTIVE_PROVIDER
    )