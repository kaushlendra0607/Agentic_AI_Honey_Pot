import re

# --- 1. CORE PATTERNS (Strict Guvi Schema) ---
UPI_REGEX = re.compile(r"\b[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}\b")
PHONE_REGEX = re.compile(r"(?:\+91[\-\s]?)?[6-9]\d{9}\b")
URL_REGEX = re.compile(r"\b(?:https?://|www\.)\S+\b")

# Bank Account (9-18 digits) - Wide enough for most banks
BANK_REGEX = re.compile(r"\b\d{9,18}\b")

# --- 2. NEW INTELLIGENCE TYPES ---
# MPIN / OTP: 4 to 6 digits. 
# We use logic later to ensure it's not a Year (1990-2029) or simple Amount (500)
MPIN_REGEX = re.compile(r"\b\d{4,6}\b")

# IFSC Code: 4 Letters + 0 + 6 Alphanumeric (e.g., SBIN0001234)
IFSC_REGEX = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")

# PAN Card: 5 Letters + 4 Digits + 1 Letter (e.g., ABCDE1234F)
PAN_REGEX = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b")

# Aadhaar: 12 Digits (often usually space separated like 1234 5678 9012)
AADHAAR_REGEX = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")

# Card Expiry: MM/YY or MM/YYYY
EXPIRY_REGEX = re.compile(r"\b(0[1-9]|1[0-2])\/?([2-9][0-9])\b")

# --- 3. ADVANCED SCAM MAPPING ---
BTC_REGEX = re.compile(r"\b(?:1|3|bc1)[a-zA-Z0-9]{25,39}\b")
ETH_REGEX = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
GIFT_CODE_REGEX = re.compile(r"\b[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}\b")

REMOTE_APPS = [
    "anydesk", "teamviewer", "quicksupport", "alpemix", "rustdesk", 
    "screen share", "remote support", "any desk"
]

GIFT_BRANDS = [
    "google play", "amazon gift", "steam card", "apple card", "itunes", 
    "vanilla visa", "play station", "xbox gift", "razer gold"
]

# Keywords that suggest the numbers found are definitely sensitive
SENSITIVE_CONTEXT_WORDS = ["mpin", "pin", "otp", "code", "password", "cvv"]

def extract_intelligence(text: str):
    """
    Extracts structured data + Advanced Scams (Gift Cards, Crypto, RATs, MPINs).
    """
    
    # 1. Raw Extraction
    upi_list = list(set(UPI_REGEX.findall(text)))
    phone_list = list(set(PHONE_REGEX.findall(text)))
    url_list = list(set(URL_REGEX.findall(text)))
    raw_bank_list = list(set(BANK_REGEX.findall(text)))
    raw_mpin_list = list(set(MPIN_REGEX.findall(text)))
    
    # 2. Advanced Extraction -> Mapped to 'suspiciousKeywords'
    extra_keywords = []
    
    # --- A. FINANCIAL CODES (IFSC, PAN, AADHAAR) ---
    for ifsc in IFSC_REGEX.findall(text):
        extra_keywords.append(f"IFSC:{ifsc}")
    
    for pan in PAN_REGEX.findall(text):
        extra_keywords.append(f"PAN:{pan}")
        
    for aadhaar in AADHAAR_REGEX.findall(text):
        extra_keywords.append(f"Aadhaar:{aadhaar}")

    # --- B. MPIN / OTP LOGIC (Smart Filtering) ---
    # We don't want to flag the year "2025" or amount "5000" as an MPIN.
    lower_text = text.lower()
    for num in raw_mpin_list:
        # Filter 1: Check if it looks like a year (19xx or 20xx)
        if len(num) == 4 and (num.startswith("19") or num.startswith("20")):
            continue
            
        # Filter 2: If it's 6 digits, it's likely an OTP or 2FA code
        if len(num) == 6:
            extra_keywords.append(f"Potential-OTP/PIN:{num}")
            
        # Filter 3: If 4 digits, check context (is 'pin' or 'code' nearby?)
        elif len(num) == 4:
            # Simple context check: is a sensitive word in the text?
            if any(w in lower_text for w in SENSITIVE_CONTEXT_WORDS):
                extra_keywords.append(f"Potential-MPIN:{num}")

    # --- C. CRYPTO & GIFT CARDS ---
    for wallet in BTC_REGEX.findall(text):
        extra_keywords.append(f"Crypto-BTC:{wallet}")
    for wallet in ETH_REGEX.findall(text):
        extra_keywords.append(f"Crypto-ETH:{wallet}")
    for code in GIFT_CODE_REGEX.findall(text):
        extra_keywords.append(f"GiftCard-Code:{code}")

    # --- D. KEYWORD MAPPING ---
    for app in REMOTE_APPS:
        if app in lower_text:
            extra_keywords.append(f"App-Detected:{app}")
            
    for brand in GIFT_BRANDS:
        if brand in lower_text:
            extra_keywords.append(f"Scam-Type:{brand}")

    # --- 3. CLEANING LOGIC (Phone vs Bank) ---
    # Scammers typically send numbers like "9876543210" which Regex sees as BOTH Phone AND Bank.
    # We must remove Phone Numbers from the Bank List.
    
    normalized_phones = [re.sub(r"\D", "", p)[-10:] for p in phone_list]
    clean_bank_list = []
    
    for acc in raw_bank_list:
        # If this number is already identified as a phone number, skip it
        # Also check if it's found inside a phone number string
        is_phone = False
        for p in normalized_phones:
            if acc in p or p in acc:
                is_phone = True
                break
        
        if not is_phone:
            clean_bank_list.append(acc)

    return {
        "upiIds": upi_list,
        "phoneNumbers": phone_list,
        "phishingLinks": url_list,
        "bankAccounts": clean_bank_list,
        "suspiciousKeywords": extra_keywords 
    }