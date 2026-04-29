"""Tests for the markdown table extractor."""

from __future__ import annotations

from app.triz.markdown_parser import find_table_by_header, parse_tables


def test_parse_single_table():
    md = """
some prose

| Name | Age |
|:-----|:----|
| Alice | 30 |
| Bob | 25 |

trailing prose
"""
    tables = parse_tables(md)
    assert len(tables) == 1
    assert tables[0] == [
        {"Name": "Alice", "Age": "30"},
        {"Name": "Bob", "Age": "25"},
    ]


def test_strips_emphasis_in_cells():
    md = """
| ID | Status |
|:---|:-------|
| **R-001** | *HIGH* |
| `R-002` | normal |
"""
    rows = parse_tables(md)[0]
    assert rows[0]["ID"] == "R-001"
    assert rows[0]["Status"] == "HIGH"
    assert rows[1]["ID"] == "R-002"


def test_no_separator_no_table():
    md = """
| Name | Age |
| Alice | 30 |
"""
    assert parse_tables(md) == []


def test_finds_multiple_tables():
    md = """
| A | B |
|:--|:--|
| 1 | 2 |

| X | Y |
|:--|:--|
| a | b |
"""
    tables = parse_tables(md)
    assert len(tables) == 2


def test_find_table_by_header_matches_subset():
    md = """
| Foo | Bar |
|:----|:----|
| 1 | 2 |

| ID | Name | Age |
|:---|:-----|:----|
| 7 | x | 1 |
"""
    table = find_table_by_header(md, ["ID"])
    assert table is not None
    assert table[0]["ID"] == "7"


def test_find_table_returns_none_when_no_match():
    md = "| A | B |\n|:--|:--|\n| 1 | 2 |\n"
    assert find_table_by_header(md, ["NotThere"]) is None


def test_short_rows_padded():
    md = """
| A | B | C |
|:--|:--|:--|
| 1 |
"""
    rows = parse_tables(md)[0]
    assert rows[0] == {"A": "1", "B": "", "C": ""}
