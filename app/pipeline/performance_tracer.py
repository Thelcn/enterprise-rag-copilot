from collections.abc import Iterator
from contextlib import contextmanager
from time import perf_counter

from app.schemas.trace import TraceInfo, TraceStage, new_trace_id


TraceMetadataValue = str | int | float | bool | None


class PerformanceTracer:
    def __init__(self, trace_id: str | None = None) -> None:
        self.trace_id = trace_id or new_trace_id()
        self._started_at = perf_counter()
        self._stages: list[TraceStage] = []
        self._total_latency_ms: float | None = None

    @contextmanager
    def span(self, name: str, **metadata: TraceMetadataValue) -> Iterator[None]:
        started_at = perf_counter()
        try:
            yield
        finally:
            self.record_stage(
                name=name,
                latency_ms=(perf_counter() - started_at) * 1000,
                metadata=metadata,
            )

    def record_stage(
        self,
        name: str,
        latency_ms: float,
        metadata: dict[str, TraceMetadataValue] | None = None,
    ) -> None:
        self._stages.append(
            TraceStage(
                name=name,
                latency_ms=round(max(latency_ms, 0.0), 4),
                metadata=metadata or {},
            )
        )

    def finish(self) -> TraceInfo:
        self._total_latency_ms = round((perf_counter() - self._started_at) * 1000, 4)
        return self.to_trace_info()

    def to_trace_info(self) -> TraceInfo:
        return TraceInfo(
            trace_id=self.trace_id,
            total_latency_ms=self._total_latency_ms,
            stages=list(self._stages),
        )
