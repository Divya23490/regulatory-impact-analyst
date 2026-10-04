"""KnowledgeBase: the one object the agents talk to.

It owns the whole RAG stack — chunks, BM25, vector index, hybrid retriever —
and exposes the handful of operations the workflow needs:

    search_regulation(query, source)  -> top-k regulation chunks (one regulation only)
    search_policies(query)            -> top-k internal-policy chunks
    get(chunk_id)                     -> a chunk, for citation checks / provision lookup
    outline(source)                   -> chapter/article map for triage
    resolve(chunk_id)                 -> which real chunks a cited id refers to

`load()` builds the vector index on first use and reuses it afterwards; it
rebuilds automatically if the corpus or the embedding model changed.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from .chunking import (
    Chunk,
    chunk_policy_register,
    chunk_regulation,
    fingerprint,
    metadata_fingerprint,
    outline,
)
from .embeddings import Embedder, default_embedder
from .retriever import Hit, HybridRetriever
from .store import VectorStore


def resolve_mode(mode: str, embedder: Embedder) -> str:
    """Pick the retrieval mode the agents use.

    Measured on the 50-query gold set (docs/ARCHITECTURE.md §5):
      * gemini-embedding-001: dense 100% recall@5; equal-weight hybrid 96% —
        fusing BM25 in *costs* accuracy, because RRF rewards agreement and a
        much weaker retriever's agreement is noise.
      * offline hashing embedder: hybrid 84% vs dense 74% — two weak
        retrievers that fail differently, so fusion helps.
    Hence "auto": dense for a semantic model, hybrid for the offline one.
    """
    if mode != "auto":
        return mode
    return "hybrid" if embedder.name.startswith("hashing:") else "dense"


class KnowledgeBase:
    def __init__(self, chunks: list[Chunk], store: VectorStore, embedder: Embedder, mode: str = "auto"):
        self.chunks = chunks
        self.by_id = {c.chunk_id: c for c in chunks}
        self.store = store
        self.embedder = embedder
        self.retriever = HybridRetriever(chunks, store, embedder)
        self.mode = resolve_mode(mode, embedder)

    # ------------------------------------------------------------------ build
    @classmethod
    def load(
        cls,
        *,
        regulations_dir: Path | str,
        policies_csv: Path | str,
        index_dir: Path | str,
        embedder: Embedder | None = None,
        rebuild: bool = False,
        mode: str | None = None,
        log=print,
    ) -> "KnowledgeBase":
        from ..config import RETRIEVAL_MODE

        chunks: list[Chunk] = []
        for md in sorted(Path(regulations_dir).glob("*.md")):
            chunks.extend(chunk_regulation(md))
        chunks.extend(chunk_policy_register(policies_csv))

        embedder = embedder or default_embedder()
        store = VectorStore(index_dir)
        fp, meta_fp = fingerprint(chunks), metadata_fingerprint(chunks)
        if rebuild or not store.is_fresh(fp, embedder.name, len(chunks)):
            log(f"[rag] building vector index: {len(chunks)} chunks with {embedder.name} …")
            store.build(chunks, embedder, fp, meta_fp)
            log(f"[rag] index ready at {index_dir}")
        elif store.sync_metadata(chunks, meta_fp):
            log("[rag] metadata changed — refreshed in place (vectors unchanged, no re-embedding)")
        return cls(chunks, store, embedder, mode or RETRIEVAL_MODE)

    # --------------------------------------------------------------- queries
    def search_regulation(self, query: str, source: str, k: int = 5) -> list[Hit]:
        return self.retriever.search(query, top_k=k, kind="regulation", source=source, mode=self.mode)

    def search_policies(self, query: str, k: int = 4) -> list[Hit]:
        return self.retriever.search(query, top_k=k, kind="policy", mode=self.mode)

    def get(self, chunk_id: str) -> Chunk | None:
        return self.by_id.get(chunk_id)

    def resolve(self, chunk_id: str) -> list[str]:
        """A cited id may name a whole split paragraph ("dora::art19::p1")
        whose parts are indexed as "dora::art19::p1.1", "…p1.2"."""
        if chunk_id in self.by_id:
            return [chunk_id]
        return [cid for cid in self.by_id if cid.startswith(chunk_id + ".")]

    def outline(self, source: str) -> str:
        return outline(self.chunks, source)

    def sources(self) -> list[str]:
        return sorted({c.source for c in self.chunks if c.kind == "regulation"})


def format_hits(hits: list[Hit]) -> str:
    """Render hits for an LLM: id + citation header, then the provision text.
    The bracketed id is what the model must cite back."""
    if not hits:
        return "No matching provisions found."
    blocks = []
    for h in hits:
        c = h.chunk
        head = f"[{c.chunk_id}] {c.citation}"
        if c.article_title:
            head += f" — {c.article_title}"
        blocks.append(f"{head}\n{c.body}")
    return "\n\n---\n\n".join(blocks)


@lru_cache(maxsize=4)
def get_knowledge_base(policies_csv: str) -> KnowledgeBase:
    """Process-wide instance, keyed by the policy register in use."""
    from ..config import INDEX_DIR, REGULATIONS_DIR

    return KnowledgeBase.load(
        regulations_dir=REGULATIONS_DIR, policies_csv=policies_csv, index_dir=INDEX_DIR
    )
