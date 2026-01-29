import os
from google import genai
from groq import Groq
from dotenv import load_dotenv
from app.agent.prompts import HONEYPOT_SYSTEM_PROMPT

load_dotenv()

# 1. Initialize the Client (New 2026 Syntax)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
client1 = Groq(api_key=os.getenv("GROQ_API_KEY"))

model_gemini = "gemini-2.5-flash-lite"
model_groq = "llama3-70b-8192"


def generate_agent_reply(session):
    """
    Decides on a strategy and asks Gemini to write the response.
    """

    # 1. Get the Context
    intel = session.get("intelligence", {})
    user_message = session.get("last_user_message", "")
    recent_history = session.get("messages", [])[-3:] 
    chat_context = "\n".join([f"{m['sender'].upper()}: {m['text']}" for m in recent_history])
    # 2. Define the Strategy
    if not intel.get("upiIds") and not intel.get("bankAccounts"):
        strategy = "INSTRUCTION: The scammer has NOT given payment info yet. Ignore everything else and ask for a UPI ID or Bank Details so you can transfer the money."
    elif not intel.get("phishingLinks"):
        strategy = "INSTRUCTION: We have the bank details, but the app is failing. Ask if they have a direct link or website you can visit."
    else:
        strategy = "INSTRUCTION: Stall them. Say you are typing the details but your internet is slow."

    # 3. Generate the Reply
    try:
        full_prompt = f"{HONEYPOT_SYSTEM_PROMPT}\n\n--- CONVERSATION HISTORY(last 3 messages from history) ---\n{chat_context}\n\nSCAMMER WROTE: {user_message}\n\n{strategy}\n\nARTHUR'S REPLY:"

        # New SDK Call Syntax
        # response = client.models.generate_content(
        #     model=model_groq, contents=full_prompt
        # )

        chat_completion = client1.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": full_prompt,
                }
            ],
            model="llama-3.3-70b-versatile",  # Or "llama3-8b-8192" for faster/cheaper
            temperature=0.7
        )

        return (chat_completion.choices[0].message.content or "").strip()
        # return (response.text or "").strip() #this is for gemini one

    except Exception as e:
        print(f"⚠️ AI model Error: {e}")
        return "I am clicking the button but nothing is happening... wait."
