from fastapi import APIRouter
from pydantic import BaseModel

from sse_starlette.sse import EventSourceResponse

from backend.services.rag_pipeline import generate_answer
from backend.services.streaming_service import stream_answer


router = APIRouter()


class ChatRequest(BaseModel):
    query: str


@router.post("/")
async def stream_chat(
    request: ChatRequest
):

    result = await generate_answer(
        request.query
    )

    answer = result["answer"]

    return EventSourceResponse(
        stream_answer(answer)
    )