"""LangGraph multi-agent DAG with bounded retries and real human review interrupts."""
from __future__ import annotations

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt
from . import core
from .analysis import analyze_experiments
from .config import model_mode, use_mcp
from .llm import synthesize
from .mcp_client import analyze_via_mcp


class ResearchState(TypedDict, total=False):
    question: str
    require_review: bool
    plan: list[str]
    needs_analysis: bool
    min_conductivity: float
    evidence: list[dict]
    grounded: bool
    analysis: dict | None
    analysis_error: str | None
    attempts: int
    issues: list[str]
    review: str
    report: str
    status: str
    mode: str
    tool_backend: str


def planner(state: ResearchState) -> dict:
    return core.plan(state["question"])


def researcher(state: ResearchState) -> dict:
    return core.research(state["question"])


def route_analysis(state: ResearchState) -> Literal["analyst", "validator"]:
    return "analyst" if state["needs_analysis"] else "validator"


async def analyst(state: ResearchState) -> dict:
    attempts = state.get("attempts", 0) + 1
    try:
        if use_mcp():
            result = await analyze_via_mcp(state["min_conductivity"])
            backend = "mcp-stdio"
        else:
            result = analyze_experiments(state["min_conductivity"])
            backend = "local-python"
        return {"analysis": result, "analysis_error": None, "attempts": attempts,
                "tool_backend": backend}
    except (Exception) as exc:  # convert to explicit state, not a silently substituted result
        return {"analysis": None, "attempts": attempts, "analysis_error":
                f"{type(exc).__name__}: {str(exc)[:180]}",
                "tool_backend": "mcp-stdio" if use_mcp() else "local-python"}


def route_retry(state: ResearchState) -> Literal["analyst", "validator"]:
    return "analyst" if state.get("analysis_error") and state.get("attempts", 0) < 2 else "validator"


def validator(state: ResearchState) -> dict:
    issues = core.validate(state.get("evidence", []), state.get("grounded", False),
                           state.get("analysis"))
    if state.get("analysis_error"):
        issues.append("Analysis tool failed after bounded retries: " + state["analysis_error"])
    return {"issues": issues}


def route_review(state: ResearchState) -> Literal["human_review", "writer"]:
    return "human_review" if state.get("require_review", False) else "writer"


def human_review(state: ResearchState) -> dict:
    decision = interrupt({"reason": "Review requested before final report", "question":
                          state["question"], "issues": state.get("issues", []),
                          "evidence_ids": [e["source_id"] for e in state.get("evidence", [])]})
    approved = bool(isinstance(decision, dict) and decision.get("approved") is True)
    return {"review": "approved" if approved else "rejected"}


async def writer(state: ResearchState) -> dict:
    issues = list(state.get("issues", []))
    if state.get("review") == "rejected":
        issues.append("Human reviewer rejected the draft; no recommendation issued")
    status = "completed_with_warnings" if issues else "completed"
    if state.get("review") == "rejected":
        status = "review_rejected"
    report = core.extractive_report(state["question"], state.get("evidence", []),
                                    state.get("analysis"), issues)
    mode = model_mode()
    if mode == "openai" and status != "review_rejected":
        try:
            generated = await synthesize(state["question"], state.get("evidence", []),
                                         state.get("analysis"))
            valid = core.citations_valid(generated,
                                         {e["source_id"] for e in state.get("evidence", [])})
            if not valid:
                raise ValueError("Model cited unknown source IDs")
            # Append authoritative machine-readable demo label regardless of LLM output.
            report = "**Synthetic demonstration data — not scientific findings.**\n\n" + generated
        except Exception as exc:
            issues.append("LLM unavailable/invalid; fell back to extractive report: "
                          + type(exc).__name__)
            report = core.extractive_report(state["question"], state.get("evidence", []),
                                            state.get("analysis"), issues)
            status = "completed_with_warnings"
            mode = "offline-fallback"
    return {"report": report, "issues": issues, "status": status, "mode": mode}


def build_graph():
    g = StateGraph(ResearchState)
    g.add_node("planner", planner)
    g.add_node("researcher", researcher)
    g.add_node("analyst", analyst)
    g.add_node("validator", validator)
    g.add_node("human_review", human_review)
    g.add_node("writer", writer)
    g.add_edge(START, "planner")
    g.add_edge("planner", "researcher")
    g.add_conditional_edges("researcher", route_analysis)
    g.add_conditional_edges("analyst", route_retry)
    g.add_conditional_edges("validator", route_review)
    g.add_edge("human_review", "writer")
    g.add_edge("writer", END)
    return g.compile(checkpointer=InMemorySaver())
