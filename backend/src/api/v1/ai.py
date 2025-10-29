
from fastapi import APIRouter, Depends
from qdrant_client import QdrantClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.ai.chains.completion import LLMConfig
from src.ai.chains.rag import RAGInput, SimpleRAGChain
from src.ai.embeddings.generate_embedding import GoogleEmbeddingGenerator, APIEmbeddingGenerator
from src.ai.embeddings.qdrant_store import QdrantStore
from src.ai.embeddings.search import RecipeSearch
from src.core.database.database import get_db
from src.core.database.models import Recipe, User
from src.core.security import get_current_user
from src.schemas.recipe import RecipeRead, RecommendRequest, RecommendResponse
from src.settings.env import Settings

router = APIRouter(prefix="/ai", tags=["AI"])

# Global instances (initialized once)
_rag_chain: SimpleRAGChain | None = None
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


async def get_rag_chain() -> SimpleRAGChain:
    """Dependency to get RAG chain instance."""
    global _rag_chain

    if _rag_chain is None:
        settings = get_settings()

        # Initialize embedding generator
        # embedding_generator = GoogleEmbeddingGenerator(
        #     model_name="text-embedding-004",
        #     api_key=settings.GOOGLE_API_KEY,
        #     output_dimensionality=768,
        # )

        embedding_generator = APIEmbeddingGenerator(
            model_name=settings.EMBEDDING_MODEL,
            base_url=settings.EMBEDDING_BASE_URL,
            api_key=settings.EMBEDDING_API_KEY
        )

        # Initialize Qdrant store
        qdrant_client = QdrantClient(url=settings.QDRANT_URL)
        qdrant_store = QdrantStore(
            client=qdrant_client,
            collection_name=settings.QDRANT_RECIPE_COLLECTION,
            embedding_model=embedding_generator,
            vector_size=768
        )

        # Initialize search engine
        search_engine = RecipeSearch(qdrant_store)

        # Create RAG chain
        llm_config = LLMConfig(api_key=settings.GOOGLE_API_KEY)
        _rag_chain = SimpleRAGChain(
            search_engine=search_engine,
            embedding_generator=embedding_generator,
            llm_config=llm_config
        )

    return _rag_chain


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(
    request: RecommendRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    rag_chain: SimpleRAGChain = Depends(get_rag_chain),
):
    """
    Get recipe recommendations based on user's text input using RAG.

    Quy trình:
    1. LLM generates intent từ user query
    2. Vector search tìm recipes từ Qdrant
    3. Rerank results dựa trên user query
    4. LLM generates personalized recommendation

    Requires authentication. Returns recipes matching the user's query.

    Args:
        request: RecommendRequest containing the search text
        current_user: Authenticated user (injected by dependency)
        db: Database session (injected by dependency)
        rag_chain: RAG chain instance (injected by dependency)

    Returns:
        RecommendResponse with recommended recipes and LLM message
    """
    # Run RAG chain
    rag_input: RAGInput = {
        "query": request.query,
        "top_k": 10,
        "score_threshold": 0.1,
        "rerank_top_k": 5
    }

    rag_result = await rag_chain.ainvoke(rag_input)

    # Extract recipe IDs from reranked documents
    recipe_ids = [doc.metadata.get('id') for doc in rag_result.reranked_docs]
    print(f"recipe_ids: {recipe_ids}")
    # print(f"reranked_docs: {rag_result.reranked_docs}")

    if not recipe_ids:
        # No recipes found, return empty list or default recommendations
        result = await db.execute(
            select(Recipe)
            .options(joinedload(Recipe.ingredients), joinedload(Recipe.tutorial_steps))
            .limit(5)
        )
        recipes = result.unique().scalars().all()
    else:
        # Fetch recipes from database using reranked IDs
        result = await db.execute(
            select(Recipe)
            .where(Recipe.id.in_(recipe_ids))
            .options(joinedload(Recipe.ingredients), joinedload(Recipe.tutorial_steps))
        )
        recipes = result.unique().scalars().all()

    # Convert to Pydantic models
    recipes_data = [RecipeRead.model_validate(recipe) for recipe in recipes]

    return RecommendResponse(
        message=rag_result.completion,
        recipes=recipes_data,
        total=len(recipes_data),
    )
