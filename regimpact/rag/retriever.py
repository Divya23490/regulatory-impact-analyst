"""Hybrid retrieval: BM25 + dense vectors, fused with Reciprocal Rank Fusion.

CONCEPT — why fuse, and why RRF
-------------------------------
BM25 and dense retrieval fail differently. BM25 misses paraphrase ("outage"
vs "ICT-related incident"); dense retrieval drifts on exact tokens ("Article
26", "TLPT", "three years"). Run both, then fuse.

Scores can't simply be added: BM25 is unbounded (8.7, 23.1, …) while cosine
sits in [−1, 1], so whichever scale is bigger would dominate. RRF discards
scores and fuses *ranks*:

    rrf(d) = Σ_retrievers  1 / (k + rank_r(d))          k = 60

Worked example (k = 60):
    chunk X: BM25 #1, dense #3   -> 1/61 + 1/63 = 0.0323   <- wins: both agree
    chunk Z: dense #1 only       -> 1/61        = 0.0164
    chunk Y: BM25 #2 only        -> 1/62        = 0.0161

k = 60 (from the original RRF paper) flattens the top ranks so one retriever
can't single-handedly decide the result. No normalisation, no tuning.

Every Hit keeps its per-retriever ranks — when a citation looks wrong you can
see *which* retriever put it there.
"""

from __future__ import annotations

from dataclasses import dataclass

from .bm25 import BM25
from .chunking import Chunk
from .embeddings import Embedder
from .store import VectorStore

RRF_K = 60
DEPTH = 30  # how far down each list a chunk can still earn fusion credit


@dataclass
class Hit:
    chunk: Chunk
    score: float
    bm25_rank: int | None = None
    dense_rank: int | None = None


def rrf_fuse(rankings: list[list[str]], *, k: int = RRF_K) -> list[tuple[str, float]]:
    """Fuse ranked id lists. Pure function — the unit-tested core of hybrid."""
    fused: dict[str, float] = {}
    for ranking in rankings:
        for rank, cid in enumerate(ranking, start=1):
            fused[cid] = fused.get(cid, 0.0) + 1.0 / (k + rank)
    return sorted(fused.items(), key=lambda kv: kv[1], reverse=True)


def _chroma_where(kind: str | None, source: str | None) -> dict | None:
    clauses = [{f: v} for f, v in (("kind", kind), ("source", source)) if v]
    if not clauses:
        return None
    return clauses[0] if len(clauses) == 1 else {"$and": clauses}


class HybridRetriever:
    def __init__(self, chunks: list[Chunk], store: VectorStore, embedder: Embedder):
        self.by_id = {c.chunk_id: c for c in chunks}
        self.bm25 = BM25(chunks)
        self.store = store
        self.embedder = embedder

    def _bm25_ids(self, query, kind, source) -> list[str]:
        where = lambda c: (not kind or c.kind == kind) and (not source or c.source == source)  # noqa: E731
        return [c.chunk_id for c, _ in self.bm25.search(query, top_k=DEPTH, where=where)]

    def _dense_ids(self, query, kind, source) -> list[str]:
        vec = self.embedder.embed_query(query)
        return [cid for cid, _ in self.store.query(vec, k=DEPTH, where=_chroma_where(kind, source))]

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        kind: str | None = None,
        source: str | None = None,
        mode: str = "hybrid",
    ) -> list[Hit]:
        """mode: "hybrid" (default) | "bm25" | "dense" — the latter two for eval."""
        bm25 = self._bm25_ids(query, kind, source) if mode in ("hybrid", "bm25") else []
        dense = self._dense_ids(query, kind, source) if mode in ("hybrid", "dense") else []
        rankings = [r for r in (bm25, dense) if r]
        b_rank = {cid: i for i, cid in enumerate(bm25, start=1)}
        d_rank = {cid: i for i, cid in enumerate(dense, start=1)}
        return [
            Hit(self.by_id[cid], score, b_rank.get(cid), d_rank.get(cid))
            for cid, score in rrf_fuse(rankings)[:top_k]
            if cid in self.by_id
        ]
