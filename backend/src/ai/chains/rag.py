"""Simple RAG (Retrieval-Augmented Generation) Chain with Reranking.

Module này cung cấp một RAG chain đơn giản với quy trình:
1. LLM generate recommendation/intent từ user prompt
2. Retrieval documents từ Qdrant dựa trên LLM output
3. Rerank documents dựa trên user prompt gốc
4. Final completion với ranked documents
"""

import asyncio
from dataclasses import dataclass
from typing import TypedDict

from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate

from src.ai.chains.completion import CompletionChain, CustomPromptCompletionChain, LLMConfig, PromptBasedCompletionChain
from src.ai.chains.reranker import Reranker
from src.ai.embeddings.generate_embedding import BaseEmbeddingGenerator
from src.ai.embeddings.search import RecipeSearch, RecipeSearchResult


class RAGInput(TypedDict, total=False):
    """Type definition cho RAG chain input.

    Attributes:
        query: User query (bắt buộc)
        top_k: Số documents từ retrieval (optional, mặc định 5)
        score_threshold: Ngưỡng similarity (optional, mặc định 0.1)
        rerank_top_k: Số documents sau rerank (optional, mặc định = top_k)
    """
    query: str
    top_k: int
    score_threshold: float
    rerank_top_k: int


@dataclass
class RAGResult:
    """Kết quả từ RAG chain.

    Attributes:
        query: User query gốc
        llm_intent: LLM recommendation/intent từ user prompt
        retrieved_docs: Các documents được lấy từ Qdrant
        reranked_docs: Các documents sau khi rerank dựa trên user prompt
        final_context: Context được xây dựng từ reranked documents
        completion: Kết quả completion từ LLM
    """
    query: str
    llm_intent: str
    retrieved_docs: list[RecipeSearchResult]
    reranked_docs: list[RecipeSearchResult]
    final_context: str
    completion: str


