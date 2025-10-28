import asyncio
import sys
import uuid
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters.markdown import MarkdownHeaderTextSplitter
from qdrant_client import QdrantClient
from tqdm.asyncio import tqdm

from src.core.utils.number import extract_number

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import func, select

from src.ai.embeddings.generate_embedding import APIEmbeddingGenerator
from src.ai.embeddings.qdrant_store import QdrantStore
from src.ai.embeddings.rate_limiter import BatchRateLimiter
from src.ai.embeddings.token_calculator import TokenCalculator
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

        batch_size = 10
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
        embedding_generator = APIEmbeddingGenerator(
            model_name=settings.EMBEDDING_MODEL,
            base_url="http://192.168.1.124:8000",
            api_key=settings.GOOGLE_API_KEY,
        )
        qdrant_client = QdrantClient(url=settings.QDRANT_URL)
        qdrant_store = QdrantStore(
            client=qdrant_client,
            collection_name=settings.QDRANT_RECIPE_COLLECTION,
            embedding_model=embedding_generator,
            vector_size=768,
        )
        qdrant_store.ensure_collection_exists(recreate=True)  # Recreate collection

        # Initialize rate limiter for 95 requests per minute
        rate_limiter = BatchRateLimiter(max_requests_per_minute=50)
        print(f"\n⚙️  Rate limiter configured: {rate_limiter.max_requests_per_minute} RPM")

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

        # Calculate total tokens and cost using TokenCalculator
        print("\n" + "=" * 70)
        print("📊 TOKEN & COST ANALYSIS")
        print("=" * 70)

        model_name = "embed-v4.0"  # Change to match your embedding model
        token_calculator = TokenCalculator(model_name=model_name)

        # Get all page contents for token calculation
        all_contents = [chunk.page_content for chunk in all_chunks]
        summary = token_calculator.get_summary(all_contents)

        print(f"Model: {summary['model_name']}")
        print(f"Number of chunks: {summary['num_texts']:,}")
        print(f"Total tokens: {summary['total_tokens']:,}")
        print(f"Average tokens per chunk: {summary['avg_tokens_per_text']:.2f}")
        print(f"Estimated cost: ${summary['estimated_cost_usd']:.4f}")
        print("=" * 70 + "\n")

        # Calculate optimal batch size and processing time
        batch_size_vector = 1  # Items per batch
        num_batches = (len(all_chunks) + batch_size_vector - 1) // batch_size_vector

        # Get processing estimate
        estimate = rate_limiter.get_processing_estimate(num_batches)
        print("=" * 70)
        print("⏱️  PROCESSING TIME ESTIMATE")
        print("=" * 70)
        print(f"Total chunks: {len(all_chunks):,}")
        print(f"Batch size: {batch_size_vector}")
        print(f"Total batches: {estimate.total_batches}")
        print(f"Max RPM: {estimate.max_requests_per_minute}")
        print(f"Estimated time: {estimate.estimated_minutes:.2f} minutes ({estimate.estimated_seconds:.2f} seconds)")
        print("=" * 70 + "\n")

        # Add all documents to vector store in batches with rate limiting
        print("🚀 Starting batch processing with rate limiting...")
        add_pbar = tqdm(total=num_batches, desc="Adding to vector store", unit="batch")

        for i in range(0, len(all_chunks), batch_size_vector):
            # Wait for rate limiter before making request (controls RPM)
            await rate_limiter.acquire()

            batch_chunks = all_chunks[i:i + batch_size_vector]
            batch_ids = all_ids[i:i + batch_size_vector]
            embedded_vectors = await embedding_generator.aembed_documents(
                [doc.page_content for doc in batch_chunks]
            )
            await qdrant_store.add_documents_with_embeddings(
                documents=batch_chunks,
                embeddings=embedded_vectors,
                ids=batch_ids
            )

            add_pbar.update(1)

            # Show stats every 10 batches
            if (i // batch_size_vector + 1) % 10 == 0:
                stats = rate_limiter.get_stats()
                add_pbar.set_postfix({
                    'rpm': f"{stats.current_rpm}",
                    'elapsed': f"{stats.elapsed_seconds}s"
                })

        add_pbar.close()

        # Final statistics
        final_stats = rate_limiter.get_stats()
        print("\n" + "=" * 70)
        print("✅ PROCESSING COMPLETE")
        print("=" * 70)
        print(f"Total batches processed: {final_stats.processed_count}")
        print(f"Total time elapsed: {final_stats.elapsed_seconds} seconds")
        print(f"Average RPM: {final_stats.current_rpm}")
        print(f"Total chunks embedded: {len(all_chunks):,}")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
