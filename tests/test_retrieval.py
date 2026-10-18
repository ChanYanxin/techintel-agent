from sciwork.retrieval import BM25Retriever, has_relevant_evidence
from sciwork.core import plan, research, citations_valid, validate, extractive_report


def test_bm25_ranks_known_document():
    assert BM25Retriever().search("LLZO oxide ceramic")[0].source_id == "SYN-LLZO"


def test_no_results_for_unknown_domain():
    assert BM25Retriever().search("Himalayan snow leopard breeding") == []


def test_retrieval_citation_provenance():
    hits = BM25Retriever().search("sulfide moisture stability")
    assert hits[0].provenance.startswith("Synthetic educational")


def test_grounding_gate():
    assert has_relevant_evidence("LLZO oxide", BM25Retriever().search("LLZO oxide"))
    assert not has_relevant_evidence("unicorn planet", [])


def test_planner_routes_numeric_question():
    result = plan("Screen CSV conductivity >= 0.0004")
    assert result["needs_analysis"] and result["min_conductivity"] == 0.0004


def test_planner_skips_analysis_for_retrieval():
    assert not plan("Tell me about LLZO ceramic densification")["needs_analysis"]


def test_report_stays_extractive_and_labeled():
    e = research("LLZO oxide")
    report = extractive_report("LLZO oxide", e["evidence"], None, [])
    assert "synthetic" in report.lower() and "[SYN-LLZO]" in report


def test_citation_guard_rejects_hallucinated_id():
    assert not citations_valid("According to [SYN-FAKE]", {"SYN-LLZO"})
    assert citations_valid("According to [SYN-LLZO]", {"SYN-LLZO"})


def test_validation_warns_about_noncomparable_temperatures():
    result = validate([], True, {"samples": [{"sample_id": "x"}], "comparable_temperatures": False})
    assert any("temperature" in x.lower() for x in result)
