"""RAG layer tests — fully offline (HashingEmbedder, temp Chroma dir, no API key)."""

import json
from pathlib import Path

import pytest

from regimpact.rag.bm25 import tokenize
from regimpact.rag.chunking import (
    MAX_CHARS,
    chunk_policy_register,
    chunk_regulation,
    fingerprint,
    outline,
)
from regimpact.rag.embeddings import HashingEmbedder
from regimpact.rag.ingest import parse_oj_xhtml, to_markdown
from regimpact.rag.knowledge_base import KnowledgeBase
from regimpact.rag.retriever import rrf_fuse
from regimpact.rag.verify import extract_citations, verify_citations

ROOT = Path(__file__).resolve().parents[1]
DORA = ROOT / "data" / "regulations" / "dora.md"
POLICIES = ROOT / "data" / "policies" / "policy_register.csv"


# --------------------------------------------------------------------------- ingest
_XHTML = """<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE html PUBLIC "-//W3C//DTD XHTML//EN" "x.dtd">
<html xmlns="http://www.w3.org/1999/xhtml"><body>
<p class="oj-ti-section-1">CHAPTER III</p><p class="oj-ti-section-2">Incident reporting</p>
<div class="eli-subdivision" id="art_19">
  <p class="oj-ti-art">Article 19</p>
  <div class="eli-title"><p class="oj-sti-art">Reporting of major incidents`</p></div>
  <div id="019.001"><p class="oj-normal">1.   Entities shall report<span class="oj-super oj-note-tag">(7)</span> incidents:</p>
    <table><tbody><tr><td><p class="oj-normal">(a)</p></td><td><p class="oj-normal">an initial notification;</p>
      <table><tbody><tr><td><p class="oj-normal">(i)</p></td><td><p class="oj-normal">within hours;</p></td></tr></tbody></table>
    </td></tr></tbody></table></div>
  <div id="019.002"><p class="oj-normal">2.   Entities may notify threats.</p></div>
</div></body></html>"""


def test_parser_keeps_structure_and_drops_footnote_markers():
    [art] = parse_oj_xhtml(_XHTML)
    assert (art.number, art.title) == ("19", "Reporting of major incidents")  # stray ` stripped
    assert art.chapter == "CHAPTER III — Incident reporting"
    assert art.paragraphs[0] == [
        "1. Entities shall report incidents:",
        "(a) an initial notification;",
        "  (i) within hours;",
    ]
    md = to_markdown([art], title="X — test", celex="0")
    assert "### Article 19 — Reporting of major incidents" in md


# --------------------------------------------------------------------------- chunking
def test_dora_chunks_are_paragraph_level_with_stable_ids():
    chunks = chunk_regulation(DORA)
    by_id = {c.chunk_id: c for c in chunks}
    assert len(by_id) == len(chunks)  # ids unique
    assert len({c.article for c in chunks}) == 64
    c = by_id["dora::art19::p4"]
    assert c.citation == "DORA Art. 19(4)"
    assert c.text.startswith("DORA — Article 19: Reporting of major ICT-related incidents")
    assert "CHAPTER III" in c.text  # contextual header carries the chapter


def test_long_paragraphs_split_with_lead_in_carried_over():
    chunks = chunk_regulation(DORA)
    parts = [c for c in chunks if c.chunk_id.startswith("dora::art30::p3.")]
    assert len(parts) >= 2
    lead = parts[0].body.splitlines()[0]
    assert all(p.body.splitlines()[0] == lead for p in parts)
    assert all(len(c.text) <= MAX_CHARS + 200 for c in chunks)  # header + small slack


def test_policy_rows_become_chunks():
    pol = chunk_policy_register(POLICIES)
    assert len(pol) == 12
    assert pol[2].chunk_id == "policy::POL-003"
    assert (pol[2].citation, pol[2].article_title) == ("POL-003", "Incident Management Standard")


def test_outline_lists_every_article_once():
    out = outline(chunk_regulation(DORA), "dora")
    assert out.count("Article ") == 64
    assert "CHAPTER V — Managing of ICT third-party risk" in out


# --------------------------------------------------------------------------- retrieval maths
def test_tokenize_folds_plurals_and_drops_stopwords():
    assert tokenize("The incidents shall be reported") == ["incident", "reported"]


