# LLM tools for electronic design automation (EDA 智能体)
DEMO ONLY — synthetic teaching note, not a paper or a patent; no experimental measurements are claimed.
Domain: electronic design automation, RTL, circuit design, EDA agent.
An EDA assistant can translate an engineer's request into constrained tool actions such as querying a netlist, reading design-rule reports or launching an existing synthesis script. The language model is an orchestrator, not the EDA compiler or formal verification engine.
Tool input validation, sandboxing, artifact paths, timeout handling and user confirmation before destructive operations are important. Human approval should be required before changing source RTL or tape-out-critical settings.
研究要点：EDA Agent 可以调用 RTL 分析、综合与静态时序工具，但不能把大模型解释当成形式验证结果；工具权限、超时与设计规则检查同样重要。
Evaluation: Test tool-choice accuracy and whether the assistant refuses unsupported timing claims.
