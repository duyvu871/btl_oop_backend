"""
Reranker service using embedding generators from generate_embedding.py.
"""

from typing import List, Tuple

import numpy as np

from src.ai.embeddings.generate_embedding import BaseEmbeddingGenerator


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity score
    """
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


class Reranker:
    """
    Reranker class that uses an embedding generator to rerank documents based on query similarity.
    """

    def __init__(self, embedding_generator: BaseEmbeddingGenerator):
        """
        Initialize the reranker with an embedding generator.

        Args:
            embedding_generator: Instance of a class inheriting from BaseEmbeddingGenerator
        """
        self.embedding_generator = embedding_generator

    def rerank(self, query: str, documents: List[str]) -> List[Tuple[str, float]]:
        """
        Rerank documents based on their similarity to the query.

        Args:
            query: The query string
            documents: List of document strings to rerank

        Returns:
            List of tuples (document, similarity_score) sorted by similarity descending
        """
        # Generate embedding for the query
        query_emb = self.embedding_generator.embed_text(query)

        # Generate embeddings for the documents
        doc_embs = self.embedding_generator.embed_texts(documents)

        # Calculate similarities
        similarities = [cosine_similarity(query_emb, doc_emb) for doc_emb in doc_embs]

        # Rank documents by similarity (highest first)
        ranked = sorted(zip(documents, similarities), key=lambda x: x[1], reverse=True)

        return ranked
