from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.core.database.database import AsyncSessionLocal
from src.core.database.models import Recipe

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/recommend")
async def recommend(text: str):
    """
    Mock recommend endpoint that returns recipes with joined ingredients and steps.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Recipe)
            .options(joinedload(Recipe.ingredients), joinedload(Recipe.tutorial_steps))
            .limit(5)
        )
        recipes = result.unique().scalars().all()

    # Convert to dict format
    recipes_data = []
    for recipe in recipes:
        recipe_dict = {
            "id": recipe.id,
            "link": recipe.link,
            "title": recipe.title,
            "thumbnail": recipe.thumbnail,
            "tutorial": recipe.tutorial,
            "quantitative": recipe.quantitative,
            "ingredientTitle": recipe.ingredientTitle,
            "ingredientMarkdown": recipe.ingredientMarkdown,
            "stepMarkdown": recipe.stepMarkdown,
            "created_at": recipe.created_at.isoformat() if recipe.created_at else None,
            "updated_at": recipe.updated_at.isoformat() if recipe.updated_at else None,
            "ingredients": [
                {
                    "id": ing.id,
                    "name": ing.name,
                    "quantity": ing.quantity,
                    "unit": ing.unit,
                }
                for ing in recipe.ingredients
            ],
            "tutorial_steps": [
                {
                    "id": step.id,
                    "index": step.index,
                    "title": step.title,
                    "content": step.content,
                    "box_gallery": step.box_gallery,
                }
                for step in recipe.tutorial_steps
            ],
        }
        recipes_data.append(recipe_dict)

    return {
        "message": f"Mock recommendations for text: '{text}'",
        "recipes": recipes_data,
    }
