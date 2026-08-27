from fastapi import APIRouter

from . import auth, education, inventory, journal, profile, routine, scan, twin

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(profile.router)
api_router.include_router(routine.router)
api_router.include_router(scan.router)
api_router.include_router(inventory.router)
api_router.include_router(journal.router)
api_router.include_router(twin.router)
api_router.include_router(twin.experiments_router)
api_router.include_router(education.router)

__all__ = ["api_router"]
