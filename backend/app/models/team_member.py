from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from datetime import datetime
from app.core.database import Base


class TeamMember(Base):
    """
    Phase 9: Junction table for team membership with roles.

    Purpose:
    - Track which users belong to which teams
    - Enforce role-based permissions (owner, manager, member)
    - No auto-enrollment (explicit invite/accept required)

    Roles:
    - "owner": Created the team, full permissions
    - "manager": Can view team aggregates, generate team baselines
    - "member": Can only view personal data (no team aggregates)

    Privacy:
    - Members cannot see other members' individual call data
    - Team baselines show ONLY aggregated averages
    - No cross-user raw call access
    """
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String, nullable=False)  # "owner", "manager", "member"
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Ensure user can only be in a team once
    __table_args__ = (
        UniqueConstraint("team_id", "user_id", name="uq_team_user"),
    )
