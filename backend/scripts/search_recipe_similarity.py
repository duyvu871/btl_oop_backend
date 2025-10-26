import asyncio
import sys
from pathlib import Path

from qdrant_client import QdrantClient, models

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai.embeddings.generate_embedding import EmbeddingGenerator
from src.ai.embeddings.qdrant_store import QdrantStore
from src.ai.embeddings.search import RecipeSearch
from src.settings.env import settings


async def main():
    """Main function to demonstrate similarity search."""
    # Initialize services using the new classes
    embedding_generator = EmbeddingGenerator()
    qdrant_client = QdrantClient(url=settings.QDRANT_URL)
    qdrant_store = QdrantStore(
        client=qdrant_client,
        collection_name=settings.QDRANT_RECIPE_COLLECTION,
        embedding_model=embedding_generator.embedding_model
    )
    search_engine = RecipeSearch(qdrant_store)

    # Check collection status
    try:
        collection_info = qdrant_client.get_collection(
            collection_name=settings.QDRANT_RECIPE_COLLECTION
        )
        print("Collection Info:")
        print(f"  Name: {settings.QDRANT_RECIPE_COLLECTION}")
        print("  Status: ready")
        print(f"  Points: {collection_info.points_count}")
        print()
    except Exception as e:
        print(f"Collection Info: error - {str(e)}")
        return

    # Example queries to test
    test_queries = [
        "Cách làm",
    ]

    print("Testing Similarity Search:")
    print("=" * 50)

    # filter with metadata type
    langchain_filter = models.Filter(
        should=[
            models.FieldCondition(
                key="metadata.type",
                match=models.MatchValue(value="Cách làm")
            )
        ]
    )

    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        print("-" * 40)

        # Search for similar recipes
        results = await search_engine.search_similar_recipes(
            query=query,
            top_k=10,
            score_threshold=0.1,  # Only show results with >10% similarity
            filter=langchain_filter
        )

        if not results:
            print("❌ No similar recipes found.")
            continue

        for i, result in enumerate(results, 1):
            print(f"{i}. 📖 {result['title']}")
            print(f"   Similarity: {result.get('score', 'N/A')}%")
            print(f"   Recipe ID: {result['id']}")
            print(f"   Preview: {result['content'][:200]}..." if len(result['content']) > 200 else result['content'])
            print(f"   Type: {result['metadata'].get('type', 'N/A')}")
            print()

    print("\n✅ Similarity search testing complete!")


if __name__ == "__main__":
    asyncio.run(main())
