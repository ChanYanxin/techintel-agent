"""Real MCP stdio client; fails visibly when tool or server is unavailable."""
from __future__ import annotations

import json
import os
from pathlib import Path
from .config import ROOT, experiments_path


async def analyze_via_mcp(min_conductivity: float) -> dict:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    server_js = ROOT / "mcp-server" / "dist" / "index.js"
    if not server_js.exists():
        raise RuntimeError("MCP server not built. Run: cd mcp-server && npm install && npm run build")
    params = StdioServerParameters(command="node", args=[str(server_js)],
                                   env={**os.environ, "SCIW_EXPERIMENTS_CSV": str(experiments_path())})
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("analyze_experiments", {"min_conductivity": min_conductivity})
            if result.isError:
                raise RuntimeError("MCP tool returned an error")
            for item in result.content:
                if item.type == "text":
                    data = json.loads(item.text)
                    if isinstance(data, dict) and "samples" in data:
                        return data
            raise ValueError("MCP tool returned no structured experiment data")
