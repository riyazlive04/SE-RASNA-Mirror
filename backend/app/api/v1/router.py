from fastapi import APIRouter

from app.api.v1.endpoints import calls, auth, baseline

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
