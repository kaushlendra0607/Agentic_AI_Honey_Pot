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

# 🕵️ GLOBAL DEBUG VAR
_debug_last_payload = {"status": "No data sent yet"}

# --- CALLBACK LOGIC ---
async def send_guvi_callback(payload: dict):
    global _debug_last_payload
    _debug_last_payload = payload 

    target_url = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
    
    # Debug Log
    # print(f"📤 [CALLBACK] Sending Payload: {payload}")

    try:
        async with httpx.AsyncClient() as client:
            # ✅ TIMEOUT OPTIMIZATION: Reduced to 5.0s to prevent hanging
            response = await client.post(
                target_url,
                json=payload,
                timeout=5.0 
            )
            if response.status_code == 200:
                print(f"✅ GUVI ACCEPTED DATA")
            elif response.status_code == 422:
                print(f"❌ GUVI REJECTED (Schema Error): {response.text}")
            else:
                print(f"⚠️ GUVI STATUS {response.status_code}: {response.text}")

    except Exception as e:
        print(f"⚠️ Callback Network Error: {e}")

def generate_agent_notes(intel):
    notes = []
    if intel.get("upiIds"): notes.append("Asked for UPI.")
    if intel.get("bankAccounts"): notes.append("Provided Bank Info.")
    if intel.get("phishingLinks"): notes.append("Sent Link.")
    if intel.get("phoneNumbers"): notes.append("Shared Phone Number.")
    
    keywords = str(intel.get("suspiciousKeywords", []))
    if "GiftCard" in keywords: notes.append("Demanded Gift Cards.")
    if "Crypto" in keywords: notes.append("Demanded Crypto.")
    if "App-Detected" in keywords: notes.append("Attempted Remote Access.")
    
    if not notes: return "Scam detected, engaging."
    return "Scammer behavior identified: " + " ".join(notes)

# ✅ ALIASES
@router.post("/honeypot", response_model=HoneypotResponse, dependencies=[Depends(verify_api_key)])
@router.post("/h", response_model=HoneypotResponse, dependencies=[Depends(verify_api_key)])
async def honeypot_endpoint(payload: HoneypotRequest): # <--- ✅ CLEAN SIGNATURE (No BackgroundTasks)
    start_cpu = time.perf_counter()

    # 1. Get Session
    session = get_or_create_session(payload.sessionId)
    
    # History Sync (Safe Handling)
    incoming_history = payload.conversationHistory
    if incoming_history is None:
        incoming_history = []
        
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
    final_notes = generate_agent_notes(session["intelligence"])
    if session.get("scamDetected"):
        guvi_payload = {
            "sessionId": payload.sessionId,
            "scamDetected": True,
            "totalMessagesExchanged": session["messageCount"],
            "extractedIntelligence": session["intelligence"],
            "agentNotes": final_notes
        }
        await send_guvi_callback(guvi_payload)

    # 7. Save Session
    save_session(payload.sessionId, session)

    # ⏱️ SMART SLEEP LOGIC
    # Only sleep if we were too fast. If we were slow (Cold Start), don't sleep!
    end_cpu = time.perf_counter()
    processing_time = end_cpu - start_cpu
    
    target_time = 1.0 # Minimum time the request should take
    
    if processing_time < target_time:
        sleep_needed = target_time - processing_time
        print(f"⏱️ [SPEED] Too Fast ({processing_time:.4f}s). Sleeping {sleep_needed:.4f}s...")
        await asyncio.sleep(sleep_needed)
    else:
        print(f"⏱️ [SPEED] Slow Request ({processing_time:.4f}s). No sleep needed.")

    return HoneypotResponse(
        status="success",
        reply=agent_reply or "..."
    )

@router.get("/debug/guvi-log")
async def get_last_guvi_data():
    return _debug_last_payload