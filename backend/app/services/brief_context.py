"""Brief-stage context aggregator for the TRIZ context-aware coverage audit.

Single responsibility: given a project_id, build one
:class:`BriefContextSnapshot` so downstream Step H-1 (decompose) and
Step H-2 (audit) can judge every solution direction against the
*original* problem context (mission / constraints / KPIs / socratic
insights / CLD risks) rather than the contradiction string alone.

Design rules
------------
- **No LLM calls** — pure data shaping. The shaping is intentionally
  conservative (truncation / dedupe) so the prompt block stays bounded
  no matter how chatty the upstream Explore stage was.
- **Tolerant of partial data** — every Supabase fetch is wrapped so a
  missing table or empty result yields an empty list, not an exception.
  Empty fields surface as ``"(未提供)"`` in the prompt assembler, which
  tells the LLM *explicitly* that a context channel is missing instead
  of silently producing a context-blind verdict.
- **Length-bounded** — Socratic Q&A and CLD blocks have hard caps so
  context injection cannot dominate the prompt window. See module
  constants ``MAX_SOCRATIC_INSIGHTS`` / ``MAX_CLD_NODES`` /
  ``MAX_CLD_EDGES``.

Refs
----
- Architect plan: 方案 A 「Context-aware coverage audit」
- Supabase tables: ``briefs`` / ``constraints`` / ``kpis`` /
  ``socratic_questions`` / ``cld_nodes`` / ``cld_edges``
  (see ``supabase/migrations/000_full_deploy.sql``)
"""

from __future__ import annotations

import logging

