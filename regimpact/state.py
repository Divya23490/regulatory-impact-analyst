"""The shared state for the LangGraph spine.

CONCEPT — LangGraph state
-------------------------
A LangGraph graph is a state machine. Every node is a plain function:

    (state) -> partial state update

LangGraph merges that partial dict back into the running state using a *reducer*
per field. The default reducer is "last write wins" (the new value replaces the
old one), which is what most fields here need. `retrieval_calls` instead uses
`operator.add`, so the research agent's searches and the review committee's
searches *accumulate* into one audit log rather than overwrite each other.

We use `total=False` so a node can return just the keys it changed.
"""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict


class ImpactState(TypedDict, total=False):
    # ---- inputs ----
    regulation_source: str        # corpus key, e.g. "dora" (data/regulations/dora.md)
    regulation_name: str          # display name, e.g. "DORA"
    policy_register_path: str     # CSV of the bank's internal policies

    # ---- triage ----
    outline: str                  # chapter/article map of the regulation
    themes: list[str]             # 3-6 impact areas to research

    # ---- Deep Agents research (agentic RAG) ----
    research_findings: str        # findings.md, citing [chunk_id]s
    research_files: dict[str, dict]  # agent's virtual FS: name -> FileData
    # every search any agent ran: {"tool", "query", "chunk_ids"}; accumulates
    retrieval_calls: Annotated[list[dict], operator.add]

    # ---- deterministic citation check ----
    citation_report: dict         # verified / not_retrieved / unknown ids

    # ---- drafting ----
    draft_report: str

    # ---- AutoGen review committee ----
    committee_transcript: str
    committee_redlines: str

    # ---- human-in-the-loop ----
    human_decision: str           # "approve" or free-text revision instructions
    revision_count: int

    # ---- final ----
    final_citation_report: dict   # same check, run on the approved report
    final_report: str             # citations rendered + Sources appendix