def test_rrf_worked_example():
    # X: BM25 #1, dense #3 | Y: BM25 #2 only | Z: dense #1 only
    fused = dict(rrf_fuse([["X", "Y"], ["Z", "W", "X"]]))
    assert fused["X"] == pytest.approx(1 / 61 + 1 / 63)
    assert fused["Z"] == pytest.approx(1 / 61)
    assert fused["Y"] == pytest.approx(1 / 62)
    assert max(fused, key=fused.get) == "X"  # agreement beats one first place


def test_hashing_embedder_is_deterministic_and_unit_length():
    e = HashingEmbedder()
    a, b = e.embed_query("incident reporting"), e.embed_query("incident reporting")
    assert a == b
    assert sum(x * x for x in a) == pytest.approx(1.0)


# --------------------------------------------------------------------------- knowledge base
@pytest.fixture(scope="module")
def kb(tmp_path_factory):
    return KnowledgeBase.load(
        regulations_dir=ROOT / "data" / "regulations",
        policies_csv=POLICIES,
        index_dir=tmp_path_factory.mktemp("index"),
        embedder=HashingEmbedder(),
        log=lambda _m: None,
    )


def test_index_is_fresh_until_corpus_changes(kb):
    fp = fingerprint(kb.chunks)
    assert kb.store.is_fresh(fp, kb.embedder.name, len(kb.chunks))
    assert not kb.store.is_fresh("other-corpus", kb.embedder.name, len(kb.chunks))
    assert not kb.store.is_fresh(fp, "gemini:some-other-model:768", len(kb.chunks))


def test_metadata_filter_scopes_search_to_one_regulation(kb):
    hits = kb.search_regulation("penalties and fines", source="eu_ai_act", k=10)
    assert hits and all(h.chunk.source == "eu_ai_act" for h in hits)
    pol = kb.search_policies("incident severity", k=4)
    assert pol and all(h.chunk.kind == "policy" for h in pol)


def test_auto_mode_follows_the_eval():
    from regimpact.rag.knowledge_base import resolve_mode

    class Semantic:
        name = "gemini:gemini-embedding-001:768"

    assert resolve_mode("auto", Semantic()) == "dense"           # dense won the live eval
    assert resolve_mode("auto", HashingEmbedder()) == "hybrid"   # hybrid won the offline eval
    assert resolve_mode("bm25", Semantic()) == "bm25"            # explicit setting wins


def test_hybrid_hits_report_per_retriever_ranks(kb):
    hits = kb.search_regulation("threat-led penetration testing every 3 years", source="dora")
    assert hits[0].chunk.article == "26"
    assert any(h.bm25_rank and h.dense_rank for h in hits)


# --------------------------------------------------------------------------- citation verification
def test_verify_classifies_citations(kb):
    text = (
        "Report major incidents [dora::art19::p4]. Board owns ICT risk [dora::art5::p2]. "
        "Made up [dora::art99::p1]. Split paragraph cited whole [dora::art19::p1]."
    )
    retrieved = {"dora::art19::p4", "dora::art19::p1.2"}
    rep = verify_citations(text, kb, retrieved)
    assert rep.verified == ["dora::art19::p4", "dora::art19::p1"]  # parent id resolves to parts
    assert rep.not_retrieved == ["dora::art5::p2"]                   # real, but never retrieved
    assert rep.unknown == ["dora::art99::p1"]                        # fabricated
    assert extract_citations("[policy::POL-005] and [policy::POL-005]") == ["policy::POL-005"]


def test_grouped_citations_are_all_checked(kb):
    # Models write "[a, b]" — a live run showed single-id parsing missed these.
    text = "Board approves [dora::art5::p2.2, dora::art6::p5]; policy [policy::POL-001]. Not a cite [see Art. 5]."
    assert extract_citations(text) == ["dora::art5::p2.2", "dora::art6::p5", "policy::POL-001"]
    rep = verify_citations(text, kb, {"dora::art6::p5", "policy::POL-001"})
    assert rep.verified == ["dora::art6::p5", "policy::POL-001"]
    assert rep.not_retrieved == ["dora::art5::p2.2"]


def test_point_suffixes_normalise_and_malformed_ids_are_flagged_not_dropped(kb):
    # Live run: "[dora::art17::p3(b)]" was silently skipped by the verifier,
    # left out of the review evidence pack, and the committee then claimed the
    # provision didn't exist.
    text = "Severity criteria [dora::art17::p3(b)]. Garbled [dora::art 17]."
    assert extract_citations(text) == ["dora::art17::p3", "dora::art 17"]
    rep = verify_citations(text, kb, {"dora::art17::p3"})
    assert rep.verified == ["dora::art17::p3"]
    assert rep.unknown == ["dora::art 17"]  # flagged, not vanished


