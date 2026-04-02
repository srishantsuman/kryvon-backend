from fastapi import APIRouter
from app.api.v1.endpoints import auth, trades, dashboard, analytics

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(trades.router)
api_router.include_router(dashboard.router)
api_router.include_router(analytics.router)
