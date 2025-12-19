from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_database, get_current_user
from app.models.user import User
from app.services.coaching_playbooks import CoachingPlaybookService
from app.services.team import TeamService
from app.schemas.coaching_playbook import PersonalCoachingPlaybook, TeamCoachingPlaybook

router = APIRouter()


@router.get("/personal", status_code=status.HTTP_200_OK)
async def get_personal_coaching(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Phase 10: Get personal coaching playbook.

    Generates actionable improvement suggestions based on:
    - Personal baseline (strengths, improvement areas)
    - Personal trends (what's improving, what's declining)

    This is NOT:
    - Performance evaluation or ranking
    - Mandatory training requirements
    - Surveillance or monitoring

    Returns structured coaching suggestions:
    - Focus areas (dimensions needing attention)
    - Strengths to preserve (dimensions performing well)
    - Suggested actions (specific, actionable next steps)

    Returns 204 No Content if user has no baseline.
    Requires user to have generated baseline first.

    User isolation: Uses ONLY current user's own data
    No side effects: Pure GET operation, no data mutation
    Read-only: Zero database writes
    """
    coaching_service = CoachingPlaybookService(db)

    playbook = coaching_service.generate_personal_playbook(current_user.id)

    if not playbook:
        # Graceful degradation: No baseline exists yet
        # HTTP 204 No Content = success but no data available yet
        # No response body per HTTP semantics
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return playbook


@router.get("/teams/{team_id}", status_code=status.HTTP_200_OK)
async def get_team_coaching(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Phase 10: Get team coaching playbook.

    Generates team-level improvement suggestions based on:
    - Team baseline (aggregated averages)
    - Team trends (team-level evolution)

    This is NOT:
    - Individual performance tracking
    - Personal coaching (that's GET /coaching/personal)
    - Ranking or surveillance

    Privacy:
    - Uses ONLY aggregated team data
    - NO individual performance exposure
    - NO reverse-engineering of individual scores

    Returns structured team coaching suggestions:
    - Team focus areas (dimensions below team average)
    - Team strengths (dimensions performing well collectively)
    - Suggested team actions (practices to adopt)

    Returns 204 No Content if team has no baseline.
    Requires team owner/manager to have generated team baseline first.

    Permission: Owner or Manager only
    - Members CANNOT view team playbooks (prevents comparison/ranking)

    User isolation: Only team owners/managers can access
    No side effects: Pure GET operation, no data mutation
    Read-only: Zero database writes
    """
    team_service = TeamService(db)
    coaching_service = CoachingPlaybookService(db)

    # Phase 10: Enforce access control
    # Team playbooks are owner/manager-only to prevent:
    # - Members comparing themselves to aggregates
    # - Perception of surveillance or ranking
    # - Reverse-engineering of individual scores (small teams)
    if not team_service.can_view_team_aggregates(team_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Only team owners and managers can view team coaching playbooks. "
                "Members can view their personal coaching at GET /coaching/personal."
            )
        )

    playbook = coaching_service.generate_team_playbook(team_id)

    if not playbook:
        # Graceful degradation: No team baseline exists yet
        # HTTP 204 No Content = success but no data available yet
        # No response body per HTTP semantics
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return playbook
