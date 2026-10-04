# Example run

A real, unedited output of `regimpact run --regulation dora --auto-approve`,
2026-10-04 — generation with `gemini-3.5-flash-lite`, retrieval over the official
DORA text indexed with `gemini-embedding-001` (dense mode, per the eval).

| File | What it shows |
|---|---|
| [impact_assessment.md](impact_assessment.md) | The final report. Every claim cites a provision ("[DORA Art. 28(3)]"); the **Sources** appendix maps each to its chunk id. Citation check: **22/22** verified against retrieved text. |
| [research_files/](research_files/) | The Deep Agent's virtual filesystem: its plan, one note per theme, and `findings.md` (24/24 citations verified). |
| [retrieval_log.json](retrieval_log.json) | The RAG audit trail — all 17 retrieval calls: 5 `search_regulation` and 5 `search_policies` by the research agent, 6 `get_provision` by its citation-checker sub-agent, and the review evidence pack (14 DORA provisions + 8 policies). |
| [citation_report.json](citation_report.json) | Verified / not-retrieved / unknown citations, for the research findings and for the approved report. |
| [committee_transcript.md](committee_transcript.md) | The AutoGen committee reviewing the draft *against the source text* — e.g. the Compliance Officer flags that the draft omits the yearly reporting duty in Art. 28(3) and the notification on leaving an information-sharing arrangement in Art. 45(3). |

The previous example in this folder (pre-RAG) was drafted from the agent's
3-sentence summary rather than its findings because of a filesystem-path bug,
and gave three internal policies the wrong titles. Nothing caught it then;
the citation verifier is the response.
