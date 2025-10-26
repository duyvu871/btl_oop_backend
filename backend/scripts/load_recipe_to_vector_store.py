import asyncio
import sys
import uuid
from pathlib import Path

from langchain_core.documents import Document

# from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from sentence_transformers import SentenceTransformer
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters.markdown import MarkdownHeaderTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

# from pydantic import SecretStr
from tqdm.asyncio import tqdm

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import func, select

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

        # Initialize splitter, embedding model, and Qdrant client once
        splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[
            ("#", "recipe_name"),
            ("##", "type"),
        ])
        # Initialize embedding model
        embedding_model = HuggingFaceEmbeddings(
            model_name="keepitreal/vietnamese-sbert",
            model_kwargs={"device": "cpu"},
            encode_kwargs={'normalize_embeddings': False}
        )
        # Initialize Qdrant client
        qdrant_client = QdrantClient(url=settings.QDRANT_URL)

        # Ensure collection exists
        collection_exist = qdrant_client.collection_exists(settings.QDRANT_RECIPE_COLLECTION)
        if not collection_exist:
            vector_size = 768
            qdrant_client.create_collection(
                collection_name=settings.QDRANT_RECIPE_COLLECTION,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
        else:
            qdrant_client.delete_collection(collection_name=settings.QDRANT_RECIPE_COLLECTION)
            vector_size = 768
            qdrant_client.create_collection(
                collection_name=settings.QDRANT_RECIPE_COLLECTION,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )

        # Initialize Qdrant vector store
        vector_store = QdrantVectorStore(
            client=qdrant_client,
            collection_name=settings.QDRANT_RECIPE_COLLECTION,
            embedding=embedding_model
        )

        # Collect all chunks
        all_chunks = []
        all_ids = []

        # Progress bar
        pbar = tqdm(total=total_count, desc="Processing recipes", unit="recipe")

        # Process each recipe
        for recipe in all_recipes:
            try:
                # Prepare document content
                content = f"## Tên món {recipe.title}\n\n"
                content += f"## Nguyên Liệu \n\n{recipe.ingredientMarkdown}"
                content += f"## Cách làm \n\n {recipe.stepMarkdown}"

                # Create Document
                document = Document(
                    page_content=content,
                    metadata={
                        "title": recipe.title,
                        "id": recipe.id,
                        "source": settings.QDRANT_RECIPE_COLLECTION,
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

        # Add all documents to vector store in batches
        batch_size_vector = 500
        num_batches = (len(all_chunks) + batch_size_vector - 1) // batch_size_vector
        add_pbar = tqdm(total=num_batches, desc="Adding to vector store", unit="batch")
        for i in range(0, len(all_chunks), batch_size_vector):
            batch_chunks = all_chunks[i:i + batch_size_vector]
            batch_ids = all_ids[i:i + batch_size_vector]
            await vector_store.aadd_documents(
                documents=batch_chunks,
                ids=batch_ids
            )
            add_pbar.update(1)
        add_pbar.close()

if __name__ == "__main__":
    asyncio.run(main())
