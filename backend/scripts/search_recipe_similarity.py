import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.settings.env import settings


class RecipeSimilaritySearch:
    """Class to handle recipe similarity search using vector embeddings."""

    def __init__(self):
        """Initialize the similarity search with embedding model and Qdrant client."""
        # Initialize embedding model
        self.embedding_model = HuggingFaceEmbeddings(
            model_name="keepitreal/vietnamese-sbert",
            model_kwargs={"device": "cpu"},
            encode_kwargs={'normalize_embeddings': False}
        )

        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(url=settings.QDRANT_URL)

        # Initialize Qdrant vector store
        self.vector_store = QdrantVectorStore(
            client=self.qdrant_client,
            collection_name=settings.QDRANT_RECIPE_COLLECTION,
            embedding=self.embedding_model
        )

    async def search_similar_recipes(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for similar recipes based on the query text.

        Args:
            query: The search query text (e.g., "chicken pasta with tomatoes")
            top_k: Number of top similar results to return
            score_threshold: Minimum similarity score threshold (0.0 to 1.0)

        Returns:
            List of dictionaries containing recipe info and similarity scores
        """
        try:
            # Perform similarity search
            docs_with_scores = await self.vector_store.asimilarity_search_with_score(
                query=query,
                k=top_k
            )

            results = []
            for doc, score in docs_with_scores:
                # Convert score to similarity percentage (higher is better for cosine)
                # Cosine similarity ranges from -1 to 1, but in practice for text it's 0 to 1
                similarity_percentage = max(0, min(100, (score + 1) * 50))  # Convert to 0-100%

                if similarity_percentage / 100 >= score_threshold:
                    result = {
                        "recipe_id": doc.metadata.get("id"),
                        "title": doc.metadata.get("title"),
                        "content_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                        "similarity_score": round(similarity_percentage, 2),
                        "raw_score": round(score, 4),
                        "source": doc.metadata.get("source"),
                        "chunk_metadata": doc.metadata
                    }
                    results.append(result)

            return results

        except Exception as e:
            print(f"Error during similarity search: {e}")
            return []

    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the Qdrant collection."""
        try:
            collection_info = self.qdrant_client.get_collection(
                collection_name=settings.QDRANT_RECIPE_COLLECTION
            )
            return {
                "collection_name": settings.QDRANT_RECIPE_COLLECTION,
                "vectors_count": collection_info.vectors_count,
                "points_count": collection_info.points_count,
                "status": "ready"
            }
        except Exception as e:
            return {
                "collection_name": settings.QDRANT_RECIPE_COLLECTION,
                "status": f"error: {str(e)}"
            }


async def main():
    """Main function to demonstrate similarity search."""
    # Initialize search engine
    search_engine = RecipeSimilaritySearch()

    # Check collection status
    collection_info = search_engine.get_collection_info()
    print("Collection Info:")
    print(f"  Name: {collection_info.get('collection_name')}")
    print(f"  Status: {collection_info.get('status')}")
    print(f"  Points: {collection_info.get('points_count', 'N/A')}")
    print()

    # Example queries to test
    test_queries = [
        "Tôi muốn ăn phở, phải có bò và nước dùng thơm ngon",
    ]

    print("Testing Similarity Search:")
    print("=" * 50)

    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        print("-" * 40)

        # Search for similar recipes
        results = await search_engine.search_similar_recipes(
            query=query,
            top_k=10,
            score_threshold=0.1  # Only show results with >10% similarity
        )

        if not results:
            print("❌ No similar recipes found.")
            continue

        for i, result in enumerate(results, 1):
            print(f"{i}. 📖 {result['title']}")
            print(f"   Similarity: {result['similarity_score']}%")
            print(f"   Recipe ID: {result['recipe_id']}")
            print(f"   Preview: {result['content_preview']}")
            print(f"   Type: {result['chunk_metadata']['type']}")
            print()

    print("\n✅ Similarity search testing complete!")


if __name__ == "__main__":
    asyncio.run(main())
