from fastapi import APIRouter

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/recommend")
async def recommend(text: str):
    """
    Recommend endpoint that takes text input.
    Currently not implemented, returns a placeholder message.
    """
    # TODO: Implement recommendation logic using embeddings and Qdrant
    return {"message": "Recommend endpoint not implemented yet"}
