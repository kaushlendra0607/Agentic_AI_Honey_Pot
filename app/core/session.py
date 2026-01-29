from datetime import datetime, timezone

# In-Memory Database (RAM)
# Note: If you restart the server, all session data is lost!
_sessions = {}

def get_or_create_session(session_id: str):
    if session_id not in _sessions:
        _sessions[session_id] = {
            "sessionId": session_id,
            
            # Use safe UTC time
            "startTime": datetime.now(timezone.utc),
            
            "messages": [],
            "messageCount": 0,
            
            # STATE FLAGS
            "scamDetected": False,
            "reported": False,  # True if we already sent data to Guvi
            
            # CRITICAL ADDITION: The AI needs this to read the latest text
            "last_user_message": "", 
            
            # THE TRAP DATA
            "intelligence": {
                "bankAccounts": [],
                "upiIds": [],
                "phishingLinks": [],
                "phoneNumbers": [],
                "suspiciousKeywords": []
            }
        }

    return _sessions[session_id]