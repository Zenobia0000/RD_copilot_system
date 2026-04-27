"""Knowledge Writeback: auto-assetization of project artifacts.

SOW Module: 知識回寫 (knowledge)
SOW Endpoints:
  - POST /knowledge/writeback

WP-4.7: Full 6-asset writeback pipeline.
"""

from fastapi import APIRouter

from app.agents.knowledge_wb import writeback_knowledge
from app.models.schemas import KnowledgeWritebackRequest, KnowledgeWritebackResponse

router = APIRouter()


@router.post("/knowledge/writeback", response_model=KnowledgeWritebackResponse)
def knowledge_writeback(req: KnowledgeWritebackRequest):
    """Auto-assetize 6 artifact types to knowledge base."""
    asset_types = req.asset_types if req.asset_types else None
    return writeback_knowledge(req.project_id, asset_types=asset_types)
