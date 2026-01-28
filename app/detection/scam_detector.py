SCAM_KEYWORDS=[
    "blocked","suspended","verify","urgent","account",
    "upi","otp","freeze","immediately","bank"
]

def detect_scam(text:str):
    text_lower=text.lower()
    hits=[kw for kw in SCAM_KEYWORDS if kw in text_lower]
    score=len(hits)
    return score>=2,hits
