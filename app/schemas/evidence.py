from pydantic import BaseModel, Field

from app.schemas.document import MetadataValue

# 证据模型：就是说这个答案依据了哪段的什么材料，分别表示来源、内容和相关度分数
class Evidence(BaseModel):
    source: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    score: float = Field(..., ge=0.0, le=1.0)
    metadata: dict[str, MetadataValue] = Field(default_factory=dict)
