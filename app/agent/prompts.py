# app/agent/prompts.py
from app.agent.persona import get_persona_system_instruction

# It calls the function we just wrote in persona.py
HONEYPOT_SYSTEM_PROMPT = get_persona_system_instruction()