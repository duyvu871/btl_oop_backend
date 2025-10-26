"""
Recipe search service using vector similarity search.
"""

from typing import Any

from .qdrant_store import QdrantStore


class RecipeSearch:
    """
    Service for searching recipes using vector similarity.
    """

    def __init__(self, qdrant_store: QdrantStore):
        """
        Initialize the recipe search service.

        Args:
            qdrant_store: QdrantStore instance for vector operations
        """
        self.qdrant_store = qdrant_store

    async def search_similar_recipes(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.0,
        **kwargs
    ) -> list[dict[str, Any]]:
        """
        Search for similar recipes based on the query text.

        Args:
            query: The search query text (e.g., "chicken pasta with tomatoes")
            top_k: Number of top similar results to return
            score_threshold: Minimum similarity score threshold (0.0 to 1.0)
            **kwargs: Additional search parameters

        Returns:
            List of dictionaries containing recipe information and similarity scores
        """
        # Perform similarity search
        docs = await self.qdrant_store.search_similar(
            query=query,
            k=top_k,
            score_threshold=score_threshold,
            **kwargs
        )

        # Format results
        results = []
        for doc in docs:
            result = {
                "title": doc.metadata.get("title", ""),
                "id": doc.metadata.get("id", ""),
                "content": doc.page_content,
                "score": getattr(doc, 'score', None),  # If available
                "metadata": doc.metadata
            }
            results.append(result)

        return results

    async def search_by_ingredients(self, ingredients: list[str], top_k: int = 5) -> list[dict[str, Any]]:
        """
        Search recipes by ingredients.

        Args:
            ingredients: List of ingredient names
            top_k: Number of top results to return

        Returns:
            List of recipe dictionaries
        """
        # Combine ingredients into a query string
        query = " ".join(ingredients)
        return await self.search_similar_recipes(query=query, top_k=top_k)

    async def search_by_title(self, title: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Search recipes by title.

        Args:
            title: Recipe title to search for
            top_k: Number of top results to return

        Returns:
            List of recipe dictionaries
        """
        return await self.search_similar_recipes(query=title, top_k=top_k)
