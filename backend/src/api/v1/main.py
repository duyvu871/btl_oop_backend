from fastapi import APIRouter

from src.api.v1.admin import router as admin_router
from src.api.v1.auth import router as auth_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(admin_router)


# if settings.ENVIRONMENT == "local":
#     api_router.include_router(private.router)
