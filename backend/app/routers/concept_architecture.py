"""Concept Architecture Pack — generate and retrieve concept-level architecture.

Bridges TRIZ contradiction solving → Subsystem Definition in the Create page's
forward analysis track.  Two endpoints:

  - POST /concept-architecture/generate-pack  — LLM-generated pack
  - GET  /concept-architecture/latest-pack/{project_id} — rehydrate latest

Ref: plans/concept-architecture-pack.md §5.6
"""

from fastapi import APIRouter

from app.models.schemas import (
    ConceptArchitecturePackRequest,
    ConceptArchitecturePackResponse,
)
from app.agents.concept_architecture import (
    generate_concept_architecture_pack,
    fetch_latest_pack,
)

router = APIRouter()


@router.post(
    "/concept-architecture/generate-pack",
    response_model=ConceptArchitecturePackResponse,
)
def generate_pack(req: ConceptArchitecturePackRequest):
    """Generate a concept architecture pack from upstream artifacts.

    Integrates Brief, Explore (Socratic Q&A / causal loop), and TRIZ results
    into a concept-level subsystem decomposition with interfaces and rationale.
    """
    return generate_concept_architecture_pack(req)


@router.get(
    "/concept-architecture/latest-pack/{project_id}",
    response_model=ConceptArchitecturePackResponse | None,
)
def get_latest_pack(project_id: str):
    """Retrieve the most recently persisted concept architecture pack for a project.

    Returns ``null`` if no pack has been generated yet.
    """
    return fetch_latest_pack(project_id)
