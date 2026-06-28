from fastapi import APIRouter, HTTPException
import json
import os

from backend.schemas.chat import (
    ChatRequest,
    ChatResponse
)

from backend.services.rag_pipeline import (
    generate_answer
)

router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)

LOG_FILE = "logs/chat_history.json"


@router.post(
    "/",
    response_model=ChatResponse
)
async def chat(
    request: ChatRequest
):
    """
    Ask questions against uploaded documents.
    """

    try:

        result = await generate_answer(
            request.query
        )

        return ChatResponse(
            answer=result["answer"],
            confidence=result["confidence"],
            citations=result["citations"]
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get(
    "/history"
)
async def get_chat_history():
    """
    Return all previous chat interactions.
    """

    try:

        if not os.path.exists(
            LOG_FILE
        ):
            return []

        with open(
            LOG_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        return data

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )