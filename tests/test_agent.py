from pathlib import Path
from techintel.agent import TechIntelAgent
from techintel.retrieval import KnowledgeIndex
from techintel.memory import SessionMemory

BASE = Path(__file__).resolve().parents[1]


def agent():
    return TechIntelAgent(KnowledgeIndex([BASE / "corpus" / "demo"]), SessionMemory())


def test_offline_has_grounded_citations():
    output = agent().run("PEO polymer electrolyte flexibility")
    assert not output.abstained
    assert output.sources
    assert all(f"[source:{doc_id}]" in output.answer for doc_id in output.sources)
    assert output.trace[0]["tool"] == "search_knowledge"


def test_abstain_on_out_of_domain():
    output = agent().run("What is the capital of Uruguay?")
    assert output.abstained
    assert output.sources == []


def test_memory_separated_between_sessions():
    a = agent()
    a.memory.add("alice", "Interested in solid electrolyte safety")
    assert a.memory.recent("bob") == []
    assert a.memory.recent("alice") == ["Interested in solid electrolyte safety"]


def test_tool_whitelist_and_missing_doc():
    a = agent()
    assert a._call("run_shell", {}, "demo") == {"error": "unknown_tool"}
    assert a._call("get_document", {"doc_id": "fake"}, "demo")["error"] == "document_not_found"


def test_unconfigured_llm_fails_explicitly(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    try:
        agent().run("sulfide", mode="llm")
    except RuntimeError as exc:
        assert "OPENAI_API_KEY" in str(exc)
    else:
        assert False, "should require an explicit API key"
