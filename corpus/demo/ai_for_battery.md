# Agentic literature review for battery research (科研智能体)
DEMO ONLY — synthetic teaching note, not a paper or a patent; no experimental measurements are claimed.
Domain: AI for Science, battery research agent, tools, RAG.
A battery research assistant can decompose a broad technical request into evidence retrieval, parameter extraction, unit normalization, and a comparison table. RAG retrieves relevant document passages before any model synthesis. A separate calculator tool can normalize ionic conductivity units or estimate simple quantities when equations and assumptions are explicit.
Tool calls must validate inputs and capture failures. Citations should point to source documents, and unknown values should remain unknown rather than be guessed. User memory should be separated from source evidence and never silently overwrite the retrieved corpus.
研究要点：材料科研 Agent 通过任务拆解、RAG 证据检索、工具调用、单位换算和带来源报告完成重复工作。模型生成内容不等于实验验证。
Evaluation: Use gold document IDs for retrieval hit rate; judge evidence-grounding separately from linguistic fluency.
