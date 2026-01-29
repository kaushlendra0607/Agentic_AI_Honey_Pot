from pydantic import BaseModel, Field
from typing import List, Optional

# --- SUB-MODELS ---
class Message(BaseModel):
    sender: str
    text: str
    timestamp: str 

class Metadata(BaseModel):
    channel: Optional[str] = "SMS"
    language: Optional[str] = "English"
    locale: Optional[str] = "IN"

class EngagementMetrics(BaseModel):
    engagementDurationSeconds: int
    totalMessagesExchanged: int

class ExtractedIntelligence(BaseModel):
    bankAccounts: List[str] = Field(default_factory=list)
    upiIds: List[str] = Field(default_factory=list)
    phishingLinks: List[str] = Field(default_factory=list)
    phoneNumbers: List[str] = Field(default_factory=list)
    suspiciousKeywords: List[str] = Field(default_factory=list)

# --- MAIN REQUEST (Section 6 Compliant) ---
class HoneypotRequest(BaseModel):
    sessionId: str
    message: Message
    conversationHistory: List[Message] = Field(default_factory=list) 
    metadata: Optional[Metadata] = None

# --- MAIN RESPONSE (Section 8 Compliant) ---
class HoneypotResponse(BaseModel):
    status: str
    
    # ✅ FIX: Renamed 'generated_reply' to 'reply' (Per Section 8)
    reply: str  
    
    # We keep these as Optional so your Dashboard still works, 
    # but they won't cause validation errors if Guvi ignores them.
    scamDetected: Optional[bool] = None
    engagementMetrics: Optional[EngagementMetrics] = None
    extractedIntelligence: Optional[ExtractedIntelligence] = None
    agentNotes: Optional[str] = None