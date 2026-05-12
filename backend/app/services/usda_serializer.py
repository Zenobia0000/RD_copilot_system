"""USDA Serializer — Pure Python string renderer for USD ASCII (.usda) export.

Converts the Create-phase subsystem tree, engineering spec drafts, and
interface contracts into a valid ``.usda`` text file. No binary dependencies
required — follows the same string-list concatenation pattern used in
``package_svg.py``.

USD Hierarchy mapping:
    Project   → ``def Xform`` root wrapper (kind = "assembly")
    System    → ``def Xform`` (kind = "assembly")
    Module    → ``def Xform`` (kind = "group")
    Component → ``def Xform`` (kind = "component")

Proxy geometry: When ``include_proxy_geometry=True``, nodes with spatial
data (``extent_mm``) emit a child ``Cube`` or ``Cylinder`` prim so that
Blender/usdview show visible shapes instead of empty transforms.

Shape inference: ``proxy_geometry_mode="inferred"`` uses keyword matching
against the node name — terms like shaft/spindle/housing/shell map to
``Cylinder``; everything else defaults to ``Cube``.

See ``plans/usda-export-feasibility.md`` §3 for full specification.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from app.models.schemas import (
        BBox,
        DraftValue,
        EngineeringSpecDraft,
        InterfaceContract,
        PackageMap,
        SpatialEstimate,
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

# Keywords that map to Cylinder proxy geometry (case-insensitive).
_CYLINDER_KEYWORDS: set[str] = {
    "shaft", "spindle", "rotor", "stator", "housing", "shell",
    "bb",
    # CJK equivalents
    "軸", "踏軸", "轉子", "定子", "殼體", "外殼",
}

# Mapping from geometry_archetype → USD prim type used by _resolve_shape().
_ARCHETYPE_TO_USD_PRIM: dict[str, str] = {
    "cube": "Cube",
    "cylinder": "Cylinder",
    "disc": "Cylinder",       # disc ≈ flat cylinder
    "l_bracket": "Cube",      # approximate with box
    "sphere": "Sphere",
    "flat_plate": "Cube",     # approximate with flat box
    "custom": "Cube",         # safe fallback
}

# Color palette for per-assembly coloring (sRGB float triples).
# Cycles through this list for each top-level subsystem.
_ASSEMBLY_COLORS: list[tuple[float, float, float]] = [
    (0.216, 0.494, 0.722),   # Steel-blue
    (0.894, 0.102, 0.110),   # Crimson
    (0.302, 0.686, 0.290),   # Green
    (0.596, 0.306, 0.639),   # Purple
    (1.000, 0.498, 0.000),   # Orange
    (0.651, 0.337, 0.157),   # Brown
    (0.969, 0.506, 0.749),   # Pink
    (0.600, 0.600, 0.600),   # Grey
    (0.737, 0.741, 0.133),   # Olive
    (0.090, 0.745, 0.812),   # Teal
]

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


def _compute_prim_name(node: "SuggestedSubsystem") -> str:
    """Derive a USD-safe prim name for *node*.

    Priority:
      1. ``concept_origin_code`` (e.g. "A1", "S1_M1") — always ASCII-safe
      2. ``_sanitize_name(node.name)`` when it yields a real result
      3. Fallback ``_unnamed``
    """
    if node.concept_origin_code:
        candidate = _sanitize_name(node.concept_origin_code)
        if candidate and candidate != "_unnamed":
            return candidate
    candidate = _sanitize_name(node.name)
    return candidate


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


def _infer_shape(name: str) -> Literal["Cube", "Cylinder"]:
    """Infer proxy geometry shape from a subsystem name.

    Returns ``"Cylinder"`` when the name contains any keyword from
    ``_CYLINDER_KEYWORDS`` (case-insensitive match), ``"Cube"`` otherwise.
    """
    lower = name.lower()
    for kw in _CYLINDER_KEYWORDS:
        if kw.lower() in lower:
            return "Cylinder"
    return "Cube"


def _resolve_shape(bbox: "BBox", name: str) -> str:
    """Pick a USD prim type from *bbox.geometry_archetype*, falling back to
    ``_infer_shape(name)`` when the archetype is not set.

    Returns one of ``"Cube"``, ``"Cylinder"``, or ``"Sphere"``.
    """
    archetype = getattr(bbox, "geometry_archetype", None)
    if archetype and archetype in _ARCHETYPE_TO_USD_PRIM:
        return _ARCHETYPE_TO_USD_PRIM[archetype]
    return _infer_shape(name)


# ---------------------------------------------------------------------------
# Emitters
# ---------------------------------------------------------------------------


def _emit_bbox(
    bbox: "BBox | None",
    mass_g: float | None,
    mounting_pattern: str,
    confidence: str,
    lod_hint: str,
    geometry_is_placeholder: bool,
    indent: int,
    lines: list[str],
) -> None:
    """Emit spatial properties from a BBox + SpatialEstimate."""
    pad = _indent(indent)
    if bbox is not None:
        ox, oy, oz = bbox.origin_mm
        lines.append(f"{pad}double3 xformOp:translate = ({ox}, {oy}, {oz})")
        sx, sy, sz = bbox.x_mm, bbox.y_mm, bbox.z_mm
        lines.append(f"{pad}double3 xformOp:scale = ({sx}, {sy}, {sz})")
        lines.append(
            f'{pad}uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:scale"]'
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
    if lod_hint:
        lines.append(
            f"{pad}custom string lod_hint = {_usd_string(lod_hint)}"
        )
    lines.append(
        f"{pad}custom string is_placeholder = {_usd_string(str(geometry_is_placeholder))}"
    )


def _emit_proxy_geometry(
    bbox: "BBox",
    shape: str,
    color: tuple[float, float, float],
    indent: int,
    lines: list[str],
) -> None:
    """Emit a child proxy geometry prim (Cube, Cylinder or Sphere) under the current Xform.

    The proxy prim is named ``proxy_<shape>`` and sized using xformOp:scale
    derived from the BBox extents.  ``primvars:displayColor`` is set so
    Blender renders the shape with the assembly colour.
    """
    pad = _indent(indent)
    prim_name = f"proxy_{shape}"

    if shape == "Cylinder":
        # Cylinder in USD: default radius=1, height=2, axis=Z
        # We scale so that diameter = max(x_mm, y_mm) and height = z_mm
        r = max(bbox.x_mm, bbox.y_mm) / 2.0
        h = bbox.z_mm / 2.0  # half-height because default height=2
        lines.append("")
        lines.append(f'{pad}def Cylinder "{prim_name}"')
        lines.append(f"{pad}{{")
        inner = _indent(indent + 1)
        lines.append(f"{inner}double radius = {r}")
        lines.append(f"{inner}double height = {bbox.z_mm}")
        lines.append(
            f"{inner}color3f[] primvars:displayColor = [({color[0]}, {color[1]}, {color[2]})]"
        )
        lines.append(f"{pad}}}")
    elif shape == "Sphere":
        # Sphere in USD: default radius=1
        r = max(bbox.x_mm, bbox.y_mm, bbox.z_mm) / 2.0
        lines.append("")
        lines.append(f'{pad}def Sphere "{prim_name}"')
        lines.append(f"{pad}{{")
        inner = _indent(indent + 1)
        lines.append(f"{inner}double radius = {r}")
        lines.append(
            f"{inner}color3f[] primvars:displayColor = [({color[0]}, {color[1]}, {color[2]})]"
        )
        lines.append(f"{pad}}}")
    else:
        # Cube in USD: default size=2 (±1 on each axis)
        # Scale by half-extents so cube matches the BBox
        lines.append("")
        lines.append(f'{pad}def Cube "{prim_name}"')
        lines.append(f"{pad}{{")
        inner = _indent(indent + 1)
        lines.append(f"{inner}double size = 1.0")
        lines.append(
            f"{inner}double3 xformOp:scale = ({bbox.x_mm}, {bbox.y_mm}, {bbox.z_mm})"
        )
        lines.append(
            f'{inner}uniform token[] xformOpOrder = ["xformOp:scale"]'
        )
        lines.append(
            f"{inner}color3f[] primvars:displayColor = [({color[0]}, {color[1]}, {color[2]})]"
        )
        lines.append(f"{pad}}}")


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
    seen: set[tuple[str, str]] = set()
    for target_name, contract in contracts.items():
        safe_target = _sanitize_name(target_name)
        for dim in dimensions:
            val = getattr(contract, dim, "")
            if val:
                key = (dim, safe_target)
                if key in seen:
                    continue
                seen.add(key)
                lines.append(
                    f"{pad}rel interface:{dim} = </{root_prim_name}/{safe_target}>"
                )


def _emit_ports(
    contracts: dict[str, "InterfaceContract"],
    indent: int,
    lines: list[str],
) -> None:
    """Emit port locations from InterfaceContract dicts as USD custom properties.

    Each port becomes a group of custom properties under a ``ports`` section:
        custom double3 ports:<target>:<index>:position_mm = (x, y, z)
        custom double3 ports:<target>:<index>:normal = (nx, ny, nz)
        custom string  ports:<target>:<index>:port_type = "..."
    """
    if not contracts:
        return
    pad = _indent(indent)
    any_ports = False
    for target_name, contract in contracts.items():
        if not contract.ports:
            continue
        if not any_ports:
            lines.append("")
            lines.append(f"{pad}# --- Port Locations ---")
            any_ports = True
        safe_target = _sanitize_name(target_name)
        for idx, port in enumerate(contract.ports):
            prefix = f"ports:{safe_target}:{idx}"
            px, py, pz = port.position_mm
            nx, ny, nz = port.normal
            lines.append(
                f"{pad}custom double3 {prefix}:position_mm = ({px}, {py}, {pz})"
            )
            lines.append(
                f"{pad}custom double3 {prefix}:normal = ({nx}, {ny}, {nz})"
            )
            if port.port_type:
                lines.append(
                    f"{pad}custom string {prefix}:port_type = {_usd_string(port.port_type)}"
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
    used_names: set[str] | None = None,
    *,
    proxy_mode: Literal["none", "cube", "inferred"] = "none",
    assembly_color: tuple[float, float, float] = (0.5, 0.5, 0.5),
) -> None:
    """Recursively emit a SuggestedSubsystem as a USD ``def Xform``."""
    pad = _indent(indent)
    safe_name = _compute_prim_name(node)
    # Ensure sibling uniqueness — avoids duplicate prim names at the same level
    if used_names is not None:
        base = safe_name
        counter = 1
        while safe_name in used_names:
            safe_name = f"{base}_{counter}"
            counter += 1
        used_names.add(safe_name)
    kind = _LEVEL_KIND.get(node.level, "group")

    # --- customData block ---
    custom_data_items: list[str] = []
    # Always store the original human-readable name (may contain CJK / Unicode)
    custom_data_items.append(
        f'{_indent(indent + 2)}string display_name = {_usd_string(node.name)}'
    )
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
            spatial.lod_hint if hasattr(spatial, "lod_hint") else "",
            spatial.geometry_is_placeholder if hasattr(spatial, "geometry_is_placeholder") else True,
            body_indent,
            lines,
        )
        # --- Proxy geometry ---
        if proxy_mode != "none" and spatial.bbox is not None:
            if proxy_mode == "inferred":
                shape = _resolve_shape(spatial.bbox, node.name)
            else:
                shape = "Cube"
            _emit_proxy_geometry(
                spatial.bbox, shape, assembly_color, body_indent, lines,
            )

    # --- Clashes ---
    clashes = clash_map.get(node.name, [])
    _emit_clashes(clashes, body_indent, lines)

    # --- Interface relationships ---
    _emit_relationships(node.interface_contracts, root_prim_name, body_indent, lines)

    # --- Port locations ---
    _emit_ports(node.interface_contracts, body_indent, lines)

    # --- Engineering Spec Drafts ---
    draft_key = node.concept_origin_code or _sanitize_name(node.name)
    draft = drafts_by_code.get(draft_key)
    if draft:
        if draft.component_type_hint:
            lines.append(
                f'{body_indent}custom string component_type_hint = '
                f'{_usd_string(draft.component_type_hint)}'
            )
        _emit_specs(draft.specs, body_indent, lines)

    # --- Children (recursive) ---
    child_used_names: set[str] = set()
    for child in node.children:
        lines.append("")
        _emit_subsystem(
            child, root_prim_name, drafts_by_code, clash_map, body_indent, lines,
            child_used_names,
            proxy_mode=proxy_mode,
            assembly_color=assembly_color,
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
    include_proxy_geometry: bool = True,
    proxy_geometry_mode: Literal["none", "cube", "inferred"] = "inferred",
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
    include_proxy_geometry:
        When *True* (default), emit visual proxy geometry (Cube/Cylinder)
        for nodes that have spatial data (``extent_mm``).
    proxy_geometry_mode:
        ``"none"`` — no proxy geometry regardless of *include_proxy_geometry*.
        ``"cube"`` — always use Cube for all nodes.
        ``"inferred"`` (default) — Cylinder for shaft/housing keywords,
        Cube otherwise.

    Returns
    -------
    str
        Complete USDA text ready to write to a ``.usda`` file.
    """
    drafts_by_code = _build_drafts_by_code(drafts)
    clash_map = _build_clash_map(package_map)

    # Effective proxy mode
    effective_proxy: Literal["none", "cube", "inferred"]
    if not include_proxy_geometry or proxy_geometry_mode == "none":
        effective_proxy = "none"
    else:
        effective_proxy = proxy_geometry_mode

    # Root wrapper prim name — always create a wrapper so defaultPrim
    # always points to an existing prim (Req #1).
    if len(subsystems) == 1:
        root_name = _compute_prim_name(subsystems[0])
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

    # --- Root wrapper prim (Req #1) ---
    # When there are multiple subsystems we emit a wrapper Xform named
    # ``root_name`` so that ``defaultPrim`` always resolves.  For a single
    # subsystem the subsystem itself *is* the root prim (backward compat).
    if len(subsystems) != 1:
        lines.append(f'def Xform "{root_name}" (kind = "assembly")')
        lines.append("{")

    # --- Emit each top-level subsystem ---
    top_used_names: set[str] = set()
    base_indent = 1 if len(subsystems) != 1 else 0
    for i, sub in enumerate(subsystems):
        if i > 0:
            lines.append("")
        color = _ASSEMBLY_COLORS[i % len(_ASSEMBLY_COLORS)]
        _emit_subsystem(
            sub, root_name, drafts_by_code, clash_map, base_indent, lines,
            top_used_names,
            proxy_mode=effective_proxy,
            assembly_color=color,
        )

    # Close root wrapper if we opened one
    if len(subsystems) != 1:
        lines.append("}")

    # Ensure trailing newline
    lines.append("")
    return "\n".join(lines)
