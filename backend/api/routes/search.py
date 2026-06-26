from pydantic import BaseModel
from fastapi import APIRouter

from backend.services.retriever import (
    retrieve_chunks
)

router = APIRouter(
    prefix="/search",
    tags=["search"]
)

class SearchRequest(BaseModel):
    query: str


@router.post("/")
async def search(
    request: SearchRequest
):

    results = await retrieve_chunks(
        request.query
    )

    return {
        "query": request.query,
        "confidence": results["confidence"],
        "retrieved_chunks": results["chunks"]
    }