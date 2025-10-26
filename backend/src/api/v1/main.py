from fastapi import APIRouter

from src.api.v1.admin import router as admin_router
from src.api.v1.ai import router as ai_router
from src.api.v1.auth import router as auth_router
from src.api.v1.recipe import router as recipe_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(admin_router)
api_router.include_router(ai_router)
api_router.include_router(recipe_router)


# if settings.ENVIRONMENT == "local":
#     api_router.include_router(private.router)
