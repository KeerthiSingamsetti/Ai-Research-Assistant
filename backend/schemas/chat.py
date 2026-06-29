from typing import List, Optional

from pydantic import BaseModel, Field


class Citation(BaseModel):
    page: int
    section: Optional[str] = None


class Evaluation(BaseModel):
    evaluation_score: float
    faithfulness: float
    citation_count: int


class ChatRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1
    )


class ChatResponse(BaseModel):
    answer: str

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0
    )

    citations: List[Citation]

    evaluation: Evaluation