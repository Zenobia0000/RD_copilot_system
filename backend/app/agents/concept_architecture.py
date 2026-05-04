"""Concept Architecture Pack Agent — generates concept-level architecture from upstream artifacts.

Follows the same patterns as triz_solver.py:
- phase_timer for observability
- call_llm_json → json.loads → model_validate
- _persist_* with non-fatal try/except upsert
- emit_counter for metrics
"""

import json
import logging
from typing import Any

from app.agents.base import call_llm_json
from app.core.supabase import get_client
from app.data.concept_subsystem_templates import format_template_for_prompt, get_template
from app.models.schemas import (
    ConceptArchitecturePack,
    ConceptArchitecturePackRequest,
    ConceptArchitecturePackResponse,
    UpstreamArtifactSummary,
)
from app.prompts.concept_architecture import (
    CONCEPT_ARCHITECTURE_PACK_PROMPT,
    CONCEPT_ARCHITECTURE_PACK_SYSTEM,
)

try:
    from app.core.logging import emit_counter, phase_timer
except ImportError:  # pragma: no cover — graceful fallback
    from contextlib import contextmanager

    @contextmanager  # type: ignore[arg-type]
    def phase_timer(name: str, **kw: Any):  # type: ignore[misc]
        yield None

    def emit_counter(name: str, value: int = 1, **kw: Any) -> None:  # type: ignore[misc]
        pass


log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_concept_architecture_pack(
    req: ConceptArchitecturePackRequest,
) -> ConceptArchitecturePackResponse:
    """生成概念架構包 — 整合上游產出物，透過 LLM 產出概念級架構."""
    with phase_timer("generate_concept_architecture_pack", project_id=req.project_id):
        # 1. 選擇模板
        template = get_template(req.template_id)
        template_text = format_template_for_prompt(template)

        # 2. 組裝 prompt
        upstream = req.upstream
        user_prompt = CONCEPT_ARCHITECTURE_PACK_PROMPT.format(
            mission=upstream.mission or "(未提供)",
            constraints_text=upstream.constraints_text or "(未提供)",
            kpis_text=upstream.kpis_text or "(未提供)",
            socratic_text=upstream.socratic_text or "(未提供)",
            contradiction_text=upstream.contradiction_text or "(未提供)",
            triz_text=upstream.triz_text or "(未提供)",
            template_subsystems=template_text,
        )

        # 3. call_llm_json → json.loads → model_validate
        raw = call_llm_json(CONCEPT_ARCHITECTURE_PACK_SYSTEM, user_prompt)
        data = json.loads(raw)
        pack = ConceptArchitecturePack.model_validate(data)

        # 4. 計算 source badges
        source_badges = _compute_source_badges(upstream)

        # 5. persist (non-fatal)
        _persist_concept_architecture_pack(req.project_id, pack, req.template_id)

        emit_counter("concept_architecture_pack_generated", project_id=req.project_id)

        return ConceptArchitecturePackResponse(
            pack=pack,
            source_badges=source_badges,
        )


def fetch_latest_pack(project_id: str) -> ConceptArchitecturePackResponse | None:
    """從資料庫讀取最新的概念架構包."""
    try:
        sb = get_client()
        result = (
            sb.table("concept_architecture_packs")
            .select("*")
            .eq("project_id", project_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if not result.data:
            return None
        row = result.data[0]
        pack = ConceptArchitecturePack.model_validate(row["pack_json"])
        return ConceptArchitecturePackResponse(
            pack=pack,
            source_badges=row.get("source_badges", []),
        )
    except Exception:
        log.warning("fetch_latest_pack failed for project %s", project_id, exc_info=True)
        return None


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _compute_source_badges(upstream: UpstreamArtifactSummary) -> list[str]:
    """根據上游產出物的可用性計算 source badges."""
    badges: list[str] = []
    if upstream.mission:
        badges.append("Brief")
    if upstream.constraints_text:
        badges.append("Constraints")
    if upstream.kpis_text:
        badges.append("KPIs")
    if upstream.socratic_text:
        badges.append("Socratic Q&A")
    if upstream.contradiction_text:
        badges.append("Contradictions")
    if upstream.triz_text:
        badges.append("TRIZ Solutions")
    return badges


def _persist_concept_architecture_pack(
    project_id: str,
    pack: ConceptArchitecturePack,
    template_id: str,
) -> None:
    """Upsert concept architecture pack into DB. Non-fatal on failure."""
    try:
        sb = get_client()
        sb.table("concept_architecture_packs").upsert(
            {
                "project_id": project_id,
                "pack_json": pack.model_dump(mode="json"),
                "template_id": template_id,
                "applied": False,
                "source_badges": _compute_source_badges_from_pack(pack),
            },
            on_conflict="project_id",
        ).execute()
    except Exception:
        log.warning(
            "Failed to persist concept architecture pack for project %s",
            project_id,
            exc_info=True,
        )


def _compute_source_badges_from_pack(pack: ConceptArchitecturePack) -> list[str]:
    """Derive minimal badge list from pack content (fallback for persist)."""
    badges: list[str] = []
    if pack.subsystems:
        badges.append("Architecture")
    if pack.interfaces:
        badges.append("Interfaces")
    return badges
