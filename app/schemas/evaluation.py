from pydantic import BaseModel, Field


class EvaluationCase(BaseModel):
    id: str = Field(..., min_length=1)
    query: str = Field(..., min_length=2)
    expected_intent: str = Field(..., min_length=1)
    expected_route: str = Field(..., min_length=1)
    required_evidence_keywords: list[str] = Field(default_factory=list)
    expected_fallback: bool
    expected_fallback_reason: str | None = None
    notes: str = ""


class EvaluationResult(BaseModel):
    case_id: str
    query: str
    expected_intent: str
    actual_intent: str | None = None
    expected_route: str
    actual_route: str | None = None
    expected_fallback: bool
    actual_fallback: bool | None = None
    expected_fallback_reason: str | None = None
    actual_fallback_reason: str | None = None
    required_evidence_keywords: list[str] = Field(default_factory=list)
    evidence_count: int = 0
    evidence_keyword_hit: bool | None = None
    evidence_present: bool = False
    trace_id: str | None = None
    total_latency_ms: float | None = None
    passed: bool = False
    error: str | None = None


class EvaluationMetrics(BaseModel):
    total_cases: int
    passed_cases: int
    intent_accuracy: float
    route_accuracy: float
    fallback_correctness: float
    fallback_reason_accuracy: float | None = None
    evidence_presence_rate: float
    evidence_keyword_hit_rate: float | None = None
    error_count: int
    average_total_latency_ms: float | None = None


class EvaluationReport(BaseModel):
    metrics: EvaluationMetrics
    results: list[EvaluationResult]
