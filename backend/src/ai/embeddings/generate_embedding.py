"""
Embedding generation service using Google AI models.
"""

from langchain_community.embeddings.vertexai import VertexAIEmbeddings


class EmbeddingGenerator:
    """
    Service for generating embeddings from text using Google AI models.
    """

    def __init__(self, model_name: str = "text-embedding-004", api_key: str = None):
        """
        Initialize the embedding generator.

        Args:
            model_name: Name of the Google AI embedding model to use
            api_key: Google AI API key (if not set in environment)
        """
        self.embedding_model = VertexAIEmbeddings(
            model_name=model_name,
            api_key=api_key
        )

    def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        return self.embedding_model.embed_query(text)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors
        """
        return self.embedding_model.embed_documents(texts)

    async def aembed_text(self, text: str) -> list[float]:
        """
        Asynchronously generate embedding for a single text.

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        return await self.embedding_model.aembed_query(text)

    async def aembed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Asynchronously generate embeddings for multiple texts.

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors
        """
        return await self.embedding_model.aembed_documents(texts)
