from fastapi import APIRouter, Depends
from datetime import datetime
from datetime import timezone

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
    # No "if scamDetected" check anymore. We always talk.
    agent_reply = generate_agent_reply(session)

    # 7. GUVI Callback
    should_report = (
        session["scamDetected"] 
        and not session.get("reported", False)
        and (len(session["intelligence"]["upiIds"]) > 0 or session["messageCount"] >= 3)
    )

    if should_report:
        await send_report(session, duration, session["messageCount"])
        session["reported"] = True

    # 8. Return Response
    intel_obj = ExtractedIntelligence(**session["intelligence"])

    return HoneypotResponse(
        status="success",
        reply= agent_reply or '....',
        scamDetected=session["scamDetected"],
        engagementMetrics=metrics_obj,
        extractedIntelligence=intel_obj,
        agentNotes="Engaging target."
    )