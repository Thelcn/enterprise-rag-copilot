from pydantic import BaseModel, Field


MetadataValue = str | int | float | bool | None


class Document(BaseModel):
    id: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    metadata: dict[str, MetadataValue] = Field(default_factory=dict)
