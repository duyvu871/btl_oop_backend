"""
Embedding generation service using Google AI and OpenAI models.
"""

from abc import ABC, abstractmethod

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings


class BaseEmbeddingGenerator(ABC):
    """
    Abstract base class for embedding generators.
    """

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors
        """
        pass

    @abstractmethod
    async def aembed_text(self, text: str) -> list[float]:
        """
        Asynchronously generate embedding for a single text.

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    async def aembed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Asynchronously generate embeddings for multiple texts.

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors
        """
        pass


class GoogleEmbeddingGenerator(BaseEmbeddingGenerator):
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
        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model=model_name,
            google_api_key=api_key
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


class OpenAIEmbeddingGenerator(BaseEmbeddingGenerator):
    """
    Service for generating embeddings from text using OpenAI models.
    """

    def __init__(self, model_name: str = "text-embedding-3-small", api_key: str = None):
        """
        Initialize the embedding generator.

        Args:
            model_name: Name of the OpenAI embedding model to use
            api_key: OpenAI API key (if not set in environment)
        """
        self.embedding_model = OpenAIEmbeddings(
            model=model_name,
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


# Backward compatibility alias
EmbeddingGenerator = OpenAIEmbeddingGenerator
