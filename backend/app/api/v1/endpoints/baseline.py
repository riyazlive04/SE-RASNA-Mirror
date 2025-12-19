from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_database, get_current_user
from app.models.user import User
from app.services.baseline import BaselineService
from app.services.baseline_trends import BaselineTrendService

router = APIRouter()


@router.post("/generate", status_code=status.HTTP_200_OK)
async def generate_baseline(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Generate or regenerate personal baseline from user's best calls.

    Phase 7: Creates aggregated intelligence from calls marked as "Best Call".

    Prerequisites:
    - At least 1 call marked as is_baseline=True
    - All baseline calls must have completed evaluations

    Returns:
    - Generated baseline data with RASNA averages and insights

    User isolation: Only generates baseline from current user's calls
    """
    baseline_service = BaselineService(db)

    try:
        baseline = baseline_service.generate_baseline_for_user(current_user.id)
        return baseline
    except ValueError as e:
        # Prerequisites not met (e.g., no baseline calls, incomplete evaluations)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate baseline: {str(e)}"
        )


@router.get("/", status_code=status.HTTP_200_OK)
async def get_baseline(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Get current user's personal baseline.

    Returns existing baseline or 404 if not yet generated.

    User isolation: Only returns current user's baseline
    """
    baseline_service = BaselineService(db)

    baseline = baseline_service.get_baseline_for_user(current_user.id)

    if not baseline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Baseline not found. Generate your baseline first by marking calls as 'Best Call' and clicking 'Generate My Baseline'."
        )

    return baseline


@router.get("/trends", status_code=status.HTTP_200_OK)
async def get_baseline_trends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Phase 8: Get baseline evolution trends for current user.

    Compares last two baseline snapshots to show:
    - Which RASNA dimensions improved
    - Which dimensions declined
    - Which dimensions stayed stable
    - Delta values per dimension

    Returns 204 No Content if user has <2 snapshots.
    Requires user to have regenerated baseline at least twice.

    User isolation: Only returns current user's trends
    No side effects: Pure GET operation, no data mutation
    """
    trend_service = BaselineTrendService(db)

    trend = trend_service.get_trend_for_user(current_user.id)

    if not trend:
        # Graceful degradation: <2 snapshots available
        # HTTP 204 No Content = success but no data available yet
        # No response body per HTTP semantics
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return trend
