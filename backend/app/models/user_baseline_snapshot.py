from sqlalchemy import Column, Integer, JSON, DateTime, ForeignKey
from datetime import datetime

from app.core.database import Base


class UserBaselineSnapshot(Base):
    """
    Phase 8: Historical snapshots of user baselines for trend analysis.

    Purpose:
    - Track baseline evolution over time
    - Enable "how am I evolving?" insights
    - Compare consecutive snapshots to show progress/regression
    - Completely user-scoped and optional

    Design:
    - One snapshot created each time user regenerates baseline
    - No automatic creation - user must explicitly regenerate
    - No deletion - preserves full history
    - Used only for analytics, not for comparison logic

    This is NOT:
    - Team analytics (Phase 9)
    - Forecasting or prediction
    - ML training data
    """
    __tablename__ = "user_baseline_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Snapshot of RASNA averages at this point in time
    # Structure: {"rapport": 8.5, "ask": 9.0, "situation": 7.8, "next_steps": 8.2, "articulation": 8.8}
    rasna_averages = Column(JSON, nullable=False)

    # Snapshot of summary insights at this point in time
    # Structure: {
    #   "common_strengths": ["rapport", "articulation"],
    #   "common_improvement_themes": ["ask"],
    #   "average_overall_score": 8.46
    # }
    summary_json = Column(JSON, nullable=False)

    # Number of baseline calls used to generate this snapshot
    call_count = Column(Integer, nullable=False)

    # When this snapshot was created (NOT when baseline was last updated)
    # This is the explicit moment user regenerated their baseline
    snapshot_created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
