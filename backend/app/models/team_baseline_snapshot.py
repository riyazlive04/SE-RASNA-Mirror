from sqlalchemy import Column, Integer, JSON, DateTime, ForeignKey
from datetime import datetime
from app.core.database import Base


class TeamBaselineSnapshot(Base):
    """
    Phase 9: Aggregated team baseline snapshots for trend analysis.

    ⚠️ CRITICAL: This table contains ONLY aggregated data.
    - NO individual call data
    - NO personal scores
    - NO cross-user raw data exposure

    Purpose:
    - Track team-level performance evolution over time
    - Enable "how is the team improving?" insights
    - Compare consecutive team snapshots (similar to Phase 8 personal trends)

    Design:
    - Created ONLY when manager explicitly generates team baseline
    - Aggregates data from team members who have completed evaluations
    - Stores averaged RASNA scores across team
    - Immutable (no updates after creation)

    Privacy Guarantees:
    - Individual agent scores are NEVER stored here
    - Only team-wide averages are computed
    - Members cannot reverse-engineer individual performance
    - Team trends show aggregate deltas only
    """
    __tablename__ = "team_baseline_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)

    # Aggregated RASNA averages (team-wide)
    # Example: {"rapport": 7.8, "ask": 8.2, "situation": 7.5, ...}
    aggregated_rasna_averages = Column(JSON, nullable=False)

    # Number of team members included in this snapshot
    agent_count = Column(Integer, nullable=False)

    # When this snapshot was created (explicit action by manager)
    snapshot_created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
