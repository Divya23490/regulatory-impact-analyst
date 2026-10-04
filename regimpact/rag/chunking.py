"""Turn regulation markdown and the policy register into retrieval chunks.

CONCEPT — chunking strategy
---------------------------
A chunk is the unit you retrieve, cite and show the model. Three choices:

1. **Structure-aware boundaries, not fixed token windows.** One chunk per
   numbered *paragraph* of an Article ("Article 19(1)"). A paragraph is the
   unit a compliance officer cites, it never cuts a rule in half, and the
   chunk id doubles as a legal citation. Fixed 512-token windows with overlap
   would split obligations mid-sentence and make citations meaningless.

2. **Contextual headers.** Every chunk's indexed text starts with
   "DORA — Article 19: Reporting of major ICT-related incidents … / CHAPTER III …".
   A bare paragraph like "2. Financial entities may, on a voluntary basis…"
   says nothing about *what* it governs; the header gives both BM25 and the
   embedding model the topic words.

3. **Size cap with lead-in carry-over.** Some paragraphs are huge (Article 3
   has ~65 definitions in one paragraph). Those are split at line boundaries
   into ~2,000-character parts, and each later part repeats the paragraph's
   lead-in line ("The contractual arrangements … shall include at least the
   following elements:") so a lone "(f) exit strategies…" keeps its meaning.
   2,000 characters is ~500 tokens: well under the embedding model's input
   limit, and small enough that a top-5 retrieval stays cheap to put in a
   prompt.

Chunk ids are stable and human-readable:
    dora::art19::p1        DORA Art. 19(1)
    dora::art3::p1.4       DORA Art. 3(1), part 4
    eu_ai_act::art4::s1    EU AI Act Art. 4   (unnumbered article text)
    policy::POL-005        internal policy row
"""

from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

MAX_CHARS = 2000
_ARTICLE_RE = re.compile(r"^### Article (\S+) — (.*)$")
_PARA_NUM_RE = re.compile(r"^(\d+)\.\s")


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    text: str            # what is embedded and BM25-indexed (header + body)
    body: str            # the provision text alone, for display
    kind: str            # "regulation" | "policy"
    source: str          # "dora" | "eu_ai_act" | "policy_register"
    citation: str        # "DORA Art. 19(1)" | "POL-005"
    article: str = ""
    article_title: str = ""
    chapter: str = ""

    def metadata(self) -> dict:
        """Flat metadata for the vector store (filterable at query time)."""
        return {
            "kind": self.kind,
            "source": self.source,
            "citation": self.citation,
            "article": self.article,
            "article_title": self.article_title,
            "chapter": self.chapter,
        }


# --------------------------------------------------------------------------- #
# regulations                                                                 #
# --------------------------------------------------------------------------- #
def short_name(markdown: str, fallback: str) -> str:
    """'# DORA — Regulation (EU) …' -> 'DORA'."""
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].split(" — ")[0].strip()
    return fallback


def chunk_regulation(path: Path | str) -> list[Chunk]:
    path = Path(path)
    source = path.stem
    md = path.read_text(encoding="utf-8")
    name = short_name(md, source.upper())

    chunks: list[Chunk] = []
    chapter = ""
    article = title = ""
    block: list[str] = []
    blocks: list[list[str]] = []

    def flush_article() -> None:
        if article:
            chunks.extend(_article_chunks(source, name, chapter_of_article, article, title, blocks))

    chapter_of_article = ""
    for line in md.splitlines():
        if line.startswith("## "):
            if block:
                blocks.append(block)
                block = []
            chapter = line[3:].strip()
            continue
        m = _ARTICLE_RE.match(line)
        if m:
            if block:
                blocks.append(block)
                block = []
            flush_article()
            article, title = m.group(1), m.group(2).strip()
            chapter_of_article = chapter
            blocks = []
            continue
        if not article or line.startswith("#") or line.startswith(">"):
            continue
        if line.strip():
            block.append(line.rstrip())
        elif block:
            blocks.append(block)
            block = []
    if block:
        blocks.append(block)
    flush_article()
    return chunks