from app.core.supabase import get_supabase
from app.models.schemas import (
    BriefConstraint,
    BriefContextSnapshot,
    BriefKpi,
    CldEdgeSummary,
    CldNodeSummary,
    CldSummary,
    SocraticInsight,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Length caps — keep prompt block bounded regardless of project size.
# Tuning rationale:
#   - 12 Socratic insights ≈ 3-4kb context; covers the "key already-answered
#     questions" without dumping every clarification.
#   - 30 CLD nodes / 60 edges is enough for typical 2-3 reinforcing loops
#     plus a few balancing arrows; bigger graphs are very rare in this UI.
# These numbers are intentionally generous on the first iteration —
# Todo 16 (e2e 基準) will measure real token cost and tighten if needed.
# ---------------------------------------------------------------------------
MAX_SOCRATIC_INSIGHTS = 12
MAX_CLD_NODES = 30
MAX_CLD_EDGES = 60


# ---------------------------------------------------------------------------
# Public entry
# ---------------------------------------------------------------------------

def fetch_brief_context(project_id: str) -> BriefContextSnapshot:
    """Build a :class:`BriefContextSnapshot` from Supabase for one project.

    Always returns a snapshot, never raises — missing data degrades to
    empty fields. Each sub-fetch is isolated so a flaky single query
    cannot wipe out the whole context.
    """
    if not project_id:
        logger.warning("fetch_brief_context: empty project_id, returning empty snapshot")
        return BriefContextSnapshot(project_id="")

    sb = get_supabase()
    snapshot = BriefContextSnapshot(project_id=project_id)

    snapshot.mission = _fetch_mission(sb, project_id)
    snapshot.constraints = _fetch_constraints(sb, project_id)
    snapshot.kpis = _fetch_kpis(sb, project_id)
    snapshot.socratic_summary = _fetch_socratic_summary(sb, project_id)
    snapshot.cld_summary = _fetch_cld_summary(sb, project_id)

    logger.info(
        "fetch_brief_context: project=%s mission=%s constraints=%d kpis=%d "
        "socratic=%d cld_nodes=%d cld_edges=%d",
        project_id,
        bool(snapshot.mission),
        len(snapshot.constraints),
        len(snapshot.kpis),
        len(snapshot.socratic_summary),
        len(snapshot.cld_summary.nodes),
        len(snapshot.cld_summary.edges),
    )
    return snapshot


# ---------------------------------------------------------------------------
# Per-table fetchers — each isolates its own try/except so a partial
# failure (e.g. CLD missing) still yields mission/constraints/KPIs.
# ---------------------------------------------------------------------------

def _fetch_mission(sb, project_id: str) -> str:
    """Read briefs.mission. Empty string if no row."""
    try:
        res = (
            sb.table("briefs")
            .select("mission")
            .eq("project_id", project_id)
            .limit(1)
            .execute()
        )
        rows = res.data or []
        if rows and rows[0].get("mission"):
            return str(rows[0]["mission"]).strip()
    except Exception as exc:  # noqa: BLE001
        logger.warning("fetch mission failed for project %s: %s", project_id, exc)
    return ""


def _fetch_constraints(sb, project_id: str) -> list[BriefConstraint]:
    """Read constraints table. Empty list on error."""
    try:
        res = (
            sb.table("constraints")
            .select("constraint_code,description,type,feasibility")
            .eq("project_id", project_id)
            .execute()
        )
        out: list[BriefConstraint] = []
        for r in res.data or []:
            out.append(
                BriefConstraint(
                    code=str(r.get("constraint_code") or "").strip(),
                    description=str(r.get("description") or "").strip(),
                    type=str(r.get("type") or "hard").strip() or "hard",
                    feasibility=str(r.get("feasibility") or "unknown").strip() or "unknown",
                )
            )
        return out
    except Exception as exc:  # noqa: BLE001
        logger.warning("fetch constraints failed for project %s: %s", project_id, exc)
        return []


def _fetch_kpis(sb, project_id: str) -> list[BriefKpi]:
    """Read kpis table. Empty list on error."""
    try:
        res = (
            sb.table("kpis")
            .select("kpi_name,target_value,unit,current_value,current_status")
            .eq("project_id", project_id)
            .execute()
        )
        out: list[BriefKpi] = []
        for r in res.data or []:
            out.append(
                BriefKpi(
                    name=str(r.get("kpi_name") or "").strip(),
                    target_value=str(r.get("target_value") or "").strip(),
                    unit=str(r.get("unit") or "").strip(),
                    current_value=str(r.get("current_value") or "").strip(),
                    current_status=str(r.get("current_status") or "unknown").strip() or "unknown",
                )
            )
        return out
    except Exception as exc:  # noqa: BLE001
        logger.warning("fetch kpis failed for project %s: %s", project_id, exc)
        return []


def _fetch_socratic_summary(sb, project_id: str) -> list[SocraticInsight]:
    """Read socratic_questions with non-empty answers.

    Only answered questions enter the audit — empty answers cannot
    inform whether a direction is valid in the original context.
    Capped at :const:`MAX_SOCRATIC_INSIGHTS`.
    """
    try:
        res = (
            sb.table("socratic_questions")
            .select("category,text,answer,tagged_as_assumption")
            .eq("project_id", project_id)
            .execute()
        )
        out: list[SocraticInsight] = []
        for r in res.data or []:
            answer = str(r.get("answer") or "").strip()
            if not answer:
                continue  # silent skip — unanswered questions add noise
            out.append(
                SocraticInsight(
                    category=str(r.get("category") or "").strip(),
                    question=str(r.get("text") or "").strip(),
                    answer=answer,
                    is_assumption=bool(r.get("tagged_as_assumption")),
                )
            )
        # Prefer tagged assumptions first — they are the highest-signal
        # context for the audit (direction may silently depend on them).
        out.sort(key=lambda s: (not s.is_assumption, s.category))
        return out[:MAX_SOCRATIC_INSIGHTS]
    except Exception as exc:  # noqa: BLE001
        logger.warning("fetch socratic_summary failed for project %s: %s", project_id, exc)
        return []


def _fetch_cld_summary(sb, project_id: str) -> CldSummary:
    """Read cld_nodes / cld_edges. Empty CldSummary on error.

    Capped at :const:`MAX_CLD_NODES` / :const:`MAX_CLD_EDGES`. When the
    graph is over-capped, leverage nodes are kept preferentially so
    the audit can still spot breakpoint-related side-effects.
    """
    try:
        nodes_res = (
            sb.table("cld_nodes")
            .select("id,label,node_type,is_leverage")
            .eq("project_id", project_id)
            .execute()
        )
        edges_res = (
            sb.table("cld_edges")
            .select("from_node,to_node,polarity")
            .eq("project_id", project_id)
            .execute()
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("fetch cld_summary failed for project %s: %s", project_id, exc)
        return CldSummary()

    raw_nodes = nodes_res.data or []
    raw_edges = edges_res.data or []

    # Build id→label map first; edges use UUIDs but the LLM needs labels.
    id_to_label: dict[str, str] = {}
    leverage_labels: list[str] = []
    nodes: list[CldNodeSummary] = []

    # Stable ordering: leverage nodes first so they survive truncation.
    raw_nodes_sorted = sorted(
        raw_nodes,
        key=lambda r: (not r.get("is_leverage"), r.get("label") or ""),
    )
    for r in raw_nodes_sorted[:MAX_CLD_NODES]:
        label = str(r.get("label") or "").strip()
        if not label:
            continue
        node_type = str(r.get("node_type") or "variable").strip() or "variable"
        is_lev = bool(r.get("is_leverage"))
        id_to_label[str(r.get("id"))] = label
        if is_lev:
            leverage_labels.append(label)
        nodes.append(
            CldNodeSummary(label=label, node_type=node_type, is_leverage=is_lev)
        )

    edges: list[CldEdgeSummary] = []
    for r in raw_edges[:MAX_CLD_EDGES]:
        f_label = id_to_label.get(str(r.get("from_node")))
        t_label = id_to_label.get(str(r.get("to_node")))
        if not f_label or not t_label:
            # Edge references a truncated node — drop rather than emit
            # an orphan reference the LLM cannot ground.
            continue
        edges.append(
            CldEdgeSummary(
                from_label=f_label,
                to_label=t_label,
                polarity=str(r.get("polarity") or "+").strip() or "+",
            )
        )

    return CldSummary(nodes=nodes, edges=edges, leverage_points=leverage_labels)
