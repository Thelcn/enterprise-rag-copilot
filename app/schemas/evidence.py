from pydantic import BaseModel, Field


class Evidence(BaseModel):
    source: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    score: float = Field(..., ge=0.0, le=1.0)
