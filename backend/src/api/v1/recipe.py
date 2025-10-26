from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.domains.recipe.use_cases import get_recipe_usecase
from src.schemas.recipe import RecipeRead, SearchResponse

router = APIRouter(
    prefix="/recipe",
    tags=["recipe"],
)

@router.get("/{recipe_id}", response_model=RecipeRead)
async def get_recipe(
    recipe_id: UUID,
    db: AsyncSession = Depends(get_db),
    helper = Depends(get_recipe_usecase)
):
    """Get a recipe by ID."""
    recipe = await helper.get_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    return recipe


@router.get("/search", response_model=SearchResponse)
async def search_recipes(
    q: str = Query(..., min_length=1, max_length=100),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    helper = Depends(get_recipe_usecase)
):
    """Search recipes by title or ingredients with pagination."""
    result = await helper.search_recipes(db, q, page, size)
    return SearchResponse(recipes=cast("list[RecipeRead]", result["recipes"]), total=result["total"])
