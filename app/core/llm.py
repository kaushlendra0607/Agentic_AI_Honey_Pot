# app/core/llm.py
import os
import random
from groq import Groq

class LLMService:
    def __init__(self):
        # 1. Initialize Clients for THREE Keys 🛡️🛡️🛡️
        self.clients = []
        
        # Add keys dynamically if they exist
        env_keys = ["GROQ_API_KEY", "GROQ_API_KEY2", "GROQ_API_KEY3"]
        for env_var in env_keys:
            key = os.getenv(env_var)
            if key:
                self.clients.append(Groq(api_key=key, max_retries=0))
        
        if not self.clients:
            raise ValueError("❌ No Groq API Keys found in .env!")

        # 2. Set Model
        self.model = "llama-3.1-8b-instant" 

    def generate(self, system_prompt, user_prompt, provider="groq"):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # 🎲 STEP 1: PICK A RANDOM KEY
        # We try up to 3 times to find a working key
        shuffled_clients = random.sample(self.clients, len(self.clients))
        
        for client in shuffled_clients:
            try:
                return self._call_groq(client, messages)
            except Exception as e:
                print(f"⚠️ Key Failed ({e}). Switching... 🔄")
                continue # Try the next key in the list
        
        # If we get here, ALL keys failed
        print("❌ CRITICAL: ALL Keys Exhausted.")
        return "I am having trouble with my connection, dear. One moment."

    def _call_groq(self, client, messages):
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=400,
            timeout=5.0 
        )
        content = response.choices[0].message.content
        return str(content) if content else ""

llm = LLMService()