"""Embedders: text -> unit-length vector.

CONCEPT — embeddings for retrieval
----------------------------------
An embedding model maps text to a point in a high-dimensional space where
texts with similar meaning land close together. Retrieval then becomes
"which chunk vectors point in nearly the same direction as the query vector"
— cosine similarity. Two practical details matter here:

* **Asymmetric task types.** Gemini embeddings take a `task_type`:
  RETRIEVAL_DOCUMENT for the corpus, RETRIEVAL_QUERY for the question. A
  question ("how fast must we report an outage?") and the passage answering
  it ("financial entities shall report major ICT-related incidents…") are
  phrased very differently; the model embeds each side for its role.

* **Normalisation.** gemini-embedding-001 is trained so its vectors can be
  truncated (Matryoshka representation learning): the first 768 of 3,072
  dimensions still work. But only the full-size output is unit length — at
  768 dims the norm comes back ≈0.59 (measured). We L2-normalise ourselves,
  so cosine similarity equals the plain dot product everywhere.

Two implementations share one interface:

* `GeminiEmbedder`   — the real semantic model (needs GOOGLE_API_KEY).
* `HashingEmbedder`  — offline, deterministic character-n-gram hashing. No
  semantics beyond spelling overlap, but it lets every test and the CI path
  exercise the full index/retrieve stack without a network call.

`name` identifies the embedder; the vector store records it and rebuilds the
index if it changes — vectors from different models are not comparable.
"""

from __future__ import annotations

import math
import re
import time
import zlib
from functools import lru_cache
from typing import Protocol, runtime_checkable

_BATCH = 100  # Gemini's max inputs per batch-embed request


@runtime_checkable
class Embedder(Protocol):
    name: str

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


def l2_normalize(v: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


# --------------------------------------------------------------------------- #
# Gemini                                                                      #
# --------------------------------------------------------------------------- #
class GeminiEmbedder:
    def __init__(self, model: str, dim: int, api_key: str, *, max_retries: int = 8):
        from google import genai

        self.model = model
        self.dim = dim
        self.name = f"gemini:{model}:{dim}"
        self.max_retries = max_retries
        self._client = genai.Client(api_key=api_key)
        # Cache query vectors: agents re-ask near-identical questions, and each
        # embed call is a rate-limited network round trip.
        self.embed_query = lru_cache(maxsize=512)(self._embed_query)  # type: ignore[method-assign]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for i in range(0, len(texts), _BATCH):
            out.extend(self._call(texts[i : i + _BATCH], "RETRIEVAL_DOCUMENT"))
        return out

    def _embed_query(self, text: str) -> list[float]:
        return self._call([text], "RETRIEVAL_QUERY")[0]

    def _call(self, texts: list[str], task_type: str) -> list[list[float]]:
        from google.genai import errors, types

        cfg = types.EmbedContentConfig(task_type=task_type, output_dimensionality=self.dim)
        for attempt in range(self.max_retries):
            try:
                resp = self._client.models.embed_content(model=self.model, contents=texts, config=cfg)
                vecs = [l2_normalize(list(e.values)) for e in resp.embeddings]
                if len(vecs) != len(texts):  # defensive: never silently misalign ids/vectors
                    raise RuntimeError(f"asked for {len(texts)} embeddings, got {len(vecs)}")
                return vecs
            except errors.APIError as exc:
                if exc.code not in (429, 500, 503) or attempt == self.max_retries - 1:
                    raise
                time.sleep(_retry_delay(str(exc), attempt))
        raise RuntimeError("unreachable")


def _retry_delay(message: str, attempt: int) -> float:
    """Honour the server's 'retry in 39.2s' hint on 429s; else back off."""
    m = re.search(r"retry in ([\d.]+)s", message, re.IGNORECASE)
    return float(m.group(1)) + 1 if m else min(2 ** attempt, 60)


# --------------------------------------------------------------------------- #
# Offline                                                                     #
# --------------------------------------------------------------------------- #
class HashingEmbedder:
    """Character 3-5-gram feature hashing into a fixed-size signed vector.

    The "hashing trick": instead of a vocabulary, each n-gram is hashed to one
    of `dim` buckets (with a hashed sign to cancel collisions on average).
    crc32 is used because Python's built-in hash() is salted per process,
    which would make vectors differ between runs.
    """

    def __init__(self, dim: int = 1024):
        self.dim = dim
        self.name = f"hashing:char3-5:{dim}"

    def _vec(self, text: str) -> list[float]:
        v = [0.0] * self.dim
        for tok in re.findall(r"[a-z0-9]+", text.lower()):
            padded = f"#{tok}#"
            for n in (3, 4, 5):
                for i in range(len(padded) - n + 1):
                    h = zlib.crc32(padded[i : i + n].encode())
                    v[h % self.dim] += 1.0 if (h >> 16) & 1 else -1.0
        return l2_normalize(v)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vec(text)


def default_embedder() -> Embedder:
    """Gemini if a key is configured, else the offline embedder."""
    from ..config import EMBED_DIM, EMBED_MODEL, google_api_key

    key = google_api_key()
    return GeminiEmbedder(EMBED_MODEL, EMBED_DIM, key) if key else HashingEmbedder()
