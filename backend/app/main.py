"""FastAPI application entry point.

Ref: AI_Agent_Architecture.md §6.1 — FastAPI backend for multi-agent orchestration.
"""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.middleware.auth import get_current_user
from app.middleware.error_handler import register_error_handlers
from app.middleware.request_id import RequestIDMiddleware
from app.routers import (
    brief, socratic, cld, anti_anchor, triz, scamper,
    risk, action, convergence, must,
    contradictions, assumptions, pre_cad, want, gates, exports, knowledge_wb,
    validation, unknown_factors, spatial, observability,
    analyst_v2,
    evidence,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up TRIZ KB cache on startup
    from app.tools.triz_kb import load_39_parameters, load_40_principles, load_76_standard_solutions
    import logging as _log
    try:
        load_39_parameters()
        load_40_principles()
        load_76_standard_solutions()
    except FileNotFoundError:
        _log.getLogger(__name__).warning(
            "TRIZ KB files not found — TRIZ endpoints will return degraded results"
        )
    yield


setup_logging()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

register_error_handlers(app)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth dependency applied to all business routers.
# Health and docs endpoints remain public (no auth required).
# To apply per-router instead:
#   router = APIRouter(dependencies=[Depends(get_current_user)])
_auth = [Depends(get_current_user)]
API_PREFIX = "/api/v1"

# Register routers — aligned with SOW module naming
app.include_router(brief.router, prefix=API_PREFIX, tags=["任務定義 definitions"], dependencies=_auth)
app.include_router(socratic.router, prefix=API_PREFIX, tags=["蘇格拉底問答 questions"], dependencies=_auth)
app.include_router(cld.router, prefix=API_PREFIX, tags=["因果迴路 causal-loops"], dependencies=_auth)
app.include_router(contradictions.router, prefix=API_PREFIX, tags=["矛盾管理 contradictions"], dependencies=_auth)
app.include_router(assumptions.router, prefix=API_PREFIX, tags=["假設台帳 assumptions"], dependencies=_auth)
app.include_router(anti_anchor.router, prefix=API_PREFIX, tags=["方案管理 alternatives"], dependencies=_auth)
app.include_router(triz.router, prefix=API_PREFIX, tags=["TRIZ 求解 triz"], dependencies=_auth)
app.include_router(scamper.router, prefix=API_PREFIX, tags=["SCAMPER scamper"], dependencies=_auth)
app.include_router(risk.router, prefix=API_PREFIX, tags=["風險登錄 risks"], dependencies=_auth)
app.include_router(action.router, prefix=API_PREFIX, tags=["行動建議 actions"], dependencies=_auth)
app.include_router(convergence.router, prefix=API_PREFIX, tags=["收斂掃描 convergence"], dependencies=_auth)
app.include_router(must.router, prefix=API_PREFIX, tags=["MUST 篩選 must"], dependencies=_auth)
app.include_router(pre_cad.router, prefix=API_PREFIX, tags=["Pre-CAD 審查 pre-cad-reviews"], dependencies=_auth)
app.include_router(want.router, prefix=API_PREFIX, tags=["WANT 評分 want"], dependencies=_auth)
app.include_router(gates.router, prefix=API_PREFIX, tags=["Gate 檢查 gates"], dependencies=_auth)
app.include_router(exports.router, prefix=API_PREFIX, tags=["匯出 export"], dependencies=_auth)
app.include_router(knowledge_wb.router, prefix=API_PREFIX, tags=["知識回寫 knowledge"], dependencies=_auth)
app.include_router(validation.router, prefix=API_PREFIX, tags=["驗證護照 validation"], dependencies=_auth)
app.include_router(unknown_factors.router, prefix=API_PREFIX, tags=["未知集合 unknown-factors"], dependencies=_auth)
app.include_router(spatial.router, prefix=API_PREFIX, tags=["空間查找 spatial"], dependencies=_auth)
app.include_router(analyst_v2.router, prefix=API_PREFIX, tags=["Auto-TRIZ v2 分析 analyst"], dependencies=_auth)
app.include_router(evidence.router, prefix=API_PREFIX, tags=["Evidence 追蹤 evidence"], dependencies=_auth)
# Web Vitals beacon — no auth: sendBeacon can't reliably attach auth headers.
app.include_router(observability.router, prefix=API_PREFIX, tags=["observability"])


@app.get(f"{API_PREFIX}/health")
async def health():
    return {"status": "ok"}
