"""Prompt templates for LLM-based USDA generation.

Provides the system prompt and user-message builder used by
``usda_llm_generator.generate_node_usda``.
"""

from __future__ import annotations

USDA_SYSTEM_PROMPT = """\
You are a USD ASCII expert engineer. Your task is to generate valid .usda files
for engineering subsystem descriptions.

## USD ASCII Rules
1. File MUST start with `#usda 1.0` header
2. Use `def Xform` for organizational nodes with `kind = "assembly"` or `kind = "component"`
3. Use `custom` prefix for all non-standard attributes
4. String values use double quotes
5. Numeric arrays use parentheses: `float3 = (1.0, 2.0, 3.0)`
6. Indent with 4 spaces per level
7. Use `metersPerUnit = 0.001` for millimeter-based designs
8. Use `upAxis = "Z"`

## Attribute Naming Convention
- Engineering specs: `custom string eng:field_name = "value"`
- Spatial data: `custom float3 spatial:dimensions_mm = (x, y, z)`
- Material info: `custom string material:name = "value"`
- Thermal specs: `custom float thermal:max_temp_c = value`

## Structure Rules
- System level: `def Xform "SystemName" (kind = "assembly")`
- Module level: `def Xform "ModuleName" (kind = "group")`
- Component level: `def Xform "ComponentName" (kind = "component")`
- Proxy geometry: `def Cube "Proxy"` or `def Cylinder "Proxy"` inside component
- Use `custom string description = "..."` for node descriptions

## Output Requirements
- Output ONLY the .usda content, no markdown code fences
- All prim names must be valid USD identifiers: alphanumeric + underscore only
- Include meaningful comments with `#` for engineering context
- Generate proxy geometry with reasonable dimensions based on specs
"""


def build_usda_user_message(
    node_name: str,
    node_level: str,
    node_description: str,
    specs_summary: list[dict],
    interface_contracts: dict,
    children_names: list[str],
) -> str:
    """Assemble user message for USDA generation.

    Parameters
    ----------
    node_name:
        Human-readable node name, e.g. ``"Drive_System"``.
    node_level:
        One of ``"system"``, ``"module"``, ``"component"``.
    node_description:
        Concatenated description text (node reason + children reasons).
    specs_summary:
        List of dicts with keys ``field_name``, ``value``, ``unit``, ``category``.
    interface_contracts:
        Mapping of partner name → contract description dict.
    children_names:
        Direct child subsystem names.

    Returns
    -------
    str
        Fully-assembled user prompt string.
    """
    parts: list[str] = []
    parts.append(
        f"Generate a complete .usda file for the following {node_level}-level subsystem:\n"
    )
    parts.append(f"## Node: {node_name}")
    parts.append(f"Level: {node_level}")
    parts.append(f"\n## Description\n{node_description}")

    if specs_summary:
        parts.append("\n## Engineering Specifications")
        for spec in specs_summary:
            unit_str = f" {spec['unit']}" if spec.get("unit") else ""
            parts.append(
                f"- {spec['field_name']}: {spec['value']}{unit_str} [{spec['category']}]"
            )

    if children_names:
        parts.append("\n## Child Subsystems")
        for name in children_names:
            parts.append(f"- {name}")
        parts.append("\nCreate Xform prims for each child subsystem.")

    if interface_contracts:
        parts.append("\n## Interface Contracts")
        for partner, contract in interface_contracts.items():
            parts.append(f"- Interface with {partner}: {contract}")

    parts.append("\nGenerate the .usda now.")
    return "\n".join(parts)
