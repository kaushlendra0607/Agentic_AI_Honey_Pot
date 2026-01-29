import re

# --- 1. CORE PATTERNS (Strict Guvi Schema) ---
UPI_REGEX = re.compile(r"\b[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}\b")
PHONE_REGEX = re.compile(r"(?:\+91[\-\s]?)?[6-9]\d{9}\b")
URL_REGEX = re.compile(r"\b(?:https?://|www\.)\S+\b")
BANK_REGEX = re.compile(r"\b\d{9,18}\b")

# --- 2. ADVANCED INTELLIGENCE (Mapped to 'suspiciousKeywords') ---
BTC_REGEX = re.compile(r"\b(?:1|3|bc1)[a-zA-Z0-9]{25,39}\b")
ETH_REGEX = re.compile(r"\b0x[a-fA-F0-9]{40}\b")

# NEW: Gift Card Pattern (4 blocks of 4 chars: ABCD-1234-EFGH-5678)
GIFT_CODE_REGEX = re.compile(r"\b[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}\b")

REMOTE_APPS = [
    "anydesk", "teamviewer", "quicksupport", "alpemix", "rustdesk", 
    "screen share", "remote support"
]

# NEW: Common Gift Card Names
GIFT_BRANDS = [
    "google play", "amazon gift", "steam card", "apple card", "itunes", 
    "vanilla visa", "play station", "xbox gift"
]

def extract_intelligence(text: str):
    """
    Extracts structured data + Advanced Scams (Gift Cards, Crypto, RATs).
    """
    
    # 1. Raw Extraction
    upi_list = list(set(UPI_REGEX.findall(text)))
    phone_list = list(set(PHONE_REGEX.findall(text)))
    url_list = list(set(URL_REGEX.findall(text)))
    raw_bank_list = list(set(BANK_REGEX.findall(text)))
    
    # 2. Advanced Extraction -> Mapped to 'suspiciousKeywords'
    extra_keywords = []
    
    # Crypto
    for wallet in BTC_REGEX.findall(text):
        extra_keywords.append(f"Crypto-BTC:{wallet}")
    for wallet in ETH_REGEX.findall(text):
        extra_keywords.append(f"Crypto-ETH:{wallet}")
    
    # NEW: Gift Card Codes
    for code in GIFT_CODE_REGEX.findall(text):
        extra_keywords.append(f"GiftCard-Code:{code}")

    # Case Insensitive Checks
    lower_text = text.lower()
    
    # Remote Apps
    for app in REMOTE_APPS:
        if app in lower_text:
            extra_keywords.append(f"App-Detected:{app}")
            
    # NEW: Gift Card Brands
    for brand in GIFT_BRANDS:
        if brand in lower_text:
            extra_keywords.append(f"Scam-Type:{brand}")

    # 3. CLEANING LOGIC (Phone vs Bank)
    normalized_phones = [re.sub(r"\D", "", p)[-10:] for p in phone_list]
    clean_bank_list = []
    for acc in raw_bank_list:
        if acc not in normalized_phones and acc not in [p.replace(" ", "") for p in phone_list]:
            clean_bank_list.append(acc)

    return {
        "upiIds": upi_list,
        "phoneNumbers": phone_list,
        "phishingLinks": url_list,
        "bankAccounts": clean_bank_list,
        "suspiciousKeywords": extra_keywords 
    }