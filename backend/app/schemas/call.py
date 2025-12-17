from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any


class CallCreate(BaseModel):
    agent_name: str = Field(..., description="Name of the sales agent")
    customer_name: Optional[str] = Field(None, description="Name of the customer")
    call_type: str = Field(..., description="Type of call (e.g., sales, support)")


class TranscriptionResponse(BaseModel):
    text: Optional[str]
    status: str

    class Config:
        from_attributes = True


class EvaluationResponse(BaseModel):
    score: Optional[float]
    details: Optional[dict[str, Any]]
    status: str

    class Config:
        from_attributes = True


class CallResponse(BaseModel):
    id: int
    agent_name: str
    customer_name: Optional[str]
    call_type: str
    call_date: datetime

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
