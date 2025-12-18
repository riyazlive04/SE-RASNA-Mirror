from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from datetime import datetime

from app.core.database import Base


class UserBaseline(Base):
    """
    Personal baseline intelligence derived from user's "Best Calls".

    Phase 7: Stores aggregated intelligence from calls marked as is_baseline=True.
    This is NOT ML model training - it's structured intelligence aggregation.

    Purpose:
    - Each user generates their own baseline from their best calls
    - Used for comparing new evaluations against personal best patterns
    - Completely optional and user-driven
    - Scoped by user_id for multi-user isolation

    Design decision: Separate table (vs JSON on User) for:
    - Cleaner schema evolution
    - Easier querying and indexing
    - Clear separation of concerns
    - Better audit trail with timestamps
    """
    __tablename__ = "user_baselines"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    # Aggregated RASNA averages from baseline calls
    # Structure: {"rapport": 8.5, "ask": 9.0, "situation": 7.8, "next_steps": 8.2, "articulation": 8.8}
    rasna_averages = Column(JSON, nullable=False)

    # Aggregated insights summary
    # Structure: {
    #   "common_strengths": ["rapport", "articulation"],
    #   "common_improvement_themes": ["ask"],
    #   "average_overall_score": 8.46
    # }
    summary_json = Column(JSON, nullable=False)

    # Number of baseline calls used to generate this baseline
    call_count = Column(Integer, nullable=False)

    # Audit timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
