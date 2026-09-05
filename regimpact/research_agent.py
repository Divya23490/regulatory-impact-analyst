"""The deep-research worker, built with Deep Agents.

CONCEPT — Deep Agents
---------------------
`deepagents` is a thin layer on top of a LangGraph ReAct agent that adds the
four things you need for *long-horizon* work:

  1. A planning tool ("write_todos") so the model keeps an explicit task list
     instead of losing the thread after a few tool calls.
  2. A virtual filesystem (ls / read_file / write_file / edit_file) that lives in
     graph state. The agent writes intermediate notes to "files" and reads them
     back later — this is how it works on something bigger than one context
     window without drowning in its own output.
  3. Sub-agents: specialised child agents it can delegate to. Each sub-agent runs
     with its own clean context, so a big search dump does not pollute the main
     thread. Here we give it one `citation-checker`.
  4. A detailed system prompt describing the workflow.

`create_deep_agent(...)` returns a compiled LangGraph graph. We invoke it with a
`{"messages": [...]}` dict, exactly like any other LangGraph agent, and read the
resulting `files` dict out of its final state.
"""

from __future__ import annotations

import os
from pathlib import Path

from deepagents import create_deep_agent

from .config import langchain_model

# --------------------------------------------------------------------------- #
# Tools we hand to the agent                                                   #
# --------------------------------------------------------------------------- #


def search_regulatory_context(query: str) -> str:
    """Search for background on a regulatory topic.

    Uses Tavily if TAVILY_API_KEY is set; otherwise returns a clearly-marked
    stub so the demo runs offline. Swap this for your internal document store
    (Confluence, SharePoint, a vector DB) in a real deployment.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return (
            f"[STUB SEARCH — no TAVILY_API_KEY set] No external sources retrieved "
            f"for query: {query!r}. Reason from the regulation text provided in the "
            f"task and from the policy register."
        )
    try:
        from tavily import TavilyClient

        results = TavilyClient(api_key=api_key).search(query, max_results=4)
        lines = [f"- {r['title']}: {r['content'][:400]}" for r in results["results"]]
        return "\n".join(lines) or "No results."
    except Exception as exc:  # keep the agent running even if search breaks
        return f"[SEARCH ERROR] {exc}"


def read_policy_register(path: str) -> str:
    """Return the bank's internal policy register (a CSV) as text."""
    p = Path(path)
    if not p.exists():
        return f"[NOT FOUND] {path}"
    return p.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# Sub-agent: fact/citation checker                                             #
# --------------------------------------------------------------------------- #

CITATION_CHECKER = {
    "name": "citation-checker",
    "description": (
        "Use to sanity-check a specific factual claim about the regulation before "
        "it goes in the findings. Give it the claim and the relevant regulation "
        "text; it replies SUPPORTED / UNSUPPORTED / PARTIAL with a one-line reason."
    ),
    "system_prompt": (
        "You verify a single claim against the supplied regulation text. "
        "Answer with SUPPORTED, UNSUPPORTED, or PARTIAL, then one sentence of "
        "justification quoting the relevant phrase. Do not add anything else."
    ),
}


RESEARCH_SYSTEM_PROMPT = """\
You are a senior regulatory analyst at a Nordic bank. You produce the *research
layer* of a regulatory impact assessment — not the final report.

Workflow:
1. Call `write_todos` to lay out one research task per theme you were given.
2. For each theme:
     - Call `read_policy_register` once to see which internal policies exist.
     - Call `search_regulatory_context` for background if useful.
     - When you make a load-bearing factual claim about the regulation, delegate
       it to the `citation-checker` sub-agent before relying on it.
     - Write your notes for that theme to a file named `theme_<n>.md` using
       `write_file`.
3. When every theme file is written, use `write_file` to create `findings.md`:
   a consolidated markdown document with one `##` section per theme, each
   containing: what the regulation requires, which existing policies are
   affected (cite them by ID from the register), and the gap you see.
4. Reply to the user with a 3-sentence summary and nothing else — the detail
   belongs in `findings.md`.

Be concrete and cite policy IDs. If the search tool returns a stub, say so in the
findings and rely on the regulation text you were given.
"""


def build_research_agent():
    """Compile the Deep Agent. Called once; the returned graph is reusable."""
    return create_deep_agent(
        model=langchain_model(),
        tools=[search_regulatory_context, read_policy_register],
        system_prompt=RESEARCH_SYSTEM_PROMPT,
        subagents=[CITATION_CHECKER],
    )


def run_research(regulation_name: str, regulation_text: str, themes: list[str],
                 policy_register_path: str) -> tuple[str, dict[str, str]]:
    """Run the deep research pass.

    Returns (findings_markdown, files) where `files` is the agent's whole virtual
    filesystem so the caller can persist it for the audit trail.
    """
    agent = build_research_agent()
    theme_list = "\n".join(f"{i+1}. {t}" for i, t in enumerate(themes))
    task = (
        f"Regulation: {regulation_name}\n"
        f"Policy register path: {policy_register_path}\n\n"
        f"Themes to research:\n{theme_list}\n\n"
        f"--- REGULATION TEXT ---\n{regulation_text}\n"
    )

    # `recursion_limit` guards against a runaway plan-act loop.
    result = agent.invoke(
        {"messages": [{"role": "user", "content": task}]},
        {"recursion_limit": 50},
    )

    # Each virtual-filesystem entry is a `FileData` dict — {"content": ...,
    # "encoding": ..., "created_at": ..., "modified_at": ...} — not a bare
    # string, so callers need `_file_text` rather than reading the dict directly.
    files: dict[str, dict] = result.get("files", {}) or {}
    findings = _file_text(files, "findings.md")
    if not findings:
        # Fall back to the agent's chat summary if it forgot to write the file.
        findings = result["messages"][-1].text
    return findings, files


def _file_text(files: dict[str, dict], name: str) -> str | None:
    """Pull the text content out of a deepagents virtual-filesystem entry.

    deepagents' virtual filesystem is root-based — it writes `/findings.md`,
    not `findings.md` — but the exact leading-slash convention isn't part of
    its public contract, so we look up both forms rather than assume one.
    """
    bare = name.lstrip("/")
    entry = files.get(name, files.get(bare, files.get(f"/{bare}")))
    if entry is None:
        return None
    return entry["content"] if isinstance(entry, dict) else entry
