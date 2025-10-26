import asyncio
import sys
import uuid
from asyncio import sleep
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters.markdown import MarkdownHeaderTextSplitter
# from pydantic import SecretStr
from tqdm.asyncio import tqdm
# from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from sentence_transformers import SentenceTransformer
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from src.core.database.database import AsyncSessionLocal
from src.core.database.models import Recipe
from src.settings.env import settings


async def main():
    """
    Fetch all recipes from the database and process each one.
    """
    async with AsyncSessionLocal() as session:
        batch_size = 200
        offset = 0
        result = await session.execute(select(Recipe).offset(offset).limit(batch_size))
        recipes = result.scalars().all()

        print(f"Found {len(recipes)} recipes in the database.")

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
        # Progress bar
        pbar = tqdm(total=len(recipes), desc="Processing recipes", unit="recipe")

        # Process each recipe
        for recipe in recipes:
            # Process each recipe
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

                chunks = []
                # Split document into chunks
                split_docs = splitter.split_text(document.page_content)
                for split_doc in split_docs:
                    chunks.append(
                        Document(
                            page_content=split_doc.page_content,
                            metadata={**split_doc.metadata, **document.metadata},
                        )
                    )
                # Generate unique IDs for each chunk
                chunks_ids = [str(uuid.uuid4()) for _ in range(len(chunks))]
                # Add documents to vector store
                await vector_store.aadd_documents(
                    documents=chunks,
                    ids=chunks_ids
                )

                await sleep(0.001)

            except Exception as e:
                print(f"Error processing recipe {recipe.id}: {e}")
                raise e
            # Process each recipe
            pbar.update(1)
        pbar.close()

if __name__ == "__main__":
    asyncio.run(main())
