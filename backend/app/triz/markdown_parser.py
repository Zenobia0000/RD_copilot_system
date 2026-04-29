"""Markdown table extraction utilities.

The engineering deliverables in ``docs/engineering/`` carry their structured
data inside markdown tables (KC list, risk register, ICD specs, MC property
tables). The front-end needs JSON, so this module finds the right table by
its header row and returns each data row as a dict.

Why not bring in a full markdown library:
We only need to parse pipe-style tables with a header + separator + body.
A 40-line scanner is faster, has zero deps, and keeps the failure modes
obvious — a malformed table just yields an empty list, never raises.

Limitations (intentional):
- No support for HTML tables, list tables, or fenced tables in code blocks.
- Cells that span multiple lines (rare in our docs) are not joined.
- Inline pipes inside cell content must be escaped (``\\|``) to survive,
  or the cell will split. None of our deliverables use unescaped pipes.
"""

from __future__ import annotations

import re

# A markdown emphasis stripper that keeps the inner text:
#   "**Critical**" → "Critical"
#   "*HIGH*"       → "HIGH"
#   "`code`"       → "code"
_EMPHASIS_RE = re.compile(r"\*{1,3}([^*]+)\*{1,3}|`([^`]+)`")


def _strip_emphasis(text: str) -> str:
    """Remove markdown bold/italic/code markers, keep inner text."""
    return _EMPHASIS_RE.sub(lambda m: m.group(1) or m.group(2) or "", text)


def _is_separator_row(line: str) -> bool:
    """A separator row consists of cells like ``---``, ``:---``, ``:---:``.

    Returns True iff every non-empty cell matches that shape.
    """
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if not cells or any(not c for c in cells):
        return False
    # GFM allows 1+ dashes; we don't enforce a higher minimum.
    return all(re.fullmatch(r":?-+:?", c) for c in cells)


def _split_row(line: str) -> list[str]:
    """Split a pipe-row into trimmed, emphasis-stripped cells."""
    raw = line.strip()
    if raw.startswith("|"):
        raw = raw[1:]
    if raw.endswith("|"):
        raw = raw[:-1]
    return [_strip_emphasis(c).strip() for c in raw.split("|")]


def parse_tables(markdown: str) -> list[list[dict[str, str]]]:
    """Find every pipe-style table in the document.

    Returns a list of tables; each table is a list of row-dicts keyed by the
    table's header cells. Tables without a separator row are ignored.
    """
    lines = markdown.splitlines()
    tables: list[list[dict[str, str]]] = []
    i = 0
    while i < len(lines) - 1:
        line = lines[i].strip()
        next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
        if line.startswith("|") and _is_separator_row(next_line):
            headers = _split_row(line)
            rows: list[dict[str, str]] = []
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                cells = _split_row(lines[j])
                # Pad short rows / truncate over-long ones to header length
                cells = (cells + [""] * len(headers))[: len(headers)]
                rows.append(dict(zip(headers, cells)))
                j += 1
            tables.append(rows)
            i = j
            continue
        i += 1
    return tables


def find_table_by_header(
    markdown: str,
    required_headers: list[str],
) -> list[dict[str, str]] | None:
    """Return the first table whose header set is a superset of ``required_headers``.

    Headers are matched case-insensitively after stripping whitespace, but
    not after stripping punctuation — callers should pass the exact header
    text used in the source document.
    """
    targets = {h.lower().strip() for h in required_headers}
    for table in parse_tables(markdown):
        if not table:
            continue
        keys = {k.lower().strip() for k in table[0].keys()}
        if targets.issubset(keys):
            return table
    return None
