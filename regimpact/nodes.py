"""Node functions for the LangGraph spine.

Each function takes the whole `ImpactState` and returns a dict with only the keys
it changed. Nothing here knows *how* the graph is wired — that is graph.py's job.

Where RAG shows up:
  triage    sees the regulation's *outline* (chapter/article titles), not its
            ~50k-token text — enough to choose themes.
  research  the Deep Agent retrieves provisions itself (agentic RAG).
  verify    deterministic check that every [chunk_id] cited was retrieved.
  review    retrieve-then-read: the AutoGen committee gets the source text of
            every provision the draft cites, and checks claims against it.
  finalize  re-verifies the approved report and renders citations + sources.
"""

from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.types import interrupt

from .config import langchain_model
from .rag.knowledge_base import KnowledgeBase, get_knowledge_base
from .rag.verify import CITE_GROUP_RE, extract_citations, parse_cite, verify_citations
from .research_agent import run_research
from .review_committee import review_draft
from .state import ImpactState

_MAX_REVISIONS = 2


def _kb(state: ImpactState) -> KnowledgeBase:
    return get_knowledge_base(state["policy_register_path"])


def _retrieved_ids(state: ImpactState) -> set[str]:
    """Chunks the agents actually searched for and read.

    Excludes the review evidence pack: that is fetched *from* the draft's
    citations, so counting it would mark every real-but-never-researched
    citation as "verified" and blind the final check.
    """
    return {
        cid
        for call in state.get("retrieval_calls", [])
        if call["tool"] != "review_evidence"
        for cid in call["chunk_ids"]
    }


# --------------------------------------------------------------------------- #
# 1. triage — pick researchable themes from the regulation's outline           #
# --------------------------------------------------------------------------- #
def triage(state: ImpactState) -> dict:
    outline = _kb(state).outline(state["regulation_source"])
    msg = langchain_model().invoke([
        SystemMessage(
            "You are a regulatory analyst. From the regulation's table of "
            "contents, return the 4-6 distinct areas where it will most affect a "
            "retail/commercial bank's internal policies. Each theme is a short "
            "phrase specific enough to search for. Reply with ONLY a JSON array "
            "of strings."
        ),
        HumanMessage(f"Regulation: {state['regulation_name']}\n\n{outline}"),
    ])
    # `.text` (not `.content`) — Gemini returns content as a list of typed
    # blocks (text + a "thought signature" for its reasoning), not a plain
    # string. `.text` is LangChain's provider-agnostic way to get the string.
    return {"outline": outline, "themes": _parse_json_list(msg.text), "revision_count": 0}


# --------------------------------------------------------------------------- #
# 2. research — the Deep Agent, doing agentic RAG                               #
# --------------------------------------------------------------------------- #
def research(state: ImpactState) -> dict:
    findings, files, calls = run_research(
        kb=_kb(state),
        source=state["regulation_source"],
        regulation_name=state["regulation_name"],
        themes=state["themes"],
    )
    return {"research_findings": findings, "research_files": files, "retrieval_calls": calls}


# --------------------------------------------------------------------------- #
# 3. verify — deterministic citation check on the research                     #
# --------------------------------------------------------------------------- #
def verify(state: ImpactState) -> dict:
    report = verify_citations(state["research_findings"], _kb(state), _retrieved_ids(state))
    return {"citation_report": report.as_dict()}


# --------------------------------------------------------------------------- #
# 4. draft — write the report from verified research only                      #
# --------------------------------------------------------------------------- #
def draft(state: ImpactState) -> dict:
    rep = state.get("citation_report", {})
    untrusted = rep.get("not_retrieved", []) + rep.get("unknown", [])
    caution = (
        "\nThese citations FAILED verification — do not rely on the claims "
        f"they support: {', '.join(untrusted)}\n" if untrusted else ""
    )
    msg = langchain_model().invoke([
        SystemMessage(
            "You write the formal Regulatory Impact Assessment for a bank's "
            "board. Use these sections exactly: '# <Regulation> — Impact "
            "Assessment', '## Executive summary', '## Affected policies', "
            "'## Gap analysis', '## Recommended actions' (a numbered list with an "
            "owner and a priority H/M/L each), '## Open questions'. Use ONLY the "
            "research findings. Keep every bracketed citation exactly as written "
            "(e.g. [dora::art19::p4], [policy::POL-003]) after the claim it "
            "supports, and use policy titles exactly as the findings give them."
        ),
        HumanMessage(
            f"Regulation: {state['regulation_name']}\n{caution}\n"
            f"=== RESEARCH FINDINGS ===\n{state['research_findings']}"
        ),
    ])
    return {"draft_report": msg.text}


# --------------------------------------------------------------------------- #
# 5. review — the AutoGen committee, reading the cited source text             #
# --------------------------------------------------------------------------- #
_MAX_EVIDENCE = 30


def build_evidence(draft: str, kb: KnowledgeBase) -> tuple[str, list[str]]:
    """Retrieve-then-read: the source text of every provision the draft cites.

    Deterministic — no model decides what to look up, so every citation in
    the draft is checkable by the committee. Capped to keep the prompt bounded.
    """
    ids: list[str] = []
    for cid in extract_citations(draft):
        for real in kb.resolve(cid):
            if real not in ids:
                ids.append(real)
    ids = ids[:_MAX_EVIDENCE]
    blocks = [f"[{i}] {kb.get(i).citation}\n{kb.get(i).body}" for i in ids]
    return "\n\n".join(blocks), ids


