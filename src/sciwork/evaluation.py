"""Offline retrieval evaluation: predefined synthetic queries; no fake accuracy claims."""
from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path
from .config import ROOT
from .core import research


def evaluate(path: Path | None = None) -> dict:
    fixture = path or (ROOT / "data" / "eval_demo.jsonl")
    cases = [json.loads(l) for l in fixture.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not cases:
        raise ValueError("Empty evaluation fixture")
    hits, abstentions, latency_ms = 0, 0, []
    breakdown = []
    for case in cases:
        start = time.perf_counter()
        result = research(case["query"], k=3)
        latency_ms.append((time.perf_counter() - start) * 1000)
        found = {x["source_id"] for x in result["evidence"]}
        expected = set(case["expected_source_ids"])
        hit = bool(expected & found) if expected else not result["grounded"]
        if not expected and not result["grounded"]:
            abstentions += 1
        if hit:
            hits += 1
        breakdown.append({"query": case["query"], "expected": sorted(expected),
                          "retrieved": sorted(found), "pass": hit})
    return {"dataset": "synthetic, author-written; same-source evaluation, not independent",
            "queries": len(cases), "hits_at_3_or_correct_abstentions": hits,
            "hit_or_abstention_rate": round(hits / len(cases), 4),
            "negative_cases_correctly_abstained": abstentions,
            "median_retrieval_latency_ms": round(statistics.median(latency_ms), 3),
            "breakdown": breakdown}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--save", type=Path, help="JSON report output path")
    args = parser.parse_args()
    result = evaluate()
    if args.save:
        args.save.parent.mkdir(parents=True, exist_ok=True)
        args.save.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
