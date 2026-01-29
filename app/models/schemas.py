from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# --- SUB-MODELS ---
class Message(BaseModel):
    sender: str
    text: str
    timestamp: datetime

class Metadata(BaseModel):
    channel: Optional[str] = None
    language: Optional[str] = None
    locale: Optional[str] = None

class EngagementMetrics(BaseModel):
    engagementDurationSeconds: int
    totalMessagesExchanged: int

class ExtractedIntelligence(BaseModel):
    # We use default_factory=list to ensure every user gets a FRESH list
    bankAccounts: List[str] = Field(default_factory=list)
    upiIds: List[str] = Field(default_factory=list)
    phishingLinks: List[str] = Field(default_factory=list)
    phoneNumbers: List[str] = Field(default_factory=list)
    suspiciousKeywords: List[str] = Field(default_factory=list)

# --- MAIN REQUEST ---
class HoneypotRequest(BaseModel):
    sessionId: str
    message: Message
    conversationHistory: Optional[List[Message]] = Field(default_factory=list)
    metadata: Optional[Metadata] = None

# --- MAIN RESPONSE ---
class HoneypotResponse(BaseModel):
    status: str
    scamDetected: bool
    
    # This is the critical field that lets your bot "talk"
    generated_reply: str = Field(..., description="The text your bot wants to say back to the scammer")
    
    engagementMetrics: Optional[EngagementMetrics] = None
    extractedIntelligence: Optional[ExtractedIntelligence] = None
    agentNotes: Optional[str] = None