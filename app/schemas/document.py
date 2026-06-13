from pydantic import BaseModel, Field


MetadataValue = str | int | float | bool | None | list[str]

# 定义文档和文本块的模型，包含id、来源、内容和附加信息等字段
class Document(BaseModel):
    id: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    metadata: dict[str, MetadataValue] = Field(default_factory=dict)

# 定义文本块模型，包含文档id、来源、内容和附加信息等字段
class Chunk(BaseModel):
    id: str = Field(..., min_length=1)
    document_id: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    metadata: dict[str, MetadataValue] = Field(default_factory=dict)
