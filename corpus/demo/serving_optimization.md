# LLM serving latency and deployment (推理服务部署)
DEMO ONLY — synthetic teaching note, not a paper or a patent; no experimental measurements are claimed.
Domain: LLM inference, serving, GPU, batching, Docker FastAPI.
Model inference latency can be decomposed into network overhead, token generation, retrieval and tool execution. Continuous batching and KV caching can improve throughput on suitable GPU serving stacks, but optimization must be measured under realistic concurrency and input lengths.
FastAPI can expose validated request and response schemas. Docker packages a repeatable environment, but building an image locally is not the same as deploying to production. A production service also needs authentication, observability, rate limiting and operational monitoring.
研究要点：推理优化需测量延迟、吞吐、token 使用量、并发与显存，而不是仅报告一次运行速度。FastAPI 提供接口，Docker 提供容器镜像，不自动等于线上部署。
Research validation: Compare cold vs warm latency, p50 and p95, with fixed model and request distribution.
