"""
Helper class for recipe use cases.
Provides convenient wrappers around use cases.
"""


from .get_recipe_by_id import GetRecipeByIdUseCase
from .search_recipes import SearchRecipesUseCase


class RecipeUseCase:
    """
    Helper class that wraps recipe use cases.
    Designed to be used with FastAPI dependency injection.

    Example:
        @app.get("/recipe/{recipe_id}")
        async def get_recipe(
            recipe_id: UUID,
            helper: RecipeUseCase = Depends(get_recipe_usecase)
        ):
            recipe = await helper.get_recipe(db, recipe_id)
    """

    def __init__(self):
        pass

    async def get_recipe(self, db, recipe_id):
        """
        Get a recipe by ID.

        Args:
            db: Database session
            recipe_id: Recipe UUID

        Returns:
            Recipe object or None
        """
        use_case = GetRecipeByIdUseCase()
        return await use_case.execute(db, recipe_id)

    async def search_recipes(self, db, q, page, size):
        """
        Search recipes by query with pagination.

        Args:
            db: Database session
            q: Search query
            page: Page number
            size: Items per page

        Returns:
            Dict with recipes and total
        """
        use_case = SearchRecipesUseCase()
        return await use_case.execute(db, q, page, size)


def get_recipe_usecase():
    """
    Dependency injection for RecipeUseCase.
    """
    return RecipeUseCase()
