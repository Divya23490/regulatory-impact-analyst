"""Retrieval eval — BM25 vs dense vs hybrid, on a hand-labelled gold set.

CONCEPT — evaluate retrieval separately from generation
-------------------------------------------------------
If the final report is wrong, was it retrieval (the right article never
reached the model) or generation (it was there and the model misread it)?
End-to-end evaluation can't tell. So retrieval gets its own eval, with no LLM
in the loop:

* recall@k — is a chunk from the right article in the top k? recall@5 is the
  operational number: the agent's `search_regulation` tool returns 5 chunks,
  so anything ranked 6th is invisible to it.
* MRR (mean reciprocal rank) — 1/rank of the first correct chunk, averaged.
  Separates a retriever that finds the answer at #1 from one that finds it at #5.

Relevance is article-level: a question about incident reporting deadlines is
answered by Article 19 whichever of its paragraphs ranks first.

Gold set: data/eval/retrieval_gold.json — questions phrased the way an analyst
asks them, deliberately not reusing article titles, so the eval measures
paraphrase handling rather than title matching.
"""

from __future__ import annotations

import json
from pathlib import Path

from .rag.knowledge_base import KnowledgeBase

GOLD = Path(__file__).resolve().parent.parent / "data" / "eval" / "retrieval_gold.json"
DEPTH = 10


def load_gold(path: Path = GOLD) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["cases"]


def first_relevant_rank(kb: KnowledgeBase, case: dict, mode: str) -> int | None:
    hits = kb.retriever.search(
        case["q"], top_k=DEPTH, kind="regulation", source=case["source"], mode=mode
    )
    for rank, h in enumerate(hits, start=1):
        if h.chunk.article in case["articles"]:
            return rank
    return None


def score(ranks: list[int | None]) -> dict:
    n = len(ranks)
    found = [r for r in ranks if r is not None]
    return {
        "recall@1": sum(r <= 1 for r in found) / n,
        "recall@3": sum(r <= 3 for r in found) / n,
        "recall@5": sum(r <= 5 for r in found) / n,
        "MRR": sum(1 / r for r in found) / n,
    }


MODES = ("bm25", "dense", "hybrid")


def run_retrieval_eval(kb: KnowledgeBase, *, console=None, gold: list[dict] | None = None) -> dict:
    """Score every retriever on every case, reported per query type and overall."""
    gold = gold or load_gold()
    ranks = {mode: [first_relevant_rank(kb, c, mode) for c in gold] for mode in MODES}

    groups = {"all": list(range(len(gold)))}
    for i, c in enumerate(gold):
        groups.setdefault(c.get("type", "paraphrase"), []).append(i)

    results = {
        g: {mode: score([ranks[mode][i] for i in idx]) for mode in MODES}
        for g, idx in groups.items()
    }
    misses = {
        mode: [c["q"] for c, r in zip(gold, ranks[mode]) if r is None or r > 5] for mode in MODES
    }

    if console is not None:
        from rich.table import Table

        for g, idx in groups.items():
            t = Table(title=f"{g} — {len(idx)} queries · {kb.embedder.name}")
            for col in ("retriever", "recall@1", "recall@3", "recall@5", "MRR"):
                t.add_column(col, justify="right" if col != "retriever" else "left")
            for mode, m in results[g].items():
                t.add_row(mode, *(f"{m[k]:.0%}" for k in ("recall@1", "recall@3", "recall@5")),
                          f"{m['MRR']:.2f}")
            console.print(t)
        for mode in MODES:
            if misses[mode]:
                console.print(f"[bold]{mode} misses (not in top 5):[/bold] " + " | ".join(misses[mode]))
    return {"results": results, "misses": misses, "n": len(gold), "embedder": kb.embedder.name}
