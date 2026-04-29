#!/usr/bin/env python3
"""
build_graph.py — Scan docs/engineering/ frontmatter, build typed property graph.

Outputs:
  - docs/engineering/_graph.json  (single source of truth)
  - Lint report to stdout
  - Optionally injects mermaid views into target files (between AUTO-GRAPH markers)

Usage:
  python tools/build_graph.py             # scan + lint + write _graph.json
  python tools/build_graph.py --inject    # also inject mermaid views
  python tools/build_graph.py --strict    # exit nonzero on any lint warning
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "engineering"
GRAPH_JSON = DOCS / "_graph.json"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
INJECT_END = "<!-- AUTO-GRAPH:END -->"


def _start_marker(view: str) -> str:
    return f"<!-- AUTO-GRAPH:START view={view} -->"


# ── Schema ────────────────────────────────────────────────────────────
RELATION_FIELDS = {
    "traces_to":       "TRACES_TO",
    "cites":           "CITES",
    "uses":            "USES",
    "used_by":         "USED_BY",         # MC reverse convenience
    "feeds":           "FEEDS",
    "supports_icd":    "SUPPORTS",
    "links":           "LINKS",            # ICD ↔ WI bidirectional
    "mitigates":       "MITIGATES",
    "satisfies_gates": "SATISFIES",
    "blocks":          "BLOCKS",
    "depends_on":      "DEPENDS_ON",
    "measures":        "MEASURES",
}

NODE_TYPES = {"WI", "ICD", "MC", "Risk", "KC", "Gate", "TC", "SOL", "Claim", "Principle"}

# Framework files don't represent graph nodes — they are aggregation views.
FRAMEWORK_FILES = {
    "README.md",
    "FILE_DEPENDENCY_GUIDE.md",
    "tr_gate_framework.md",
    "critical_path.md",
    "risk_register.md",
    "kc_list.md",
}


# ── Frontmatter parsing ───────────────────────────────────────────────
def parse_frontmatter(path: Path) -> dict[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    try:
        return yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        print(f"[YAML ERROR] {path.relative_to(ROOT)}: {e}", file=sys.stderr)
        return None


def collect_nodes(meta: dict, source_path: Path) -> dict:
    """Build a node entry from frontmatter."""
    node = {k: v for k, v in meta.items() if k not in RELATION_FIELDS}
    node["_source"] = str(source_path.relative_to(ROOT))
    return node


def collect_edges(meta: dict, source_id: str) -> list[dict]:
    edges = []
    for field, relation in RELATION_FIELDS.items():
        items = meta.get(field) or []
        if not isinstance(items, list):
            continue
        for it in items:
            if isinstance(it, str):
                edges.append({"source": source_id, "target": it, "relation": relation})
            elif isinstance(it, dict):
                # e.g. feeds: { target, artifact, purpose }
                tgt = it.get("target")
                if not tgt:
                    continue
                edge = {"source": source_id, "target": tgt, "relation": relation}
                edge.update({k: v for k, v in it.items() if k != "target"})
                edges.append(edge)
    return edges


# ── Build graph ───────────────────────────────────────────────────────
def build_graph() -> tuple[dict[str, dict], list[dict]]:
    """Scan docs/engineering/ recursively, return (nodes_by_id, edges)."""
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    skipped = []

    for md in DOCS.rglob("*.md"):
        if md.name.startswith("_"):
            continue
        meta = parse_frontmatter(md)
        if not meta:
            skipped.append(md.relative_to(ROOT))
            continue
        node_id = meta.get("id")
        if not node_id:
            print(f"[SKIP] {md.relative_to(ROOT)}: frontmatter has no `id`", file=sys.stderr)
            continue
        if node_id in nodes:
            print(f"[DUP]  {node_id} appears in {nodes[node_id]['_source']} and {md.relative_to(ROOT)}", file=sys.stderr)
            continue
        nodes[node_id] = collect_nodes(meta, md)
        edges.extend(collect_edges(meta, node_id))

    return nodes, edges, skipped


# ── Lint ──────────────────────────────────────────────────────────────
def lint(nodes: dict, edges: list, skipped: list) -> list[str]:
    warnings = []

    # Implicit nodes — referenced but no doc file. Allowed for TC/SOL/Claim/Principle/Gate/Risk/KC
    # because those live inside other docs (state JSON, risk_register, kc_list).
    referenced = {e["target"] for e in edges}
    referenced |= {e["source"] for e in edges}
    implicit_only = {r for r in referenced if r not in nodes}

    # Categorize implicit refs by prefix (strip leading alpha chars)
    by_prefix = {}
    prefix_re = re.compile(r"^([A-Za-z]+)")
    for ref in implicit_only:
        m = prefix_re.match(ref)
        prefix = m.group(1) if m else ref
        by_prefix.setdefault(prefix, []).append(ref)

    # 1. Unknown ID prefix
    known_prefixes = {"WI", "ICD", "MC", "TC", "SOL", "C", "R", "KC", "TR", "principle"}
    for prefix, ids in by_prefix.items():
        if prefix not in known_prefixes:
            warnings.append(f"[UNKNOWN-PREFIX] {prefix}: {sorted(ids)[:3]}...")

    # 2. WI without traces_to (skip cross-cutting WIs that support all TCs)
    for nid, n in nodes.items():
        if n.get("type") == "WI" and n.get("role") != "cross-cutting":
            traces = [e for e in edges if e["source"] == nid and e["relation"] == "TRACES_TO"]
            if not traces:
                warnings.append(f"[NO-TRACE] {nid} has no traces_to")

    # 3. Unclosed risks: Risk that nothing mitigates
    referenced_risks = {e["target"] for e in edges if e["relation"] == "MITIGATES"}
    for ref in implicit_only:
        if ref.startswith("R-") and ref not in referenced_risks:
            warnings.append(f"[OPEN-RISK]  {ref} not mitigated by any WI")

    # 4. LOW confidence claim still cited
    for nid, n in nodes.items():
        if n.get("type") == "Claim" and n.get("confidence") == "LOW":
            cites_in = [e for e in edges if e["target"] == nid and e["relation"] == "CITES"]
            if cites_in:
                warnings.append(f"[LOW-CLAIM] {nid} (LOW) is cited by {[e['source'] for e in cites_in]}")

    # 5. Files without frontmatter (skip framework/index files)
    for path in skipped:
        if path.name in FRAMEWORK_FILES:
            continue
        warnings.append(f"[NO-FRONTMATTER] {path}")

    return warnings


# ── Mermaid renderers ─────────────────────────────────────────────────
COLOR_BY_TYPE = {
    "WI":        ("wi",        "#e1f5ff", "#0288d1"),
    "ICD":       ("icd",       "#fce4ec", "#ad1457"),
    "MC":        ("mc",        "#e8f5e9", "#388e3c"),
    "TC":        ("tc",        "#fff3e0", "#f57c00"),
    "SOL":       ("tc",        "#fff3e0", "#f57c00"),
    "Claim":     ("ev",        "#f3e5f5", "#7b1fa2"),
    "Risk":      ("risk",      "#ffebee", "#c62828"),
    "Gate":      ("gate",      "#fffde7", "#f9a825"),
    "KC":        ("kc",        "#e0f2f1", "#00796b"),
    "Principle": ("p",         "#fafafa", "#616161"),
}


def _classdefs() -> str:
    lines = []
    for _, (klass, fill, stroke) in COLOR_BY_TYPE.items():
        lines.append(f"    classDef {klass} fill:{fill},stroke:{stroke}")
    return "\n".join(dict.fromkeys(lines))  # dedup


def _node_class(nid: str, nodes: dict) -> str:
    n = nodes.get(nid)
    if n and n.get("type") in COLOR_BY_TYPE:
        return COLOR_BY_TYPE[n["type"]][0]
    # implicit type by prefix
    prefix = nid.split("-")[0] if "-" in nid else nid.split(":")[0]
    type_map = {"WI": "WI", "ICD": "ICD", "MC": "MC", "TC": "TC", "SOL": "SOL",
                "C": "Claim", "R": "Risk", "TR": "Gate", "KC": "KC", "principle": "Principle"}
    t = type_map.get(prefix)
    return COLOR_BY_TYPE[t][0] if t in COLOR_BY_TYPE else "wi"


def _safe_id(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "_", s)


def _mermaid_label(text: str) -> str:
    """Sanitize text for mermaid label inside quotes.

    Mermaid quoted labels still choke on raw double-quotes; replace with HTML entity.
    """
    return text.replace('"', "&quot;")


# ── Type inference for implicit nodes ────────────────────────────────
def _infer_type(nid: str) -> str | None:
    """Infer node type from ID prefix when no explicit frontmatter exists."""
    prefix_pairs = [
        ("WI-", "WI"), ("ICD-", "ICD"), ("MC-", "MC"),
        ("TC-", "TC"), ("SOL-", "SOL"),
        ("C-", "Claim"), ("R-", "Risk"), ("KC-", "KC"),
        ("TR", "Gate"), ("principle:", "Principle"),
    ]
    for prefix, t in prefix_pairs:
        if nid.startswith(prefix):
            return t
    return None


# ── Ego-graph renderer (per-node Relations view) ─────────────────────
NEIGHBOR_GROUP = {
    "TC":        "TRIZ 溯源",
    "SOL":       "TRIZ 溯源",
    "Principle": "TRIZ 原理",
    "Claim":     "Evidence",
    "MC":        "Materials",
    "WI":        "相關 WI",
    "ICD":       "Interfaces",
    "Risk":      "Risks",
    "Gate":      "TR Gates",
    "KC":        "KC",
}


def _node_in_subgraph(nid: str, type_: str | None) -> str:
    """Mermaid shape for a neighbor node inside a subgraph (compact: ID only)."""
    klass = COLOR_BY_TYPE.get(type_, ("wi",))[0] if type_ else "wi"
    if type_ == "WI":
        return f'{_safe_id(nid)}(["{nid}"]):::{klass}'
    if type_ == "ICD":
        return f'{_safe_id(nid)}[/"{nid}"/]:::{klass}'
    if type_ == "MC":
        return f'{_safe_id(nid)}[("{nid}")]:::{klass}'
    if type_ == "Risk":
        return f'{_safe_id(nid)}(("{nid}")):::{klass}'
    if type_ == "Gate":
        return f'{_safe_id(nid)}{{{{"{nid}"}}}}:::{klass}'
    return f'{_safe_id(nid)}["{nid}"]:::{klass}'


def render_ego_graph(center_id: str, nodes: dict, edges: list) -> str | None:
    """Render relations graph centered on one node (its 1-hop neighborhood)."""
    if center_id not in nodes:
        return None

    out_edges = [e for e in edges if e["source"] == center_id]
    in_edges = [e for e in edges if e["target"] == center_id]
    if not out_edges and not in_edges:
        return None

    # Group neighbors by inferred type
    related = {}  # nid -> type
    for e in out_edges:
        n = nodes.get(e["target"], {})
        related[e["target"]] = n.get("type") or _infer_type(e["target"])
    for e in in_edges:
        n = nodes.get(e["source"], {})
        related[e["source"]] = n.get("type") or _infer_type(e["source"])

    by_group: dict[str, list] = {}
    for nid, t in related.items():
        group = NEIGHBOR_GROUP.get(t, "其他")
        by_group.setdefault(group, []).append((nid, t))

    # Stable group ordering
    group_order = ["TRIZ 溯源", "TRIZ 原理", "Evidence", "Materials",
                   "相關 WI", "Interfaces", "Risks", "TR Gates", "KC", "其他"]

    lines = ["```mermaid", "flowchart LR"]

    # Center node — bold, distinct class
    title = _mermaid_label(nodes[center_id].get("title", center_id))
    lines.append(f'    {_safe_id(center_id)}(["<b>{center_id}</b><br/>{title}"]):::center')
    lines.append("")

    # Subgraphs by neighbor type
    for group in group_order:
        if group not in by_group:
            continue
        sg_id = re.sub(r"\W+", "_", group)
        lines.append(f'    subgraph {sg_id}["{group}"]')
        lines.append("        direction TB")
        for nid, t in sorted(by_group[group]):
            lines.append(f'        {_node_in_subgraph(nid, t)}')
        lines.append("    end")

    lines.append("")

    # Outgoing edges (center → neighbor)
    for e in out_edges:
        if e["relation"] == "FEEDS":
            label = _mermaid_label(e.get("artifact", "feeds"))
        elif e["relation"] == "DEPENDS_ON":
            label = _mermaid_label(e.get("artifact", "depends on"))
        else:
            label = e["relation"].lower()
        lines.append(f'    {_safe_id(center_id)} -->|"{label}"| {_safe_id(e["target"])}')

    # Incoming edges (neighbor → center)
    for e in in_edges:
        rel = e["relation"].lower()
        lines.append(f'    {_safe_id(e["source"])} -->|"{rel}"| {_safe_id(center_id)}')

    # Class definitions
    lines.append("")
    lines.append(_classdefs())
    lines.append("    classDef center fill:#fff,stroke:#000,stroke-width:3px,font-weight:bold")
    lines.append("```")
    return "\n".join(lines)


def render_overall_topology(nodes: dict, edges: list) -> str:
    """Topology of WI ↔ WI feeds + WI → ICD. (主架構視圖)"""
    wi_nodes = [n for n, v in nodes.items() if v.get("type") == "WI"]
    icd_nodes = [n for n, v in nodes.items() if v.get("type") == "ICD"]

    lines = ["```mermaid", "flowchart LR"]
    for nid in sorted(wi_nodes):
        title = _mermaid_label(nodes[nid].get("title", nid))
        # Quoted label handles parens/+/↔/etc.
        lines.append(f'    {_safe_id(nid)}(["<b>{nid}</b><br/>{title}"]):::wi')
    for nid in sorted(icd_nodes):
        title = _mermaid_label(nodes[nid].get("title", nid))
        lines.append(f'    {_safe_id(nid)}[/"<b>{nid}</b><br/>{title}"/]:::icd')

    for e in edges:
        if e["source"] not in nodes or e["target"] not in nodes:
            continue
        if e["relation"] == "FEEDS":
            label = _mermaid_label(e.get("artifact", "feeds"))
            lines.append(f'    {_safe_id(e["source"])} -->|"{label}"| {_safe_id(e["target"])}')
        elif e["relation"] == "SUPPORTS":
            lines.append(f'    {_safe_id(e["source"])} -.-> {_safe_id(e["target"])}')

    lines.append("")
    lines.append(_classdefs())
    lines.append("```")
    return "\n".join(lines)


def render_risk_matrix(nodes: dict, edges: list, all_risk_ids: set[str]) -> str:
    """Risk × WI matrix view. Shows which WI/ICD/MC mitigates which Risk.

    Filtered to source = WI only by default to keep the matrix focused.
    """
    wi_nodes = sorted([n for n, v in nodes.items() if v.get("type") == "WI"])
    risks = sorted(all_risk_ids)

    lines = ["```mermaid", "flowchart LR"]
    for rid in risks:
        lines.append(f'    {_safe_id(rid)}(["{rid}"]):::risk')
    for wid in wi_nodes:
        title = _mermaid_label(nodes[wid].get("title", wid))
        lines.append(f'    {_safe_id(wid)}["<b>{wid}</b><br/>{title}"]:::wi')

    # Only show WI-sourced mitigations to keep matrix readable
    for e in edges:
        if e["relation"] != "MITIGATES":
            continue
        src = nodes.get(e["source"], {}).get("type")
        if src != "WI":
            continue
        lines.append(f'    {_safe_id(e["source"])} -->|mitigates| {_safe_id(e["target"])}')

    lines.append("")
    lines.append(_classdefs())
    lines.append("```")
    return "\n".join(lines)


# ── Inject between markers ───────────────────────────────────────────
def inject_into_file(file_path: Path, content: str, view_name: str) -> bool:
    if not file_path.exists():
        print(f"[INJECT-SKIP] {file_path.relative_to(ROOT)} not found", file=sys.stderr)
        return False
    text = file_path.read_text(encoding="utf-8")
    start = _start_marker(view_name)
    pattern = re.compile(
        rf"{re.escape(start)}.*?{re.escape(INJECT_END)}",
        re.DOTALL,
    )
    new_block = f"{start}\n\n{content}\n\n{INJECT_END}"
    if pattern.search(text):
        new_text = pattern.sub(new_block, text)
        if new_text == text:
            return False
        file_path.write_text(new_text, encoding="utf-8")
        return True
    print(f"[NO-MARKER] {file_path.relative_to(ROOT)} has no {start}", file=sys.stderr)
    return False


# ── Scaffold: insert ego markers into files lacking them ─────────────
EGO_MARKER_BLOCK = (
    "## Relations Graph (auto-generated)\n\n"
    "<!-- AUTO-GRAPH:START view=ego -->\n"
    "<!-- AUTO-GRAPH:END -->"
)
SEPARATOR_RE = re.compile(r"\n---\n+## ")


def scaffold_ego_marker(file_path: Path) -> str:
    """Insert Relations Graph marker before the first content section.

    Returns: 'added', 'exists', or 'skipped'.
    """
    text = file_path.read_text(encoding="utf-8")
    if "view=ego" in text:
        return "exists"
    m = SEPARATOR_RE.search(text)
    if not m:
        return "skipped"
    insert_pos = m.start()
    new_text = text[:insert_pos] + "\n\n" + EGO_MARKER_BLOCK + "\n" + text[insert_pos:]
    file_path.write_text(new_text, encoding="utf-8")
    return "added"


def scaffold_all() -> dict:
    """Add ego markers to all WI/ICD/MC files lacking them."""
    counts = {"added": 0, "exists": 0, "skipped": 0}
    for md in DOCS.rglob("*.md"):
        if md.name.startswith("_") or md.name in FRAMEWORK_FILES:
            continue
        meta = parse_frontmatter(md)
        if not meta or not meta.get("id"):
            continue
        result = scaffold_ego_marker(md)
        counts[result] += 1
        if result == "added":
            print(f"  [scaffold] {md.relative_to(ROOT)}")
    return counts


# ── Main ─────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--inject", action="store_true", help="Inject mermaid views into marked files")
    p.add_argument("--scaffold", action="store_true", help="Insert ego markers into WI/ICD/MC files lacking them")
    p.add_argument("--strict", action="store_true", help="Exit nonzero on lint warnings")
    args = p.parse_args()

    if args.scaffold:
        print("Scaffolding ego markers...")
        c = scaffold_all()
        print(f"  added={c['added']} exists={c['exists']} skipped={c['skipped']}\n")

    nodes, edges, skipped = build_graph()
    warnings = lint(nodes, edges, skipped)

    # Write _graph.json
    graph = {
        "version": "1.0",
        "nodes": [{"id": k, **v} for k, v in nodes.items()],
        "edges": edges,
        "stats": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "by_type": {t: sum(1 for v in nodes.values() if v.get("type") == t) for t in sorted(NODE_TYPES)},
        },
    }
    GRAPH_JSON.write_text(json.dumps(graph, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"✓ {GRAPH_JSON.relative_to(ROOT)}: {len(nodes)} nodes, {len(edges)} edges")

    # Lint report
    if warnings:
        print(f"\n--- Lint warnings ({len(warnings)}) ---")
        for w in warnings:
            print(f"  {w}")
    else:
        print("\n--- Lint clean ---")

    # Inject views
    if args.inject:
        # Collect all referenced risk IDs (implicit nodes)
        risk_ids = {e["target"] for e in edges if e["target"].startswith("R-")}
        risk_ids |= {e["source"] for e in edges if e["source"].startswith("R-")}

        # Aggregate views
        injections = [
            (DOCS / "README.md",        "topology",     render_overall_topology(nodes, edges)),
            (DOCS / "risk_register.md", "risk-matrix",  render_risk_matrix(nodes, edges, risk_ids)),
        ]
        for path, view, content in injections:
            ok = inject_into_file(path, content, view)
            tag = "INJECTED" if ok else "NO-CHANGE"
            print(f"  [{tag}] {path.relative_to(ROOT)}  view={view}")

        # Per-node ego graphs (one per WI/ICD/MC file with ego marker)
        ego_count = 0
        for md in DOCS.rglob("*.md"):
            if md.name.startswith("_") or md.name in FRAMEWORK_FILES:
                continue
            meta = parse_frontmatter(md)
            if not meta or not meta.get("id"):
                continue
            content = render_ego_graph(meta["id"], nodes, edges)
            if content is None:
                continue
            ok = inject_into_file(md, content, "ego")
            if ok:
                ego_count += 1
        print(f"  [INJECTED] {ego_count} ego graphs across WI/ICD/MC")

    if args.strict and warnings:
        sys.exit(1)


if __name__ == "__main__":
    main()
