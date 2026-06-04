from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_chat_returns_stable_mock_contract() -> None:
    response = client.post(
        "/chat",
        json={
            "user_id": "u1",
            "session_id": "s1",
            "query": "退货政策是什么？",
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert set(payload.keys()) == {
        "answer",
        "intent",
        "evidence",
        "fallback",
        "fallback_reason",
        "trace_id",
    }
    assert payload["answer"]
    assert payload["intent"] == "mock_intent"
    assert payload["evidence"] == []
    assert payload["fallback"] is True
    assert payload["fallback_reason"] == "Day 2 mock mode: retrieval is not connected yet."
    assert payload["trace_id"].startswith("trace_")


def test_chat_strips_whitespace_from_query() -> None:
    response = client.post(
        "/chat",
        json={
            "user_id": " u1 ",
            "session_id": " s1 ",
            "query": "  退货  ",
        },
    )

    assert response.status_code == 200


def test_chat_rejects_empty_query() -> None:
    response = client.post(
        "/chat",
        json={
            "user_id": "u1",
            "session_id": "s1",
            "query": "   ",
        },
    )

    assert response.status_code == 422


def test_chat_rejects_too_short_query() -> None:
    response = client.post(
        "/chat",
        json={
            "user_id": "u1",
            "session_id": "s1",
            "query": "a",
        },
    )

    assert response.status_code == 422
