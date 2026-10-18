import pytest
pytest.importorskip("langgraph")
from fastapi.testclient import TestClient
from sciwork.api import app


def test_health_and_demo():
    client = TestClient(app)
    assert client.get("/healthz").json()["status"] == "ok"
    assert "Scientific Research Copilot" in client.get("/demo").text


def test_chat_and_thread_conflict(monkeypatch):
    monkeypatch.setenv("SCIW_MODEL_MODE", "offline")
    monkeypatch.setenv("SCIW_USE_MCP", "false")
    client = TestClient(app)
    body = {"question": "Compare LLZO oxide and sulfide moisture stability", "thread_id": "api-once"}
    first = client.post("/chat", json=body)
    assert first.status_code == 200
    assert first.json()["evidence"]
    assert client.post("/chat", json=body).status_code == 409


def test_api_approval_path(monkeypatch):
    monkeypatch.setenv("SCIW_MODEL_MODE", "offline")
    monkeypatch.setenv("SCIW_USE_MCP", "false")
    client = TestClient(app)
    response = client.post("/chat", json={"question": "LLZO oxide ceramic densification",
                                                  "require_review": True, "thread_id": "api-review"})
    assert response.json()["status"] == "awaiting_review"
    resumed = client.post("/runs/api-review/resume", json={"approved": False})
    assert resumed.json()["status"] == "review_rejected"
