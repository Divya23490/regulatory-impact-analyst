"""The deep-research worker, built with Deep Agents — retrieval-augmented.

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
     with its own clean context, so a big retrieval dump does not pollute the
     main thread. Here: a `citation-checker`.
  4. A detailed system prompt describing the workflow.

CONCEPT — agentic RAG
---------------------
Classic RAG is one fixed step: embed the question, fetch top-k, generate. Here
the *agent* decides what to retrieve and when: it plans one task per theme,
issues its own search queries (several per theme, reformulating if the first
results miss), reads the provisions, and cites them by id. The regulation is
~50k tokens — too big to paste in — so retrieval is the only way the agent
sees it at all.

Tools are built per run as closures over the KnowledgeBase and a RetrievalLog,
so (a) the agent can only search the regulation under analysis (metadata
filter), and (b) every chunk it was shown is recorded — the citation verifier
uses that log to prove each citation was actually retrieved, not recalled.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field

from deepagents import create_deep_agent

from .config import langchain_model
from .rag.knowledge_base import KnowledgeBase, format_hits


# --------------------------------------------------------------------------- #
# Retrieval log — the audit trail of what the agent actually read             #
# --------------------------------------------------------------------------- #
@dataclass
class RetrievalLog:
    calls: list[dict] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def record(self, tool: str, query: str, chunk_ids: list[str]) -> None:
        # Deep Agents may run several tool calls of one turn in parallel threads.
        with self._lock:
            self.calls.append({"tool": tool, "query": query, "chunk_ids": chunk_ids})

    @property
    def chunk_ids(self) -> set[str]:
        return {cid for call in self.calls for cid in call["chunk_ids"]}


def make_rag_tools(kb: KnowledgeBase, source: str, log: RetrievalLog):
    """Build the agent's retrieval tools, scoped to one regulation.

    LangChain turns each function's name, type hints and docstring into the
    tool schema the model sees — so the docstrings below are prompt text.
    """

    def search_regulation(query: str) -> str:
        """Search the official regulation text. Returns the 5 most relevant
        provisions, each headed by its [chunk_id] and article citation. Use
        specific queries (e.g. 'deadline for initial notification of major
        ICT-related incident'), and search again with different wording if
        the results don't answer the question."""
        hits = kb.search_regulation(query, source=source, k=5)
        log.record("search_regulation", query, [h.chunk.chunk_id for h in hits])
        return format_hits(hits)

    def search_policies(query: str) -> str:
        """Search the bank's internal policy register. Returns the most
        relevant internal policies, each headed by its [policy::ID]."""
        hits = kb.search_policies(query, k=4)
        log.record("search_policies", query, [h.chunk.chunk_id for h in hits])
        return format_hits(hits)

    def get_provision(chunk_id: str) -> str:
        """Fetch the exact text of one provision by its chunk_id
        (e.g. 'dora::art19::p4'). Use to check a claim against the source."""
        ids = kb.resolve(chunk_id.strip("[] "))
        if not ids:
            return f"No provision with id {chunk_id!r} exists in the corpus."
        log.record("get_provision", chunk_id, ids)
        return "\n\n".join(f"[{i}] {kb.get(i).citation}\n{kb.get(i).body}" for i in ids)

    return search_regulation, search_policies, get_provision


# --------------------------------------------------------------------------- #
# Agent                                                                       #
# --------------------------------------------------------------------------- #
RESEARCH_SYSTEM_PROMPT = """\
You are a senior regulatory analyst at a Nordic bank. You produce the *research
layer* of a regulatory impact assessment — not the final report.

You can only see the regulation through `search_regulation`, and the bank's
policies through `search_policies`. Do not rely on memory of the regulation:
if you didn't retrieve it, you can't cite it.

Workflow:
1. Call `write_todos` with one research task per theme you were given.
2. For each theme:
     - Call `search_regulation` with a focused query; search again with
       different wording if the results don't cover the theme.
     - Call `search_policies` to find the internal policies it affects.
     - For any load-bearing claim (deadlines, frequencies, thresholds,
       mandatory contract terms), delegate to the `citation-checker`
       sub-agent with the claim and the chunk_id you're relying on.
     - Write notes for the theme to `theme_<n>.md` with `write_file`.
3. Then `write_file` a consolidated `findings.md`: one `##` section per
   theme with (a) what the regulation requires, (b) which internal policies
   are affected, (c) the gap.
4. Reply with a 3-sentence summary only — the detail belongs in findings.md.

CITATION RULE: every statement about the regulation or a policy ends with the
bracketed id(s) exactly as shown in the search results, e.g.
"Major incidents need an initial notification [dora::art19::p4]" or
"…not covered by the outsourcing policy [policy::POL-005]". Never invent an id.
"""

CITATION_CHECKER_PROMPT = (
    "You verify ONE claim about a regulation. Fetch the cited provision with "
    "`get_provision` (and `search_regulation` if the citation looks wrong). "
    "Answer SUPPORTED, UNSUPPORTED or PARTIAL, then one sentence quoting the "
    "decisive phrase and its [chunk_id]. Nothing else."
)


def run_research(
    *,
    kb: KnowledgeBase,
    source: str,
    regulation_name: str,
    themes: list[str],
) -> tuple[str, dict, list[dict]]:
    """Run the deep research pass.

    Returns (findings_markdown, files, retrieval_calls): `files` is the agent's
    virtual filesystem and `retrieval_calls` every search it made — both are
    persisted for the audit trail.
    """
    log = RetrievalLog()
    search_regulation, search_policies, get_provision = make_rag_tools(kb, source, log)

    agent = create_deep_agent(
        model=langchain_model(),
        tools=[search_regulation, search_policies],
        system_prompt=RESEARCH_SYSTEM_PROMPT,
        subagents=[{
            "name": "citation-checker",
            "description": (
                "Checks one factual claim against the regulation text. Give it "
                "the claim and the [chunk_id] it relies on; it replies "
                "SUPPORTED / UNSUPPORTED / PARTIAL with the decisive quote."
            ),
            "system_prompt": CITATION_CHECKER_PROMPT,
            "tools": [get_provision, search_regulation],
        }],
    )

    theme_list = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(themes))
    task = (
        f"Regulation: {regulation_name}\n\n"
        f"Themes to research:\n{theme_list}\n"
    )
    # recursion_limit bounds the plan-act loop (each tool round trip is 2 steps).
    result = agent.invoke(
        {"messages": [{"role": "user", "content": task}]},
        {"recursion_limit": 150},
    )

    # Each virtual-filesystem entry is a `FileData` dict — {"content": ...,
    # "encoding": ..., "created_at": ..., "modified_at": ...} — not a bare
    # string, so callers need `_file_text` rather than reading the dict directly.
    files: dict[str, dict] = result.get("files", {}) or {}
    findings = _file_text(files, "findings.md")
    if not findings:
        # Fall back to the agent's chat summary if it forgot to write the file.
        findings = result["messages"][-1].text
    return findings, files, log.calls


def _file_text(files: dict[str, dict], name: str) -> str | None:
    """Pull the text content out of a deepagents virtual-filesystem entry.

    `create_deep_agent`'s default backend keys files by an absolute path
    (e.g. "/Users/you/project/findings.md"), so match on the basename.
    """
    bare = name.lstrip("/")
    entry = files.get(name, files.get(bare, files.get(f"/{bare}")))
    if entry is None:
        entry = next((v for k, v in files.items() if k.rsplit("/", 1)[-1] == bare), None)
    if entry is None:
        return None
    return entry["content"] if isinstance(entry, dict) else entry
