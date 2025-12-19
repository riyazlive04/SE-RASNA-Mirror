from pydantic import BaseModel, Field
from typing import Literal


class CoachingPlaybook(BaseModel):
    """
    Phase 10: Base coaching playbook schema.

    Coaching playbooks translate baseline and trend data into
    actionable improvement suggestions.

    This is NOT:
    - Performance evaluation or ranking
    - Mandatory training requirements
    - Surveillance or monitoring
    """
    focus_areas: list[str] = Field(
        ...,
        description="RASNA dimensions to focus on improving"
    )
    strengths_to_preserve: list[str] = Field(
        ...,
        description="RASNA dimensions that are strengths (maintain current practices)"
    )
    suggested_actions: list[str] = Field(
        ...,
        description="Specific, actionable coaching suggestions"
    )
    tone: Literal["supportive"] = Field(
        ...,
        description="Tone of suggestions (always 'supportive')"
    )
    confidence: Literal["high", "medium", "low"] = Field(
        ...,
        description="Confidence level based on data quality"
    )
    disclaimer: str = Field(
        ...,
        description="Reminder that suggestions are advisory, not evaluative"
    )
    generated_from: Literal["baseline", "trends", "both"] = Field(
        ...,
        description="Data sources used to generate playbook"
    )

    class Config:
        from_attributes = True


class PersonalCoachingPlaybook(CoachingPlaybook):
    """
    Phase 10: Personal coaching playbook schema.

    Generated from user's own baseline and trend data.
    Privacy: Uses ONLY the user's own performance data.
    """
    baseline_status: Literal["current", "stale"] = Field(
        ...,
        description="Whether baseline is current or stale (needs regeneration)"
    )
    last_updated_context: str = Field(
        ...,
        description="ISO timestamp of baseline last update (context for suggestions)"
    )

    class Config:
        from_attributes = True


class TeamCoachingPlaybook(CoachingPlaybook):
    """
    Phase 10: Team coaching playbook schema.

    Generated from aggregated team baseline and trend data.
    Privacy: Uses ONLY aggregated team data (no individual exposure).

    Access control:
    - Team owners and managers can view
    - Team members CANNOT view (prevents comparison/ranking)
    """
    agent_count: int = Field(
        ...,
        description="Number of agents in team (for context)"
    )
    last_updated_context: str = Field(
        ...,
        description="ISO timestamp of team baseline last update"
    )

    class Config:
        from_attributes = True
