"""Structural tests — no API key required.

They check the wiring (nodes, routing, parsing helpers), not the model output.
Run: .venv/bin/python -m pytest
"""

from regimpact.graph import build_graph
from regimpact.nodes import _parse_json_list, route_after_human
from regimpact.research_agent import _file_text


def test_graph_has_all_nodes():
    g = build_graph()
    nodes = set(g.get_graph().nodes)
    assert {"triage", "research", "draft", "review",
            "human_gate", "revise", "finalize"} <= nodes


def test_router_approve_goes_to_finalize():
    assert route_after_human({"human_decision": "approve"}) == "finalize"
    assert route_after_human({"human_decision": "Approve, looks good"}) == "finalize"


def test_router_feedback_goes_to_revise():
    state = {"human_decision": "tighten the exec summary", "revision_count": 0}
    assert route_after_human(state) == "revise"


def test_router_stops_looping_after_max_revisions():
    state = {"human_decision": "more changes", "revision_count": 2}
    assert route_after_human(state) == "finalize"


def test_parse_json_list_handles_a_json_array():
    assert _parse_json_list('["a", "b", "c"]') == ["a", "b", "c"]


def test_parse_json_list_falls_back_to_lines():
    out = _parse_json_list("- first\n- second")
    assert out == ["first", "second"]


def test_file_text_unwraps_a_filedata_dict():
    # deepagents stores each virtual file as {"content": ..., "encoding": ...},
    # not a bare string — this was a live bug (persistence crashed on it) until
    # `_file_text` was added to normalize both shapes.
    files = {"findings.md": {"content": "# Findings", "encoding": "utf-8"}}
    assert _file_text(files, "findings.md") == "# Findings"


def test_file_text_still_accepts_a_plain_string():
    files = {"findings.md": "# Findings"}
    assert _file_text(files, "findings.md") == "# Findings"


def test_file_text_missing_file_returns_none():
    assert _file_text({}, "findings.md") is None
