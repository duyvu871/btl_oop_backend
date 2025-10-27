import asyncio
import sys
import uuid
from asyncio import sleep
from pathlib import Path

import tiktoken
from langchain_core.documents import Document
from langchain_text_splitters.markdown import MarkdownHeaderTextSplitter
from qdrant_client import QdrantClient
from tqdm.asyncio import tqdm

from src.core.utils.number import extract_number

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import func, select

from src.ai.embeddings.generate_embedding import EmbeddingGenerator
from src.ai.embeddings.qdrant_store import QdrantStore
from src.core.database.database import AsyncSessionLocal
from src.core.database.models import Recipe
from src.settings.env import settings


async def main():
    """
    Fetch all recipes from the database and process each one.
    """
    async with AsyncSessionLocal() as session:
        # Get total count of recipes
        total_recipes = await session.execute(select(func.count(Recipe.id)))
        total_count = total_recipes.scalar()
        print(f"Found {total_count} recipes in the database.")

        batch_size = 200
        all_recipes = []
        offset = 0
        while True:
            result = await session.execute(select(Recipe).offset(offset).limit(batch_size))
            recipes = result.scalars().all()
            if not recipes:
                break
            all_recipes.extend(recipes)
            offset += batch_size

        # Initialize services using the new classes
        embedding_generator = EmbeddingGenerator(model_name="gemini-embedding-001", api_key=settings.GOOGLE_API_KEY)
        qdrant_client = QdrantClient(url=settings.QDRANT_URL)
        qdrant_store = QdrantStore(
            client=qdrant_client,
            collection_name=settings.QDRANT_RECIPE_COLLECTION,
            embedding_model=embedding_generator.embedding_model,
            vector_size=3072,
        )
        qdrant_store.ensure_collection_exists(recreate=True)  # Recreate collection

        # Initialize splitter
        splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[
            ("#", "recipe_name"),
            ("##", "type"),
        ])

        # Collect all chunks
        all_chunks = []
        all_ids = []

        # Progress bar
        pbar = tqdm(total=total_count, desc="Processing recipes", unit="recipe")

        # Process each recipe
        for recipe in all_recipes:
            try:
                # Prepare document content
                content = f"# Tên món: {recipe.title}\n\n"
                content += f"## Nguyên Liệu \n\n{recipe.ingredientMarkdown}\n\n"
                content += f"## Cách làm \n\n{recipe.stepMarkdown}"

                servings_num = extract_number(recipe.quantitative)
                # Create Document
                document = Document(
                    page_content=content,
                    metadata={
                        "title": recipe.title,
                        "id": recipe.id,
                        "source": settings.QDRANT_RECIPE_COLLECTION,
                        "quantitative_text": recipe.quantitative,
                        "servings": servings_num
                    }
                )

                # Split document into chunks
                split_docs = splitter.split_text(document.page_content)
                for split_doc in split_docs:
                    all_chunks.append(
                        Document(
                            page_content=split_doc.page_content,
                            metadata={**split_doc.metadata, **document.metadata},
                        )
                    )
                    all_ids.append(str(uuid.uuid4()))

            except Exception as e:
                print(f"Error processing recipe {recipe.id}: {e}")
                raise e
            pbar.update(1)
        pbar.close()

        # Calculate total tokens
        enc = tiktoken.get_encoding("cl100k_base")
        total_tokens = sum(len(enc.encode(chunk.page_content)) for chunk in all_chunks)
        print(f"Total tokens to embed: {total_tokens}")

        # Add all documents to vector store in batches
        batch_size_vector = 1
        num_batches = (len(all_chunks) + batch_size_vector - 1) // batch_size_vector
        add_pbar = tqdm(total=num_batches, desc="Adding to vector store", unit="batch")
        for i in range(0, len(all_chunks), batch_size_vector):
            batch_chunks = all_chunks[i:i + batch_size_vector]
            batch_ids = all_ids[i:i + batch_size_vector]
            await qdrant_store.add_documents(
                documents=batch_chunks,
                ids=batch_ids
            )
            await sleep(60 / 95) # wait to limit to 95 requests per minute
            add_pbar.update(1)
        add_pbar.close()

if __name__ == "__main__":
    asyncio.run(main())
