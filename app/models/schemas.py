from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Message(BaseModel):
    sender:str
    text:str
    timestamp:datetime

class Metadata(BaseModel):
    channel:Optional[str]=None
    language:Optional[str]=None
    locale:Optional[str]=None

class HoneypotRequest(BaseModel):
    sessionId:str
    message:Message
    conversationHistory:Optional[List[Message]]=[]
    metadata:Optional[Metadata]=None

class EngagementMetrics(BaseModel):
    engagementDurationSeconds:int
    totalMessagesExchanged:int

class ExtractedIntelligence(BaseModel):
    bankAccounts:List[str]=[]
    upiIds:List[str]=[]
    phishingLinks:List[str]=[]
    phoneNumbers:List[str]=[]
    suspiciousKeywords:List[str]=[]

class HoneypotResponse(BaseModel):
    status:str
    scamDetected:bool
    engagementMetrics:Optional[EngagementMetrics]=None
    extractedIntelligence:Optional[ExtractedIntelligence]=None
    agentNotes:Optional[str]=None

