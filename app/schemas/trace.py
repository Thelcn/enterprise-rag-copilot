from uuid import uuid4

from pydantic import BaseModel, Field


class TraceStage(BaseModel):
    name: str = Field(..., min_length=1)
    latency_ms: float = Field(..., ge=0.0)
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


# 追踪每一次请求，记录 trace_id、总耗时和关键阶段耗时
class TraceInfo(BaseModel):
    trace_id: str = Field(..., min_length=1)
    total_latency_ms: float | None = Field(default=None, ge=0.0)
    stages: list[TraceStage] = Field(default_factory=list)


def new_trace_id() -> str:
    return f"trace_{uuid4().hex}"
