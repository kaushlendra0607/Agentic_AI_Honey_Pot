from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional, Any, Union

# --- SUB-MODELS ---

class Message(BaseModel):
    # Ignore extra fields like 'id' or 'metadata' inside message
    model_config = ConfigDict(extra='ignore') 
    
    sender: str = Field(
        ..., 
        description="Identifies who sent the message (scammer/user)."
    )
    text: str = Field(
        ..., 
        description="The actual content of the message."
    )
    
    # Accept String OR Int, but describe it clearly
    timestamp: Union[str, int, float] = Field(
        ..., 
        description="Timestamp (accepts ISO string or Unix epoch)."
    )

    # Validator to force numbers into strings so your code doesn't break
    @field_validator('timestamp', mode='before')
    def convert_timestamp_to_string(cls, v):
        return str(v)

class Metadata(BaseModel):
    model_config = ConfigDict(extra='ignore')
    
    # ✅ FIX: Use 'default=' explicitly to satisfy the Type Checker
    channel: Optional[str] = Field(
        default="SMS", 
        description="Communication medium (SMS, WhatsApp, etc)."
    )
    language: Optional[str] = Field(
        default="English", 
        description="Language code."
    )
    locale: Optional[str] = Field(
        default="IN", 
        description="Region locale (e.g., IN)."
    )

class EngagementMetrics(BaseModel):
    engagementDurationSeconds: int = Field(
        ..., 
        description="Time in seconds since session started."
    )
    totalMessagesExchanged: int = Field(
        ..., 
        description="Total count of messages sent by both parties."
    )

class ExtractedIntelligence(BaseModel):
    bankAccounts: List[str] = Field(
        default_factory=list, 
        description="Detected Bank Account numbers."
    )
    upiIds: List[str] = Field(
        default_factory=list, 
        description="Detected UPI IDs."
    )
    phishingLinks: List[str] = Field(
        default_factory=list, 
        description="Detected malicious URLs."
    )
    phoneNumbers: List[str] = Field(
        default_factory=list, 
        description="Detected phone numbers."
    )
    suspiciousKeywords: List[str] = Field(
        default_factory=list, 
        description="Scam triggers detected."
    )

# --- MAIN REQUEST ---
class HoneypotRequest(BaseModel):
    model_config = ConfigDict(extra='ignore') # CRITICAL: Guvi sends extra stuff

    sessionId: str = Field(
        ..., 
        description="Unique Session ID provided by the platform."
    )
    message: Message = Field(
        ..., 
        description="The latest message object."
    )
    
    # Handle Missing Key AND Null value gracefully
    conversationHistory: Optional[List[Message]] = Field(
        default_factory=list, 
        description="History of chat. Defaults to empty list."
    )
    
    # ✅ FIX: Use lambda to silence the "Argument type" error
    metadata: Optional[Metadata] = Field(
        default_factory=lambda: Metadata(),
        description="Optional context."
    )

# --- MAIN RESPONSE ---
class HoneypotResponse(BaseModel):
    status: str = Field(
        ..., 
        description="API status (Section 8 compliant)."
    )
    reply: str = Field(
        ..., 
        description="The AI Agent's response."
    )
    scamDetected: Optional[bool] = Field(
        default=None, 
        description="True if scam detected."
    )
    engagementMetrics: Optional[EngagementMetrics] = Field(
        default=None, 
        description="Session metrics."
    )
    extractedIntelligence: Optional[ExtractedIntelligence] = Field(
        default=None, 
        description="Structured intelligence."
    )
    agentNotes: Optional[str] = Field(
        default=None, 
        description="Summary of scammer behavior."
    )