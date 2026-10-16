"""Optional *actual embedding* retrieval experiment, separate from offline TF-IDF pipeline.

Needs OPENAI_API_KEY or an injected embedding callable for tests. This module is
NOT exercised by the offline benchmark unless explicitly run.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
from typing import Callable
import numpy as np

from .retrieval import KnowledgeIndex, Hit
from .app import get_agent


def openai_embed(texts: list[str]) -> np.ndarray:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Set OPENAI_API_KEY to use paid remote embeddings")
    from openai import OpenAI
    client = OpenAI(timeout=30, max_retries=1)
    model = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
    response = client.embeddings.create(model=model, input=texts, encoding_format="float")
    ordered = sorted(response.data, key=lambda x: x.index)
    return np.asarray([x.embedding for x in ordered], dtype=np.float32)


def _unit_norm(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float32)
    norm = np.linalg.norm(x, axis=-1, keepdims=True)
    return x / np.maximum(norm, 1e-12)


class VectorIndex:
    """In-memory cosine similarity search for small corpora; not a vector database."""
    def __init__(self, index: KnowledgeIndex, embed: Callable[[list[str]], np.ndarray] = openai_embed):
        self.index = index
        self.embed = embed
        vectors = np.asarray(embed([c.text for c in index.chunks]), dtype=np.float32)
        if vectors.ndim != 2 or vectors.shape[0] != len(index.chunks):
            raise ValueError("Embedding backend returned an invalid array")
        self.vectors = _unit_norm(vectors)

    def search(self, query: str, k: int = 3, min_score: float = 0.28) -> list[Hit]:
        if not query.strip():
            return []
        q_vec = np.asarray(self.embed([query]), dtype=np.float32)
        if q_vec.shape != (1, self.vectors.shape[1]):
            raise ValueError("Query embedding dimension mismatch")
        scores = self.vectors @ _unit_norm(q_vec)[0]
        out = []
        for i in np.argsort(-scores):
            if scores[i] < min_score:
                break
            chunk = self.index.chunks[i]
            out.append(Hit(chunk.id, chunk.doc_id, chunk.title, chunk.text[:750],
                           round(float(scores[i]), 5), chunk.path))
            if len(out) >= k:
                break
        return out


def main():
    parser = argparse.ArgumentParser(description="Paid embedding-based RAG experiment")
    parser.add_argument("query")
    parser.add_argument("--min-score", type=float, default=0.28)
    args = parser.parse_args()
    index = VectorIndex(get_agent().index)
    print(json.dumps([h.to_dict() for h in index.search(args.query, min_score=args.min_score)],
                     indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
