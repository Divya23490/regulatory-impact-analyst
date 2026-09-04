"""Command-line entrypoint.

Run:
    regimpact --regulation dora
    regimpact --regulation dora --auto-approve      # non-interactive demo

The interesting part is the interrupt/resume loop: `graph.invoke` returns with an
`__interrupt__` key instead of a final state whenever a node called `interrupt()`.
We show the payload, collect a human answer, and call `invoke` again with
`Command(resume=answer)` and the SAME thread_id so the checkpointer picks up
exactly where it stopped.
"""

from __future__ import annotations

import argparse
import datetime as dt
import uuid
from pathlib import Path

from langgraph.types import Command
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .graph import build_graph

console = Console()
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "outputs"


def _load_inputs(reg: str, policies: str | None):
    reg_path = DATA / "regulations" / f"{reg}.md"
    if not reg_path.exists():
        raise SystemExit(f"No regulation file at {reg_path}")
    pol_path = Path(policies) if policies else DATA / "policies" / "policy_register.csv"
    return {
        "regulation_name": reg.upper(),
        "regulation_text": reg_path.read_text(encoding="utf-8"),
        "policy_register_path": str(pol_path),
    }


def _show_interrupt(payload: dict) -> None:
    console.rule("[bold yellow]HUMAN REVIEW REQUIRED")
    console.print(f"[bold]Regulation:[/bold] {payload.get('regulation')}  "
                  f"(revision {payload.get('revision_count', 0)})")
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
    research_dir = run_dir / "research_files"
    research_dir.mkdir(exist_ok=True)
    for name, entry in (state.get("research_files") or {}).items():
        # deepagents stores each virtual file as a FileData dict
        # ({"content": ..., "encoding": ...}), not a bare string.
        body = entry["content"] if isinstance(entry, dict) else entry
        (research_dir / name).write_text(body, encoding="utf-8")
    return run_dir


def main() -> None:
    ap = argparse.ArgumentParser(description="Regulatory Change Impact Analyst")
    ap.add_argument("--regulation", default="dora",
                    help="basename of a file in data/regulations/ (default: dora)")
    ap.add_argument("--policies", help="path to a policy-register CSV")
    ap.add_argument("--auto-approve", action="store_true",
                    help="answer every human gate with 'approve' (non-interactive)")
    args = ap.parse_args()

    graph = build_graph()
    config = {"configurable": {"thread_id": f"regimpact-{uuid.uuid4().hex[:8]}"}}
    state_in = _load_inputs(args.regulation, args.policies)

    console.rule(f"[bold green]Analysing {state_in['regulation_name']}")
    result = graph.invoke(state_in, config)

    # interrupt/resume loop
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
    console.print(f"\n[green]Saved to[/green] {run_dir}")


if __name__ == "__main__":
    main()
