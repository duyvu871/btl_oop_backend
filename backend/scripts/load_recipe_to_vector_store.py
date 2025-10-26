import asyncio
import sys
from asyncio import sleep
from pathlib import Path

from tqdm.asyncio import tqdm

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from src.core.database.database import AsyncSessionLocal
from src.core.database.models import Recipe


async def process_recipe(recipe: Recipe):
    """
    Placeholder function to process a single recipe.
    Currently just prints the recipe title.
    TODO: Implement embedding generation and Qdrant insertion.
    """
    await sleep(0.001)  # Simulate some processing time
    # print(f"Processing recipe: {recipe.title} (ID: {recipe.id})")


async def main():
    """
    Fetch all recipes from the database and process each one.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Recipe))
        recipes = result.scalars().all()

        print(f"Found {len(recipes)} recipes in the database.")
        pbar = tqdm(total=len(recipes), desc="Processing recipes", unit="recipe")
        for recipe in recipes:
            await process_recipe(recipe)
            pbar.update(1)
        pbar.close()


if __name__ == "__main__":
    asyncio.run(main())