class SimpleRAGChain:
    """Simple RAG Chain with LLM-guided Retrieval and Reranking.

    Quy trình:
    1. LLM phân tích user prompt → generate recommendation/intent
    2. Tìm kiếm documents từ Qdrant dựa trên LLM intent
    3. Rerank documents dựa trên user prompt gốc (để refine kết quả)
    4. Xây dựng final context từ reranked documents
    5. Tạo final completion với context
    6. Trả về kết quả kèm tất cả thông tin chi tiết

    Ví dụ:
        from src.ai.embeddings.qdrant_store import QdrantStore
        from src.ai.embeddings.search import RecipeSearch
        from src.ai.embeddings.generate_embedding import BaseEmbeddingGenerator
        from qdrant_client import QdrantClient

        qdrant_store = QdrantStore(
            client=QdrantClient(...),
            collection_name="recipes",
            embedding_model=embedding_generator
        )
        search_engine = RecipeSearch(qdrant_store)

        rag_chain = SimpleRAGChain(
            search_engine=search_engine,
            embedding_generator=embedding_generator,
            llm_config=LLMConfig()
        )

        result = await rag_chain.ainvoke({
            "query": "Tôi có thịt bò, làm gì ngon?",
            "top_k": 5
        })

        print(f"LLM Intent: {result.llm_intent}")
        print(f"Completion: {result.completion}")
        print(f"Reranked docs: {result.reranked_docs}")
    """

    def __init__(
        self,
        search_engine: RecipeSearch,
        embedding_generator: BaseEmbeddingGenerator,
        llm_config: LLMConfig | None = None,
        llm_system_prompt: str | None = None,
        final_system_prompt: str | None = None
    ) -> None:
        """Khởi tạo RAG chain.

        Args:
            search_engine: RecipeSearch instance để tìm kiếm documents.
            embedding_generator: BaseEmbeddingGenerator để rerank documents.
            llm_config: Cấu hình LLM (sử dụng mặc định nếu None).
            llm_system_prompt: Custom system prompt cho LLM intent generation.
            final_system_prompt: Custom system prompt cho final completion.
        """
        self.search_engine: RecipeSearch = search_engine
        self.embedding_generator: BaseEmbeddingGenerator = embedding_generator
        self.reranker: Reranker = Reranker(embedding_generator)
        self.llm_config: LLMConfig = llm_config or LLMConfig()
        self.llm_system_prompt: str = llm_system_prompt or self._get_default_llm_system_prompt()
        self.final_system_prompt: str = final_system_prompt or self._get_default_final_system_prompt()
        self.intent_chain: CompletionChain | None = None
        self.final_chain: CompletionChain | None = None

    @staticmethod
    def _get_default_llm_system_prompt() -> str:
        """Default system prompt cho LLM intent generation.

        Returns:
            str: System prompt.
        """
        return """Bạn là một chuyên gia phân tích nhu cầu nấu ăn. Dựa trên câu hỏi của người dùng, hãy:
1. Xác định các nguyên liệu chính
2. Xác định loại món ăn
3. Xác định các yêu cầu đặc biệt
4. Tạo một query tối ưu để tìm kiếm công thức nấu ăn

Trả lời súc tích, chỉ bao gồm những thông tin cần thiết cho việc tìm kiếm.

viết theo format: <Cách làm|Nguyên liệu>: <tên món nếu có> <các nguyên liệu nếu có>, <Loại món ăn nếu có>, <Yêu cầu đặc biệt nếu có>."""

    @staticmethod
    def _get_default_final_system_prompt() -> str:
        """Default system prompt cho final completion.

        Returns:
            str: System prompt.
        """
        return """Bạn là một trợ lý nấu ăn thông minh được hỗ trợ bởi cơ sở dữ liệu công thức nấu ăn Việt Nam.

Nhiệm vụ của bạn:
1. Trả lời câu hỏi về nấu ăn dựa trên các công thức được cung cấp
2. Đưa ra khuyến nghị công thức nấu ăn phù hợp
3. Giải thích cách nấu một cách rõ ràng
4. Cung cấp mẹo và thủ thuật hữu ích


Hướng dẫn:
- Luôn dựa vào thông tin từ các công thức được cung cấp
- Nếu công thức phù hợp, hãy đề xuất nó trước tiên
- Cung cấp thông tin chi tiết nhưng súc tích
- Trả về đoạn text đủ ngắn, không sử dụng markdown để hiển thị (vẫn có xuống dòng, list các kiểu nhưng không dùng markdown)
- Viết theo tiếng Việt"""

    def _build_intent_chain(self) -> CompletionChain:
        """Xây dựng chain để generate LLM intent.

        Trả về một CustomPromptCompletionChain sử dụng llm_system_prompt
        để phân tích user query và generate intent.

        Returns:
            CompletionChain: Intent generation chain (đã build).
        """
        return CustomPromptCompletionChain(
            self.llm_config,
            "{query}",
            self.llm_system_prompt
        ).build()

    def _build_final_chain(self) -> CompletionChain:
        """Xây dựng chain cho final completion.

        Trả về một PromptBasedCompletionChain sử dụng final_system_prompt
        và final completion template.

        Returns:
            CompletionChain: Final completion chain (đã build).
        """
        system: SystemMessagePromptTemplate = SystemMessagePromptTemplate.from_template(self.final_system_prompt)
        human: HumanMessagePromptTemplate = HumanMessagePromptTemplate.from_template(
            "Context (Các công thức nấu ăn liên quan):\n{context}\n\n"
            "Câu hỏi: {query}"
        )
        prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages([system, human])
        return PromptBasedCompletionChain(self.llm_config, prompt).build()

    @staticmethod
    def _format_context(docs: list[RecipeSearchResult]) -> str:
        """Format reranked documents thành context string.

        Args:
            docs: Danh sách RecipeSearchResult (đã rerank), không được None.

        Returns:
            str: Formatted context string (non-empty).
        """
        if not docs:
            return "Không có công thức nấu ăn liên quan được tìm thấy."

        context_parts: list[str] = []
        for i, doc in enumerate(docs, 1):
            context_parts.append(
                f"[{i}] {doc.title} (Độ liên quan: {doc.similarity_score}%)\n"
                f"ID: {doc.id}\n"
                f"Nội dung:\n{doc.content}\n"
            )

        return "\n".join(context_parts)

    async def ainvoke(
        self,
        user_input: RAGInput
    ) -> RAGResult:
        """Gọi RAG chain bất đồng bộ.

        Quy trình:
        1. Generate LLM intent từ user query
        2. Tìm kiếm documents từ Qdrant dựa trên LLM intent
        3. Rerank documents dựa trên user query gốc
        4. Generate final completion với reranked documents

        Args:
            user_input: RAGInput dict chứa:
                - query (str): User query (bắt buộc)
                - top_k (int): Số documents để lấy (mặc định 5)
                - score_threshold (float): Ngưỡng similarity (mặc định 0.1)
                - rerank_top_k (int): Số documents giữ lại sau rerank (mặc định bằng top_k)

        Returns:
            RAGResult: Kết quả RAG đầy đủ thông tin.

        Raises:
            ValueError: Nếu 'query' không có trong user_input.
            TypeError: Nếu user_input không phải RAGInput format.
        """
        if "query" not in user_input:
            raise ValueError("'query' là bắt buộc trong user_input")

        query: str = user_input["query"]
        if not isinstance(query, str) or not query.strip():
            raise ValueError("'query' phải là non-empty string")

        top_k: int = user_input.get("top_k", 5)
        if not isinstance(top_k, int) or top_k <= 0:
            raise ValueError("'top_k' phải là positive integer")

        score_threshold: float = user_input.get("score_threshold", 0.1)

        rerank_top_k: int = user_input.get("rerank_top_k", top_k)
        if not isinstance(rerank_top_k, int) or rerank_top_k <= 0:
            raise ValueError("'rerank_top_k' phải là positive integer")

        # Bước 1: LLM generate intent từ user query
        if not self.intent_chain:
            self.intent_chain = self._build_intent_chain()

        llm_intent: str = await self.intent_chain.ainvoke({"query": query})
        print(f"LLM generated intent: {llm_intent}")

        # Bước 2: Tìm kiếm documents từ Qdrant dựa trên LLM intent
        retrieved_docs: list[RecipeSearchResult] = await self.search_engine.search_similar_recipes(
            query=llm_intent,
            top_k=top_k,
            score_threshold=score_threshold
        )
        print(f"Retrieved {len(retrieved_docs)} documents from search engine")

        # Bước 3: Rerank documents dựa trên user query gốc
        reranked_docs_with_score: list[tuple[RecipeSearchResult, float]] = await self.reranker.arerank_objects(
            query=query,
            documents=retrieved_docs,
            text_attr='content'
        )
        print("Reranked documents based on user query")

        # Giữ lại top rerank_top_k documents
        reranked_docs: list[RecipeSearchResult] = [doc for doc, _ in reranked_docs_with_score[:rerank_top_k]]

        # Bước 4: Xây dựng final context từ reranked documents
        final_context: str = self._format_context(reranked_docs)
        print(f"Built final context from reranked documents {final_context}")

        # Bước 5: Gọi final completion chain
        if not self.final_chain:
            self.final_chain = self._build_final_chain()

        completion: str = await self.final_chain.ainvoke({
            "query": query,
            "context": final_context
        })
        print(f"Final completion context: {completion}")

        # Bước 6: Trả về kết quả
        return RAGResult(
            query=query,
            llm_intent=llm_intent,
            retrieved_docs=retrieved_docs,
            reranked_docs=reranked_docs,
            final_context=final_context,
            completion=completion
        )

    def invoke(
        self,
        user_input: RAGInput
    ) -> RAGResult:
        """Gọi RAG chain đồng bộ (wrapper cho ainvoke).

        Args:
            user_input: RAGInput dict (xem ainvoke).

        Returns:
            RAGResult: Kết quả RAG đầy đủ thông tin.

        Raises:
            ValueError: Nếu input không hợp lệ.
        """

        return asyncio.run(self.ainvoke(user_input))


