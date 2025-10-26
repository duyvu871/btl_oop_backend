import asyncio
import os
import sys
from pathlib import Path
import ijson
import json
from tqdm.asyncio import tqdm
# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database.database import AsyncSessionLocal
from src.core.database.models import Ingredient, Recipe, Step

from typing import List, Optional
from pydantic import BaseModel, HttpUrl

class IngredientRaw(BaseModel):
    name: str
    quantitative: Optional[str]
    unit: Optional[str]

class TutorialStepRaw(BaseModel):
    index: int
    title: Optional[str]
    content: Optional[str]
    box_gallery: Optional[List[HttpUrl]]

class DishRaw(BaseModel):
    link: HttpUrl
    title: str
    thumbnail: Optional[HttpUrl]
    ingredient_markdown: Optional[str]
    step_markdown: Optional[str]
    ingredient_title: Optional[str]
    tutorial: Optional[str]
    quantitative: Optional[str]
    ingredients: Optional[List[IngredientRaw]]
    tutorial_step: Optional[List[TutorialStepRaw]]

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
                        print(dish.title)
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
    print(f"\nProcessing complete!")
    print(f"Total dishes: {total_items}")
    print(f"Successfully inserted: {success_count}")
    print(f"Failed: {failed_count}")

async def main():
    await process_file("resources/recipesDB.recipes.json")

if __name__ == "__main__":
    asyncio.run(main())
