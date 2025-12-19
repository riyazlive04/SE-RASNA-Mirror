from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_database, get_current_user
from app.models.user import User
from app.services.team import TeamService
from app.services.team_baseline import TeamBaselineService
from app.services.team_trends import TeamTrendService
from app.schemas.team import TeamCreate, Team, TeamMemberAdd, TeamMember, TeamBaseline
from app.schemas.team_trend import TeamTrend

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Phase 9: Create a new team.

    Creator automatically becomes owner.
    No other members added until explicitly invited.

    User isolation: Team is owned by current user
    """
    team_service = TeamService(db)

    try:
        team = team_service.create_team(team_data.name, current_user.id)
        return team
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create team: {str(e)}"
        )


@router.get("/", status_code=status.HTTP_200_OK)
async def get_user_teams(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Phase 9: Get all teams current user is a member of.

    Returns teams with user's role in each.
    User isolation: Only returns teams user belongs to
    """
    team_service = TeamService(db)
    teams = team_service.get_user_teams(current_user.id)
    return {"teams": teams}


@router.post("/{team_id}/members", status_code=status.HTTP_201_CREATED)
async def add_team_member(
    team_id: int,
    member_data: TeamMemberAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Phase 9: Add a member to a team.

    Only owners and managers can invite members.
    Role must be "manager" or "member" (owner role cannot be assigned).

    Permission: Owner or Manager only
    """
    team_service = TeamService(db)

    try:
        member = team_service.add_member(
            team_id=team_id,
            user_id=member_data.user_id,
            role=member_data.role,
            inviter_user_id=current_user.id
        )
        return member
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add team member: {str(e)}"
        )


@router.get("/{team_id}/members", status_code=status.HTTP_200_OK)
async def get_team_members(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Phase 9: Get all members of a team.

    Requester must be a member of the team.
    Returns member list with roles but NO personal performance data.

    Permission: Any team member
    """
    team_service = TeamService(db)

    try:
        members = team_service.get_team_members(team_id, current_user.id)
        return {"members": members}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch team members: {str(e)}"
        )


@router.post("/{team_id}/baseline/generate", status_code=status.HTTP_200_OK)
async def generate_team_baseline(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Phase 9: Generate team baseline from aggregated evaluations.

    Computes team-wide averaged RASNA scores.
    NO individual scores exposed.
    Explicit action only - no automatic generation.

    Permission: Owner or Manager only
    """
    team_service = TeamService(db)
    baseline_service = TeamBaselineService(db)

    # Check permission
    if not team_service.can_manage_team(team_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners and managers can generate team baselines"
        )

    try:
        baseline = baseline_service.generate_team_baseline(team_id)
        return baseline
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate team baseline: {str(e)}"
        )


@router.get("/{team_id}/baseline", status_code=status.HTTP_200_OK)
async def get_team_baseline(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Phase 9: Get latest team baseline.

    Returns aggregated team RASNA averages.
    NO individual scores exposed.

    Permission: Owner or Manager only
    """
    team_service = TeamService(db)
    baseline_service = TeamBaselineService(db)

    # Check permission
    if not team_service.can_view_team_aggregates(team_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners and managers can view team baselines. Members can only view their personal data."
        )

    baseline = baseline_service.get_latest_team_baseline(team_id)

    if not baseline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team baseline not found. Generate team baseline first."
        )

    return baseline


@router.get("/{team_id}/trends", status_code=status.HTTP_200_OK)
async def get_team_trends(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Phase 9: Get team baseline evolution trends.

    Compares last two team baseline snapshots to show:
    - Which RASNA dimensions improved at team level
    - Which dimensions declined
    - Which dimensions stayed stable
    - Delta values per dimension

    Returns 204 No Content if team has <2 snapshots.
    Requires team to have generated baseline at least twice.

    Permission: Owner or Manager only
    No side effects: Pure GET operation, no data mutation
    """
    team_service = TeamService(db)
    trend_service = TeamTrendService(db)

    # Check permission
    if not team_service.can_view_team_aggregates(team_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners and managers can view team trends. Members can only view their personal data."
        )

    trend = trend_service.get_team_trend(team_id)

    if not trend:
        # Graceful degradation: <2 snapshots available
        # HTTP 204 No Content = success but no data available yet
        # No response body per HTTP semantics
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return trend