# Convenience function
async def create_rag_completion(
    search_engine: RecipeSearch,
    embedding_generator: BaseEmbeddingGenerator,
    query: str,
    top_k: int = 5,
    score_threshold: float = 0.1,
    rerank_top_k: int | None = None,
    llm_config: LLMConfig | None = None
) -> RAGResult:
    """Tạo RAG completion nhanh chóng (convenience function).

    Hàm này tạo SimpleRAGChain instance và gọi ainvoke() với các tham số đã cho.

    Args:
        search_engine: RecipeSearch instance (không được None).
        embedding_generator: BaseEmbeddingGenerator instance (không được None).
        query: User query string (bắt buộc, phải non-empty).
        top_k: Số documents từ retrieval (default 5, phải positive).
        score_threshold: Ngưỡng similarity (default 0.1).
        rerank_top_k: Số documents sau rerank (default None = bằng top_k).
        llm_config: LLMConfig instance (default None = mặc định).

    Returns:
        RAGResult: Kết quả RAG đầy đủ thông tin.

    Raises:
        ValueError: Nếu query empty hoặc parameters không hợp lệ.
        TypeError: Nếu arguments type không đúng.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query phải là non-empty string")

    if not isinstance(top_k, int) or top_k <= 0:
        raise ValueError("top_k phải là positive integer")

    if not isinstance(score_threshold, (int, float)) or not (0.0 <= score_threshold <= 1.0):
        raise ValueError("score_threshold phải trong range [0.0, 1.0]")

    if rerank_top_k is not None and (not isinstance(rerank_top_k, int) or rerank_top_k <= 0):
        raise ValueError("rerank_top_k phải là positive integer hoặc None")

    rag_chain: SimpleRAGChain = SimpleRAGChain(search_engine, embedding_generator, llm_config)

    final_rerank_top_k: int = rerank_top_k if rerank_top_k is not None else top_k
    rag_input: RAGInput = {
        "query": query,
        "top_k": top_k,
        "score_threshold": score_threshold,
        "rerank_top_k": final_rerank_top_k
    }

    return await rag_chain.ainvoke(rag_input)

