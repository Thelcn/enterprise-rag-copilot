from uuid import uuid4

from pydantic import BaseModel, Field

# 追踪每一次的请求，目前只记录了一个id，之后可以拓展
class TraceInfo(BaseModel):
    trace_id: str = Field(..., min_length=1)


def new_trace_id() -> str:
    return f"trace_{uuid4().hex}"
