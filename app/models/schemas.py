from pydantic import BaseModel, Field
from typing import List, Optional

# --- SUB-MODELS ---

class Message(BaseModel):
    sender: str = Field(
        ..., 
        description="Identifies who sent the message.",
        json_schema_extra={"example": "scammer"}
    )
    text: str = Field(
        ..., 
        description="The actual content of the message.",
        json_schema_extra={"example": "Your account is blocked. Verify now."}
    )
    timestamp: str = Field(
        ..., 
        description="ISO-8601 timestamp string.",
        json_schema_extra={"example": "2026-01-21T10:15:30Z"}
    )

class Metadata(BaseModel):
    channel: Optional[str] = Field(
        default="SMS", 
        description="Communication medium.",
        json_schema_extra={"example": "WhatsApp"}
    )
    language: Optional[str] = Field(
        default="English", 
        description="Language code.",
        json_schema_extra={"example": "English"}
    )
    locale: Optional[str] = Field(
        default="IN", 
        description="Region locale.",
        json_schema_extra={"example": "IN"}
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
        description="Scam triggers, Gift Card codes, Crypto addresses."
    )

# --- MAIN REQUEST ---
class HoneypotRequest(BaseModel):
    sessionId: str = Field(
        ..., 
        description="Unique Session ID provided by the platform.",
        json_schema_extra={"example": "wertyu-dfghj-ertyui"}
    )
    message: Message = Field(
        ..., 
        description="The latest message object."
    )
    conversationHistory: List[Message] = Field(
        default_factory=list, 
        description="List of all previous messages."
    )
    metadata: Optional[Metadata] = Field(
        default=None, 
        description="Optional context."
    )

# --- MAIN RESPONSE ---
class HoneypotResponse(BaseModel):
    status: str = Field(
        ..., 
        description="API status.", 
        json_schema_extra={"example": "success"}
    )
    reply: str = Field(
        ..., 
        description="The AI Agent's response.",
        json_schema_extra={"example": "Why is my account blocked?"}
    )
    
    # Optional Fields
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