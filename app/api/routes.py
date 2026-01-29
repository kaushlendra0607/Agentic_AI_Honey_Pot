from fastapi import APIRouter, Depends
from datetime import datetime, timezone
import requests  # <--- Added this

from app.models.schemas import (
    HoneypotRequest, 
    HoneypotResponse, 
    EngagementMetrics, 
    ExtractedIntelligence
)
from app.core.auth import verify_api_key
from app.core.session import get_or_create_session
from app.detection.scam_detector import detect_scam
from app.agent.agent import generate_agent_reply
from app.intelligence.extractor import extract_intelligence

router = APIRouter()

# --- HELPER FUNCTION: Smart Notes ---
def generate_agent_notes(intel):
    """Creates a summary based on what was found."""
    notes = []
    if intel.get("upiIds"): notes.append("Asked for UPI transfer.")
    if intel.get("bankAccounts"): notes.append("Provided Bank Account details.")
    if intel.get("phishingLinks"): notes.append("Sent Phishing Link.")
    if intel.get("phoneNumbers"): notes.append("Shared Phone Number.")
    
    # Check suspicious keywords for specifics
    keywords = str(intel.get("suspiciousKeywords", []))
    if "GiftCard" in keywords: notes.append("Demanded Gift Cards.")
    if "Crypto" in keywords: notes.append("Demanded Crypto (BTC/ETH).")
    if "App-Detected" in keywords: notes.append("Attempted Remote Access (AnyDesk/TeamViewer).")
    
    if not notes:
        return "Scam detected, engaging in conversation."
    return "Scammer behavior identified: " + " ".join(notes)


@router.post(
    "/honeypot", 
    response_model=HoneypotResponse, 
    dependencies=[Depends(verify_api_key)]
)
async def honeypot_endpoint(payload: HoneypotRequest):
    # 1. Get Session
    session = get_or_create_session(payload.sessionId)

    # If our memory is empty but they sent history, restore it.
    if len(session["messages"]) == 0 and len(payload.conversationHistory) > 0:
        for old_msg in payload.conversationHistory:
            session["messages"].append(old_msg.dict())
        session["messageCount"] = len(payload.conversationHistory)

    # 2. Add the New Message
    session["messages"].append(payload.message.dict())
    session["messageCount"] += 1
    session["last_user_message"] = payload.message.text

    # 3. Scam Detection
    if not session["scamDetected"]:
        is_scam, keywords = detect_scam(payload.message.text)
        if is_scam:
            session["scamDetected"] = True
            session["intelligence"]["suspiciousKeywords"].extend(keywords)

    # 4. Extract Intelligence
    intel = extract_intelligence(payload.message.text)
    for key, values in intel.items():
        if key in session["intelligence"]:
            for value in values:
                if value not in session["intelligence"][key]:
                    session["intelligence"][key].append(value)

    # 5. Calculate Metrics
    duration = int((datetime.now(timezone.utc) - session["startTime"]).total_seconds())
    metrics_obj = EngagementMetrics(
        engagementDurationSeconds=duration,
        totalMessagesExchanged=session["messageCount"]
    )

    # 6. Generate Agent Reply (ALWAYS REPLY)
    agent_reply = generate_agent_reply(session)

    # 7. Generate Dynamic Notes
    final_notes = generate_agent_notes(session["intelligence"])

    # 8. MANDATORY CALLBACK (Section 12 Compliance)
    # We send this every time we detect a scam to ensure the dashboard is live-updated.
    try:
        if session.get("scamDetected"):
            guvi_payload = {
                "sessionId": payload.sessionId,  # Fixed variable name
                "scamDetected": True,
                "totalMessagesExchanged": session["messageCount"],
                "extractedIntelligence": session["intelligence"], # Sending raw dict
                "agentNotes": final_notes  # Sending smart notes
            }
            
            # Send to Guvi (with 5s deadline)
            requests.post(
                "https://hackathon.guvi.in/api/updateHoneyPotFinalResult",
                json=guvi_payload,
                timeout=5 
            )
    except Exception as e:
        print(f"Callback Failed (Non-fatal): {e}")

    # 9. Return Response (Section 8 + 3 Compliance)
    intel_obj = ExtractedIntelligence(**session["intelligence"])

    return HoneypotResponse(
        status="success",
        reply=agent_reply or '....',
        scamDetected=session["scamDetected"],
        engagementMetrics=metrics_obj,
        extractedIntelligence=intel_obj,
        agentNotes=final_notes  # <--- Using the smart notes here too
    )