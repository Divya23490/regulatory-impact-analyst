"""BM25: the lexical (keyword) half of hybrid retrieval.

CONCEPT — why keep a keyword retriever next to embeddings
---------------------------------------------------------
Embeddings capture meaning ("outage" ≈ "ICT-related incident"), but they are
fuzzy on exact tokens: article numbers, defined terms ("TLPT", "Lead
Overseer"), dates and thresholds. Regulatory questions are full of those.
BM25 scores a chunk by how many query terms it contains, weighted by rarity:

    score(q, d) = Σ_t idf(t) · tf(t,d)·(k1+1) / (tf(t,d) + k1·(1 − b + b·|d|/avgdl))
    idf(t)      = ln(1 + (N − df(t) + 0.5) / (df(t) + 0.5))

* tf: term count in the chunk (saturates via k1 — the 10th mention adds little)
* idf: rare terms ("TLPT") outweigh common ones ("financial")
* b: length normalisation — long chunks don't win just by being long

Hand-rolled (~40 lines) on purpose: it's fully inspectable when you need to
explain why a chunk ranked where it did. Same implementation as
danish-legal-checker, with an English tokenizer.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Callable

from .chunking import Chunk

_STOP = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have",
    "in", "is", "it", "its", "of", "on", "or", "shall", "that", "the", "their",
    "this", "to", "which", "with", "where", "what", "when", "who", "how", "do",
    "does", "we", "our", "us", "any", "such", "those", "these", "been", "was",
    "may", "must", "should", "can", "if", "not", "into", "other", "than",
}
_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Lowercase, drop stopwords, and fold simple plurals ("incidents" -> "incident")."""
    out = []
    for t in _TOKEN_RE.findall(text.lower()):
        if t in _STOP:
            continue
        if len(t) > 4 and t.endswith("s") and not t.endswith("ss"):
            t = t[:-1]
        out.append(t)
    return out


class BM25:
    def __init__(self, chunks: list[Chunk], *, k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1, self.b = k1, b
        docs = [tokenize(c.text) for c in chunks]
        self.freqs = [Counter(d) for d in docs]
        self.lens = [len(d) for d in docs]
        self.avgdl = sum(self.lens) / len(docs) if docs else 0.0
        df: Counter[str] = Counter()
        for d in docs:
            df.update(set(d))
        n = len(docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def _score(self, terms: list[str], i: int) -> float:
        freq, dl, s = self.freqs[i], self.lens[i], 0.0
        for t in terms:
            tf = freq.get(t)
            if not tf:
                continue
            denom = tf + self.k1 * (1 - self.b + self.b * dl / (self.avgdl or 1))
            s += self.idf.get(t, 0.0) * tf * (self.k1 + 1) / denom
        return s

    def search(
        self, query: str, *, top_k: int = 10, where: Callable[[Chunk], bool] | None = None
    ) -> list[tuple[Chunk, float]]:
        terms = tokenize(query)
        scored = [
            (c, self._score(terms, i))
            for i, c in enumerate(self.chunks)
            if where is None or where(c)
        ]
        scored = [cs for cs in scored if cs[1] > 0]
        scored.sort(key=lambda cs: cs[1], reverse=True)
        return scored[:top_k]