def review(state: ImpactState) -> dict:
    evidence, ids = build_evidence(state["draft_report"], _kb(state))
    transcript, redlines = review_draft(
        draft_report=state["draft_report"],
        regulation_name=state["regulation_name"],
        evidence=evidence,
    )
    return {
        "committee_transcript": transcript,
        "committee_redlines": redlines,
        # appended via the operator.add reducer — the audit log shows exactly
        # which source text the committee was given
        "retrieval_calls": [{"tool": "review_evidence", "query": "provisions cited in draft",
                             "chunk_ids": ids}],
    }


# --------------------------------------------------------------------------- #
# 6. human_gate — pause for a compliance officer                               #
# --------------------------------------------------------------------------- #
def human_gate(state: ImpactState) -> dict:
    """CONCEPT — interrupt()

    `interrupt(payload)` freezes the graph mid-run and persists everything to the
    checkpointer. The payload is handed back to whoever called `.invoke`. The run
    resumes only when the caller invokes again with
    `Command(resume=<their answer>)`, and execution re-enters THIS node from the
    top with `interrupt(...)` now returning that answer.
    """
    decision = interrupt({
        "question": "Approve this assessment, or type revision instructions.",
        "regulation": state["regulation_name"],
        "draft_report": state["draft_report"],
        "committee_redlines": state["committee_redlines"],
        "citation_report": state.get("citation_report", {}),
        "revision_count": state.get("revision_count", 0),
    })
    return {"human_decision": str(decision).strip()}


# --------------------------------------------------------------------------- #
# 7. revise — apply redlines + human feedback                                  #
# --------------------------------------------------------------------------- #
def revise(state: ImpactState) -> dict:
    msg = langchain_model().invoke([
        SystemMessage(
            "Revise the impact assessment. Apply the committee redlines and the "
            "reviewer's instructions. Keep the same section structure and keep "
            "every bracketed [chunk_id] citation. Return the full revised document."
        ),
        HumanMessage(
            f"=== CURRENT DRAFT ===\n{state['draft_report']}\n\n"
            f"=== COMMITTEE REDLINES ===\n{state['committee_redlines']}\n\n"
            f"=== REVIEWER INSTRUCTIONS ===\n{state.get('human_decision', '')}"
        ),
    ])
    return {
        "draft_report": msg.text,
        "revision_count": state.get("revision_count", 0) + 1,
    }


# --------------------------------------------------------------------------- #
# 8. finalize — re-verify, render citations, append sources                    #
# --------------------------------------------------------------------------- #
def finalize(state: ImpactState) -> dict:
    kb = _kb(state)
    report = verify_citations(state["draft_report"], kb, _retrieved_ids(state))
    return {
        "final_citation_report": report.as_dict(),
        "final_report": render_report(state["draft_report"], kb, report),
    }


def render_report(text: str, kb: KnowledgeBase, report) -> str:
    """Swap [chunk_id] tags for human citations and append a Sources section.

    Board readers get "[DORA Art. 19(4)]"; anything that failed verification
    is visibly marked rather than silently kept.
    """
    flagged = set(report.not_retrieved) | set(report.unknown)

    def label(token: str) -> str:
        cid, points = parse_cite(token)  # keep "(b)" for the reader
        ids = kb.resolve(cid)
        text_ = (kb.get(ids[0]).citation if ids else cid) + points
        return f"{text_} — unverified" if cid in flagged else text_

    def human(m: re.Match) -> str:
        tokens = [t for t in re.split(r"[,;]", m.group(1)) if "::" in t]
        if not tokens:
            return m.group(0)  # not a citation group — leave as written
        labels = dict.fromkeys(label(t) for t in tokens)  # dedupe, keep order
        return f"[{'; '.join(labels)}]"

    body = CITE_GROUP_RE.sub(human, text)
    lines = ["", "## Sources", ""]
    for cid in extract_citations(text):
        ids = kb.resolve(cid)
        if not ids:
            lines.append(f"- `{cid}` — **not found in corpus**")
            continue
        c = kb.get(ids[0])
        title = f" — {c.article_title}" if c.article_title else ""
        status = "" if cid not in flagged else " — **cited but never retrieved**"
        lines.append(f"- {c.citation}{title} (`{cid}`){status}")
    lines.append("")
    lines.append(
        f"_Citation check: {len(report.verified)}/{report.total} citations "
        f"verified against retrieved source text._"
    )
    return body.rstrip() + "\n" + "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# conditional edge: where to go after the human gate                           #
# --------------------------------------------------------------------------- #
def route_after_human(state: ImpactState) -> str:
    decision = state.get("human_decision", "").lower()
    if decision.startswith("approve"):
        return "finalize"
    if state.get("revision_count", 0) >= _MAX_REVISIONS:
        return "finalize"  # safety valve: don't loop forever
    return "revise"


# --------------------------------------------------------------------------- #
# helpers                                                                      #
# --------------------------------------------------------------------------- #
def _parse_json_list(text: str) -> list[str]:
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            return [str(x) for x in json.loads(match.group(0))]
        except json.JSONDecodeError:
            pass
    # last resort: split lines
    return [ln.strip("-* ").strip() for ln in text.splitlines() if ln.strip()][:6]
