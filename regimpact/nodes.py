"""Node functions for the LangGraph spine.

Each function takes the whole `ImpactState` and returns a dict with only the keys
it changed. Nothing here knows *how* the graph is wired — that is graph.py's job.
"""

from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.types import interrupt

from .config import langchain_model
from .research_agent import run_research
from .review_committee import review_draft
from .state import ImpactState

_MAX_REVISIONS = 2


# --------------------------------------------------------------------------- #
# 1. triage — split the regulation into researchable themes                     #
# --------------------------------------------------------------------------- #
def triage(state: ImpactState) -> dict:
    model = langchain_model()
    msg = model.invoke([
        SystemMessage(
            "You are a regulatory analyst. Read the regulation excerpt and return "
            "the 3-6 distinct areas where it will most affect a retail/commercial "
            "bank. Reply with ONLY a JSON array of short strings."
        ),
        HumanMessage(
            f"Regulation: {state['regulation_name']}\n\n{state['regulation_text']}"
        ),
    ])
    # `.text` (not `.content`) — Gemini returns content as a list of typed
    # blocks (text + a "thought signature" for its reasoning), not a plain
    # string. `.text` is LangChain's provider-agnostic way to get the string.
    themes = _parse_json_list(msg.text)
    return {"themes": themes, "revision_count": 0}


# --------------------------------------------------------------------------- #
# 2. research — hand off to the Deep Agent                                      #
# --------------------------------------------------------------------------- #
def research(state: ImpactState) -> dict:
    findings, files = run_research(
        regulation_name=state["regulation_name"],
        regulation_text=state["regulation_text"],
        themes=state["themes"],
        policy_register_path=state["policy_register_path"],
    )
    return {"research_findings": findings, "research_files": files}


# --------------------------------------------------------------------------- #
# 3. draft — assemble the first full report                                     #
# --------------------------------------------------------------------------- #
def draft(state: ImpactState) -> dict:
    model = langchain_model()
    msg = model.invoke([
        SystemMessage(
            "You write the formal Regulatory Impact Assessment for a bank's "
            "board. Use these sections exactly: '# <Regulation> — Impact "
            "Assessment', '## Executive summary', '## Affected policies', "
            "'## Gap analysis', '## Recommended actions' (a numbered list with an "
            "owner and a priority H/M/L each), '## Open questions'. Ground every "
            "claim in the research findings; cite policy IDs."
        ),
        HumanMessage(
            f"Regulation: {state['regulation_name']}\n\n"
            f"=== RESEARCH FINDINGS ===\n{state['research_findings']}"
        ),
    ])
    return {"draft_report": msg.text}


# --------------------------------------------------------------------------- #
# 4. review — hand off to the AutoGen committee                                #
# --------------------------------------------------------------------------- #
def review(state: ImpactState) -> dict:
    transcript, redlines = review_draft(
        draft_report=state["draft_report"],
        regulation_name=state["regulation_name"],
    )
    return {"committee_transcript": transcript, "committee_redlines": redlines}


# --------------------------------------------------------------------------- #
# 5. human_gate — pause for a compliance officer                               #
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
        "revision_count": state.get("revision_count", 0),
    })
    return {"human_decision": str(decision).strip()}


# --------------------------------------------------------------------------- #
# 6. revise — apply redlines + human feedback                                  #
# --------------------------------------------------------------------------- #
def revise(state: ImpactState) -> dict:
    model = langchain_model()
    msg = model.invoke([
        SystemMessage(
            "Revise the impact assessment. Apply the committee redlines and the "
            "reviewer's instructions. Keep the same section structure. Return the "
            "full revised document."
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
# 7. finalize                                                                  #
# --------------------------------------------------------------------------- #
def finalize(state: ImpactState) -> dict:
    return {"final_report": state["draft_report"]}


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
