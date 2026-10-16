from fastapi.testclient import TestClient
from techintel.app import app, get_agent


def client():
    get_agent.cache_clear()
    return TestClient(app)


def test_health_docs():
    c = client()
    assert c.get("/health").status_code == 200
    assert c.get("/health").json()["documents"] >= 16
    assert len(c.get("/documents").json()) >= 12


def test_ask_schema_and_citations():
    c = client()
    response = c.post("/ask", json={"query": "硫化物电解质湿度和界面阻抗"})
    assert response.status_code == 200
    assert response.json()["mode"] == "offline"
    assert response.json()["sources"]
    assert c.post("/ask", json={"query": ""}).status_code == 422


def test_memory_endpoint():
    c = client()
    assert c.post("/memory", json={"session_id": "x", "note": "check LLZO"}).status_code == 200
    assert c.get("/memory/x").json()["notes"] == ["check LLZO"]
