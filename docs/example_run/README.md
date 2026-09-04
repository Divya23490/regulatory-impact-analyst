# Example run

A real, unedited output from `regimpact --regulation dora --auto-approve`,
run against Gemini (`gemini-3.5-flash-lite`), 2026-09-04.

- [impact_assessment.md](impact_assessment.md) — the final report: LangGraph's
  `triage` → Deep Agents' `research` → `draft` → AutoGen's `review` committee,
  auto-approved at the human gate.
- [committee_transcript.md](committee_transcript.md) — the full AutoGen
  committee debate (Compliance / Risk / Legal / Devil's Advocate / Editor) that
  produced the redlines behind that report.

The per-run `research_files/` (the Deep Agent's virtual filesystem —
`theme_*.md` + `findings.md`) aren't included here: that run hit the free-tier
Gemini daily quota one step before the CLI wrote them to disk, which is also
what surfaced (and got a regression test for) the `FileData`-unwrapping bug in
`_persist` — see [tests/test_cli_persist.py](../../tests/test_cli_persist.py).
Run the CLI yourself to see the full `research_files/` set.
