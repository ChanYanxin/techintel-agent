"""Opt-in OpenAI-compatible LLM report synthesis, with citations verified elsewhere."""
from __future__ import annotations

import os
import httpx


async def synthesize(question: str, evidence: list[dict], analysis: dict | None) -> str:
    key = os.getenv("SCIW_OPENAI_API_KEY")
    if not key:
        raise RuntimeError("SCIW_OPENAI_API_KEY is required when SCIW_MODEL_MODE=openai")
    base = os.getenv("SCIW_OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    if not base.startswith("https://") and not base.startswith("http://localhost"):
        raise ValueError("Only HTTPS or localhost model API URLs are allowed")
    payload = {
        "model": os.getenv("SCIW_OPENAI_MODEL", "gpt-4.1-mini"),
        "temperature": 0,
        "messages": [
            {"role": "system", "content": "You are a cautious scientific analysis assistant. "
             "Use only supplied evidence and tool output. Do not claim synthetic records are real. "
             "Cite every factual claim using the exact [SOURCE_ID] tokens. If evidence is missing, "
             "say it is unknown. Never present the ranking as scientifically validated."},
            {"role": "user", "content": f"Question: {question}\nEvidence: {evidence}\nData: {analysis}"},
        ],
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(base + "/chat/completions", json=payload,
                                     headers={"Authorization": f"Bearer {key}"})
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
