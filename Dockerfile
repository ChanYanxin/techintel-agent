FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 TECHINTEL_CORPUS_DIR=/app/corpus
WORKDIR /app
COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir .
COPY corpus/ ./corpus/
EXPOSE 8000
CMD ["uvicorn", "techintel.app:app", "--host", "0.0.0.0", "--port", "8000"]
