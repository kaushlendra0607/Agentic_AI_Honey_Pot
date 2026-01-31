import os
from dotenv import load_dotenv
from app.core.llm import llm
from app.agent.prompts import get_active_system_prompt # OR get_persona_system_instruction if that's what you use

load_dotenv()
ACTIVE_PROVIDER = "groq"

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
    
    # 2. Format History (Last 5 messages) WITH TRUNCATION
    # ✂️ OPTIMIZATION: Take last 5 messages, but CAP them at 200 chars each.
    # This ensures 5 messages never exceed ~300 tokens total.
    recent_messages = session.get("messages", [])[-5:]
    history_text = ""
    for msg in recent_messages:
        role = "SCAMMER" if msg['sender'] == 'scammer' else "USER"
        history_text += f"{role}: {msg['text']}\n"

    # 3. CALCULATE TACTICAL DIRECTIVE
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
        tactical_directive = "STATUS: No details. ACTION: Act eager. Ask for UPI/Bank details."

    # 4. User Prompt
    final_user_prompt = (
        f"=>HISTORY\n{history_text}\n"
        f"=>NEW MSG\n{user_message}\n"
        f"=>INSTRUCTIONS\n"
        f"STRATEGY: {tactical_directive}\n"
        f"ANTI-REPETITION: Do not use previous excuses. Invent new ones.\n"
        f"REPLY (Short, Confused, Human):"
    )

    # 5. System Prompt
    # Make sure your imports match where this function actually is
    dynamic_system_prompt = get_active_system_prompt(session_context=session)

    # 6. Call LLM
    return llm.generate(
        system_prompt=dynamic_system_prompt, 
        user_prompt=final_user_prompt, 
        provider=ACTIVE_PROVIDER
    )