from pydantic import BaseModel, Field, field_validator

from app.schemas.evidence import Evidence

# /chat 的请求
class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    session_id: str = Field(..., min_length=1)
    query: str = Field(..., min_length=2, max_length=1000)

    # 去除输入前后的空格
    @field_validator("user_id", "session_id", "query", mode="before")
    @classmethod
    def strip_string_fields(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    # 确保query至少有2个非空字符
    @field_validator("query")
    @classmethod
    def query_must_have_enough_text(cls, value: str) -> str:
        if len(value) < 2:
            raise ValueError("query must contain at least 2 non-whitespace characters")
        return value

# 相应：包含答案、意图、证据列表、是否是fallback、fallback原因和追踪id
class ChatResponse(BaseModel):
    answer: str
    intent: str
    evidence: list[Evidence] = Field(default_factory=list)
    fallback: bool
    fallback_reason: str | None = None
    trace_id: str
