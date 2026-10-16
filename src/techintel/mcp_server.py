"""MCP v2 tool server. Requires: pip install -e '.[mcp]' (not needed for API/CLI)."""
from .app import get_agent


def main():
    try:
        from mcp.server import MCPServer  # official MCP Python SDK v2
    except ImportError as exc:
        raise SystemExit("Install the MCP SDK: pip install -e '.[mcp]'") from exc
    mcp = MCPServer("TechIntel Research Tools")

    @mcp.tool()
    def search_research(query: str, k: int = 3) -> list[dict]:
        """Retrieve cited snippets from local technical research documents."""
        return [h.to_dict() for h in get_agent().index.search(query, min(max(k, 1), 5))]

    @mcp.tool()
    def read_research_document(doc_id: str) -> dict:
        """Read research document by identifier from search results."""
        return get_agent().index.get_document(doc_id)

    @mcp.tool()
    def remember_research_note(session_id: str, note: str) -> dict:
        """Save a session-scoped research note."""
        return get_agent().memory.add(session_id, note)

    mcp.run()  # stdio


if __name__ == "__main__":
    main()
