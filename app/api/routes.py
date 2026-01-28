from fastapi import APIRouter, Depends
from datetime import datetime

from app.models.schemas import HoneypotRequest, HoneypotResponse
from app.core.auth import verify_api_key
from app.core.session import get_or_create_session
from app.detection.scam_detector import detect_scam
from app.agent.agent import generate_agent_reply
from app.intelligence.extractor import extract_intelligence
from app.callback.guvi_client import send_final_result

router = APIRouter()

@router.post(
    "/honeypot",
    response_model=HoneypotResponse,
    dependencies=[Depends(verify_api_key)]
)
def honeypot_endpoint(payload: HoneypotRequest):
    session = get_or_create_session(payload.sessionId)

    # 1. Update session memory
    session["messages"].append(payload.message.dict())
    session["messageCount"] += 1

    # 2. Scam detection (only once)
    if not session["scamDetected"]:
        is_scam, keywords = detect_scam(payload.message.text)
        if is_scam:
            session["scamDetected"] = True
            session["intelligence"]["suspiciousKeywords"].extend(keywords)

    # 3. Extract intelligence from incoming message
    intel = extract_intelligence(payload.message.text)
    for key, values in intel.items():
        for value in values:
            if value not in session["intelligence"][key]:
                session["intelligence"][key].append(value)

    # 4. Engagement metrics
    engagement_metrics = None
    if session["scamDetected"]:
        duration = int(
            (datetime.utcnow() - session["startTime"]).total_seconds()
        )
        engagement_metrics = {
            "engagementDurationSeconds": duration,
            "totalMessagesExchanged": session["messageCount"]
        }

    # 5. Agent response (after intel + metrics)
    agent_reply = None
    if session["scamDetected"]:
        agent_reply = generate_agent_reply(session)

    # 6. Mandatory GUVI callback (one-time)
    if (
        session["scamDetected"]
        and session["messageCount"] >= 2
        and not session.get("reported", False)
    ):
        payload = {
            "sessionId": session["sessionId"],
            "scamDetected": True,
            "totalMessagesExchanged": session["messageCount"],
            "extractedIntelligence": session["intelligence"],
            "agentNotes": "Scammer used urgency tactics and payment redirection"
        }
        send_final_result(payload)
        session["reported"] = True

    # 7. Response
    return HoneypotResponse(
        status="success",
        scamDetected=session["scamDetected"],
        engagementMetrics=engagement_metrics,
        extractedIntelligence=session["intelligence"],
        agentNotes=agent_reply
    )
