from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from app.schemas.document import MetadataValue


EvidenceType = Literal["structured", "document"]
EvidenceContent = str | dict[str, MetadataValue]


# 证据模型：就是说这个答案依据了哪段的什么材料，分别表示来源、内容和相关度分数
class Evidence(BaseModel):
    evidence_id: str = Field(default_factory=lambda: f"ev_{uuid4().hex}", min_length=1)
    evidence_type: EvidenceType = "document"
    source: str = Field(..., min_length=1)
    content: EvidenceContent
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, MetadataValue] = Field(default_factory=dict)
