from datetime import datetime

_sessions={}

def get_or_create_session(session_id:str):
    if session_id not in _sessions:
        _sessions[session_id] = {
          "sessionId": session_id,
          "startTime": datetime.utcnow(),
          "messages": [],
          "scamDetected": False,
          "messageCount": 0,
          "reported": False,
          "intelligence": {
          "bankAccounts": [],
          "upiIds": [],
          "phishingLinks": [],
          "phoneNumbers": [],
          "suspiciousKeywords": []
    }
}

    return _sessions[session_id]
