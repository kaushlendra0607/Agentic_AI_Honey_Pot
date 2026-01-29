import re

# 1. Enhanced Regex Patterns
# UPI: Handles standard IDs (e.g., name@okicici)
UPI_REGEX = re.compile(r"[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}")

# PHONE: Handles +91, 0, or plain 10 digits (India specific start 6-9)
PHONE_REGEX = re.compile(r"(?:\+91[\-\s]?)?[6-9]\d{9}")

# URL: Catches http/https links
URL_REGEX = re.compile(r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+")

# BANK ACC: Matches 9 to 18 digits (standard range), ensuring distinct word boundaries
BANK_REGEX = re.compile(r"\b\d{9,18}\b")

def extract_intelligence(text: str):
    """
    Extracts structured data using strict pattern matching.
    """
    
    # We use set() to remove duplicates (e.g., if they send the same link twice)
    return {
        "upiIds": list(set(UPI_REGEX.findall(text))),
        "phoneNumbers": list(set(PHONE_REGEX.findall(text))),
        "phishingLinks": list(set(URL_REGEX.findall(text))),
        
        # Added this field because your Schema requires it!
        "bankAccounts": list(set(BANK_REGEX.findall(text))),
        
        # We leave keywords empty here because 'detect_scam' handles them
        "suspiciousKeywords": [] 
    }