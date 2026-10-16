"""Reproducible retrieval benchmark, with no LLM claims and no benchmark fabrication."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .app import get_agent

BASE = Path(__file__).resolve().parents[2]


def evaluate(gold_path: str | Path = BASE / "evals" / "gold.jsonl") -> dict:
    index = get_agent().index
    cases = [json.loads(line) for line in Path(gold_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    report: dict = {"dataset": "synthetic hand-authored demo queries", "corpus_documents": index.document_count,
                    "total_queries": len(cases), "answerable_queries": sum(c["answerable"] for c in cases),
                    "unanswerable_queries": sum(not c["answerable"] for c in cases), "methods": {}}
    for method in ("word", "hybrid"):
        hits, mrr, abstain_correct, unanswered, failures = 0, 0.0, 0, 0, []
        for case in cases:
            result = index.search(case["query"], k=3, mode=method)
            retrieved = [h.doc_id for h in result]
            if case["answerable"]:
                gold = set(case["gold_docs"])
                ranks = [idx + 1 for idx, doc in enumerate(retrieved) if doc in gold]
                if ranks:
                    hits += 1
                    mrr += 1 / min(ranks)
                else:
                    failures.append({"query": case["query"], "retrieved": retrieved,
                                     "gold": case["gold_docs"]})
            else:
                unanswered += 1
                if not retrieved:
                    abstain_correct += 1
                else:
                    failures.append({"query": case["query"], "retrieved": retrieved,
                                     "gold": []})
        n_answerable = sum(c["answerable"] for c in cases)
        report["methods"][method] = {
            "hit_at_3": round(hits / n_answerable, 4),
            "mrr": round(mrr / n_answerable, 4),
            "correct_abstention_rate": round(abstain_correct / unanswered, 4) if unanswered else None,
            "failures": failures,
        }
    report["limitations"] = [
        "This is a small synthetic corpus with manually-authored benchmark questions.",
        "Hybrid is word + character TF-IDF, NOT dense embedding retrieval or reranking.",
        "Metrics evaluate retrieval only, NOT factual answer quality or real production performance.",
        "No baseline or improvement claim should be made until numbers are inspected."
    ]
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--save", help="write JSON metrics report to path")
    args = parser.parse_args()
    report = evaluate()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if args.save:
        path = Path(args.save)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
