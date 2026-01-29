import httpx
from app.core.config import GUVI_ENDPOINT

async def send_report(session_data: dict, duration: int, message_count: int):
    """
    Sends the final report to the Hackathon Judge Server.
    Schema fixed based on 422 Error Log from Jan 29, 2026.
    """
    
    # 1. Construct the FLAT Payload (Exactly what the server asked for)
    payload = {
        "sessionId": session_data["sessionId"],
        "scamDetected": session_data.get("scamDetected", False),
        
        # FIX 1: Rename 'intelligence' to 'extractedIntelligence'
        "extractedIntelligence": session_data.get("intelligence", {
            "bankAccounts": [],
            "upiIds": [],
            "phishingLinks": [],
            "phoneNumbers": [],
            "suspiciousKeywords": []
        }),
        
        # FIX 2: Flatten the metrics (No "engagementMetrics" wrapper)
        "totalMessagesExchanged": message_count,
        "engagementDurationSeconds": duration,
        
        # FIX 3: Add the missing 'agentNotes' field
        "agentNotes": "Automated HoneyPot Report: Target engaged and intelligence extracted."
    }

    # 2. Send it
    async with httpx.AsyncClient() as client:
        try:
            print(f"🚀 Sending Report to Guvi for {payload['sessionId']}...")
            response = await client.post(GUVI_ENDPOINT, json=payload, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Report Sent Successfully! Server replied: {response.text}")
            else:
                print(f"⚠️ Report Failed with {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Connection Error sending report: {e}")