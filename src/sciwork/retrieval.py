"""Transparent, offline BM25 RAG over explicitly attributed source notes.

Demo data are synthetic teaching notes, NOT real scientific papers.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from .config import PAPERS

TOKEN = re.compile(r"[\w.+-]+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    # Include Chinese character bigrams in addition to Latin terms.
    latin = [w.lower() for w in TOKEN.findall(text)]
    zh = re.findall(r"[\u4e00-\u9fff]", text)
    return latin + [zh[i] + zh[i + 1] for i in range(len(zh) - 1)]


@dataclass(frozen=True)
class Evidence:
    source_id: str
    title: str
    excerpt: str
    score: float
    provenance: str

    def as_dict(self) -> dict:
        return {"source_id": self.source_id, "title": self.title,
                "excerpt": self.excerpt, "score": round(self.score, 4),
                "provenance": self.provenance}


class BM25Retriever:
    def __init__(self, path: Path = PAPERS) -> None:
        items = json.loads(path.read_text(encoding="utf-8"))
        if not items or len({x["id"] for x in items}) != len(items):
            raise ValueError("Corpus must contain unique, nonempty source IDs")
        self.docs = items
        self.tokens = [tokenize(x["title"] + " " + x["content"]) for x in items]
        self.tf = [Counter(t) for t in self.tokens]
        self.avglen = sum(map(len, self.tokens)) / len(self.tokens)
        df = Counter(t for words in self.tokens for t in set(words))
        self.idf = {term: math.log(1 + (len(items) - freq + 0.5) / (freq + 0.5))
                    for term, freq in df.items()}

    def search(self, query: str, k: int = 3) -> list[Evidence]:
        if not query.strip() or not (1 <= k <= 10):
            return []
        hits = []
        for doc, tokens, counts in zip(self.docs, self.tokens, self.tf):
            score = 0.0
            for term in set(tokenize(query)):
                tf = counts[term]
                if tf:
                    score += self.idf.get(term, 0) * tf * 2.2 / (
                        tf + 1.2 * (0.25 + 0.75 * len(tokens) / self.avglen))
            if score > 0:
                hits.append(Evidence(doc["id"], doc["title"], doc["content"],
                                     score, doc["provenance"]))
        return sorted(hits, key=lambda h: (-h.score, h.source_id))[:k]


def has_relevant_evidence(query: str, hits: list[Evidence]) -> bool:
    """Basic gate: two shared non-stopword tokens when possible; not a calibrated confidence."""
    q = set(tokenize(query)) - {"what", "is", "the", "and", "compare", "please", "about", "的", "材料"}
    if not q or not hits:
        return False
    return any(len(q & set(tokenize(x.title + " " + x.excerpt))) >= min(2, len(q)) for x in hits)
