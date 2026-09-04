"""Assemble the LangGraph spine.

CONCEPT — StateGraph
--------------------
`StateGraph(ImpactState)` is a builder. You:
  * `add_node("name", fn)`         — register a step
  * `add_edge("a", "b")`           — always go a -> b
  * `add_conditional_edges("a", router, {...})` — branch based on a function
  * `.compile(checkpointer=...)`   — freeze it into a runnable graph

CONCEPT — checkpointer
----------------------
The checkpointer persists state after every super-step, keyed by a `thread_id`
you pass in the run config. It is what makes `interrupt()` and "resume later"
possible, and in a bank it doubles as the audit trail. `MemorySaver` keeps it in
RAM (fine for a demo / tests); swap in `SqliteSaver` or `PostgresSaver` for real
persistence with no other code change.

CONCEPT — per-node retry policy
--------------------------------
Free-tier Gemini throws transient `503 high demand` errors often enough that a
demo run can otherwise die mid-pipeline. Rather than hand-roll retry loops
inside every node, LangGraph lets you attach a `RetryPolicy` to a node in
`add_node(...)`: if the node function raises, LangGraph re-invokes the *whole
node* with exponential backoff before giving up. For `research`, that means
re-running the entire Deep Agent task on failure — coarser than retrying just
the one failed LLM call, but simple, and fine for a step whose one job is to
produce `findings.md` from scratch each time.
"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from . import nodes
from .state import ImpactState

# Applied to every node that calls out to Gemini. `default_retry_on` already
# retries most exceptions (it excludes things like ValueError/TypeError that
# are almost certainly bugs, not transient faults).
_LLM_RETRY = RetryPolicy(max_attempts=4, initial_interval=2.0, backoff_factor=2.0)


def build_graph(checkpointer=None):
    g = StateGraph(ImpactState)

    g.add_node("triage", nodes.triage, retry_policy=_LLM_RETRY)
    g.add_node("research", nodes.research, retry_policy=_LLM_RETRY)
    g.add_node("draft", nodes.draft, retry_policy=_LLM_RETRY)
    g.add_node("review", nodes.review, retry_policy=_LLM_RETRY)
    g.add_node("human_gate", nodes.human_gate)
    g.add_node("revise", nodes.revise, retry_policy=_LLM_RETRY)
    g.add_node("finalize", nodes.finalize)

    g.add_edge(START, "triage")
    g.add_edge("triage", "research")
    g.add_edge("research", "draft")
    g.add_edge("draft", "review")
    g.add_edge("review", "human_gate")

    # after the human decides: approve -> finalize, else -> revise
    g.add_conditional_edges(
        "human_gate",
        nodes.route_after_human,
        {"finalize": "finalize", "revise": "revise"},
    )
    # a revision goes back through the committee
    g.add_edge("revise", "review")
    g.add_edge("finalize", END)

    return g.compile(checkpointer=checkpointer or MemorySaver())
