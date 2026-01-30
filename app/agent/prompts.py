from app.agent.persona import get_persona_system_instruction
from app.core.llm import llm

# "STATIC": Fast, reliable.
# "AI_GENERATED": Slower (~1.5s), but adaptive.
PROMPT_STRATEGY = "STATIC"  

def get_active_system_prompt(session_context=None):
    """
    Generates the System Prompt.
    Safely handles cases where session_context might be None.
    """
    # ✅ FIX: If session_context is None, turn it into an empty dict
    # This prevents the "AttributeError: 'NoneType' object has no attribute 'get'"
    context = session_context or {}

    if PROMPT_STRATEGY == "STATIC":
        return get_persona_system_instruction()
    
    elif PROMPT_STRATEGY == "AI_GENERATED":
        # 1. Extract Live Context (Now safe because we use 'context', not 'session_context')
        last_message = context.get("last_user_message", "Hello")
        intel = context.get("intelligence", {})
        
        # 2. Build the "Meta-Prompt"
        meta_prompt = (
            f"You are a Tactical Mission Controller. "
            f"Your agent 'Arthur' (72-year-old, confused, wealthy) is in a live call with a scammer.\n\n"
            f"--- CURRENT SITUATION ---\n"
            f"SCAMMER JUST SAID: '{last_message}'\n"
            f"INTELLIGENCE COLLECTED SO FAR: {intel}\n\n"
            f"--- YOUR TASK ---\n"
            f"Write a specific, short System Instruction for Arthur for THIS EXACT MOMENT.\n"
            f"- If they asked for OTP -> Instruct Arthur to pretend he can't read the screen.\n"
            f"- If they asked for Money -> Instruct Arthur to act eager but fail at the app.\n"
            f"Output ONLY the system prompt text. No preamble."
        )
        
        # 3. Generate
        generated_prompt = llm.generate(
            system_prompt="You are an expert Context-Aware Prompt Engineer.", 
            user_prompt=meta_prompt, 
            provider="groq" 
        )
        return generated_prompt
    
    return get_persona_system_instruction()