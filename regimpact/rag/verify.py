"""Citation verification — the anti-hallucination guard for RAG output.

CONCEPT — grounding you can check
---------------------------------
RAG reduces hallucination but doesn't eliminate it: a model can cite a
provision it never retrieved (recalled from training data, possibly wrong or
outdated) or invent an id outright. Because every chunk has a stable id and
the research agent must cite those ids in [brackets], verification is plain
deterministic code — no second LLM call:

    verified       id exists in the corpus AND was retrieved in this run
    not_retrieved  id exists, but was never retrieved — the model "knew" it
                   rather than read it; plausible, not grounded
    unknown        id doesn't exist in the corpus — fabricated

Same principle as danish-legal-checker's CitationVerifier: an unverifiable
claim is worse than an admitted gap, so unverified citations are reported,
not silently passed through.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from .knowledge_base import KnowledgeBase

# A bracket group holding one or more ids: "[dora::art19::p4]" or, as models
# often write it, "[dora::art5::p2.2, dora::art6::p1]". Matching single-id
# brackets only once let every grouped citation go unchecked (a live-run bug).
CITE_GROUP_RE = re.compile(r"\[([^\[\]]*?::[^\[\]]*?)\]")
# An id, optionally followed by point references the model adds: "p3(b)", "p3(e)(i)".
_ID_RE = re.compile(r"^([a-z_]+::[A-Za-z0-9_.:-]+?)((?:\([a-z0-9]+\))*)$")


def parse_cite(token: str) -> tuple[str, str]:
    """'dora::art17::p3(b)' -> ('dora::art17::p3', '(b)').

    Anything that looks like a citation (contains '::') but doesn't parse is
    returned as-is, so it resolves to nothing and is flagged `unknown`.
    A verifier must never silently drop a citation-shaped string — an earlier
    version did, and an unchecked citation looks exactly like a passing one.
    """
    token = token.strip()
    m = _ID_RE.match(token)
    return (m.group(1), m.group(2)) if m else (token, "")


def split_group(group: str) -> list[str]:
    """'dora::art5::p2.2, dora::art17::p3(b)' -> normalised ids."""
    return [parse_cite(p)[0] for p in re.split(r"[,;]", group) if "::" in p]


@dataclass
class CitationReport:
    verified: list[str] = field(default_factory=list)
    not_retrieved: list[str] = field(default_factory=list)
    unknown: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.verified) + len(self.not_retrieved) + len(self.unknown)

    @property
    def grounded_ratio(self) -> float:
        return len(self.verified) / self.total if self.total else 0.0

    def as_dict(self) -> dict:
        return {**asdict(self), "total": self.total, "grounded_ratio": round(self.grounded_ratio, 3)}


def extract_citations(text: str) -> list[str]:
    """Unique bracketed chunk ids, in order of first appearance."""
    seen: dict[str, None] = {}
    for m in CITE_GROUP_RE.finditer(text):
        for cid in split_group(m.group(1)):
            seen.setdefault(cid, None)
    return list(seen)


def verify_citations(text: str, kb: KnowledgeBase, retrieved_ids: set[str]) -> CitationReport:
    report = CitationReport()
    for cid in extract_citations(text):
        real = kb.resolve(cid)
        if not real:
            report.unknown.append(cid)
        elif any(r in retrieved_ids for r in real):
            report.verified.append(cid)
        else:
            report.not_retrieved.append(cid)
    return report
