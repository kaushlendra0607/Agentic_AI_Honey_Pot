import re

# --- 1. CORE PATTERNS ---
UPI_REGEX = re.compile(r"\b[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}\b")
PHONE_REGEX = re.compile(r"(?:\+91[\-\s]?)?[6-9]\d{9}\b")
URL_REGEX = re.compile(r"\b(?:https?://|www\.)\S+\b")
BANK_REGEX = re.compile(r"\b\d{9,18}\b")  # 9-18 digits

# --- 2. NEW INTELLIGENCE TYPES ---
MPIN_REGEX = re.compile(r"\b\d{4,6}\b")
IFSC_REGEX = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")
PAN_REGEX = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b")
# Removed Aadhaar from core list to avoid bank conflict, handled in loop below
AADHAAR_REGEX = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")

# --- 3. ADVANCED SCAM MAPPING ---
BTC_REGEX = re.compile(r"\b(?:1|3|bc1)[a-zA-Z0-9]{25,39}\b")
ETH_REGEX = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
GIFT_CODE_REGEX = re.compile(r"\b[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}\b")

REMOTE_APPS = [
    "anydesk",
    "teamviewer",
    "quicksupport",
    "alpemix",
    "rustdesk",
    "screen share",
    "remote support",
    "any desk",
]
GIFT_BRANDS = [
    "google play",
    "amazon gift",
    "steam card",
    "apple card",
    "itunes",
    "vanilla visa",
    "play station",
    "xbox gift",
    "razer gold",
]
SENSITIVE_CONTEXT_WORDS = ["mpin", "pin", "otp", "code", "password", "cvv"]


def extract_intelligence(text: str):
    """
    Extracts structured data + Advanced Scams.
    """

    # 1. Raw Extraction
    upi_list = list(set(UPI_REGEX.findall(text)))
    phone_list = list(set(PHONE_REGEX.findall(text)))
    url_list = list(set(URL_REGEX.findall(text)))
    raw_bank_list = list(set(BANK_REGEX.findall(text)))
    raw_mpin_list = list(set(MPIN_REGEX.findall(text)))

    # 2. Advanced Extraction
    extra_keywords = []

    for ifsc in IFSC_REGEX.findall(text):
        extra_keywords.append(f"IFSC:{ifsc}")
    for pan in PAN_REGEX.findall(text):
        extra_keywords.append(f"PAN:{pan}")
    for aadhaar in AADHAAR_REGEX.findall(text):
        extra_keywords.append(f"Aadhaar:{aadhaar}")

    # MPIN Logic
    lower_text = text.lower()
    for num in raw_mpin_list:
        if len(num) == 4 and (num.startswith("19") or num.startswith("20")):
            continue
        if len(num) == 6:
            extra_keywords.append(f"Potential-OTP/PIN:{num}")
        elif len(num) == 4:
            if any(w in lower_text for w in SENSITIVE_CONTEXT_WORDS):
                extra_keywords.append(f"Potential-MPIN:{num}")

    # Crypto & Gift
    for wallet in BTC_REGEX.findall(text):
        extra_keywords.append(f"Crypto-BTC:{wallet}")
    for wallet in ETH_REGEX.findall(text):
        extra_keywords.append(f"Crypto-ETH:{wallet}")
    for code in GIFT_CODE_REGEX.findall(text):
        extra_keywords.append(f"GiftCard-Code:{code}")

    # Keyword Mapping
    for app in REMOTE_APPS:
        if app in lower_text:
            extra_keywords.append(f"App-Detected:{app}")
    for brand in GIFT_BRANDS:
        if brand in lower_text:
            extra_keywords.append(f"Scam-Type:{brand}")

    # --- 3. CLEANING LOGIC (✅ FIXED) ---
    normalized_phones = [re.sub(r"\D", "", p)[-10:] for p in phone_list]
    clean_bank_list = []

    for acc in raw_bank_list:
        # ✅ FIX 2: If account is > 12 digits, it is DEFINITELY a bank/card.
        # Do not check if it contains a phone number.
        if len(acc) > 12:
            clean_bank_list.append(acc)
            continue

        # Only perform the overlap check for smaller numbers (9-12 digits)
        is_phone = False
        for p in normalized_phones:
            if acc == p:  # Exact match
                is_phone = True
                break
            if len(acc) >= 10 and p in acc:  # Phone inside Bank (Collision)
                is_phone = True
                break

        if not is_phone:
            clean_bank_list.append(acc)

    return {
        "upiIds": upi_list,
        "phoneNumbers": phone_list,
        "phishingLinks": url_list,
        "bankAccounts": clean_bank_list,
        "suspiciousKeywords": extra_keywords,
    }
