"""
Markdown/HTML-entity/mojibake → plain text (finding L8: literal **, ###,
pipe tables, &nbsp;, and mojibake printed onto court PDFs).

The cleanup loops until the text is stable, which also makes it idempotent.
One aggregate info Correction is emitted when anything changed.
"""
import html
import re
from typing import List, Tuple

from app.services.fact_gate.types import Correction

_MAX_PASSES = 5

_FENCE_RE = re.compile(r"(?m)^[ \t]*```[^\n]*$\n?")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_UNDERLINE_RE = re.compile(r"__(.+?)__")
_BACKTICK_RE = re.compile(r"`([^`\n]+)`")
_HEADING_RE = re.compile(r"(?m)^[ \t]{0,3}#{1,6}[ \t]+")

# Longest sequences first so the bare 'â€' fallback never eats a prefix.
_MOJIBAKE = [
    ("â€™", "'"),
    ("â€˜", "'"),
    ("â€œ", '"'),
    ("â€\x9d", '"'),
    ("â€“", "-"),
    ("â€”", "-"),
    ("â€¦", "..."),
    ("â€", '"'),
]

_TABLE_LINE_RE = re.compile(r"^\s*\|?.*\|.*\|?\s*$")
_SEPARATOR_CELL_RE = re.compile(r"^[:\-\s]*$")

MESSAGE = (
    "Formatting characters (markdown symbols, HTML codes, or garbled "
    "punctuation) were removed so the document prints as plain text."
)


def _is_table_line(line: str) -> bool:
    return line.count("|") >= 2 and bool(_TABLE_LINE_RE.match(line))


def _cells(line: str) -> List[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _table_block_to_lines(block: List[str]) -> List[str]:
    rows = [_cells(line) for line in block]
    rows = [row for row in rows if not all(_SEPARATOR_CELL_RE.match(c) for c in row)]
    if not rows:
        return []
    header, body = rows[0], rows[1:]
    if not body:
        return ["; ".join(cell for cell in header if cell)]
    return [
        "; ".join(f"{h}: {c}" for h, c in zip(header, row) if c)
        for row in body
    ]


def _convert_tables(text: str) -> str:
    lines = text.split("\n")
    out: List[str] = []
    block: List[str] = []
    for line in lines + [""]:  # sentinel flushes a trailing block
        if _is_table_line(line):
            block.append(line)
            continue
        if len(block) >= 2:
            out.extend(_table_block_to_lines(block))
        else:
            out.extend(block)
        block = []
        out.append(line)
    return "\n".join(out[:-1])  # drop the sentinel


def _clean_once(text: str) -> str:
    text = _FENCE_RE.sub("", text)
    text = _convert_tables(text)
    text = _BOLD_RE.sub(r"\1", text)
    text = _UNDERLINE_RE.sub(r"\1", text)
    text = _BACKTICK_RE.sub(r"\1", text)
    text = _HEADING_RE.sub("", text)
    text = html.unescape(text).replace(" ", " ")
    for bad, good in _MOJIBAKE:
        text = text.replace(bad, good)
    return text


def strip_markdown(text: str) -> Tuple[str, List[Correction]]:
    """Plain text plus one aggregate info Correction when anything changed."""
    original = text
    for _ in range(_MAX_PASSES):
        cleaned = _clean_once(text)
        if cleaned == text:
            break
        text = cleaned
    if text == original:
        return text, []
    correction = Correction(
        type="markdown",
        severity="info",
        section="",
        original="",
        replacement=None,
        message=MESSAGE,
    )
    return text, [correction]
