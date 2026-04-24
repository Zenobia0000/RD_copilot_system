"""Evidence Registry — centralised claim tracking for AI-generated assertions.

WBS 8.4.1: Core service for registering, verifying, and measuring evidence
coverage across a project. Works against the Supabase `evidence_claims` table.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from app.core.supabase import get_supabase

logger = logging.getLogger(__name__)

ClaimType = Literal["assumption", "hypothesis", "result", "constraint"]
ClaimStatus = Literal["unverified", "verified", "refuted", "partial"]


async def register_claim(
    project_id: str,
    claim_text: str,
    claim_type: ClaimType,
    linked_artifact_id: str | None = None,
    linked_artifact_type: str | None = None,
) -> dict:
    """Register a new evidence claim into the evidence_claims table.

    Returns the created row as a dict.
    """
    sb = get_supabase()
    payload: dict = {
        "id": str(uuid4()),
        "project_id": project_id,
        "claim_text": claim_text,
        "claim_type": claim_type,
        "status": "unverified",
        "verification_sources": [],
        "confidence_score": 0.0,
    }
    if linked_artifact_id is not None:
        payload["linked_artifact_id"] = linked_artifact_id
    if linked_artifact_type is not None:
        payload["linked_artifact_type"] = linked_artifact_type

    result = sb.table("evidence_claims").insert(payload).execute()
    return result.data[0] if result.data else payload


async def verify_claim(
    claim_id: str,
    verification_source: dict,
    new_status: ClaimStatus,
    confidence_score: float | None = None,
) -> dict:
    """Verify / update a claim's status and append a verification source.

    Args:
        claim_id: UUID of the claim to update.
        verification_source: A dict describing the evidence, e.g.
            {"type": "test_report", "ref": "TR-001", "note": "..."}.
        new_status: Target status after verification.
        confidence_score: Optional override for confidence (0.0-1.0).

    Returns the updated row.
    """
    sb = get_supabase()

    # Fetch current sources so we can append
    existing = (
        sb.table("evidence_claims")
        .select("verification_sources")
        .eq("id", claim_id)
        .single()
        .execute()
    )
    current_sources: list = existing.data.get("verification_sources") or []
    current_sources.append(verification_source)

    update_payload: dict = {
        "status": new_status,
        "verification_sources": current_sources,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if confidence_score is not None:
        update_payload["confidence_score"] = confidence_score

    result = (
        sb.table("evidence_claims")
        .update(update_payload)
        .eq("id", claim_id)
        .execute()
    )
    return result.data[0] if result.data else update_payload


async def get_coverage(project_id: str) -> dict:
    """Calculate evidence coverage statistics for a project.

    Returns:
        {
            "total_claims": int,
            "verified_count": int,
            "refuted_count": int,
            "partial_count": int,
            "unverified_count": int,
            "coverage_ratio": float,   # verified / total (0.0 if no claims)
            "by_type": {
                "assumption": {"total": int, "verified": int, ...},
                ...
            },
        }
    """
    sb = get_supabase()
    result = (
        sb.table("evidence_claims")
        .select("claim_type, status")
        .eq("project_id", project_id)
        .execute()
    )
    rows = result.data or []

    total = len(rows)
    verified = sum(1 for r in rows if r["status"] == "verified")
    refuted = sum(1 for r in rows if r["status"] == "refuted")
    partial = sum(1 for r in rows if r["status"] == "partial")
    unverified = sum(1 for r in rows if r["status"] == "unverified")

    # Per-type breakdown
    by_type: dict[str, dict[str, int]] = {}
    for row in rows:
        ct = row["claim_type"]
        if ct not in by_type:
            by_type[ct] = {"total": 0, "verified": 0, "refuted": 0, "partial": 0, "unverified": 0}
        by_type[ct]["total"] += 1
        by_type[ct][row["status"]] += 1

    return {
        "total_claims": total,
        "verified_count": verified,
        "refuted_count": refuted,
        "partial_count": partial,
        "unverified_count": unverified,
        "coverage_ratio": round(verified / total, 4) if total > 0 else 0.0,
        "by_type": by_type,
    }
