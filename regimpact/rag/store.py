"""Vector store: Chroma, persisted on disk, cosine distance, metadata filters.

CONCEPT — what a vector database adds over "a list of vectors"
--------------------------------------------------------------
At 845 chunks, brute-force cosine over a Python list takes milliseconds. A
vector DB earns its place through what scales and what operates:

* **ANN index (HNSW).** Chroma builds a Hierarchical Navigable Small World
  graph: a layered proximity graph you greedily walk from a coarse top layer
  down to the nearest neighbours. Query cost grows ~logarithmically instead
  of linearly with corpus size, at the price of *approximate* results (a
  tunable recall/latency trade-off). That's the step from 1k to 10M chunks.
* **Metadata filtering.** Every vector carries {kind, source, article, …};
  `where={"source": "dora"}` scopes a search to one regulation, so a DORA
  analysis never retrieves AI Act text.
* **Persistence.** The index lives in data/index/ and survives restarts;
  embeddings are paid for once, not per run.

Distance metric is set to cosine at collection creation ("hnsw:space"). Chroma
returns *distance* = 1 − cosine similarity, so 0 means identical direction.

CONCEPT — index staleness
-------------------------
Vectors are only comparable within one embedding model, and the index is only
correct for the corpus it was built from. The collection metadata records the
embedder name and a content fingerprint of the chunks; `is_fresh` compares
both, and the knowledge base rebuilds automatically when either changes
(an amended regulation, a new policy row, a different model).
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from .chunking import Chunk
from .embeddings import Embedder

COLLECTION = "regimpact_corpus"


class VectorStore:
    def __init__(self, path: Path | str):
        import chromadb
        from chromadb.config import Settings

        self.path = Path(path)
        # Chroma ships anonymous usage telemetry on by default; a bank demo
        # should not phone home.
        self._client = chromadb.PersistentClient(
            path=str(self.path), settings=Settings(anonymized_telemetry=False)
        )

    def _collection(self):
        try:
            return self._client.get_collection(COLLECTION)
        except Exception:
            return None

    def is_fresh(self, fingerprint: str, embedder_name: str, n_chunks: int) -> bool:
        col = self._collection()
        if col is None:
            return False
        meta = col.metadata or {}
        return (
            meta.get("fingerprint") == fingerprint
            and meta.get("embedder") == embedder_name
            and col.count() == n_chunks
        )

    def build(self, chunks: list[Chunk], embedder: Embedder, fingerprint: str, meta_fp: str = "") -> None:
        if self._collection() is not None:
            self._client.delete_collection(COLLECTION)
        col = self._client.create_collection(
            COLLECTION,
            metadata={
                "hnsw:space": "cosine",
                "fingerprint": fingerprint,
                "meta_fingerprint": meta_fp,
                "embedder": embedder.name,
                "built_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            },
        )
        vectors = embedder.embed_documents([c.text for c in chunks])
        for i in range(0, len(chunks), 500):  # Chroma batch-size limit headroom
            part = chunks[i : i + 500]
            col.add(
                ids=[c.chunk_id for c in part],
                embeddings=vectors[i : i + 500],
                documents=[c.text for c in part],
                metadatas=[c.metadata() for c in part],
            )

    def sync_metadata(self, chunks: list[Chunk], meta_fp: str) -> bool:
        """Refresh per-chunk metadata without re-embedding. Returns True if it
        had to update anything."""
        col = self._collection()
        if col is None or (col.metadata or {}).get("meta_fingerprint") == meta_fp:
            return False
        for i in range(0, len(chunks), 500):
            part = chunks[i : i + 500]
            col.update(ids=[c.chunk_id for c in part], metadatas=[c.metadata() for c in part])
        # `hnsw:space` can't be changed after creation, so it is left out here.
        meta = {k: v for k, v in (col.metadata or {}).items() if not k.startswith("hnsw:")}
        col.modify(metadata={**meta, "meta_fingerprint": meta_fp})
        return True

    def query(self, vector: list[float], *, k: int, where: dict | None = None) -> list[tuple[str, float]]:
        """Return [(chunk_id, cosine_similarity)] best first."""
        col = self._collection()
        if col is None:
            raise RuntimeError("vector index not built — run `regimpact index`")
        res = col.query(query_embeddings=[vector], n_results=k, where=where or None)
        return [(cid, 1.0 - dist) for cid, dist in zip(res["ids"][0], res["distances"][0])]

    def info(self) -> dict:
        col = self._collection()
        return {} if col is None else {**(col.metadata or {}), "count": col.count()}
