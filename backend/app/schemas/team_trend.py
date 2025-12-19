from pydantic import BaseModel, Field
from typing import Dict


class TeamTrend(BaseModel):
    """
    Phase 9: Team baseline evolution trend response schema.

    Shows how team's aggregate performance has evolved between snapshots.
    Only populated if team has at least 2 snapshots.

    ⚠️ Contains ONLY aggregated trend data, NO individual performance.
    """
    improved_dimensions: list[str] = Field(..., description="RASNA dimensions that improved at team level")
    declined_dimensions: list[str] = Field(..., description="RASNA dimensions that declined at team level")
    stable_dimensions: list[str] = Field(..., description="RASNA dimensions that remained stable at team level")
    dimension_deltas: Dict[str, float] = Field(..., description="Score change per dimension (latest - previous)")
    summary: str = Field(..., description="Human-readable team evolution summary")
    snapshots_compared: int = Field(..., description="Number of snapshots compared (always 2)")
    latest_snapshot_date: str = Field(..., description="ISO timestamp of latest snapshot")
    previous_snapshot_date: str = Field(..., description="ISO timestamp of previous snapshot")
    latest_agent_count: int = Field(..., description="Number of team members in latest snapshot")
    previous_agent_count: int = Field(..., description="Number of team members in previous snapshot")

    class Config:
        from_attributes = True
