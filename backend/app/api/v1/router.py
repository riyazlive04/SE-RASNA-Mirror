from fastapi import APIRouter

from app.api.v1.endpoints import calls, auth, baseline, teams, coaching

api_router = APIRouter()

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"]
)

api_router.include_router(
    calls.router,
    prefix="/calls",
    tags=["calls"]
)

api_router.include_router(
    baseline.router,
    prefix="/baseline",
    tags=["baseline"]
)

# Phase 9: Team/agency intelligence endpoints
api_router.include_router(
    teams.router,
    prefix="/teams",
    tags=["teams"]
)

# Phase 10: Coaching playbooks endpoints
api_router.include_router(
    coaching.router,
    prefix="/coaching",
    tags=["coaching"]
)
