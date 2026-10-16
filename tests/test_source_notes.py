from pathlib import Path
from techintel.retrieval import KnowledgeIndex

BASE = Path(__file__).resolve().parents[1]


def test_real_publication_source_notes_are_separate_and_retrievable():
    idx = KnowledgeIndex([BASE / "corpus" / "source_notes"])
    assert idx.document_count == 4
    result = idx.search("AutoSEE 226 publications solid electrolyte GPT-4o", k=3)
    assert result[0].doc_id == "real_autosee_2026"
    article = idx.get_document("real_autosee_2026")
    assert "10.1021/acsenergylett.6c00020" in article["text"]
    assert "NOT the paper full text" in article["text"]