def _article_chunks(source, name, chapter, article, title, blocks) -> list[Chunk]:
    out: list[Chunk] = []
    header = f"{name} — Article {article}: {title}\n{chapter}"
    unnumbered = 0
    for lines in blocks:
        m = _PARA_NUM_RE.match(lines[0])
        if m:
            para = m.group(1)
            base_id = f"{source}::art{article}::p{para}"
            citation = f"{name} Art. {article}({para})"
        else:
            unnumbered += 1
            base_id = f"{source}::art{article}::s{unnumbered}"
            citation = f"{name} Art. {article}"

        parts = _split(lines)
        for i, part in enumerate(parts, start=1):
            chunk_id = base_id if len(parts) == 1 else f"{base_id}.{i}"
            body = "\n".join(part)
            out.append(Chunk(
                chunk_id=chunk_id,
                text=f"{header}\n\n{body}",
                body=body,
                kind="regulation",
                source=source,
                citation=citation,
                article=article,
                article_title=title,
                chapter=chapter,
            ))
    return out


def _split(lines: list[str]) -> list[list[str]]:
    """Greedy split at line boundaries; later parts repeat a short lead-in."""
    if sum(len(l) + 1 for l in lines) <= MAX_CHARS:
        return [lines]
    lead = lines[0] if len(lines[0]) <= 400 else ""
    parts: list[list[str]] = []
    cur: list[str] = []
    size = 0
    for line in _hard_wrap(lines):
        if cur and size + len(line) + 1 > MAX_CHARS:
            parts.append(cur)
            cur = [lead, line] if lead else [line]
            size = sum(len(l) + 1 for l in cur)
        else:
            cur.append(line)
            size += len(line) + 1
    if cur:
        parts.append(cur)
    return parts


def _hard_wrap(lines: list[str]) -> list[str]:
    """Break any single line longer than MAX_CHARS at sentence boundaries."""
    out: list[str] = []
    for line in lines:
        if len(line) <= MAX_CHARS:
            out.append(line)
            continue
        sentence, buf = re.split(r"(?<=[.;:])\s+", line), ""
        for s in sentence:
            if buf and len(buf) + len(s) + 1 > MAX_CHARS:
                out.append(buf)
                buf = s
            else:
                buf = f"{buf} {s}".strip()
        if buf:
            out.append(buf)
    return out


# --------------------------------------------------------------------------- #
# policies                                                                    #
# --------------------------------------------------------------------------- #
def chunk_policy_register(path: Path | str) -> list[Chunk]:
    """One chunk per internal policy — each row is already a citable unit."""
    out: list[Chunk] = []
    with Path(path).open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            pid = row["policy_id"].strip()
            body = (
                f"Owner: {row['owner']}. Last reviewed: {row['last_reviewed']}.\n"
                f"{row['summary']}"
            )
            out.append(Chunk(
                chunk_id=f"policy::{pid}",
                text=f"Internal policy {pid} — {row['title']}\n{body}",
                body=body,
                kind="policy",
                source="policy_register",
                citation=pid,              # the title lives in article_title,
                article_title=row["title"],  # so "[POL-003] Incident Mgmt…" isn't doubled
            ))
    return out


# --------------------------------------------------------------------------- #
# helpers                                                                     #
# --------------------------------------------------------------------------- #
def outline(chunks: list[Chunk], source: str) -> str:
    """Chapter -> article titles. Small enough to hand the triage step whole,
    which is how triage sees the *shape* of a 50k-token regulation without
    reading it."""
    lines: list[str] = []
    seen: set[str] = set()
    chapter = None
    for c in chunks:
        if c.source != source or c.article in seen:
            continue
        seen.add(c.article)
        if c.chapter != chapter:
            chapter = c.chapter
            lines.append(f"\n{chapter}")
        lines.append(f"  Article {c.article} — {c.article_title}")
    return "\n".join(lines).strip()


def fingerprint(chunks: list[Chunk]) -> str:
    """Hash of what gets *embedded* (ids + text). When this changes, vectors
    are stale and must be recomputed."""
    h = hashlib.sha256()
    for c in chunks:
        h.update(c.chunk_id.encode())
        h.update(c.text.encode())
    return h.hexdigest()[:16]


def metadata_fingerprint(chunks: list[Chunk]) -> str:
    """Hash of the filterable metadata. When only this changes, the vectors
    are still valid — refresh metadata in place, don't pay to re-embed."""
    h = hashlib.sha256()
    for c in chunks:
        h.update(repr(sorted(c.metadata().items())).encode())
    return h.hexdigest()[:16]
