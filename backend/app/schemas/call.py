from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal


class CallCreate(BaseModel):
    agent_name: str = Field(..., description="Name of the sales agent")
    customer_name: Optional[str] = Field(None, description="Name of the customer")
    call_type: str = Field(..., description="Type of call (e.g., sales, support)")
    lead_type: Literal["hot", "warm", "cold"] = Field(..., description="Lead temperature")
    call_stage: Literal["qualification", "main", "follow-up"] = Field(..., description="Call stage")
    deck_shared: bool = Field(default=False, description="Whether deck was shared during call")


class TranscriptionResponse(BaseModel):
    text: Optional[str]
    status: Literal["pending", "completed", "failed"]

    class Config:
        from_attributes = True


class RasnaScore(BaseModel):
    """RASNA Framework component scores (0-100)"""
    rapport: int = Field(..., ge=0, le=100, description="Rapport building score")
    situation: int = Field(..., ge=0, le=100, description="Situation understanding score")
    pain: int = Field(..., ge=0, le=100, description="Pain identification score")
    need: int = Field(..., ge=0, le=100, description="Need articulation score")
    ask: int = Field(..., ge=0, le=100, description="Ask/close effectiveness score")
    overall: int = Field(..., ge=0, le=100, description="Overall RASNA score")


class EvaluationResult(BaseModel):
    """Complete RASNA evaluation output"""
    scores: RasnaScore
    strengths: list[str] = Field(..., description="Key strengths identified in the call")
    improvements: list[str] = Field(..., description="Areas for improvement")
    next_call_focus: str = Field(..., description="Primary focus area for next call")


class EvaluationResponse(BaseModel):
    result: Optional[EvaluationResult]
    status: Literal["pending", "completed", "failed"]

    class Config:
        from_attributes = True


class CallResponse(BaseModel):
    id: int
    agent_name: str
    customer_name: Optional[str]
    call_type: str
    call_date: datetime

    lead_type: str
    call_stage: str
    deck_shared: bool

    audio_filename: str
    audio_format: str
    audio_size: int

    transcription: TranscriptionResponse
    evaluation: EvaluationResponse

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CallListResponse(BaseModel):
    total: int
    calls: list[CallResponse]
