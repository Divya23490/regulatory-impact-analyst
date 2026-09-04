"""The review committee, built with AutoGen (autogen-agentchat 0.4+ API).

CONCEPT — AutoGen multi-agent teams
-----------------------------------
AutoGen models a *conversation* between agents. You create several
`AssistantAgent`s, each with its own system message / persona, drop them into a
`Team`, and give the team a task. The agents then talk in turns until a
`TerminationCondition` fires.

  * `RoundRobinGroupChat` — agents speak in a fixed cycle. Deterministic, cheap,
    easy to reason about. We use this.
  * `SelectorGroupChat` — an LLM picks who speaks next. More lifelike, more
    tokens, less predictable.

Why a committee here? A single "critique this report" prompt gives you one
flattened opinion. Four agents with genuinely different mandates (compliance,
risk, legal, a contrarian) surface disagreements a bank actually cares about,
and the transcript itself is useful evidence for the audit trail.

The whole thing is async, so we expose a small sync wrapper (`review_draft`) that
the LangGraph node can call.
"""

from __future__ import annotations

import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat

from .config import autogen_model_client

_STOP = "REDLINES_COMPLETE"


def _committee(model_client) -> RoundRobinGroupChat:
    compliance = AssistantAgent(
        "ComplianceOfficer",
        model_client=model_client,
        system_message=(
            "You are the Group Compliance Officer. Check the draft impact "
            "assessment for: missing obligations, wrong deadlines, and articles "
            "of the regulation that are not addressed. Be specific and terse. "
            "Raise at most 3 points."
        ),
    )
    risk = AssistantAgent(
        "RiskOfficer",
        model_client=model_client,
        system_message=(
            "You are the Chief Risk Officer. Focus only on whether the draft "
            "correctly sizes operational, ICT and third-party risk, and whether "
            "the proposed actions are proportionate. Raise at most 3 points."
        ),
    )
    legal = AssistantAgent(
        "LegalCounsel",
        model_client=model_client,
        system_message=(
            "You are Legal Counsel. Focus only on contractual and enforceability "
            "issues: outsourcing clauses, liability, notification duties. Raise "
            "at most 3 points."
        ),
    )
    contrarian = AssistantAgent(
        "DevilsAdvocate",
        model_client=model_client,
        system_message=(
            "You are the Devil's Advocate. Challenge the draft's assumptions, "
            "call out anything vague or over-confident, and name one risk the "
            "others missed. Exactly 2 points."
        ),
    )
    editor = AssistantAgent(
        "Editor",
        model_client=model_client,
        system_message=(
            "You are the Editor. You speak LAST. Consolidate every point raised "
            "into a single numbered redline list titled 'REDLINES'. Each item: "
            "one sentence, actionable, referencing the section it changes. "
            f"After the list, output the token {_STOP} on its own line."
        ),
    )

    termination = TextMentionTermination(_STOP) | MaxMessageTermination(12)
    return RoundRobinGroupChat(
        [compliance, risk, legal, contrarian, editor],
        termination_condition=termination,
    )


async def _run(draft_report: str, regulation_name: str) -> tuple[str, str]:
    model_client = autogen_model_client()
    team = _committee(model_client)
    task = (
        f"Review this draft {regulation_name} impact assessment. One round only; "
        f"the Editor then consolidates.\n\n--- DRAFT ---\n{draft_report}"
    )
    result = await team.run(task=task)

    transcript_lines = [
        f"### {m.source}\n{m.to_text()}" for m in result.messages
    ]
    transcript = "\n\n".join(transcript_lines)

    # The redlines are whatever the Editor said last, minus the stop token.
    redlines = next(
        (m.to_text().replace(_STOP, "").strip()
         for m in reversed(result.messages) if m.source == "Editor"),
        "REDLINES\n(none captured)",
    )
    await model_client.close()
    return transcript, redlines


def review_draft(draft_report: str, regulation_name: str) -> tuple[str, str]:
    """Sync wrapper. Returns (full_transcript, consolidated_redlines)."""
    return asyncio.run(_run(draft_report, regulation_name))
