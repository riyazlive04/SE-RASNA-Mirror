from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from app.core.database import Base


class Team(Base):
    """
    Phase 9: Team model for agency/manager collaboration.

    Purpose:
    - Enable team-level aggregated insights
    - Maintain strict ownership (created_by = owner)
    - No automatic enrollment
    - No mutation of personal baselines

    Design:
    - Each team has exactly one owner (created_by)
    - Owner can invite managers and members
    - Team baseline snapshots are derived/aggregated only
    """
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
