"""Ingest official EU regulation text into readable, chunkable markdown.

CONCEPT — why an ingestion step at all
--------------------------------------
RAG quality is capped by what goes into the index. Pasting a regulation's web
page into a vector store would mix navigation, recitals, footnotes and the
actual obligations into one soup. Instead we fetch the *structured* official
text and keep only the enacting terms (the Articles), preserving the legal
structure — Chapter > Article > numbered paragraph > lettered point — because
that structure is what the chunker and the citations rely on.

Source
------
The EU Publications Office "Cellar" endpoint serves the Official Journal
XHTML for a CELEX number by content negotiation:

    GET http://publications.europa.eu/resource/celex/{CELEX}
    Accept: application/xhtml+xml        Accept-Language: eng

(The eur-lex.europa.eu web UI sits behind a bot check and returns an empty
202 to scripts; Cellar is the documented machine endpoint for the same text.)

EU legislation is reusable with attribution (Commission Decision 2011/833/EU);
only the Official Journal version is legally authentic. The generated markdown
carries that notice in its header.

Output is intermediate markdown (data/regulations/<name>.md) rather than
chunks directly: it is human-reviewable, diffs cleanly in git when the law is
amended, and lets the same chunker handle hand-written summaries too.

Usage:
    python -m regimpact.rag.ingest --celex 32022R2554 --name dora \
        --title "DORA — Regulation (EU) 2022/2554 on digital operational resilience for the financial sector"
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REG_DIR = ROOT / "data" / "regulations"
CACHE_DIR = ROOT / "data" / "cache"

_CELLAR = "http://publications.europa.eu/resource/celex/{celex}"
_NS = "{http://www.w3.org/1999/xhtml}"


@dataclass
class Article:
    number: str
    title: str
    chapter: str
    # Each paragraph is a list of lines (subparagraphs and "(a) ..." points).
    paragraphs: list[list[str]] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# fetch                                                                       #
# --------------------------------------------------------------------------- #
def fetch_celex(celex: str, *, use_cache: bool = True, retries: int = 3) -> str:
    """Return the Official Journal XHTML for a CELEX id, cached on disk."""
    cache = CACHE_DIR / f"{celex}.xhtml"
    if use_cache and cache.exists():
        return cache.read_text(encoding="utf-8")

    req = urllib.request.Request(
        _CELLAR.format(celex=celex),
        headers={
            "Accept": "application/xhtml+xml;q=0.9, text/html;q=0.8",
            "Accept-Language": "eng",
            "User-Agent": "regulatory-impact-analyst/0.2 (research)",
        },
    )
    last: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = resp.read().decode("utf-8")
            if "oj-ti-art" not in body:
                raise ValueError(f"{celex}: response has no articles (wrong CELEX or format?)")
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(body, encoding="utf-8")
            return body
        except (urllib.error.URLError, TimeoutError) as exc:
            last = exc
            time.sleep(2**attempt)
    raise RuntimeError(f"failed to fetch {celex}: {last}")


# --------------------------------------------------------------------------- #
# parse                                                                       #
# --------------------------------------------------------------------------- #
def _classes(el: ET.Element) -> str:
    return el.get("class", "")


def _text(el: ET.Element) -> str:
    """Flatten an element's text, dropping footnote reference markers."""
    parts: list[str] = []

    def walk(node: ET.Element) -> None:
        if "oj-note-tag" in _classes(node):
            if node.tail:
                parts.append(node.tail)
            return
        if node.text:
            parts.append(node.text)
        for child in node:
            walk(child)
        if node.tail and node is not el:
            parts.append(node.tail)

    walk(el)
    return " ".join("".join(parts).split())  # collapse whitespace incl. nbsp


def _render(el: ET.Element, indent: str = "") -> list[str]:
    """Render a block (p / table / div) into lines, keeping (a)/(i) points."""
    tag = el.tag.replace(_NS, "")
    if tag == "p":
        t = _text(el)
        return [indent + t] if t else []
    if tag == "table":
        lines: list[str] = []
        # Only this table's own rows — nested tables (sub-points) are reached
        # by recursing into the cell, so they keep their extra indent.
        tbody = el.find(_NS + "tbody")
        rows = list(tbody) if tbody is not None else [r for r in el if r.tag == _NS + "tr"]
        for tr in rows:
            tds = [td for td in tr if td.tag == _NS + "td"]
            if len(tds) >= 2:
                label = _text(tds[0])
                inner: list[str] = []
                for child in tds[1]:
                    inner.extend(_render(child, indent + "  "))
                if inner:
                    inner[0] = f"{indent}{label} {inner[0].strip()}"
                lines.extend(inner)
            else:
                for td in tds:
                    for child in td:
                        lines.extend(_render(child, indent))
        return lines
    if tag == "div":
        out: list[str] = []
        for child in el:
            out.extend(_render(child, indent))
        return out
    return []


