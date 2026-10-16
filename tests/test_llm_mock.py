"""Simulated model tool loop. Does not contact OpenAI or establish API interoperability."""
from pathlib import Path
from types import SimpleNamespace
from techintel.agent import TechIntelAgent
from techintel.retrieval import KnowledgeIndex
import sys

BASE = Path(__file__).resolve().parents[1]


def test_llm_tool_call_loop_with_mock_client(monkeypatch):
    class FakeResponse:
        def __init__(self, output, output_text=""):
            self.output = output
            self.output_text = output_text

    class FakeResponses:
        def __init__(self):
            self.n = 0
        def create(self, **kwargs):
            self.n += 1
            if self.n == 1:
                return FakeResponse([SimpleNamespace(
                    type="function_call", name="search_knowledge", call_id="call_1",
                    arguments='{"query":"LLZO ceramic oxide sintering","k":3}'
                )])
            assert any(isinstance(x, dict) and x.get("call_id") == "call_1" for x in kwargs["input"])
            return FakeResponse([], "LLZO processing requires attention to sintering. [source:oxide_electrolyte]")

    fake_responses = FakeResponses()
    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.responses = fake_responses
    monkeypatch.setenv("OPENAI_API_KEY", "FAKE_KEY_FOR_TEST_ONLY")
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=FakeOpenAI))
    agent = TechIntelAgent(KnowledgeIndex([BASE / "corpus" / "demo"]))
    out = agent.run("Compare LLZO processing", mode="llm")
    assert fake_responses.n == 2
    assert out.sources == ["oxide_electrolyte"]
    assert not out.abstained
    assert out.trace[0]["tool"] == "search_knowledge"


def test_reject_hallucinated_citation_with_mock_client(monkeypatch):
    class FakeResponses:
        def create(self, **kwargs):
            return SimpleNamespace(output=[], output_text="Evidence: [source:invented_patent_999]")
    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.responses = FakeResponses()
    monkeypatch.setenv("OPENAI_API_KEY", "FAKE_KEY_FOR_TEST_ONLY")
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=FakeOpenAI))
    agent = TechIntelAgent(KnowledgeIndex([BASE / "corpus" / "demo"]))
    out = agent.run("Please answer", mode="llm")
    assert out.abstained
    assert out.sources == []
