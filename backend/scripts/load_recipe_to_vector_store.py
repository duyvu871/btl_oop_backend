import asyncio
import sys
from asyncio import sleep
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters.markdown import MarkdownHeaderTextSplitter
from tqdm.asyncio import tqdm
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from src.core.database.database import AsyncSessionLocal
from src.core.database.models import Recipe
from src.settings.env import settings

async def process_recipe(recipe: Recipe):
    """
    Placeholder function to process a single recipe.
    Currently just prints the recipe title.
    TODO: Implement embedding generation and Qdrant insertion.
    """
    content = str(recipe.title)
    content += recipe.ingredientMarkdown
    content += recipe.stepMarkdown

    document = Document(
        page_content=content,
        metadata={
            "title": recipe.title,
            "id": recipe.id,
            "source": settings.QDRANT_RECIPE_COLLECTION,
        }
    )

    headers_to_split_on = [
        ("#", "recipe_name"),
        ("##", "type"),
    ]

    splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)

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
