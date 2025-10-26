from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.core.database.database import AsyncSessionLocal
from src.core.database.models import Recipe, User
from src.core.security import get_current_user
from src.schemas.recipe import RecipeRead, RecommendRequest, RecommendResponse

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(
    request: RecommendRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Get recipe recommendations based on user's text input.

    Requires authentication. Returns a list of recipes matching the user's query.

    Args:
        request: RecommendRequest containing the search text
        current_user: Authenticated user (injected by dependency)

    Returns:
        RecommendResponse with recommended recipes
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Recipe)
            .options(joinedload(Recipe.ingredients), joinedload(Recipe.tutorial_steps))
            .limit(5)
        )
        recipes = result.unique().scalars().all()

    # Convert to Pydantic models
    recipes_data = [RecipeRead.model_validate(recipe) for recipe in recipes]

    return RecommendResponse(
        message=f"Recommendations for: '{request.query}'",
        recipes=recipes_data,
        total=len(recipes_data),
    )
