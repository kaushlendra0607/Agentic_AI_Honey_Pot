# app/core/llm.py
# | Model ID                                  | RPM | RPD   | TPM | TPD  | Notes                                                       |
# | ----------------------------------------- | --- | ----- | --- | ---- | ----------------------------------------------------------- |
# | llama-3.1-8b-instant                      | 30  | 14.4K | 6K  | 500K | Fastest small model, ideal for quick tasks browseroperator​ |
# | llama-3.3-70b-versatile                   | 30  | 1K    | 12K | 100K | High-quality large model, 276+ t/s benchmark groq​          |
# | llama-4-scout-17b-16e-instruct, no access | 30  | 1K    | 30K | 500K | Newer Llama 4 variant, strong speed groq​                   |

import os
import random
from groq import Groq

class LLMService:
    def __init__(self):
        # 1. Initialize Clients for Both Keys
        # Ensure GROQ_API_KEY and GROQ_API_KEY2 are in your .env
        self.clients = [
            Groq(api_key=os.getenv("GROQ_API_KEY"), max_retries=0),
            Groq(api_key=os.getenv("GROQ_API_KEY2"), max_retries=0)
        ]

        # 2. Set Model (Fastest)
        self.model = "llama-3.1-8b-instant" 

    def generate(self, system_prompt, user_prompt, provider="groq"):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # 🎲 STEP 1: PICK A RANDOM KEY (The Coin Flip)
        first_choice = random.choice(self.clients)
        
        # Define the backup (The one we didn't pick)
        backup_choice = self.clients[1] if first_choice == self.clients[0] else self.clients[0]

        # --- ATTEMPT 1: Primary (Random) ---
        try:
            return self._call_groq(first_choice, messages)
            
        except Exception as e:
            # ⚠️ If Random Choice fails, switch to Backup immediately
            print(f"⚠️ Primary Key Failed ({e}). Switching to Backup... 🔄")
            try:
                # --- ATTEMPT 2: The Other Key ---
                return self._call_groq(backup_choice, messages)
            except Exception as e2:
                print(f"❌ CRITICAL: Both Keys Exhausted. {e2}")
                # Fallback string so the app never crashes
                return "I am having a bit of trouble hearing you, dear. Can you repeat that?"

    def _call_groq(self, client, messages):
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=400,
            timeout=5.0 
        )
        
        # 🛡️ SAFETY CHECK: Never return None
        content = response.choices[0].message.content
        if content:
            return str(content)
        return "" # Return empty string instead of None to prevent .strip() crashes

llm = LLMService()