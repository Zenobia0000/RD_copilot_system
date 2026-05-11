"""USDA Serializer — Pure Python string renderer for USD ASCII (.usda) export.

Converts the Create-phase subsystem tree, engineering spec drafts, and
interface contracts into a valid `.usda` text file. No binary dependencies
required — follows the same string-list concatenation pattern used in
``package_svg.py``.

USD Hierarchy mapping:
    System    → ``def Xform`` (kind = "assembly")
    Module    → ``def Xform`` (kind = "group")
    Component → ``def Xform`` (kind = "component")

See ``plans/usda-export-feasibility.md`` §3 for full specification.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.schemas import (
        BBox,
        DraftValue,
        EngineeringSpecDraft,
        InterfaceContract,
        PackageMap,
        SuggestedSubsystem,
    )

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_LEVEL_KIND: dict[str, str] = {
    "system": "assembly",
    "module": "group",
    "component": "component",
}

_CONFIDENCE_FLOAT: dict[str, float] = {
    "confirmed": 1.0,
    "library": 0.92,
    "estimate": 0.7,
    "speculative": 0.4,
}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _sanitize_name(name: str) -> str:
    """Convert a human-readable subsystem name to a USD-safe identifier.

    USD prim names must match ``[a-zA-Z_][a-zA-Z0-9_]*``.
    """
    # Replace common delimiters with underscore
    s = re.sub(r"[\s\-/\.\(\)\[\]]+", "_", name.strip())
    # Remove any remaining non-alphanumeric (except underscore)
    s = re.sub(r"[^a-zA-Z0-9_]", "", s)
    # Ensure it does not start with a digit
    if s and s[0].isdigit():
        s = f"_{s}"
    return s or "_unnamed"


def _indent(level: int) -> str:
    """Return indentation string (4 spaces per level)."""
    return "    " * level


def _usd_string(value: str) -> str:
    """Wrap a Python string as a USD string literal, escaping quotes."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _usd_string_array(values: list[str]) -> str:
    """Render a USD string[] literal."""
    items = ", ".join(_usd_string(v) for v in values)
    return f"[{items}]"


