from uuid import uuid4

from pydantic import BaseModel, Field


class TraceInfo(BaseModel):
    trace_id: str = Field(..., min_length=1)


def new_trace_id() -> str:
    return f"trace_{uuid4().hex}"
