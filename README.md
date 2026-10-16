# TechIntel Agent · Agent/RAG/MCP 工程展示项目

**面向研发人员的专业技术情报辅助工具**：对研究资料检索并返回出处，提供文档工具、会话笔记、API、MCP Server、可复现评测。用于 Agent / LLM 应用算法工程师岗位展示。

> **真实性边界**：`corpus/demo` 内 **12 篇材料是人工合成教学笔记**，不是论文、专利、业务数据或经过实证的结果。当前经过自动化测试的核心能力是本地 TF-IDF 混合检索、离线证据预览、引用 ID、SQL memory 和 FastAPI；LLM 远程推理、MCP 客户端和 Docker runtime 要在你自己的环境中连接验证。`corpus/source_notes` 另有 **4 篇真实出版物的人工转述摘要**（包含可核验 URL，不是论文全文）。**没有生产上线记录。**

## 1. 五分钟本地运行（macOS、Windows、Linux）

```bash
# 下载本对话提供的 ZIP，解压到某个文件夹后：
cd techintel-agent
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1
pip install -e '.[dev]'
pytest -q
python -m techintel.evaluation --save results/metrics.json
techintel '硫化物电解质为什么对湿度敏感？'
uvicorn techintel.app:app --reload
```

浏览器打开 **http://127.0.0.1:8000/docs** （交互式 API 文档），试用：

```json
POST /ask
{"query":"LLZO 氧化物固态电解质的加工挑战是什么？", "mode":"offline", "session_id":"interview"}
```

响应有 `answer`、`sources`、`evidence`、`trace`、`latency_ms` 和 `abstained`。离线模式是**原文证据摘录**，不是 LLM 生成的答案。

也可以验证记忆（独立 session）：

```json
POST /memory
{"session_id":"interview", "note":"User wants to compare LLZO and sulfides"}
```

随后 `GET /memory/interview` 查询。默认内存型 SQLite，重启进程丢失；想持久化设置 `TECHINTEL_MEMORY_DB=./notes.sqlite`（切勿上传敏感内容）。

## 2. 技术架构与功能范围

```
Client (CLI / REST / optional MCP host)
      │
FastAPI / Agent Orchestrator
      ├── offline: retrieve → cite → extractive evidence preview
      └── llm: Responses API → model-selected tools → citation ID guard
                    │
             tool whitelist
              ├─ search_knowledge → word+char TF-IDF chunks
              ├─ get_document → local MD/TXT/text-PDF
              ├─ save_memory → session SQLite
              └─ recall_memory

Optional: VectorIndex uses remote text-embedding-3-small + cosine similarity,
          separate experimental path, not part of offline benchmark.
MCP v2: exposes search, read, note tools via stdio to compatible hosts.
```

See [design decisions](docs/ARCHITECTURE.md), [Interview guide](docs/INTERVIEW_GUIDE_CN.md), [24-hour SOP](docs/SOP_24H_CN.md), [CV bullets](docs/RESUME_BULLETS_CN.md), [Skill specification](skills/technical-intel/SKILL.md).

**技术术语准确性**：当前混合检索是 TF-IDF word + character n-gram，不是 embedding-based hybrid search，也没有 cross-encoder reranker。`vector.py` 提供真实 embedding API 可选实现，但离线演示不需要 Key。

## 3. 测评：基线对照（仅 synthetic demo）

本仓库默认加载 16 份资料（12 篇 synthetic + 4 篇 source-attributed paper notes），有 20 道人工撰写测试题：16 个可回答、4 个知识库外问题。比较 `word` 与 `hybrid` 检索：

| Retriever | Hit@3 / 16 | MRR / 16 | Correct abstention / 4 |
|---|---:|---:|---:|
| word-only TF-IDF | 0.75 | 0.75 | 1.00 |
| word + character TF-IDF | **1.00** | **1.00** | **1.00** |

**这不是 LLM 答案正确率**。问题由项目作者按自制文档编写，同源偏差显著。结果主要用于保证工程管道正常运转、观察中文词级检索失效；不能拿去宣称“真实文献检索达到 100%”。完整数值和失败案例在 `results/metrics.json`，可重新执行评价脚本核对。

下一阶段须：替换真实且可合法处理的论文/专利资料，建立独立标注的 50–100 条问题；在相同语料和 splits 上比较 lexical、embedding、rerank；增加基于证据的 claim-level answer evaluation。

## 4. 使用自己的真实资料

