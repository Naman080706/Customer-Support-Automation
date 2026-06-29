"""Task 6 — RAG (Retrieval-Augmented Generation) pipeline.

Loads the four knowledge-base documents, splits them into chunks, builds a
TF-IDF index (pure NumPy, no external API), and retrieves the most relevant
chunks for a query via cosine similarity. The retrieved context is injected
into the department agents so answers are grounded in company documents.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np

from .config import KB_DIR

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "is", "are",
    "be", "with", "your", "you", "i", "my", "me", "it", "this", "that", "at",
    "as", "by", "from", "can", "do", "how", "what", "do", "if", "we", "our",
}


def _tokenize(text: str) -> List[str]:
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS]


@dataclass
class Chunk:
    source: str   # document file name
    title: str    # nearest heading
    text: str     # chunk content


class RAGPipeline:
    """A small, self-contained TF-IDF retriever over the knowledge base."""

    def __init__(self, kb_dir=KB_DIR):
        self.kb_dir = kb_dir
        self.chunks: List[Chunk] = []
        self.vocab: dict[str, int] = {}
        self.idf: np.ndarray = np.zeros(0)
        self.matrix: np.ndarray = np.zeros((0, 0))
        self._build()

    # -- index construction -------------------------------------------------
    def _load_chunks(self) -> List[Chunk]:
        chunks: List[Chunk] = []
        for path in sorted(self.kb_dir.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            title = path.stem
            buf: List[str] = []

            def flush():
                body = "\n".join(buf).strip()
                if body:
                    chunks.append(Chunk(source=path.name, title=title, text=body))

            for line in text.splitlines():
                if line.startswith("#"):
                    flush()
                    buf = []
                    title = line.lstrip("#").strip()
                    buf.append(line.lstrip("#").strip())
                else:
                    buf.append(line)
            flush()
        return chunks

    def _build(self) -> None:
        self.chunks = self._load_chunks()
        docs_tokens = [_tokenize(c.text) for c in self.chunks]

        vocab: dict[str, int] = {}
        for toks in docs_tokens:
            for t in set(toks):
                vocab.setdefault(t, len(vocab))
        self.vocab = vocab

        n_docs = len(self.chunks)
        df = np.zeros(len(vocab))
        for toks in docs_tokens:
            for t in set(toks):
                df[vocab[t]] += 1
        # smoothed idf
        self.idf = np.log((1 + n_docs) / (1 + df)) + 1.0

        matrix = np.zeros((n_docs, len(vocab)))
        for i, toks in enumerate(docs_tokens):
            counts = Counter(toks)
            total = max(len(toks), 1)
            for t, c in counts.items():
                matrix[i, vocab[t]] = (c / total) * self.idf[vocab[t]]
        # L2-normalize rows for cosine similarity
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.matrix = matrix / norms

    # -- query --------------------------------------------------------------
    def _vectorize(self, query: str) -> np.ndarray:
        toks = _tokenize(query)
        vec = np.zeros(len(self.vocab))
        counts = Counter(toks)
        total = max(len(toks), 1)
        for t, c in counts.items():
            if t in self.vocab:
                vec[self.vocab[t]] = (c / total) * self.idf[self.vocab[t]]
        norm = np.linalg.norm(vec)
        return vec / norm if norm else vec

    def retrieve(self, query: str, k: int = 3) -> List[Tuple[Chunk, float]]:
        """Return the top-k (chunk, score) pairs for a query."""
        if not self.chunks:
            return []
        qv = self._vectorize(query)
        scores = self.matrix @ qv
        order = np.argsort(scores)[::-1][:k]
        return [(self.chunks[i], float(scores[i])) for i in order if scores[i] > 0]

    def retrieve_context(self, query: str, k: int = 3):
        """Convenience wrapper returning (context_snippets, source_names)."""
        results = self.retrieve(query, k)
        snippets = [c.text for c, _ in results]
        sources = [f"{c.source} :: {c.title}" for c, _ in results]
        return snippets, sources


# Singleton so the index is built only once per process.
_PIPELINE: RAGPipeline | None = None


def get_pipeline() -> RAGPipeline:
    global _PIPELINE
    if _PIPELINE is None:
        _PIPELINE = RAGPipeline()
    return _PIPELINE
