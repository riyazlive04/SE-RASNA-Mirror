from pydantic import BaseModel, Field
from typing import Dict


# Phase 9: Team creation request
class TeamCreate(BaseModel):
    name: str = Field(..., description="Team name", min_length=1, max_length=100)


# Phase 9: Team response
class Team(BaseModel):
    id: int
    name: str
    created_by: int
    created_at: str
    role: str  # User's role in this team ("owner", "manager", "member")

    class Config:
        from_attributes = True


# Phase 9: Add member request
class TeamMemberAdd(BaseModel):
    user_id: int = Field(..., description="User ID to add to team")
    role: str = Field(..., description="Role: 'manager' or 'member'")


# Phase 9: Team member response
class TeamMember(BaseModel):
    user_id: int
    name: str
    email: str
    role: str
    joined_at: str

    class Config:
        from_attributes = True


# Phase 9: Team baseline response (aggregated data only)
class TeamBaseline(BaseModel):
    """
    Phase 9: Team baseline response schema.

    ⚠️ Contains ONLY aggregated averages, NO individual scores.
    """
    team_id: int
    aggregated_rasna_averages: Dict[str, float] = Field(
        ...,
        description="Averaged RASNA scores across team (NO individual scores exposed)"
    )
    agent_count: int = Field(..., description="Number of team members included in aggregation")
    snapshot_created_at: str = Field(..., description="ISO timestamp of snapshot creation")

    class Config:
        from_attributes = True
