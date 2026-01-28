import re

UPI_REGEX = re.compile(r"[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}")
PHONE_REGEX = re.compile(r"\+91\d{10}")
URL_REGEX = re.compile(r"https?://[^\s]+")

def extract_intelligence(text: str):
    return {
        "upiIds": UPI_REGEX.findall(text),
        "phoneNumbers": PHONE_REGEX.findall(text),
        "phishingLinks": URL_REGEX.findall(text)
    }
