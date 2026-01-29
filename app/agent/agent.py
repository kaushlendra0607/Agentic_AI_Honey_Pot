import os
from dotenv import load_dotenv
from app.core.llm import llm  # Import our new wrapper
from app.agent.prompts import HONEYPOT_SYSTEM_PROMPT

load_dotenv()

# TOGGLE THIS TO SWITCH MODELS INSTANTLY
ACTIVE_PROVIDER = "groq"  # Options: "groq", "gemini"

def generate_agent_reply(session):
    """
    Decides strategy and calls the LLM wrapper.
    """
    # 1. Get Context
    intel = session.get("intelligence", {})
    user_message = session.get("last_user_message", "")
    
    # 2. Format History (Prevent Amnesia)
    # We take the last 6 messages to give the AI good context of the flow
    recent_messages = session.get("messages", [])[-6:]
    history_text = ""
    last_arthur_reply = ""
    for msg in recent_messages:
        role = "SCAMMER" if msg['sender'] == 'scammer' else "ARTHUR"
        history_text += f"{role}: {msg['text']}\n"

    # 3. Dynamic Strategy Logic
    has_payment_info = intel.get("upiIds") or intel.get("bankAccounts")
    has_link = intel.get("phishingLinks")

    if not has_payment_info and not has_link:
        strategy = "(STATUS: You don't know how to pay yet. Ask for a UPI ID or Bank Details to transfer the money.)"
    elif has_payment_info and not has_link:
        strategy = "(STATUS: You have the payment info, but say the bank app is loading very slowly. Ask if there is a website link instead?)"
    else:
        strategy = "(STATUS: You have everything. Stall them. Say your internet stopped working or the screen went black.)"

    # 4. Construct Prompt
    # Note: We send the history in the 'user_prompt' part so the LLM sees it as context.
    final_user_prompt = (
        f"--- CONVERSATION HISTORY ---\n{history_text}\n"
        f"----------------------------\n"
        f"CURRENT SCAMMER MESSAGE: {user_message}\n\n"
        f"HIDDEN INSTRUCTION FOR ARTHUR: {strategy}\n"
        f"ARTHUR'S REPLY:"
    )

    # 5. Call the Unified LLM
    return llm.generate(
        system_prompt=HONEYPOT_SYSTEM_PROMPT, 
        user_prompt=final_user_prompt, 
        provider=ACTIVE_PROVIDER
    )