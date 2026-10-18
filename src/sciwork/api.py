"""REST + SSE entrypoints. InMemorySaver is single-process dev only."""
from __future__ import annotations

import json
import uuid
from functools import lru_cache
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

app = FastAPI(title="Scientific Research Copilot", version="0.1.0",
              description="Synthetic-data MVP. No real scientific recommendations.")


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    thread_id: str | None = Field(default=None, max_length=96)
    require_review: bool = False


class ReviewRequest(BaseModel):
    approved: bool


@lru_cache

def graph():
    from .graph import build_graph
    return build_graph()


def _config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}, "recursion_limit": 12}


def _summary(thread_id: str, state: dict) -> dict:
    if "__interrupt__" in state:
        interruption = state["__interrupt__"]
        return {"thread_id": thread_id, "status": "awaiting_review",
                "review_request": interruption[0].value if interruption else {}}
    return {"thread_id": thread_id, "status": state.get("status", "unknown"),
            "report": state.get("report"), "evidence": state.get("evidence", []),
            "analysis": state.get("analysis"), "warnings": state.get("issues", []),
            "mode": state.get("mode"), "tool_backend": state.get("tool_backend", "none")}


@app.get("/healthz")
def health():
    return {"status": "ok", "service": "scientific-research-copilot", "version": "0.1.0"}


@app.post("/chat")
async def chat(payload: ChatRequest):
    thread_id = payload.thread_id or str(uuid.uuid4())
    # Isolation: each chat invocation is a new thread; existing IDs are not overwritten by default.
    if payload.thread_id:
        current = await graph().aget_state(_config(thread_id))
        if current.values:
            raise HTTPException(409, "Thread already exists; use /resume for pending reviews")
    inputs = {"question": payload.question, "require_review": payload.require_review,
              "attempts": 0, "review": ""}
    try:
        state = await graph().ainvoke(inputs, config=_config(thread_id))
    except Exception as exc:
        raise HTTPException(503, f"Workflow failed: {type(exc).__name__}") from exc
    return _summary(thread_id, state)


@app.post("/chat/stream")
async def chat_stream(payload: ChatRequest):
    thread_id = payload.thread_id or str(uuid.uuid4())
    if payload.thread_id:
        current = await graph().aget_state(_config(thread_id))
        if current.values:
            raise HTTPException(409, "Thread already exists")

    async def events():
        inputs = {"question": payload.question, "require_review": payload.require_review,
                  "attempts": 0, "review": ""}
        try:
            async for chunk in graph().astream(inputs, config=_config(thread_id),
                                               stream_mode="updates"):
                yield "event: node\ndata: " + json.dumps(chunk, ensure_ascii=False, default=str) + "\n\n"
            snapshot = await graph().aget_state(_config(thread_id))
            status = "awaiting_review" if snapshot.interrupts else snapshot.values.get("status", "unknown")
            yield "event: complete\ndata: " + json.dumps(
                {"thread_id": thread_id, "status": status}, ensure_ascii=False) + "\n\n"
        except Exception as exc:
            yield "event: error\ndata: " + json.dumps({"error": type(exc).__name__}) + "\n\n"
    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/runs/{thread_id}/resume")
async def resume(thread_id: str, payload: ReviewRequest):
    from langgraph.types import Command
    snapshot = await graph().aget_state(_config(thread_id))
    if not snapshot.interrupts:
        raise HTTPException(409, "No review is pending for this thread")
    result = await graph().ainvoke(Command(resume={"approved": payload.approved}),
                                  config=_config(thread_id))
    return _summary(thread_id, result)

@app.get("/demo", include_in_schema=False)
def demo():
    from pathlib import Path
    from fastapi.responses import FileResponse
    return FileResponse(Path(__file__).with_name("static") / "index.html")
