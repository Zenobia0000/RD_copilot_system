"""Export: project artifact export to Markdown/JSON/USDA.

SOW Module: 匯出 (export)
SOW Endpoints:
  - POST /export
  - POST /export/usda
"""

import json
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    ExportRequest,
    ExportResponse,
    NodeUsdaLlmRequest,
    UsdaExportRequest,
    UsdaExportResponse,
)
from app.core.supabase import get_supabase
from app.services.usda_serializer import serialize_to_usda
from app.services.usda_llm_generator import generate_node_usda

router = APIRouter()

# Sections available for export, in presentation order
SECTION_ORDER = [
    "brief",
    "constraints",
    "kpis",
    "assumptions",
    "contradictions",
    "cld",
    "alternatives",
    "triz_solutions",
    "scamper_variants",
    "risks",
    "experiments",
    "decisions",
    "knowledge",
]


def _fetch_section(sb, project_id: str, section: str) -> list[dict]:
    """Fetch rows for one section from Supabase."""
    table_map = {
        "brief": "briefs",
        "constraints": "constraints",
        "kpis": "kpis",
        "assumptions": "assumptions",
        "contradictions": "contradictions",
        "cld": "cld_nodes",
        "alternatives": "alternatives",
        "triz_solutions": "triz_solutions",
        "scamper_variants": "scamper_variants",
        "risks": "risks",
        "experiments": "experiments",
        "decisions": "decisions",
        "knowledge": "knowledge_entries",
    }
    table = table_map.get(section)
    if not table:
        return []
    result = sb.table(table).select("*").eq("project_id", project_id).execute()
    return result.data or []


def _section_to_markdown(section: str, rows: list[dict]) -> str:
    """Convert one section's rows to Markdown."""
    if not rows:
        return ""

    title_map = {
        "brief": "任務定義 Brief",
        "constraints": "約束條件 Constraints",
        "kpis": "關鍵績效指標 KPIs",
        "assumptions": "假設台帳 Assumptions",
        "contradictions": "矛盾清單 Contradictions",
        "cld": "因果迴路節點 CLD Nodes",
        "alternatives": "設計方案 Alternatives",
        "triz_solutions": "TRIZ 解法 Solutions",
        "scamper_variants": "SCAMPER 變形 Variants",
        "risks": "風險登錄 Risks",
        "experiments": "實驗記錄 Experiments",
        "decisions": "決策記錄 Decisions",
        "knowledge": "知識資產 Knowledge Entries",
    }

    lines = [f"## {title_map.get(section, section)}\n"]

    if section == "brief":
        for row in rows:
            lines.append(f"**Mission**: {row.get('mission', '—')}\n")
            td = row.get("task_definition_5w1h")
            if td and isinstance(td, dict):
                for k, v in td.items():
                    lines.append(f"- **{k.upper()}**: {v}")
            lines.append("")
        return "\n".join(lines)

    if section == "constraints":
        lines.append("| Code | Description | Type | Source | Feasibility |")
        lines.append("|------|-------------|------|--------|-------------|")
        for row in rows:
            lines.append(
                f"| {row.get('constraint_code', '—')} "
                f"| {row.get('description', '—')} "
                f"| {row.get('type', '—')} "
                f"| {row.get('source', '—')} "
                f"| {row.get('feasibility', '—')} |"
            )
        lines.append("")
        return "\n".join(lines)

    if section == "kpis":
        lines.append("| KPI | Target | Unit | Measurement | Status |")
        lines.append("|-----|--------|------|-------------|--------|")
        for row in rows:
            lines.append(
                f"| {row.get('kpi_name', '—')} "
                f"| {row.get('target_value', '—')} "
                f"| {row.get('unit', '—')} "
                f"| {row.get('measurement_method', '—')} "
                f"| {row.get('current_status', '—')} |"
            )
        lines.append("")
        return "\n".join(lines)

    if section == "assumptions":
        lines.append("| Code | Content | Severity | Status |")
        lines.append("|------|---------|----------|--------|")
        for row in rows:
            lines.append(
                f"| {row.get('code', '—')} "
                f"| {row.get('content', '—')} "
                f"| {row.get('worst_severity', '—')} "
                f"| {row.get('status', '—')} |"
            )
        lines.append("")
        return "\n".join(lines)

    if section == "contradictions":
        lines.append("| Description | Type | Severity | Resolved |")
        lines.append("|-------------|------|----------|----------|")
        for row in rows:
            lines.append(
                f"| {row.get('natural_description', '—')} "
                f"| {row.get('type', '—')} "
                f"| {row.get('severity', '—')} "
                f"| {'✅' if row.get('resolved') else '❌'} |"
            )
        lines.append("")
        return "\n".join(lines)

    if section == "alternatives":
        for row in rows:
            lines.append(f"### {row.get('name', '—')}")
            lines.append(f"- **Mechanism**: {row.get('mechanism', '—')}")
            lines.append(f"- **Source**: {row.get('source', '—')}")
            lines.append(f"- **Overall Pass**: {'✅' if row.get('overall_pass') else '❌' if row.get('overall_pass') is False else '—'}")
            lines.append("")
        return "\n".join(lines)

    if section == "risks":
        lines.append("| Description | Failure Mode | P | S | P×S | Mitigation |")
        lines.append("|-------------|-------------|---|---|-----|------------|")
        for row in rows:
            p = row.get("probability", 0)
            s = row.get("severity", 0)
            lines.append(
                f"| {row.get('description', '—')} "
                f"| {row.get('failure_mode', '—')} "
                f"| {p} | {s} | {p * s} "
                f"| {row.get('mitigation', '—')} |"
            )
        lines.append("")
        return "\n".join(lines)

    if section == "decisions":
        for row in rows:
            lines.append(f"- **選定方案**: {row.get('selected_alternative_name', '—')}")
            lines.append(f"- **理由**: {row.get('rationale', '—')}")
            lines.append(f"- **狀態**: {row.get('status', '—')}")
            lines.append(f"- **日期**: {row.get('decision_date', '—')}")
            lines.append("")
        return "\n".join(lines)

    # Generic fallback: bullet list of key fields
    for row in rows:
        label = row.get("name") or row.get("title") or row.get("label") or row.get("id", "—")
        detail = row.get("description") or row.get("content") or row.get("mechanism") or ""
        lines.append(f"- **{label}**: {detail}")
    lines.append("")
    return "\n".join(lines)


