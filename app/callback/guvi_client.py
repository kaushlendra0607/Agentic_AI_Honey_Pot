import requests

GUVI_ENDPOINT = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

def send_final_result(payload: dict):
    try:
        requests.post(GUVI_ENDPOINT, json=payload, timeout=5)
    except Exception as e:
        print("GUVI callback failed:", e)
