# app/api/routes.py
from fastapi import APIRouter, Depends, BackgroundTasks
import httpx 
import time # <--- ✅ Used for Performance Timer

from app.models.schemas import (
    HoneypotRequest, 
    HoneypotResponse
)
from app.core.auth import verify_api_key
from app.core.session import get_or_create_session, save_session 
from app.detection.scam_detector import detect_scam
from app.agent.agent import generate_agent_reply
from app.intelligence.extractor import extract_intelligence

router = APIRouter()

# --- CALLBACK LOGIC (SECTION 12) ---
async def send_guvi_callback(payload: dict):
    """
    Sends the FINAL RESULT to Guvi. 
    """
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                "https://hackathon.guvi.in/api/updateHoneyPotFinalResult",
                json=payload,
                timeout=20.0 
            )
            # print("✅ Intel sent to Guvi HQ.")
    except Exception as e:
        print(f"⚠️ Callback Error: {e}")

def generate_agent_notes(intel):
    """Generates the 'agentNotes' string for the callback."""
    notes = []
    if intel.get("upiIds"): notes.append("Asked for UPI transfer.")
    if intel.get("bankAccounts"): notes.append("Provided Bank Account.")
    if intel.get("phishingLinks"): notes.append("Sent Phishing Link.")
    if intel.get("phoneNumbers"): notes.append("Shared Phone Number.")
    
    keywords = str(intel.get("suspiciousKeywords", []))
    if "GiftCard" in keywords: notes.append("Demanded Gift Cards.")
    if "Crypto" in keywords: notes.append("Demanded Crypto.")
    if "App-Detected" in keywords: notes.append("Attempted Remote Access.")
    
    if not notes: return "Scam detected, engaging."
    return "Scammer behavior identified: " + " ".join(notes)

@router.post(
    "/honeypot", 
    response_model=HoneypotResponse, 
    dependencies=[Depends(verify_api_key)]
)
async def honeypot_endpoint(payload: HoneypotRequest, background_tasks: BackgroundTasks):
    # ⏱️ START TIMER
    start_cpu = time.perf_counter()

    # 1. Get Session
    session = get_or_create_session(payload.sessionId)
    
    # History Sync
    incoming_history = payload.conversationHistory or []
    if len(session["messages"]) == 0 and len(incoming_history) > 0:
        for old_msg in incoming_history:
            session["messages"].append(old_msg.model_dump())
        session["messageCount"] = len(incoming_history)

    # 2. Add New Message
    session["messages"].append(payload.message.model_dump())
    session["messageCount"] += 1
    session["last_user_message"] = payload.message.text

    # 3. Detect Scam
    if not session.get("scamDetected", False):
        is_scam, keywords = detect_scam(payload.message.text)
        if is_scam:
            session["scamDetected"] = True
            if "suspiciousKeywords" not in session["intelligence"]:
                session["intelligence"]["suspiciousKeywords"] = []
            session["intelligence"]["suspiciousKeywords"].extend(keywords)

    # 4. Extract Intelligence
    intel = extract_intelligence(payload.message.text)
    # Merge Logic
    for key, values in intel.items():
        if key in session["intelligence"]:
            for value in values:
                if value not in session["intelligence"][key]:
                    session["intelligence"][key].append(value)

    # 5. Generate Reply
    agent_reply = generate_agent_reply(session)
    
    # 6. Prepare Callback Data (Section 12 Compliance)
    final_notes = generate_agent_notes(session["intelligence"])
    
    if session.get("scamDetected"):
        guvi_payload = {
            "sessionId": payload.sessionId,
            "scamDetected": True,
            "totalMessagesExchanged": session["messageCount"],
            "extractedIntelligence": session["intelligence"],
            "agentNotes": final_notes
        }
        background_tasks.add_task(send_guvi_callback, guvi_payload)

    # 7. Save Session
    save_session(payload.sessionId, session)

    # ⏱️ END TIMER
    end_cpu = time.perf_counter()
    print(f"⏱️ [PERFORMANCE] Total Cycle Time: {end_cpu - start_cpu:.4f} seconds")

    # 8. RETURN ONLY STATUS & REPLY (Section 8 Compliance)
    return HoneypotResponse(
        status="success",
        reply=agent_reply or "..."
    )