def _usd_value_repr(value: object) -> str:
    """Convert a DraftValue.value to a USD-safe string representation."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (dict, list)):
        # Complex values → JSON-like string
        import json
        return _usd_string(json.dumps(value, ensure_ascii=False))
    return _usd_string(str(value))


# ---------------------------------------------------------------------------
# Emitters
# ---------------------------------------------------------------------------


def _emit_bbox(
    bbox: "BBox | None",
    mass_g: float | None,
    mounting_pattern: str,
    confidence: str,
    indent: int,
    lines: list[str],
) -> None:
    """Emit spatial properties from a BBox + SpatialEstimate."""
    pad = _indent(indent)
    if bbox is not None:
        ox, oy, oz = bbox.origin_mm
        lines.append(f"{pad}double3 xformOp:translate = ({ox}, {oy}, {oz})")
        lines.append(
            f'{pad}uniform token[] xformOpOrder = ["xformOp:translate"]'
        )
        lines.append("")
        lines.append(
            f"{pad}custom double3 extent_mm = ({bbox.x_mm}, {bbox.y_mm}, {bbox.z_mm})"
        )
        if bbox.anchor:
            lines.append(f"{pad}custom string anchor = {_usd_string(bbox.anchor)}")
    if mass_g is not None:
        lines.append(f"{pad}custom double mass_g = {mass_g}")
    if mounting_pattern:
        lines.append(
            f"{pad}custom string mounting_pattern = {_usd_string(mounting_pattern)}"
        )
    if confidence:
        lines.append(
            f"{pad}custom string spatial_confidence = {_usd_string(confidence)}"
        )


def _emit_clashes(
    clashes: list[str],
    indent: int,
    lines: list[str],
) -> None:
    """Emit AABB clash list as customData."""
    if not clashes:
        return
    pad = _indent(indent)
    lines.append(
        f"{pad}custom string[] aabb_clashes = {_usd_string_array(clashes)}"
    )


def _emit_relationships(
    contracts: dict[str, "InterfaceContract"],
    root_prim_name: str,
    indent: int,
    lines: list[str],
) -> None:
    """Emit USD relationship arcs from InterfaceContract dict.

    Each non-empty contract dimension becomes a ``rel interface:<dim>`` pointing
    to the target subsystem's prim path.
    """
    if not contracts:
        return
    pad = _indent(indent)
    lines.append("")
    lines.append(f"{pad}# --- Interface Relationships ---")
    dimensions = [
        "envelope",
        "loadPath",
        "thermalPath",
        "signalPath",
        "datumTolerance",
        "serviceability",
    ]
    for target_name, contract in contracts.items():
        safe_target = _sanitize_name(target_name)
        for dim in dimensions:
            val = getattr(contract, dim, "")
            if val:
                lines.append(
                    f"{pad}rel interface:{dim} = </{root_prim_name}/{safe_target}>"
                )


def _emit_specs(
    specs: list["DraftValue"],
    indent: int,
    lines: list[str],
) -> None:
    """Emit DraftValue list as USD custom properties grouped by category.

    Each spec becomes a set of custom properties:
        custom <type> <category>:<field_name>:value = ...
        custom string <category>:<field_name>:unit = "..."
        custom string <category>:<field_name>:source = "..."
        custom float  <category>:<field_name>:confidence = ...
        custom bool   <category>:<field_name>:needs_verification = ...
    """
    if not specs:
        return
    pad = _indent(indent)

    # Group by category for visual clarity
    by_cat: dict[str, list["DraftValue"]] = {}
    for sv in specs:
        by_cat.setdefault(sv.category, []).append(sv)

    for cat in sorted(by_cat.keys()):
        lines.append("")
        lines.append(f"{pad}# --- Engineering Spec: {cat} ---")
        for sv in by_cat[cat]:
            prefix = f"{cat}:{_sanitize_name(sv.field_name)}"
            # value — use typed USD property for numerics, string for rest
            if isinstance(sv.value, bool):
                bv = "true" if sv.value else "false"
                lines.append(
                    f'{pad}custom string {prefix}:value = "{bv}"'
                )
            elif isinstance(sv.value, float):
                lines.append(
                    f"{pad}custom double {prefix}:value = {sv.value}"
                )
            elif isinstance(sv.value, int):
                lines.append(
                    f"{pad}custom int {prefix}:value = {sv.value}"
                )
            else:
                lines.append(
                    f"{pad}custom string {prefix}:value = {_usd_value_repr(sv.value)}"
                )
            # unit
            if sv.unit:
                lines.append(
                    f"{pad}custom string {prefix}:unit = {_usd_string(sv.unit)}"
                )
            # source
            lines.append(
                f"{pad}custom string {prefix}:source = {_usd_string(sv.source)}"
            )
            # confidence (float)
            conf_float = _CONFIDENCE_FLOAT.get(sv.confidence, 0.4)
            lines.append(f"{pad}custom float {prefix}:confidence = {conf_float}")
            # needs_verification
            nv = "true" if sv.needs_verification else "false"
            lines.append(
                f"{pad}custom bool {prefix}:needs_verification = {nv}"
            )
            # rationale (optional)
            if sv.rationale:
                lines.append(
                    f"{pad}custom string {prefix}:rationale = {_usd_string(sv.rationale)}"
                )


def _emit_subsystem(
    node: "SuggestedSubsystem",
    root_prim_name: str,
    drafts_by_code: dict[str, "EngineeringSpecDraft"],
    clash_map: dict[str, list[str]],
    indent: int,
    lines: list[str],
) -> None:
    """Recursively emit a SuggestedSubsystem as a USD ``def Xform``."""
    pad = _indent(indent)
    safe_name = _sanitize_name(node.name)
    kind = _LEVEL_KIND.get(node.level, "group")

    # --- customData block ---
    custom_data_items: list[str] = []
    if node.concept_origin_code:
        custom_data_items.append(
            f'{_indent(indent + 2)}string concept_origin = {_usd_string(node.concept_origin_code)}'
        )
    if node.mapped_kpis:
        custom_data_items.append(
            f'{_indent(indent + 2)}string[] mapped_kpis = {_usd_string_array(node.mapped_kpis)}'
        )
    if node.reason:
        custom_data_items.append(
            f'{_indent(indent + 2)}string reason = {_usd_string(node.reason)}'
        )
    if node.related_contradictions:
        custom_data_items.append(
            f'{_indent(indent + 2)}string[] related_contradictions = {_usd_string_array(node.related_contradictions)}'
        )

    # Build prim header
    if custom_data_items:
        custom_data_block = "\n".join(custom_data_items)
        lines.append(f'{pad}def Xform "{safe_name}" (')
        lines.append(f"{_indent(indent + 1)}kind = {_usd_string(kind)}")
        lines.append(f"{_indent(indent + 1)}customData = {{")
        lines.append(custom_data_block)
        lines.append(f"{_indent(indent + 1)}}}")
        lines.append(f"{pad})")
    else:
        lines.append(
            f'{pad}def Xform "{safe_name}" (kind = {_usd_string(kind)})'
        )

    lines.append(f"{pad}{{")
    body_indent = indent + 1

    # --- Spatial (from interface_contracts self-spatial or first contract spatial) ---
    spatial = _find_spatial(node)
    if spatial:
        _emit_bbox(
            spatial.bbox,
            spatial.mass_g,
            spatial.mounting_pattern,
            spatial.confidence if hasattr(spatial, "confidence") else "",
            body_indent,
            lines,
        )

    # --- Clashes ---
    clashes = clash_map.get(node.name, [])
    _emit_clashes(clashes, body_indent, lines)

    # --- Interface relationships ---
    _emit_relationships(node.interface_contracts, root_prim_name, body_indent, lines)

    # --- Engineering Spec Drafts ---
    draft_key = node.concept_origin_code or _sanitize_name(node.name)
    draft = drafts_by_code.get(draft_key)
    if draft:
        _emit_specs(draft.specs, body_indent, lines)

    # --- Children (recursive) ---
    for child in node.children:
        lines.append("")
        _emit_subsystem(
            child, root_prim_name, drafts_by_code, clash_map, body_indent, lines
        )

    lines.append(f"{pad}}}")


def _find_spatial(node: "SuggestedSubsystem") -> "SpatialEstimate | None":
    """Extract the best SpatialEstimate for a subsystem node.

    Priority:
      1. Any interface contract that has a populated ``spatial`` field
      2. None if no spatial data available
    """
    for _target, contract in node.interface_contracts.items():
        if contract.spatial is not None:
            return contract.spatial
    return None


def _build_clash_map(package_map: "PackageMap | None") -> dict[str, list[str]]:
    """Build a name→clashes dict from the PackageMap."""
    if not package_map:
        return {}
    return {n.name: n.clashes for n in package_map.nodes if n.clashes}


def _build_drafts_by_code(
    drafts: list["EngineeringSpecDraft"] | None,
) -> dict[str, "EngineeringSpecDraft"]:
    """Index engineering spec drafts by subsystem_code."""
    if not drafts:
        return {}
    return {d.subsystem_code: d for d in drafts}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def serialize_to_usda(
    subsystems: list["SuggestedSubsystem"],
    *,
    project_id: str = "",
    project_name: str = "",
    drafts: list["EngineeringSpecDraft"] | None = None,
    package_map: "PackageMap | None" = None,
) -> str:
    """Serialize the full subsystem tree into a ``.usda`` text string.

    Parameters
    ----------
    subsystems:
        Top-level subsystem nodes (typically ``system``-level).
    project_id:
        Optional project identifier for layer metadata.
    project_name:
        Human-readable project name; used as ``defaultPrim`` when only one
        root system exists.
    drafts:
        Engineering spec drafts indexed by subsystem_code.
    package_map:
        Optional PackageMap for clash information.

    Returns
    -------
    str
        Complete USDA text ready to write to a ``.usda`` file.
    """
    drafts_by_code = _build_drafts_by_code(drafts)
    clash_map = _build_clash_map(package_map)

    # Determine root prim name
    if len(subsystems) == 1:
        root_name = _sanitize_name(subsystems[0].name)
    elif project_name:
        root_name = _sanitize_name(project_name)
    else:
        root_name = "Project"

    now = datetime.now(timezone.utc).isoformat()
    lines: list[str] = []

    # --- Layer header ---
    lines.append("#usda 1.0")
    lines.append("(")
    lines.append(f'    defaultPrim = "{root_name}"')
    lines.append("    metersPerUnit = 0.001")
    lines.append('    upAxis = "Z"')
    lines.append("    customLayerData = {")
    lines.append('        string generator = "RD_Design_Copilot"')
    if project_id:
        lines.append(f"        string project_id = {_usd_string(project_id)}")
    lines.append(f"        string export_timestamp = {_usd_string(now)}")
    lines.append("    }")
    lines.append(")")
    lines.append("")

    # --- Emit each top-level subsystem ---
    for i, sub in enumerate(subsystems):
        if i > 0:
            lines.append("")
        _emit_subsystem(sub, root_name, drafts_by_code, clash_map, 0, lines)

    # Ensure trailing newline
    lines.append("")
    return "\n".join(lines)
