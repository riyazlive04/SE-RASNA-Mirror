from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from datetime import datetime

from app.core.database import Base


class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)

    # Call context
    agent_name = Column(String, nullable=False)
    customer_name = Column(String, nullable=True)
    call_type = Column(String, nullable=False)
    call_date = Column(DateTime, default=datetime.utcnow)

    # Audio file info
    audio_filename = Column(String, nullable=False, unique=True)
    audio_path = Column(String, nullable=False)
    audio_format = Column(String, nullable=False)
    audio_size = Column(Integer, nullable=False)

    # Transcription
    transcription_text = Column(Text, nullable=True)
    transcription_status = Column(String, default="pending")

    # RASNA Evaluation
    evaluation_score = Column(Float, nullable=True)
    evaluation_details = Column(JSON, nullable=True)
    evaluation_status = Column(String, default="pending")

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
