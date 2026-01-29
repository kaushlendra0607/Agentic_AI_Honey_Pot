import os
from fastapi import Header, HTTPException
from dotenv import load_dotenv

# 1. Load the environment variables
load_dotenv()

def verify_api_key(x_api_key: str = Header(...)):
    """
    Verifies that the incoming request has the correct 'x-api-key' header.
    Compares it against the MY_SECRET_KEY in your .env file.
    """
    # 2. Get the real secret from .env
    # If the variable is missing, this defaults to None (security failsafe)
    required_key = os.getenv("x-api-key")
    
    # 3. Check the match
    if x_api_key != required_key:
        raise HTTPException(status_code=401, detail="Invalid API Key")