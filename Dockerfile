FROM node:22-bookworm-slim AS mcpbuild
WORKDIR /mcp
COPY mcp-server/package.json mcp-server/tsconfig.json ./
COPY mcp-server/src ./src
RUN npm install --no-audit --no-fund && npm run build

FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY src/ ./src/
COPY data/ ./data/
COPY --from=mcpbuild /mcp /app/mcp-server
RUN pip install --no-cache-dir . && useradd -m -u 10001 sciwork
ENV SCIW_PROJECT_ROOT=/app SCIW_MODEL_MODE=offline SCIW_USE_MCP=false PYTHONUNBUFFERED=1
USER sciwork
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)" || exit 1
CMD ["uvicorn", "sciwork.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