@router.post("/export", response_model=ExportResponse)
def export_project(req: ExportRequest):
    """Export project artifacts to Markdown or JSON format."""
    sb = get_supabase()

    # Verify project exists
    project = sb.table("projects").select("name").eq("id", req.project_id).maybe_single().execute()
    if not project.data:
        raise HTTPException(status_code=404, detail=f"Project {req.project_id} not found")

    project_name = project.data.get("name", "project")

    # Determine sections to export
    sections = req.sections if req.sections else SECTION_ORDER

    # Fetch all requested sections
    all_data: dict[str, list[dict]] = {}
    for section in sections:
        if section not in SECTION_ORDER:
            continue
        all_data[section] = _fetch_section(sb, req.project_id, section)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if req.format == "json":
        content = json.dumps(all_data, default=str, ensure_ascii=False, indent=2)
        filename = f"{project_name}_{timestamp}.json"
    else:
        # Markdown
        md_parts = [f"# {project_name} — Design Report\n"]
        md_parts.append(f"> Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        for section in sections:
            if section not in all_data:
                continue
            part = _section_to_markdown(section, all_data[section])
            if part:
                md_parts.append(part)
        content = "\n---\n\n".join(md_parts)
        filename = f"{project_name}_{timestamp}.md"

    return ExportResponse(
        content=content,
        format=req.format,
        filename=filename,
    )


@router.post("/export/usda", response_model=UsdaExportResponse)
def export_usda(req: UsdaExportRequest):
    """Export subsystem hierarchy as a USD ASCII (.usda) scene file.

    The caller provides the subsystem tree, optional engineering spec drafts,
    and optional PackageMap directly in the request body — no Supabase round-trip
    needed. This keeps the endpoint stateless and testable.
    """
    if not req.subsystems:
        raise HTTPException(
            status_code=422,
            detail="At least one subsystem is required for USDA export.",
        )

    project_name = req.project_name or req.project_id or "Project"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    content = serialize_to_usda(
        req.subsystems,
        project_id=req.project_id,
        project_name=project_name,
        drafts=req.drafts or None,
        package_map=req.package_map,
        include_proxy_geometry=req.include_proxy_geometry,
        proxy_geometry_mode=req.proxy_geometry_mode,
    )

    safe_name = project_name.replace(" ", "_")
    filename = f"{safe_name}_{timestamp}.usda"

    return UsdaExportResponse(content=content, filename=filename)


@router.post("/export/usda-llm", response_model=UsdaExportResponse)
def export_usda_llm(req: NodeUsdaLlmRequest):
    """Generate a USD ASCII file for a single hierarchy node via LLM.

    Unlike ``/export/usda`` which uses deterministic rule-based serialization,
    this endpoint delegates generation to an LLM for quick concept previews.
    """
    try:
        content = generate_node_usda(req)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    safe_name = req.node_name.replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_name}_{timestamp}.usda"

    return UsdaExportResponse(content=content, filename=filename)
