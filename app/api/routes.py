from fastapi import APIRouter, Depends
from datetime import datetime
from datetime import timezone

# i_mport Pydantic Models for safe data handling
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
from app.callback.guvi_client import send_report

router = APIRouter()

@router.post(
    "/honeypot", 
    response_model=HoneypotResponse, 
    dependencies=[Depends(verify_api_key)]
)
async def honeypot_endpoint(payload: HoneypotRequest):
    # 1. Get Session
    session = get_or_create_session(payload.sessionId)

    # 2. Update Memory (CRITICAL FIX: Save the text so Agent sees it!)
    session["messages"].append(payload.message.dict())
    session["messageCount"] += 1
    session["last_user_message"] = payload.message.text  # <--- FIXED: Agent needs this

    # 3. Scam Detection
    if not session["scamDetected"]:
        is_scam, keywords = detect_scam(payload.message.text)
        if is_scam:
            session["scamDetected"] = True
            session["intelligence"]["suspiciousKeywords"].extend(keywords)

    # 4. Extract Intelligence (Bank accounts, UPIs)
    intel = extract_intelligence(payload.message.text)
    for key, values in intel.items():
        # Ensure the key exists in session intel before appending
        if key in session["intelligence"]:
            for value in values:
                if value not in session["intelligence"][key]:
                    session["intelligence"][key].append(value)

    # 5. Calculate Metrics (Dynamic now, not hardcoded!)
    duration = int((datetime.now(timezone.utc) - session["startTime"]).total_seconds())
    
    # Create the Metrics Object safely
    metrics_obj = EngagementMetrics(
        engagementDurationSeconds=duration,
        totalMessagesExchanged=session["messageCount"]
    )

    # 6. Generate Agent Reply (Only if it's a scam)
    agent_reply = "Processing..."
    if session["scamDetected"]:
        agent_reply = generate_agent_reply(session)

    # 7. GUVI Callback (Report to Hackathon Dashboard)
    # We report if we found intel OR if the conversation is getting long
    should_report = (
        session["scamDetected"] 
        and not session.get("reported", False)
        and (len(session["intelligence"]["upiIds"]) > 0 or session["messageCount"] >= 3)
    )

    if should_report:
        report_payload = {
            "sessionId": session["sessionId"],
            "scamDetected": True,
            "totalMessagesExchanged": session["messageCount"],
            "extractedIntelligence": session["intelligence"],
            "agentNotes": "Scammer engaged. Payment details extracted.",
        }
        await send_report(session, duration, session["messageCount"])
        session["reported"] = True

    # 8. Return Response (Fixing the Pydantic Type Errors)
    # We convert the session dict back into the ExtractedIntelligence Object
    intel_obj = ExtractedIntelligence(**session["intelligence"])

    return HoneypotResponse(
        status="success",
        scamDetected=session["scamDetected"],
        
        # Pass the Object, not the dict
        engagementMetrics=metrics_obj,
        
        # Pass the real agent reply
        generated_reply=agent_reply or "...", 
        
        # Pass the Object, not the dict
        extractedIntelligence=intel_obj,
        
        agentNotes="Engaging target."
    )