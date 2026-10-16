from pathlib import Path
import pytest
from techintel.retrieval import KnowledgeIndex, _chunk_text

BASE = Path(__file__).resolve().parents[1]


def index():
    return KnowledgeIndex([BASE / "corpus" / "demo"])


def test_retrieval_returns_correct_doc():
    matches = index().search("SiC MOSFET gate oxide reliability", k=3)
    assert matches
    assert matches[0].doc_id == "sic_power_semiconductor"


def test_no_result_on_irrelevant_question():
    assert index().search("What is the capital of Uruguay?") == []


def test_document_not_found():
    assert index().get_document("../../etc/passwd")["error"] == "document_not_found"


def test_empty_corpus(tmp_path):
    with pytest.raises(ValueError, match="No readable text"):
        KnowledgeIndex([tmp_path])


def test_chunk_overlap():
    chunks = _chunk_text("x" * 2000, size=500, overlap=100)
    assert len(chunks) > 2
    assert all(chunks)
