"""
Use case for searching recipes.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.database.models import Recipe


class SearchRecipesUseCase:
    """
    Use case for searching recipes by title or ingredients with pagination.
    """

    async def execute(self, db: AsyncSession, q: str, page: int, size: int):
        """
        Execute the use case.

        Args:
            db: Database session
            q: Search query
            page: Page number
            size: Items per page

        Returns:
            Dict with 'recipes' and 'total'
        """
        where_clause = Recipe.title.ilike(f"%{q}%") | Recipe.ingredientMarkdown.ilike(f"%{q}%")

        # Get total count
        total_stmt = select(func.count(Recipe.id)).where(where_clause)
        total_result = await db.execute(total_stmt)
        total = total_result.scalar()

        # Get paginated results
        offset = (page - 1) * size
        stmt = (
            select(Recipe)
            .where(where_clause)
            .options(selectinload(Recipe.ingredients), selectinload(Recipe.tutorial_steps))
            .offset(offset)
            .limit(size)
        )
        result = await db.execute(stmt)
        recipes = result.scalars().all()

        return {"recipes": recipes, "total": total}
