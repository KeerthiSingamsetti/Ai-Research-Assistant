from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from backend.services.rag_pipeline import generate_answer
from backend.services.streaming_service import stream_answer


router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)


class ChatRequest(BaseModel):
    query: str


# ==========================
# NORMAL CHAT ENDPOINT
# ==========================
@router.post("/")
async def chat(request: ChatRequest):
    """
    Returns full JSON response.
    Useful for Swagger testing and frontend APIs.
    """

    result = await generate_answer(
        request.query
    )

    return result


# ==========================
# STREAMING CHAT ENDPOINT
# ==========================
@router.post("/stream")
async def stream_chat(request: ChatRequest):
    """
    Streams answer token-by-token using SSE.
    """

    result = await generate_answer(
        request.query
    )

    answer = result.get("answer", "")

    return EventSourceResponse(
        stream_answer(answer)
    )