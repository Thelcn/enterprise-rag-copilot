import argparse
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.evaluation import EvaluationCase, EvaluationReport
from evaluation.metrics import build_result, compute_metrics


def load_cases(path: Path) -> list[EvaluationCase]:
    raw_cases = json.loads(path.read_text(encoding="utf-8"))
    return [EvaluationCase.model_validate(item) for item in raw_cases]


def run_cases(cases: list[EvaluationCase]) -> EvaluationReport:
    client = TestClient(app)
    results = []

    for case in cases:
        try:
            response = client.post(
                "/chat",
                json={
                    "user_id": "eval_user",
                    "session_id": f"eval-{case.id}",
                    "query": case.query,
                },
            )
            if response.status_code != 200:
                results.append(
                    build_result(
                        case,
                        error=f"HTTP {response.status_code}: {response.text}",
                    )
                )
                continue
            results.append(build_result(case, response_payload=response.json()))
        except Exception as exc:  # pragma: no cover - defensive report path
            results.append(build_result(case, error=repr(exc)))

    return EvaluationReport(
        metrics=compute_metrics(results),
        results=results,
    )


def render_markdown_summary(report: EvaluationReport) -> str:
    metrics = report.metrics
    lines = [
        "# Evaluation Summary",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| total_cases | {metrics.total_cases} |",
        f"| passed_cases | {metrics.passed_cases} |",
        f"| intent_accuracy | {metrics.intent_accuracy} |",
        f"| route_accuracy | {metrics.route_accuracy} |",
        f"| fallback_correctness | {metrics.fallback_correctness} |",
        f"| fallback_reason_accuracy | {metrics.fallback_reason_accuracy} |",
        f"| evidence_presence_rate | {metrics.evidence_presence_rate} |",
        f"| evidence_keyword_hit_rate | {metrics.evidence_keyword_hit_rate} |",
        f"| error_count | {metrics.error_count} |",
        f"| average_total_latency_ms | {metrics.average_total_latency_ms} |",
        "",
        "## Failed Cases",
        "",
    ]
    failed = [result for result in report.results if not result.passed]
    if not failed:
        lines.append("No failed cases in this local run.")
    else:
        for result in failed:
            lines.append(
                f"- {result.case_id}: expected "
                f"({result.expected_intent}, {result.expected_route}, {result.expected_fallback}) "
                f"got ({result.actual_intent}, {result.actual_route}, {result.actual_fallback}); "
                f"error={result.error}"
            )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local ecommerce RAG evaluation cases.")
    parser.add_argument("--cases", type=Path, required=True, help="Path to evaluation cases JSON.")
    parser.add_argument("--out", type=Path, required=True, help="Path to write JSON report.")
    parser.add_argument("--markdown-out", type=Path, default=None, help="Optional markdown summary path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cases = load_cases(args.cases)
    report = run_cases(cases)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if args.markdown_out is not None:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(render_markdown_summary(report), encoding="utf-8")

    print(json.dumps(report.metrics.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
