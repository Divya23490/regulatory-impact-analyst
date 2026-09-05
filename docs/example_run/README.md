# Example run

A real, unedited output from `regimpact --regulation dora --auto-approve`,
run against Gemini (`gemini-3.5-flash-lite`), 2026-09-05.

- [impact_assessment.md](impact_assessment.md) — the final report: LangGraph's
  `triage` → Deep Agents' `research` → `draft` → AutoGen's `review` committee,
  auto-approved at the human gate.
- [committee_transcript.md](committee_transcript.md) — the full AutoGen
  committee debate (Compliance / Risk / Legal / Devil's Advocate / Editor) that
  produced the redlines behind that report.
- [research_files/](research_files/) — the Deep Agent's virtual filesystem for
  this run: `theme_1.md` … `theme_6.md` (one per researched theme) and the
  consolidated `findings.md` that `draft` was grounded in.

This particular run also happens to be why two bugs are fixed and
regression-tested (see [tests/test_cli_persist.py](../../tests/test_cli_persist.py)):
deepagents wraps each virtual file as a `{"content": ..., "encoding": ...}`
dict rather than a bare string, and its default `StateBackend` names files
after the real, absolute working directory the agent ran from rather than a
clean `/findings.md` root — both broke `_persist` on a live run before being
fixed and locked in with tests.
