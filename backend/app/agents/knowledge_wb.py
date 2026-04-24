"""Knowledge Writeback Agent — auto-assetize project artifacts into knowledge base.

WP-4.7: Extracts 6 asset types from project data, uses LLM to synthesize
concise knowledge articles, and writes them to the knowledge_entries table.

Asset types:
  1. design_pattern    — From selected alternative's mechanism + TRIZ solutions
  2. lesson_learned    — From risk mitigations + experiment results
  3. failure_mode      — From adverse_consequences + high-severity risks
  4. contradiction_solution — From resolved contradictions + TRIZ principles used
  5. design_rule       — From MUST criteria that passed + their thresholds
  6. test_method       — From experiments with evidence_level >= E3
"""

import json
import logging

from app.agents.base import call_llm_json
from app.core.config import settings
from app.core.supabase import get_supabase
from app.models.schemas import (
    KnowledgeWritebackResponse,
    WrittenAsset,
)

logger = logging.getLogger(__name__)

ALL_ASSET_TYPES = [
    "design_pattern",
    "lesson_learned",
    "failure_mode",
    "contradiction_solution",
    "design_rule",
    "test_method",
]

SYNTHESIS_SYSTEM = (
    "You are a knowledge management assistant for engineering design projects. "
    "Given source data, synthesize a concise knowledge article. "
    "Return JSON with keys: title (str), content (str). "
    "The title should be descriptive and specific. "
    "The content should be a concise, actionable summary (2-5 sentences)."
)


# ---------------------------------------------------------------------------
# Source data queries — one function per asset type
# ---------------------------------------------------------------------------


def _query_design_pattern_sources(sb, project_id: str) -> list[dict]:
    """Alternatives (selected) + TRIZ solutions."""
    alts = sb.table("alternatives").select("*").eq("project_id", project_id).eq("selected", True).execute().data
    triz = sb.table("triz_solutions").select("*").eq("project_id", project_id).execute().data
    if not alts and not triz:
        return []
    return [{"alternatives": alts, "triz_solutions": triz}]


def _query_lesson_learned_sources(sb, project_id: str) -> list[dict]:
    """Risk mitigations + experiment results."""
    risks = sb.table("risks").select("*").eq("project_id", project_id).execute().data
    exps = sb.table("experiments").select("*").eq("project_id", project_id).execute().data
    if not risks and not exps:
        return []
    return [{"risks": risks, "experiments": exps}]


def _query_failure_mode_sources(sb, project_id: str) -> list[dict]:
    """Adverse consequences + high-severity risks (severity >= 4)."""
    adverse = sb.table("adverse_consequences").select("*").eq("project_id", project_id).execute().data
    risks = sb.table("risks").select("*").eq("project_id", project_id).gte("severity", 4).execute().data
    if not adverse and not risks:
        return []
    return [{"adverse_consequences": adverse, "high_severity_risks": risks}]


def _query_contradiction_solution_sources(sb, project_id: str) -> list[dict]:
    """Resolved contradictions + TRIZ principles used."""
    contras = sb.table("contradictions").select("*").eq("project_id", project_id).eq("resolved", True).execute().data
    if not contras:
        return []
    return [{"resolved_contradictions": contras}]


def _query_design_rule_sources(sb, project_id: str) -> list[dict]:
    """MUST criteria that passed + their thresholds."""
    musts = sb.table("must_criteria").select("*").eq("project_id", project_id).eq("passed", True).execute().data
    if not musts:
        return []
    return [{"passed_must_criteria": musts}]


def _query_test_method_sources(sb, project_id: str) -> list[dict]:
    """Experiments with evidence_level >= E3."""
    exps = sb.table("experiments").select("*").eq("project_id", project_id).gte("evidence_level", "E3").execute().data
    if not exps:
        return []
    return [{"high_evidence_experiments": exps}]


