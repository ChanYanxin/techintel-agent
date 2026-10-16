"""Deterministic hybrid lexical RAG. This demo is NOT embedding-based semantic search."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import math
import re
from typing import Iterable

from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS


@dataclass(frozen=True)
class Chunk:
    id: str
    doc_id: str
    title: str
    text: str
    path: str


@dataclass(frozen=True)
class Hit:
    id: str
    doc_id: str
    title: str
    snippet: str
    score: float
    path: str

    def to_dict(self) -> dict:
        return asdict(self)


def _chunk_text(text: str, *, size: int = 1400, overlap: int = 180) -> list[str]:
    """Char-based chunks with overlap. Avoid empty chunks and infinite loops."""
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        if end < len(text):
            boundary = text.rfind(". ", start + size // 2, end)
            if boundary > start:
                end = boundary + 1
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)
    return chunks


def _extract(path: Path) -> str:
    if path.suffix.lower() in {".md", ".txt"}:
        return path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("PDF support requires: pip install pypdf") from exc
        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return ""


class KnowledgeIndex:
    def __init__(self, corpus_dirs: Iterable[str | Path]):
        self.chunks: list[Chunk] = []
        seen_docs: set[str] = set()
        for directory in corpus_dirs:
            directory = Path(directory)
            if not directory.exists():
                continue
            for path in sorted(directory.rglob("*")):
                if not path.is_file() or path.suffix.lower() not in {".md", ".txt", ".pdf"}:
                    continue
                doc_id = path.stem.lower().replace(" ", "_")
                if doc_id in seen_docs:
                    raise ValueError(f"Duplicate document ID: {doc_id}")
                seen_docs.add(doc_id)
                raw = _extract(path)
                if not raw.strip():
                    continue
                title = (raw.strip().splitlines()[0].strip("# ") or doc_id)[:160]
                for idx, content in enumerate(_chunk_text(raw)):
                    self.chunks.append(Chunk(
                        id=f"{doc_id}#c{idx}", doc_id=doc_id, title=title,
                        text=content, path=str(path)
                    ))
        if not self.chunks:
            raise ValueError("No readable text in corpus. Add .md/.txt or text-extractable .pdf files.")
        text = [chunk.text for chunk in self.chunks]
        self.word = TfidfVectorizer(lowercase=True, stop_words=list(ENGLISH_STOP_WORDS | {"does", "many", "would", "could", "might"}), ngram_range=(1, 2),
                                    token_pattern=r"(?u)\b[^\W\d_][\w]*\b", sublinear_tf=True)
        self.char = TfidfVectorizer(analyzer="char", lowercase=True, ngram_range=(2, 4), sublinear_tf=True)
        self.word_x = self.word.fit_transform(text)
        self.char_x = self.char.fit_transform(text)
        self.docs = {}
        for chunk in self.chunks:
            self.docs.setdefault(chunk.doc_id, []).append(chunk)

    def search(self, query: str, k: int = 3, mode: str = "hybrid") -> list[Hit]:
        if not query.strip():
            return []
        if mode not in {"hybrid", "word"}:
            raise ValueError("mode must be 'hybrid' or 'word'")
        q_word = self.word.transform([query])
        ws = (self.word_x @ q_word.T).toarray().ravel()
        if mode == "word":
            scores = ws
        else:
            q_char = self.char.transform([query])
            cs = (self.char_x @ q_char.T).toarray().ravel()
            # CJK queries are not segmented by the word vectorizer, so prefer
            # character n-grams. English queries require a lexical-word match
            # to avoid accepting generic shared character sequences.
            is_cjk = bool(re.search(r"[\u3400-\u9fff]", query))
            scores = (0.20 * ws + 0.80 * cs) if is_cjk else (0.70 * ws + 0.30 * cs)
            if not is_cjk:
                scores[ws < 0.045] = 0
        order = sorted(range(len(scores)), key=lambda i: (-scores[i], i))
        hits: list[Hit] = []
        for i in order:
            if scores[i] < 0.075:  # conservative retrieval threshold, adjust with eval data
                break
            c = self.chunks[i]
            hits.append(Hit(c.id, c.doc_id, c.title, c.text[:750],
                            round(float(scores[i]), 5), c.path))
            if len(hits) >= k:
                break
        return hits

    def get_document(self, doc_id: str) -> dict:
        if doc_id not in self.docs:
            return {"error": "document_not_found", "doc_id": doc_id}
        cs = self.docs[doc_id]
        return {"doc_id": doc_id, "title": cs[0].title,
                "text": "\n".join(c.text for c in cs)[:6500],
                "path": cs[0].path}

    @property
    def document_count(self) -> int:
        return len(self.docs)
