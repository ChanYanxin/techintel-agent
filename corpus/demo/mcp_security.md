# MCP tool contracts and prompt injection defenses (MCP 安全)
DEMO ONLY — synthetic teaching note, not a paper or a patent; no experimental measurements are claimed.
Domain: Model Context Protocol, MCP server, tool calling, security.
Model Context Protocol (MCP) offers a standardized interface for clients to discover and call tools. Each tool should have a clear name, typed parameters, bounded outputs and predictable error semantics. A local stdio server can expose search and read operations to a compliant host.
Prompt injection is possible when an external document contains instructions such as "ignore previous constraints". Retrieved document text is untrusted data; never execute it as a command, reveal API keys, or grant the document authority over the system prompt.
研究要点：MCP 将工具以标准协议暴露给客户端。工具的输入校验、最小权限、异常处理、提示词注入防护和可追踪调用是工程核心。
Research validation: Include tests for malicious document instructions, unauthorized tools and invalid inputs.
