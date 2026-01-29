import os
from google import genai
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    def __init__(self):
        # Initialize both clients once
        self.gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        # Default Config
        self.gemini_model = "gemini-2.5-flash-lite"
        self.groq_model = "llama-3.3-70b-versatile" # or "llama3-70b-8192"

    def generate(self, system_prompt: str, user_prompt: str, provider: str = "groq"):
        """
        Unified method to call either Groq or Gemini.
        provider: "groq" or "gemini"
        """
        try:
            if provider == "groq":
                return self._call_groq(system_prompt, user_prompt)
            elif provider == "gemini":
                return self._call_gemini(system_prompt, user_prompt)
            else:
                return "Error: Unknown provider selected."
        except Exception as e:
            print(f"⚠️ {provider.upper()} Error: {e}")
            return "I am clicking the button but nothing is happening... wait."

    def _call_groq(self, system_prompt, user_prompt):
        chat_completion = self.groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=self.groq_model,
            temperature=0.7,
            max_tokens=200
        )
        return (chat_completion.choices[0].message.content or "").strip()

    def _call_gemini(self, system_prompt, user_prompt):
        # Gemini 2026 Syntax
        full_prompt = f"{system_prompt}\n\nUSER SAYS:\n{user_prompt}"
        response = self.gemini_client.models.generate_content(
            model=self.gemini_model, 
            contents=full_prompt
        )
        return (response.text or "").strip()

# Create a singleton instance to use everywhere
llm = LLMClient()