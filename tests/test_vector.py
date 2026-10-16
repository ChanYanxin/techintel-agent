import numpy as np
from pathlib import Path
from techintel.retrieval import KnowledgeIndex
from techintel.vector import VectorIndex

BASE = Path(__file__).resolve().parents[1]


def test_vector_backend_with_injected_mock_embeddings():
    corpus = KnowledgeIndex([BASE / "corpus" / "demo"])
    def mock_embed(texts):
        # A deliberately simplistic deterministic fake backend for unit testing;
        # DOES NOT prove semantic quality or live API interoperability.
        return np.array([[1.0, 0.0] if "SiC" in t else [0.0, 1.0] for t in texts], dtype=np.float32)
    idx = VectorIndex(corpus, mock_embed)
    hits = idx.search("SiC semiconductor MOSFET", k=5, min_score=.5)
    assert hits[0].doc_id == "sic_power_semiconductor"
    assert hits[0].score == 1.0