def parse_oj_xhtml(xhtml: str) -> list[Article]:
    """Extract the Articles (enacting terms) with their chapter and paragraphs."""
    body = re.sub(r"^<\?xml[^>]*\?>", "", xhtml.lstrip())
    body = re.sub(r"<!DOCTYPE[^>]*>", "", body, count=1)
    root = ET.fromstring(body)

    articles: list[Article] = []
    chapter = ""
    pending_chapter_number = ""

    for el in root.iter():
        cls = _classes(el)
        if el.tag == _NS + "p" and cls == "oj-ti-section-1":
            t = _text(el)
            if t.upper().startswith("CHAPTER"):
                pending_chapter_number = t
                chapter = t
        elif el.tag == _NS + "p" and cls == "oj-ti-section-2" and pending_chapter_number:
            chapter = f"{pending_chapter_number} — {_text(el)}"
            pending_chapter_number = ""
        elif el.tag == _NS + "div" and re.fullmatch(r"art_\d+[a-z]?", el.get("id", "")):
            articles.append(_parse_article(el, chapter))
    return articles


def _parse_article(div: ET.Element, chapter: str) -> Article:
    number = title = ""
    paragraphs: list[list[str]] = []
    loose: list[str] = []  # content not wrapped in a numbered paragraph div

    for child in div:
        cls = _classes(child)
        tag = child.tag.replace(_NS, "")
        if tag == "p" and "oj-ti-art" in cls:
            number = _text(child).replace("Article", "").strip()
        elif tag == "div" and "eli-title" in cls:
            # The AI Act's OJ text has a stray backtick ("Subject matter`").
            title = _text(child).strip(" `'‘’")
        elif tag == "div" and re.fullmatch(r"\d{3}\.\d{3}", child.get("id", "")):
            lines = _render(child)
            if lines:
                paragraphs.append(lines)
        else:
            loose.extend(_render(child))

    if loose:
        paragraphs.insert(0, loose)
    return Article(number=number, title=title, chapter=chapter, paragraphs=paragraphs)


# --------------------------------------------------------------------------- #
# write                                                                       #
# --------------------------------------------------------------------------- #
def to_markdown(articles: list[Article], *, title: str, celex: str) -> str:
    today = dt.date.today().isoformat()
    out = [
        f"# {title}",
        "",
        f"> Source: Official Journal of the European Union, CELEX {celex}, fetched from the "
        f"EU Publications Office (Cellar) on {today}.",
        "> © European Union, https://eur-lex.europa.eu/ — reuse authorised with attribution "
        "(Commission Decision 2011/833/EU). Only the Official Journal version is authentic.",
        "> Enacting terms (Articles) only; recitals, annexes and footnotes omitted.",
        "",
    ]
    current_chapter = None
    for a in articles:
        if a.chapter and a.chapter != current_chapter:
            out += [f"## {a.chapter}", ""]
            current_chapter = a.chapter
        out += [f"### Article {a.number} — {a.title}", ""]
        for para in a.paragraphs:
            out += para
            out.append("")
    return "\n".join(out).rstrip() + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Ingest an EU regulation by CELEX id")
    ap.add_argument("--celex", required=True, help="e.g. 32022R2554 (DORA)")
    ap.add_argument("--name", required=True, help="output basename, e.g. dora")
    ap.add_argument("--title", required=True, help="human title for the markdown header")
    ap.add_argument("--refresh", action="store_true", help="ignore the local cache")
    args = ap.parse_args()

    xhtml = fetch_celex(args.celex, use_cache=not args.refresh)
    articles = parse_oj_xhtml(xhtml)
    md = to_markdown(articles, title=args.title, celex=args.celex)
    out = REG_DIR / f"{args.name}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    n_paras = sum(len(a.paragraphs) for a in articles)
    print(f"{len(articles)} articles, {n_paras} paragraphs -> {out}")


if __name__ == "__main__":
    main()
