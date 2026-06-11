from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_week1_health_baseline() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "enterprise-rag-copilot"
    assert payload["version"]
    assert payload["environment"]


def test_week1_chat_baseline_returns_answer() -> None:
    response = client.post(
        "/chat",
        json={
            "user_id": "baseline-user",
            "session_id": "baseline-session",
            "query": "退货政策是什么？",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"]
    assert isinstance(payload["answer"], str)
    assert payload["fallback"] is False
    assert payload["fallback_reason"] is None
    assert payload["trace_id"].startswith("trace_")


def test_week1_chat_baseline_returns_evidence() -> None:
    response = client.post(
        "/chat",
        json={
            "user_id": "baseline-user",
            "session_id": "baseline-session",
            "query": "退货政策是什么？",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload["evidence"], list)
    assert payload["evidence"]

    first_evidence = payload["evidence"][0]
    assert first_evidence["source"] == "return_policy.md"
    assert first_evidence["content"]
    assert isinstance(first_evidence["score"], float)


def test_week1_chat_baseline_fallback_stays_grounded() -> None:
    response = client.post(
        "/chat",
        json={
            "user_id": "baseline-user",
            "session_id": "baseline-session",
            "query": "量子咖啡会员积分怎么兑换？",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["fallback"] is True
    assert payload["evidence"] == []
    assert payload["fallback_reason"]