_SOURCE_QUERIES = {
    "design_pattern": _query_design_pattern_sources,
    "lesson_learned": _query_lesson_learned_sources,
    "failure_mode": _query_failure_mode_sources,
    "contradiction_solution": _query_contradiction_solution_sources,
    "design_rule": _query_design_rule_sources,
    "test_method": _query_test_method_sources,
}

_SYNTHESIS_PROMPTS = {
    "design_pattern": "Synthesize a reusable design pattern article from the selected alternative mechanism and TRIZ solutions below.",
    "lesson_learned": "Synthesize a lesson-learned article from the risk mitigations and experiment results below.",
    "failure_mode": "Synthesize a failure mode article from the adverse consequences and high-severity risks below.",
    "contradiction_solution": "Synthesize a contradiction-solution article from the resolved contradictions and TRIZ principles below.",
    "design_rule": "Synthesize a design rule article from the MUST criteria that passed and their thresholds below.",
    "test_method": "Synthesize a test method article from the high-evidence experiments below.",
}


# ---------------------------------------------------------------------------
# Main writeback function
# ---------------------------------------------------------------------------


def writeback_knowledge(
    project_id: str,
    asset_types: list[str] | None = None,
) -> KnowledgeWritebackResponse:
    """Run knowledge precipitation for the given project.

    Args:
        project_id: The project to extract knowledge from.
        asset_types: Subset of asset types to process. None means all 6.

    Returns:
        KnowledgeWritebackResponse with count and list of created assets.
    """
    sb = get_supabase()
    types_to_process = asset_types if asset_types else ALL_ASSET_TYPES
    created_assets: list[WrittenAsset] = []

    for asset_type in types_to_process:
        query_fn = _SOURCE_QUERIES.get(asset_type)
        if query_fn is None:
            logger.warning("Unknown asset type: %s — skipping", asset_type)
            continue

        # 1. Query source data
        sources = query_fn(sb, project_id)
        if not sources:
            logger.info("No source data for %s in project %s — skipping", asset_type, project_id)
            continue

        # 2. Use LLM to synthesize article
        prompt = _SYNTHESIS_PROMPTS[asset_type]
        user_msg = f"{prompt}\n\nSource data:\n{json.dumps(sources, default=str, ensure_ascii=False)}"

        if settings.use_harness_agents:
            from app.harness.agent_base import harness_call
            from pydantic import BaseModel as _BM

            class _SynthesisOutput(_BM):
                title: str = ""
                content: str = ""

            result = harness_call(
                f"knowledge_wb_{asset_type}", SYNTHESIS_SYSTEM, user_msg,
                _SynthesisOutput,
            )
            title = result.title or f"{asset_type} for {project_id}"
            content = result.content
        else:
            raw = call_llm_json(SYNTHESIS_SYSTEM, user_msg)
            article = json.loads(raw)
            title = article.get("title", f"{asset_type} for {project_id}")
            content = article.get("content", "")

        # 3. Idempotency check: skip if (project_id, asset_type, title) exists
        existing = (
            sb.table("knowledge_entries")
            .select("id")
            .eq("project_id", project_id)
            .eq("asset_type", asset_type)
            .eq("title", title)
            .execute()
            .data
        )
        if existing:
            logger.info("Article already exists: %s / %s / %s — skipping", project_id, asset_type, title)
            continue

        # 4. Insert into knowledge_entries
        row = {
            "project_id": project_id,
            "asset_type": asset_type,
            "title": title,
            "content": content,
            "reviewed": False,
        }
        insert_resp = sb.table("knowledge_entries").insert(row).execute()
        inserted = insert_resp.data[0] if insert_resp.data else row
        entry_id = inserted.get("id", "unknown")

        created_assets.append(
            WrittenAsset(asset_type=asset_type, title=title, id=entry_id)
        )

    return KnowledgeWritebackResponse(
        written_count=len(created_assets),
        assets=created_assets,
    )
