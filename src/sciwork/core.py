"""Testable application services backing separate LangGraph agent nodes."""
from __future__ import annotations

import re
from .analysis import analyze_experiments
from .retrieval import BM25Retriever, has_relevant_evidence

RETRIEVER = BM25Retriever()


def plan(question: str) -> dict:
    if not question.strip():
        raise ValueError("Question must not be empty")
    normalized = question.lower()
    # Grounded rule-based planner is deliberate for reproducibility; LLM synthesis is optional.
    needs_analysis = any(word in normalized for word in (
        "csv", "experiment", "conductivity", "rank", "compare", "screen",
        "实验", "电导", "筛选", "对比", "数据", "排序"))
    threshold = 0.0
    found = re.search(r"(?:>=|≥|at least)\s*(\d+(?:\.\d+)?(?:e[-+]?\d+)?)", normalized)
    if found:
        threshold = float(found.group(1))
    return {"needs_analysis": needs_analysis, "min_conductivity": threshold,
            "plan": ["retrieve_evidence", *( ["analyze_experiments"] if needs_analysis else []),
                     "validate", "write_report"]}


def research(question: str, k: int = 3) -> dict:
    hits = RETRIEVER.search(question, k)
    return {"evidence": [x.as_dict() for x in hits],
            "grounded": has_relevant_evidence(question, hits)}


def validate(evidence: list[dict], grounded: bool, analysis: dict | None) -> list[str]:
    issues = []
    if not grounded:
        issues.append("Insufficient lexical evidence; outside the demo corpus")
    if analysis is not None and not analysis.get("comparable_temperatures", False):
        issues.append("Measurements span different temperatures; raw conductivity ranking may mislead")
    if analysis is not None and not analysis.get("samples"):
        issues.append("No experimental samples meet the requested filter")
    if len({e["source_id"] for e in evidence}) != len(evidence):
        issues.append("Duplicate citation identifiers")
    return issues


def extractive_report(question: str, evidence: list[dict], analysis: dict | None,
                      issues: list[str]) -> str:
    out = ["# Scientific Research Copilot — offline evidence report",
           "**DEMO ONLY:** All included paper notes and CSV measurements are synthetic.",
           "This is an extractive preview, not an LLM-generated scientific conclusion.",
           f"## Question\n{question}"]
    if evidence:
        out.append("## Retrieved evidence (not independently verified)")
        out.extend(f"- [{e['source_id']}] {e['title']}: {e['excerpt']}" for e in evidence)
    else:
        out.append("No matching sources. Cannot answer from the available corpus.")
    if analysis is not None:
        out.append(f"## Experiment tool output\n{analysis['total_matching']} synthetic records match.")
        for s in analysis["samples"][:10]:
            out.append(f"- {s['sample_id']} {s['material']}: {s['conductivity_s_cm']:.3g} S/cm "
                       f"at {s['temperature_c']:g} °C")
    if issues:
        out.append("## Warnings")
        out.extend(f"- {i}" for i in issues)
    out.append("## Interpretation\nNo scientific recommendation is asserted by this demo.")
    return "\n\n".join(out)


def citations_valid(report: str, allowed_ids: set[str]) -> bool:
    cited = set(re.findall(r"\[([A-Z][A-Z0-9_-]{2,})\]", report))
    return cited <= allowed_ids and (not allowed_ids or bool(cited))
