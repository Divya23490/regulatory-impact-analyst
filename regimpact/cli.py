"""Command-line entrypoint.

    regimpact run --regulation dora [--auto-approve]   # the full pipeline (default command)
    regimpact index [--rebuild] [--offline]            # build / refresh the vector index
    regimpact search "how fast must we report an incident" --regulation dora [--mode bm25|dense|hybrid]
    regimpact eval [--offline]                         # retrieval eval: recall@k / MRR
    regimpact ingest --celex 32022R2554 --name dora --title "..."

`regimpact --regulation dora` (no subcommand) still means `run`.

The interesting part of `run` is the interrupt/resume loop: `graph.invoke`
returns with an `__interrupt__` key instead of a final state whenever a node
called `interrupt()`. We show the payload, collect a human answer, and call
`invoke` again with `Command(resume=answer)` and the SAME thread_id so the
checkpointer picks up exactly where it stopped.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import uuid
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from .config import INDEX_DIR, POLICIES_CSV, REGULATIONS_DIR

console = Console()
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
_COMMANDS = {"run", "index", "search", "eval", "ingest"}


# --------------------------------------------------------------------------- #
# run                                                                         #
# --------------------------------------------------------------------------- #
def _show_interrupt(payload: dict) -> None:
    console.rule("[bold yellow]HUMAN REVIEW REQUIRED")
    console.print(f"[bold]Regulation:[/bold] {payload.get('regulation')}  "
                  f"(revision {payload.get('revision_count', 0)})")
    rep = payload.get("citation_report") or {}
    if rep:
        console.print(f"[bold]Research citations:[/bold] {len(rep.get('verified', []))}"
                      f"/{rep.get('total', 0)} verified against retrieved text"
                      + (f" — [red]flagged: {rep['not_retrieved'] + rep['unknown']}[/red]"
                         if rep.get("not_retrieved") or rep.get("unknown") else ""))
    console.print(Panel(Markdown(payload.get("draft_report", "")),
                        title="Draft assessment", border_style="cyan"))
    console.print(Panel(Markdown(payload.get("committee_redlines", "")),
                        title="Committee redlines", border_style="magenta"))


def _persist(state: dict, reg: str) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = OUT / f"{reg}-{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "impact_assessment.md").write_text(state["final_report"], encoding="utf-8")
    (run_dir / "committee_transcript.md").write_text(
        state.get("committee_transcript", ""), encoding="utf-8")
    # The RAG audit trail: every search any agent ran, and the citation checks.
    (run_dir / "retrieval_log.json").write_text(
        json.dumps(state.get("retrieval_calls", []), indent=2), encoding="utf-8")
    (run_dir / "citation_report.json").write_text(json.dumps({
        "research_findings": state.get("citation_report", {}),
        "final_report": state.get("final_citation_report", {}),
    }, indent=2), encoding="utf-8")
    research_dir = run_dir / "research_files"
    research_dir.mkdir(exist_ok=True)
    for name, entry in (state.get("research_files") or {}).items():
        # deepagents stores each virtual file as a FileData dict
        # ({"content": ..., "encoding": ...}), not a bare string.
        body = entry["content"] if isinstance(entry, dict) else entry
        # deepagents' `StateBackend` names virtual files with the real,
        # absolute cwd the agent ran from (e.g.
        # "/Users/you/.../regulatory-impact-analyst/findings.md"), not a clean
        # "/findings.md" root as its docs imply. Two problems follow:
        #   1. `research_dir / name` — pathlib treats a leading "/" on the
        #      right-hand side as absolute and DISCARDS research_dir,
        #      resolving to real filesystem root (crashed as read-only once).
        #   2. Preserving that path as nested directories would recreate the
        #      operator's local username/filesystem layout inside a
        #      version-controlled example run.
        # We only want the leaf filename, so take the basename and flatten.
        dest = research_dir / Path(name).name
        dest.write_text(body, encoding="utf-8")
    return run_dir


def cmd_run(args) -> None:
    from langgraph.types import Command

    from .graph import build_graph
    from .rag.chunking import short_name
    from .rag.knowledge_base import get_knowledge_base

    reg_path = REGULATIONS_DIR / f"{args.regulation}.md"
    if not reg_path.exists():
        raise SystemExit(f"No regulation file at {reg_path} — see `regimpact ingest`.")
    policies = str(Path(args.policies) if args.policies else POLICIES_CSV)
    name = short_name(reg_path.read_text(encoding="utf-8"), args.regulation.upper())

    get_knowledge_base(policies)  # build/load the index up front, before any LLM call

    graph = build_graph()
    config = {"configurable": {"thread_id": f"regimpact-{uuid.uuid4().hex[:8]}"}}
    state_in = {
        "regulation_source": args.regulation,
        "regulation_name": name,
        "policy_register_path": policies,
    }

    console.rule(f"[bold green]Analysing {name}")
    result = graph.invoke(state_in, config)

    while "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        if args.auto_approve:
            answer = "approve"
            console.print("[dim]--auto-approve: answering 'approve'[/dim]")
        else:
            _show_interrupt(payload)
            answer = console.input(
                "\n[bold]approve[/bold] / type revision instructions > ").strip() or "approve"
        result = graph.invoke(Command(resume=answer), config)

    run_dir = _persist(result, args.regulation)
    console.rule("[bold green]FINAL ASSESSMENT")
    console.print(Markdown(result["final_report"]))
    calls = result.get("retrieval_calls", [])
    console.print(f"\n[green]Saved to[/green] {run_dir}  "
                  f"[dim]({len(calls)} retrieval calls logged)[/dim]")


# --------------------------------------------------------------------------- #
# index / search                                                              #
# --------------------------------------------------------------------------- #
def _load_kb(args, rebuild: bool = False):
    from .rag.embeddings import HashingEmbedder, default_embedder
    from .rag.knowledge_base import KnowledgeBase

    return KnowledgeBase.load(
        regulations_dir=REGULATIONS_DIR,
        policies_csv=POLICIES_CSV,
        index_dir=INDEX_DIR,
        embedder=HashingEmbedder() if getattr(args, "offline", False) else default_embedder(),
        rebuild=rebuild,
        log=lambda m: console.print(f"[dim]{m}[/dim]"),
    )


def cmd_index(args) -> None:
    from collections import Counter

    kb = _load_kb(args, rebuild=args.rebuild)
    info = kb.store.info()
    per_source = Counter(c.source for c in kb.chunks)
    console.print(f"[bold]{info.get('count')}[/bold] chunks indexed with "
                  f"[cyan]{info.get('embedder')}[/cyan] (built {info.get('built_at')})")
    for src, n in sorted(per_source.items()):
        console.print(f"  {src:18} {n:4} chunks")


def cmd_search(args) -> None:
    kb = _load_kb(args)
    kind = "policy" if args.regulation == "policies" else "regulation"
    source = None if kind == "policy" else args.regulation
    mode = args.mode or kb.mode
    hits = kb.retriever.search(args.query, top_k=args.k, kind=kind, source=source, mode=mode)
    t = Table(title=f"{mode} retrieval — {args.query!r}")
    for col in ("#", "chunk_id", "citation", "RRF", "BM25 rank", "dense rank", "text"):
        t.add_column(col, overflow="fold")
    for i, h in enumerate(hits, 1):
        t.add_row(str(i), h.chunk.chunk_id, h.chunk.citation, f"{h.score:.4f}",
                  str(h.bm25_rank or "—"), str(h.dense_rank or "—"),
                  h.chunk.body[:140].replace("\n", " ") + "…")
    console.print(t)


def cmd_eval(args) -> None:
    from .evaluation import run_retrieval_eval

    run_retrieval_eval(_load_kb(args), console=console)


# --------------------------------------------------------------------------- #
def main() -> None:
    argv = sys.argv[1:]
    if not argv or argv[0] not in _COMMANDS | {"-h", "--help"}:
        argv = ["run", *argv]  # backwards compatible: `regimpact --regulation dora`

    if argv[0] == "ingest":
        from .rag.ingest import main as ingest_main

        sys.argv = ["regimpact ingest", *argv[1:]]
        return ingest_main()

    ap = argparse.ArgumentParser(prog="regimpact", description="Regulatory Change Impact Analyst")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("run", help="run the full analysis pipeline")
    p.add_argument("--regulation", default="dora", help="basename in data/regulations/ (default: dora)")
    p.add_argument("--policies", help="path to a policy-register CSV")
    p.add_argument("--auto-approve", action="store_true",
                   help="answer every human gate with 'approve' (non-interactive)")
    p.set_defaults(fn=cmd_run)

    p = sub.add_parser("index", help="build or refresh the vector index")
    p.add_argument("--rebuild", action="store_true", help="force a rebuild")
    p.add_argument("--offline", action="store_true", help="use the offline hashing embedder")
    p.set_defaults(fn=cmd_index)

    p = sub.add_parser("search", help="query the knowledge base directly")
    p.add_argument("query")
    p.add_argument("--regulation", default="dora", help="dora | eu_ai_act | policies")
    p.add_argument("--mode", choices=["hybrid", "bm25", "dense"],
                   help="default: the mode the agents use (REGIMPACT_RETRIEVAL_MODE, 'auto')")
    p.add_argument("-k", type=int, default=5)
    p.add_argument("--offline", action="store_true", help="use the offline hashing embedder")
    p.set_defaults(fn=cmd_search)

    p = sub.add_parser("eval", help="retrieval eval: recall@k and MRR, BM25 vs dense vs hybrid")
    p.add_argument("--offline", action="store_true", help="use the offline hashing embedder")
    p.set_defaults(fn=cmd_eval)

    sub.add_parser("ingest", help="fetch an EU regulation by CELEX id (see --help)")

    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
