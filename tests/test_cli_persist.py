"""Test the output-writing path in isolation — no API key, no graph run.

This is the exact code path that crashed in a live run with
`TypeError: data must be str, not dict` before `_persist` learned to unwrap
deepagents' `FileData` dicts.
"""

from regimpact.cli import OUT, _persist


def test_persist_unwraps_filedata_entries(tmp_path, monkeypatch):
    monkeypatch.setattr("regimpact.cli.OUT", tmp_path)
    state = {
        "final_report": "# Report",
        "committee_transcript": "### Editor\nREDLINES",
        "research_files": {
            "findings.md": {"content": "# Findings", "encoding": "utf-8"},
            "theme_1.md": {"content": "notes", "encoding": "utf-8"},
        },
    }
    run_dir = _persist(state, "dora")
    assert (run_dir / "impact_assessment.md").read_text() == "# Report"
    assert (run_dir / "research_files" / "findings.md").read_text() == "# Findings"
    assert (run_dir / "research_files" / "theme_1.md").read_text() == "notes"
