"""
Use case for getting a recipe by ID.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.database.models import Recipe


class GetRecipeByIdUseCase:
    """
    Use case for retrieving a recipe by its ID.
    """

    async def execute(self, db: AsyncSession, recipe_id: UUID):
        """
        Execute the use case.

        Args:
            db: Database session
            recipe_id: Recipe UUID

        Returns:
            Recipe object or None if not found
        """
        stmt = (
            select(Recipe)
            .where(Recipe.id == recipe_id)
            .options(selectinload(Recipe.ingredients), selectinload(Recipe.tutorial_steps))
        )
        result = await db.execute(stmt)
        recipe = result.scalar_one_or_none()
        return recipe
