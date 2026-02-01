# app/api/routes.py
from fastapi import APIRouter, Depends
import httpx 
import time
import asyncio 

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

# 🕵️ GLOBAL DEBUG VAR (Stores the last payload sent to Guvi for debugging)
_debug_last_payload = {"status": "No data sent yet"}

# --- CALLBACK LOGIC ---
async def send_guvi_callback(payload: dict):
    """
    Sends the FINAL RESULT to Guvi.
    NOW AWAITED (Blocking) to ensure data reaches Guvi before the test finishes.
    """
    global _debug_last_payload
    _debug_last_payload = payload # Update debug var

    target_url = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
    
    # Debug Log
    print(f"📤 [CALLBACK] Sending Payload: {payload}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                target_url,
                json=payload,
                timeout=10.0 
            )
            # Only print if it fails or succeeds
            if response.status_code == 200:
                print(f"✅ GUVI ACCEPTED DATA: {response.text}")
            elif response.status_code == 422:
                # This is the most common error: Schema Mismatch
                print(f"❌ GUVI REJECTED (Schema Error): {response.text}")
            else:
                print(f"⚠️ GUVI STATUS {response.status_code}: {response.text}")

    except Exception as e:
        print(f"⚠️ Callback Network Error: {e}")

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

# ✅ ALIASES: Listen on both /honeypot and /h
@router.post("/honeypot", response_model=HoneypotResponse, dependencies=[Depends(verify_api_key)])
@router.post("/h", response_model=HoneypotResponse, dependencies=[Depends(verify_api_key)])
async def honeypot_endpoint(payload: HoneypotRequest): # <--- Removed BackgroundTasks here
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
    for key, values in intel.items():
        if key in session["intelligence"]:
            for value in values:
                if value not in session["intelligence"][key]:
                    session["intelligence"][key].append(value)

    # 5. Generate Reply
    agent_reply = generate_agent_reply(session)
    
    # 6. Callback (BLOCKING MODE) 🛑
    # We ensure Guvi has the data BEFORE we reply to the user.
    final_notes = generate_agent_notes(session["intelligence"])
    if session.get("scamDetected"):
        guvi_payload = {
            "sessionId": payload.sessionId,
            "scamDetected": True,
            "totalMessagesExchanged": session["messageCount"],
            "extractedIntelligence": session["intelligence"],
            "agentNotes": final_notes
        }
        # ✅ AWAITING THE CALL (No Background Task)
        await send_guvi_callback(guvi_payload)

    # 7. Save Session
    save_session(payload.sessionId, session)

    end_cpu = time.perf_counter()
    sleep_time = 0.5
    print(f"⏱️ [SPEED] Logic took {end_cpu - start_cpu:.4f}s. Sleeping for {sleep_time}s... 💤")

    # 🛑 HUMAN DELAY
    await asyncio.sleep(sleep_time)

    # 8. Return
    return HoneypotResponse(
        status="success",
        reply=agent_reply or "..."
    )

# --- ✅ DEBUG ENDPOINT ---
@router.get("/debug/guvi-log")
async def get_last_guvi_data():
    """Returns the last payload sent to Guvi."""
    return _debug_last_payload