import os
from dotenv import load_dotenv

# Load the .env file immediately
load_dotenv()

# 1. Your API Security (Matches .env MY_SECRET_KEY)
# We default to None so we know if it's missing
MY_SECRET_KEY = os.getenv("MY_SECRET_KEY")

# 2. External AI Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 3. Hackathon Configuration
GUVI_ENDPOINT = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

# 4. Optional: Database or other settings
# DATABASE_URL = os.getenv("DATABASE_URL")