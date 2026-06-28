from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """
    Incoming user query.
    """

    query: str = Field(
        ...,
        min_length=1,
        description="Question asked by the user."
    )


class Citation(BaseModel):
    """
    Source citation attached to an answer.
    """

    page: int
    section: Optional[str] = None


class ChatResponse(BaseModel):
    """
    Final response returned to frontend.
    """

    answer: str

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0
    )

    citations: List[Citation]