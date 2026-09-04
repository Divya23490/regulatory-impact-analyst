"""The shared state for the LangGraph spine.

CONCEPT — LangGraph state
-------------------------
A LangGraph graph is a state machine. Every node is a plain function:

    (state) -> partial state update

LangGraph merges that partial dict back into the running state using a *reducer*
per field. The default reducer is "last write wins" (the new value replaces the
old one), which is all we need here. When you want accumulation instead
(e.g. a chat message list that grows), you annotate the field with a reducer such
as `operator.add` or `add_messages`.

We use `total=False` so a node can return just the keys it changed.
"""

from __future__ import annotations

from typing import TypedDict


class ImpactState(TypedDict, total=False):
    # ---- inputs ----
    regulation_name: str          # e.g. "DORA"
    regulation_text: str          # raw excerpt of the regulation
    policy_register_path: str     # path to a CSV of the bank's internal policies

    # ---- produced by the triage node ----
    themes: list[str]             # 3-6 impact areas to research

    # ---- produced by the Deep Agents research worker ----
    research_findings: str        # consolidated markdown
    research_files: dict[str, dict]  # deep agent's virtual FS: name -> FileData
                                      # ({"content": ..., "encoding": ...})

    # ---- produced by the drafting node ----
    draft_report: str

    # ---- produced by the AutoGen review committee ----
    committee_transcript: str     # full debate, for the audit trail
    committee_redlines: str       # the consolidated change requests

    # ---- human-in-the-loop ----
    human_decision: str           # "approve" or free-text revision instructions
    revision_count: int

    # ---- final ----
    final_report: str