1. 把 `.md` / `.txt` / **可提取文字**的 `.pdf` 放入 `corpus/your_docs/`，原始数据不会随 Git 自动上传（默认被 `.gitignore` 忽略）。
2. 保证文件名在 demo/source_notes/your_docs 三个目录内全局唯一，文件名 stem 用作 `doc_id`。可用 OpenAlex/Crossref/论文原文元数据人工登记真实出处（此项目并未自动校验 DOI）。
3. 重启服务重新建立索引，然后执行 `/documents` 检查是否加载成功。
4. 在 `evals/gold.jsonl` 添加提问与 gold doc IDs，严禁把生成答案当作人工金标。
5. 对扫描版 PDF、表格、公式必须人工验证文本提取。此项目不做 OCR。

## 5. 开启真实 LLM 工具调用（可选，按 API 计费）

```bash
# macOS / Linux; Windows 也可使用 PowerShell 的 $env:OPENAI_API_KEY=...
export OPENAI_API_KEY='YOUR_API_KEY'
export OPENAI_MODEL='gpt-5.4-mini'
techintel 'Compare sulfide and oxide electrolytes using tool evidence' --mode llm
```

真实 LLM 模式包含模型驱动 function calling 循环。采用 OpenAI **Responses API**，调用 `search_knowledge`、`get_document`、`save_memory`、`recall_memory` 等 allowlisted 工具，上限 5 轮，并验证最终 `[source:doc_id]` 是否属于检索证据。**验证 ID 是存在性检查，不代表所引用内容在事实上支持该断言**。

公开 API/Model 文档：[Responses function calling](https://developers.openai.com/api/docs/guides/function-calling)、[Embedding](https://developers.openai.com/api/docs/guides/embeddings)。

## 6. 向量检索实验（可选，按 API 计费）

```bash
export OPENAI_API_KEY='YOUR_API_KEY'
python -m techintel.vector 'LLZO ceramic grain boundary resistance'
```

该实验使用 `text-embedding-3-small` 产生真实密集向量，在内存中执行余弦相似度检索。它不是 FAISS、Chroma 或 Milvus 向量数据库，且目前未用真实 API Key 进行网络端到端测试。可以通过 `tests/test_vector.py` 的假 embedding backend 查看向量相似度和排序逻辑；这个 mock 测试不证明语义搜索质量。

## 7. MCP tool server（可选）

```bash
pip install -e '.[mcp]'
python -m techintel.mcp_server
```

使用官方 MCP Python SDK **2.x**（`from mcp.server import MCPServer`）。通过 stdio 向兼容 MCP host 暴露 `search_research`、`read_research_document`、`remember_research_note`。启动后终端看起来停住是正常的——它在等待 MCP 客户端握手。可使用 [MCP Inspector](https://github.com/modelcontextprotocol/inspector) 执行 tool smoke test，保留真实截屏。此环境未对外部 MCP 客户端完成握手验证。

## 8. Docker (有 Docker 才能实际验证)

```bash
docker build -t techintel-agent:demo .
docker run --rm -p 8000:8000 techintel-agent:demo
# open http://localhost:8000/docs
```

Dockerfile 定义构建流程，**不等于生产上线**。真实上线需补鉴权、会话隔离、审计、访问控制、模型密钥管理、OpenTelemetry、限流和监控。

## 9. 项目目录

```
techintel-agent/
├── src/techintel/agent.py       # fixed offline flow + real LLM tool-call loop
├── src/techintel/retrieval.py   # chunking + bilingual TF-IDF
├── src/techintel/vector.py      # optional paid embedding retrieval
├── src/techintel/memory.py      # session SQLite memory
├── src/techintel/app.py         # FastAPI + OpenAPI
├── src/techintel/mcp_server.py  # optional MCP v2 server
├── src/techintel/evaluation.py  # Hit@3 / MRR / OOD
├── tests/                      # deterministic automated tests
├── corpus/demo/                # 12 synthetic teaching docs (NOT real papers)
├── corpus/source_notes/        # 4 paraphrased published-paper source notes
├── corpus/your_docs/           # untracked user-supplied documents
├── evals/gold.jsonl            # 20 author-written evaluation queries
├── results/metrics.json        # reproducible demo numbers
├── skills/technical-intel/     # task-specific skill instruction
├── docs/                       # architecture / CV / interview / SOP
├── .github/workflows/ci.yml
└── Dockerfile
```

## 10. 项目边界与求职诚信

- This repository is an **educational, independently reproducible MVP**, not a production system.
- If you use its bullets on your CV, **run it yourself and be prepared to explain the code and limitations**.
- No real patents were searched or validated; no DOI authenticity, patent claims or legal risk analysis is asserted.
- No online business customers, paid users or deployed SLA.

**相关官方资料**：[MCP Python SDK](https://py.sdk.modelcontextprotocol.io/) · [FastAPI Docker](https://fastapi.tiangolo.com/deployment/docker/) · [Ragas evaluation](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/)
