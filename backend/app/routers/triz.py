"""Step 5a — TRIZ Solver: contradiction matrix lookup + principle instantiation + Su-Field.

v8 (2026-04-20): Adds direction-centric endpoints:
  - `POST /triz/solve-directed` — single-contradiction direction solver
  - `POST /triz/consolidate` — cross-contradiction direction consolidation

The legacy `/triz/solve-layered` endpoint is kept for back-compat but
the primary flow is now `/triz/solve-directed` + `/triz/consolidate`.

Ref:
  - User flow specification §二–§四
"""

from fastapi import APIRouter

from app.models.schemas import (
    TrizLookupRequest, TrizLookupResponse,
    SuFieldRequest, SuFieldResponse,
    SolveTrizLayeredRequest, SolveTrizLayeredResponse,
    SolveDirectedRequest, SolveDirectedResponse,
    ConsolidateRequest, ConsolidateResponse,
    SIMMatrixRequest, SIMMatrixResponse,
    ComplexityCheckRequest, ComplexityCheckResponse,
)
from app.agents.triz_solver import (
    solve_triz, analyze_sufield, solve_triz_layered,
    solve_triz_directed, consolidate_solutions,
    sim_matrix, complexity_check,
)

router = APIRouter()


@router.post("/triz/solve", response_model=TrizLookupResponse)
def triz_solve(req: TrizLookupRequest):
    """TRIZ Solver Agent resolves a contradiction via a SINGLE TC / PC / SF path.

    Kept as a primitive API — direct use by the UI is deprecated.
    """
    return solve_triz(req)


@router.post("/triz/sufield", response_model=SuFieldResponse)
def triz_sufield(req: SuFieldRequest):
    """Su-Field analysis: model the system and match 76 standard solutions."""
    return analyze_sufield(req)


@router.post("/triz/solve-layered", response_model=SolveTrizLayeredResponse)
def triz_solve_layered(req: SolveTrizLayeredRequest):
    """v7 — Three-layer drill-down TRIZ solver (LEGACY — kept for back-compat).

    Prefer `/triz/solve-directed` for new consumers.
    """
    return solve_triz_layered(req)


@router.post("/triz/solve-directed", response_model=SolveDirectedResponse)
def triz_solve_directed(req: SolveDirectedRequest):
    """v8 — Direction-centric TRIZ solver for a single contradiction.

    Pipeline per contradiction:
      Step A: TC solve (matrix → 40 principles)
      Step B: Derive PC + solve (separation principles)
      Step C: Derive SF + solve (76 standard solutions)
      Step D: Merge all solutions with path tags
      Step E: LLM clusters solutions by implementation direction
      Step F: LLM + rules score each direction
      Step G: Pick Top1 + Top2

    Returns ContradictionDirectionResult with all directions + scored + top picks.
    """
    return solve_triz_directed(req)


@router.post("/triz/consolidate", response_model=ConsolidateResponse)
def triz_consolidate(req: ConsolidateRequest):
    """v8 — Cross-contradiction direction consolidation.

    Takes N ContradictionDirectionResults, checks Top1 compatibility,
    tries Top2 swap if conflicts, outputs final adopted plan or conflict report.
    """
    return consolidate_solutions(req)


@router.post("/triz/sim-matrix", response_model=SIMMatrixResponse)
def triz_sim_matrix(req: SIMMatrixRequest):
    """Auto-TRIZ v2 (WBS 8.3.1) — Solution Interaction Matrix.

    Evaluates pairwise interactions (+1 synergy / 0 neutral / -1 conflict)
    between solutions from different contradictions, finds the optimal
    non-conflicting combination, and persists the result.
    """
    return sim_matrix(req)


@router.post("/triz/complexity-check", response_model=ComplexityCheckResponse)
def triz_complexity_check(req: ComplexityCheckRequest):
    """Auto-TRIZ v2 (WBS 8.3.2) — Concept Complexity Index (CCI).

    Lightweight evaluation of whether a solution is an evolution (increases
    Ideality) or a patch (adds complexity). Does not persist to DB.
    """
    return complexity_check(req)
