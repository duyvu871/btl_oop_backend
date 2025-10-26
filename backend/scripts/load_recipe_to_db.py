import asyncio
import gzip
import os
import sys
import tempfile
from pathlib import Path

import httpx
import ijson
from tqdm.asyncio import tqdm

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))


from pydantic import BaseModel, HttpUrl

from src.core.database.database import AsyncSessionLocal
from src.core.database.models import Ingredient, Recipe, Step


class IngredientRaw(BaseModel):
    name: str
    quantitative: str | None
    unit: str | None


class TutorialStepRaw(BaseModel):
    index: int
    title: str | None
    content: str | None
    box_gallery: list[HttpUrl] | None


class DishRaw(BaseModel):
    link: HttpUrl
    title: str
    thumbnail: HttpUrl | None
    ingredient_markdown: str | None
    step_markdown: str | None
    ingredient_title: str | None
    tutorial: str | None
    quantitative: str | None
    ingredients: list[IngredientRaw] | None
    tutorial_step: list[TutorialStepRaw] | None


def count_items_in_json(path: str) -> int:
    count = 0
    with open(path, "rb") as f:
        for _ in ijson.items(f, "item"):
            count += 1
    return count


# process file json
async def process_file(path: str):
    total_items = count_items_in_json(path)
    success_count = 0
    failed_count = 0
    async with AsyncSessionLocal() as session:
        async with session.begin():
            with open(path, "rb") as f:
                pbar = tqdm(total=total_items, desc="Processing dishes", unit="dish")
                for obj in ijson.items(f, "item"):
                    try:
                        dish = DishRaw.model_validate(obj)
                        # Insert recipe
                        recipe = Recipe(
                            link=str(dish.link),
                            title=dish.title,
                            thumbnail=str(dish.thumbnail) if dish.thumbnail else None,
                            tutorial=dish.tutorial or "",
                            quantitative=dish.quantitative or "",
                            ingredientTitle=dish.ingredient_title or "",
                            ingredientMarkdown=dish.ingredient_markdown or "",
                            stepMarkdown=dish.step_markdown or "",
                        )
                        session.add(recipe)
                        await session.flush()  # Get the recipe ID

                        # Insert ingredients
                        for ing in dish.ingredients or []:
                            ingredient = Ingredient(
                                recipe_id=recipe.id,
                                name=ing.name,
                                quantity=ing.quantitative or "",
                                unit=ing.unit or "",
                            )
                            session.add(ingredient)

                        # Insert steps
                        for step in dish.tutorial_step or []:
                            step_obj = Step(
                                recipe_id=recipe.id,
                                index=step.index,
                                title=step.title or "",
                                content=step.content or "",
                                box_gallery=[str(url) for url in step.box_gallery or []],
                            )
                            session.add(step_obj)
                        success_count += 1
                    except Exception as e:
                        print("Validation or DB insert error:", e, "→ skipping dish", obj.get("title"))
                        failed_count += 1
                    pbar.update(1)
                pbar.close()
            await session.commit()  # Explicit commit for the entire batch
    print("\nProcessing complete!")
    print(f"Total dishes: {total_items}")
    print(f"Successfully inserted: {success_count}")
    print(f"Failed: {failed_count}")


async def main():
    resource_url = "https://raw.githubusercontent.com/duyvu871/btl_oop_backend/main/backend/resources/recipes.qz"
    print(f"Downloading and decompressing data from {resource_url}...")
    async with httpx.AsyncClient() as client:
        response = await client.get(resource_url)
        response.raise_for_status()
        compressed_data = response.content

    decompressed_data = gzip.decompress(compressed_data)
    print("Decompression complete. Saving to temporary file...")

    with tempfile.NamedTemporaryFile(mode="wb", suffix=".json", delete=False) as temp_file:
        temp_file.write(decompressed_data)
        temp_path = temp_file.name

    try:
        print(f"Processing file at {temp_path}...")
        await process_file(temp_path)
    finally:
        os.unlink(temp_path)
        print("Temporary file cleaned up.")


if __name__ == "__main__":
    asyncio.run(main())
