"""
Embedding generation service using HuggingFace models.
"""

from langchain_huggingface import HuggingFaceEmbeddings


class EmbeddingGenerator:
    """
    Service for generating embeddings from text using HuggingFace models.
    """

    def __init__(self, model_name: str = "keepitreal/vietnamese-sbert", device: str = "cpu", normalize_embeddings: bool = False):
        """
        Initialize the embedding generator.

        Args:
            model_name: Name of the HuggingFace model to use
            device: Device to run the model on ('cpu' or 'cuda')
            normalize_embeddings: Whether to normalize embeddings
        """
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": device},
            encode_kwargs={'normalize_embeddings': normalize_embeddings}
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

    async def embed_text(self, text: str) -> list[float]:
        """
        Asynchronously generate embedding for a single text.

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        return await self.embedding_model.aembed_query(text)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Asynchronously generate embeddings for multiple texts.

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors
        """
        return await self.embedding_model.aembed_documents(texts)
