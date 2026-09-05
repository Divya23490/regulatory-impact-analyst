"""Test the output-writing path in isolation — no API key, no graph run.

Both bugs here were caught by real runs, not written defensively in advance:
1. `TypeError: data must be str, not dict` — before `_persist` learned to
   unwrap deepagents' `FileData` dicts.
2. `OSError: Read-only file system: '/todos.md'` — `create_deep_agent`'s
   default `StateBackend` names virtual files with the real, absolute cwd
   the agent ran from (e.g. "/Users/you/project/findings.md"), not a clean
   "/findings.md" root. `research_dir / name` silently discards
   `research_dir`: pathlib treats a leading "/" on the right-hand side of
   `/` as absolute and resolves to real filesystem root. Fix: take just the
   basename.
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


def test_persist_handles_root_style_virtual_paths(tmp_path, monkeypatch):
    monkeypatch.setattr("regimpact.cli.OUT", tmp_path)
    state = {
        "final_report": "# Report",
        "committee_transcript": "",
        "research_files": {
            "/todos.md": {"content": "- [ ] task one", "encoding": "utf-8"},
            "/findings.md": {"content": "# Findings", "encoding": "utf-8"},
        },
    }
    run_dir = _persist(state, "dora")
    # Must land inside research_files/, never at the real filesystem root.
    assert (run_dir / "research_files" / "todos.md").read_text() == "- [ ] task one"
    assert (run_dir / "research_files" / "findings.md").read_text() == "# Findings"


def test_persist_flattens_a_full_absolute_virtual_path(tmp_path, monkeypatch):
    # The shape actually observed in a live run: the virtual "path" is a full
    # real-filesystem absolute path, not a tidy "/findings.md" root.
    monkeypatch.setattr("regimpact.cli.OUT", tmp_path)
    state = {
        "final_report": "# Report",
        "committee_transcript": "",
        "research_files": {
            "/Users/someone/project/findings.md": {
                "content": "# Findings", "encoding": "utf-8",
            },
        },
    }
    run_dir = _persist(state, "dora")
    assert (run_dir / "research_files" / "findings.md").read_text() == "# Findings"
    # Nothing named after the operator's home directory should be created.
    assert not (run_dir / "research_files" / "Users").exists()
