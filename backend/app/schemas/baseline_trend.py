from pydantic import BaseModel, Field
from typing import Dict


class BaselineTrend(BaseModel):
    """
    Phase 8: Baseline evolution trend response schema.

    Shows how user's baseline has evolved between snapshots.
    Only populated if user has at least 2 snapshots.
    """
    improved_dimensions: list[str] = Field(..., description="RASNA dimensions that improved")
    declined_dimensions: list[str] = Field(..., description="RASNA dimensions that declined")
    stable_dimensions: list[str] = Field(..., description="RASNA dimensions that remained stable")
    dimension_deltas: Dict[str, float] = Field(..., description="Score change per dimension (latest - previous)")
    summary: str = Field(..., description="Human-readable evolution summary")
    snapshots_compared: int = Field(..., description="Number of snapshots compared (always 2)")
    latest_snapshot_date: str = Field(..., description="ISO timestamp of latest snapshot")
    previous_snapshot_date: str = Field(..., description="ISO timestamp of previous snapshot")
    latest_call_count: int = Field(..., description="Number of baseline calls in latest snapshot")
    previous_call_count: int = Field(..., description="Number of baseline calls in previous snapshot")

    class Config:
        from_attributes = True
