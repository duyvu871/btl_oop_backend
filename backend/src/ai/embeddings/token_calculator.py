"""
Token calculator for estimating embedding costs.
"""


import tiktoken


class TokenCalculator:
    """
    Calculate tokens and estimate costs for embedding operations.
    """

    # Pricing per 1M tokens (as of 2025)
    PRICING = {
        # OpenAI models
        "text-embedding-3-small": 0.02,  # $0.02 per 1M tokens
        "text-embedding-3-large": 0.13,  # $0.13 per 1M tokens
        "text-embedding-ada-002": 0.10,  # $0.10 per 1M tokens

        # Google models (approximate pricing)
        "text-embedding-004": 0.025,  # $0.025 per 1M tokens (estimated)
        "embedding-001": 0.025,  # $0.025 per 1M tokens (estimated)
    }

    def __init__(self, model_name: str = "text-embedding-3-small"):
        """
        Initialize token calculator.

        Args:
            model_name: Name of the embedding model
        """
        self.model_name = model_name
        self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in a text string.

        Args:
            text: Input text

        Returns:
            Number of tokens
        """
        return len(self.encoding.encode(text))

    def count_tokens_batch(self, texts: list[str]) -> int:
        """
        Count total tokens in a batch of texts.

        Args:
            texts: List of input texts

        Returns:
            Total number of tokens
        """
        return sum(self.count_tokens(text) for text in texts)

    def estimate_cost(self, total_tokens: int) -> float:
        """
        Estimate cost for embedding the given number of tokens.

        Args:
            total_tokens: Total number of tokens to embed

        Returns:
            Estimated cost in USD
        """
        price_per_million = self.PRICING.get(self.model_name, 0.02)
        return (total_tokens / 1_000_000) * price_per_million

    def get_summary(self, texts: list[str]) -> dict:
        """
        Get a complete summary of tokens and cost estimation.

        Args:
            texts: List of input texts

        Returns:
            Dictionary with token count, cost estimate, and other metrics
        """
        total_tokens = self.count_tokens_batch(texts)
        estimated_cost = self.estimate_cost(total_tokens)

        return {
            "model_name": self.model_name,
            "num_texts": len(texts),
            "total_tokens": total_tokens,
            "avg_tokens_per_text": total_tokens / len(texts) if texts else 0,
            "estimated_cost_usd": round(estimated_cost, 4),
            "price_per_million_tokens": self.PRICING.get(self.model_name, 0.02),
        }

    def print_summary(self, texts: list[str]) -> None:
        """
        Print a formatted summary of token count and cost.

        Args:
            texts: List of input texts
        """
        summary = self.get_summary(texts)

        print("\n" + "="*60)
        print("TOKEN & COST ESTIMATION")
        print("="*60)
        print(f"Model: {summary['model_name']}")
        print(f"Number of texts: {summary['num_texts']:,}")
        print(f"Total tokens: {summary['total_tokens']:,}")
        print(f"Average tokens per text: {summary['avg_tokens_per_text']:.2f}")
        print(f"Price per 1M tokens: ${summary['price_per_million_tokens']}")
        print(f"Estimated cost: ${summary['estimated_cost_usd']:.4f}")
        print("="*60 + "\n")