def test_render_keeps_point_reference(kb):
    from regimpact.nodes import render_report

    text = "Severity criteria [dora::art17::p3(b)]."
    out = render_report(text, kb, verify_citations(text, kb, {"dora::art17::p3"}))
    assert "[DORA Art. 17(3)(b)]" in out


def test_render_handles_groups_and_policies(kb):
    from regimpact.nodes import render_report

    text = "Board approves [dora::art5::p2.2, dora::art6::p5]. Gap in [policy::POL-001] ICT Risk Management Framework. Keep [see Art. 5]."
    rep = verify_citations(text, kb, {"dora::art6::p5", "policy::POL-001"})
    out = render_report(text, kb, rep)
    assert "[DORA Art. 5(2) — unverified; DORA Art. 6(5)]" in out
    assert "[POL-001] ICT Risk Management Framework" in out  # title not doubled
    assert "[see Art. 5]" in out                              # non-citation brackets untouched
    assert "- POL-001 — ICT Risk Management Framework (`policy::POL-001`)" in out


def test_metadata_change_refreshes_without_reembedding(tmp_path):
    from dataclasses import replace

    from regimpact.rag.chunking import metadata_fingerprint
    from regimpact.rag.store import VectorStore

    chunks = chunk_policy_register(POLICIES)
    emb = HashingEmbedder()
    store = VectorStore(tmp_path)
    store.build(chunks, emb, fingerprint(chunks), metadata_fingerprint(chunks))
    assert not store.sync_metadata(chunks, metadata_fingerprint(chunks))  # nothing to do

    renamed = [replace(c, article_title=c.article_title + " (v2)") for c in chunks]
    assert fingerprint(renamed) == fingerprint(chunks)           # embedded text unchanged…
    assert store.sync_metadata(renamed, metadata_fingerprint(renamed))  # …so metadata-only refresh
    assert store.is_fresh(fingerprint(chunks), emb.name, len(chunks))
    # still a cosine index: a chunk's own vector is its nearest neighbour at similarity ~1
    cid, sim = store.query(emb.embed_query(chunks[0].text), k=1)[0]
    assert cid == chunks[0].chunk_id and sim == pytest.approx(1.0, abs=1e-3)


def test_render_report_marks_unverified_and_lists_sources(kb):
    from regimpact.nodes import render_report

    text = "Deadlines apply [dora::art19::p4]. Board duty [dora::art5::p2]."
    rep = verify_citations(text, kb, {"dora::art19::p4"})
    out = render_report(text, kb, rep)
    assert "[DORA Art. 19(4)]" in out
    assert "[DORA Art. 5(2) — unverified]" in out
    assert "## Sources" in out and "1/2 citations verified" in out


def test_review_evidence_is_the_cited_source_text(kb):
    from regimpact.nodes import build_evidence

    draft = "Report fast [dora::art19::p4]. Contracts [dora::art30::p2]. Again [dora::art19::p4]. Fake [dora::art99::p9]."
    evidence, ids = build_evidence(draft, kb)
    assert ids == ["dora::art19::p4", "dora::art30::p2.1", "dora::art30::p2.2"]  # deduped, split ¶ expanded, fake dropped
    assert "[dora::art19::p4] DORA Art. 19(4)" in evidence


def test_review_evidence_does_not_count_as_grounding():
    from regimpact.nodes import _retrieved_ids

    state = {"retrieval_calls": [
        {"tool": "search_regulation", "query": "q", "chunk_ids": ["dora::art19::p4"]},
        {"tool": "review_evidence", "query": "cited", "chunk_ids": ["dora::art5::p2"]},
    ]}
    assert _retrieved_ids(state) == {"dora::art19::p4"}


# --------------------------------------------------------------------------- eval set integrity
def test_every_gold_label_points_at_a_real_article():
    gold = json.loads((ROOT / "data" / "eval" / "retrieval_gold.json").read_text())["cases"]
    articles = {}
    for src in {g["source"] for g in gold}:
        articles[src] = {c.article for c in chunk_regulation(ROOT / "data" / "regulations" / f"{src}.md")}
    for g in gold:
        assert set(g["articles"]) <= articles[g["source"]], g["q"]
