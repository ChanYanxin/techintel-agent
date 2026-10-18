"""Requires optional runtime dependencies; run in an internet-enabled env."""
import pytest
pytest.importorskip("langgraph")
from langgraph.types import Command
from sciwork.graph import build_graph


@pytest.mark.asyncio
async def test_end_to_end_offline(monkeypatch):
    monkeypatch.setenv("SCIW_MODEL_MODE", "offline")
    monkeypatch.setenv("SCIW_USE_MCP", "false")
    graph = build_graph()
    result = await graph.ainvoke({"question": "Screen CSV conductivity LLZO oxide",
                                  "require_review": False, "attempts": 0},
                                 config={"configurable": {"thread_id": "test-graph-a"}})
    assert result["analysis"]["total_matching"] == 6
    assert result["status"].startswith("completed")
    assert "SYN-" in result["report"]


@pytest.mark.asyncio
async def test_human_review_interrupt_and_resume(monkeypatch):
    monkeypatch.setenv("SCIW_MODEL_MODE", "offline")
    monkeypatch.setenv("SCIW_USE_MCP", "false")
    graph = build_graph()
    cfg = {"configurable": {"thread_id": "test-review-a"}}
    result = await graph.ainvoke({"question": "LLZO oxide ceramic densification",
                                  "require_review": True, "attempts": 0}, config=cfg)
    assert "__interrupt__" in result
    resumed = await graph.ainvoke(Command(resume={"approved": True}), config=cfg)
    assert resumed["review"] == "approved"
    assert resumed["report"]


@pytest.mark.asyncio
async def test_explicit_failed_mcp_does_not_silently_fallback(monkeypatch):
    monkeypatch.setenv("SCIW_MODEL_MODE", "offline")
    monkeypatch.setenv("SCIW_USE_MCP", "true")
    graph = build_graph()
    result = await graph.ainvoke({"question": "CSV conductivity analysis", "attempts": 0},
                                 config={"configurable": {"thread_id": "test-mcp-fail"}})
    assert result["attempts"] == 2
    assert result["analysis"] is None
    assert result["status"] == "completed_with_warnings"
    assert any("failed" in x for x in result["issues"])
