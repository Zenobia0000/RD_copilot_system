"""Solver Registry — @register_solver for pluggable problem-solving pipelines.

Follows the same decorator pattern as evaluator_registry.py.
Each solver is a callable: (request) -> response.
Routers dispatch to solvers by name via solver_registry.dispatch().

Usage:
    from app.harness.solver_registry import register_solver, dispatch

    @register_solver("triz_layered", description="L1→critic→L2→L3 drill-down")
    def solve_layered(req: SolveTrizLayeredRequest) -> SolveTrizLayeredResponse:
        ...

    # In router:
    result = dispatch("triz_layered", req)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)

SolverFn = Callable[..., Any]


@dataclass
class SolverDefinition:
    """Metadata for a registered solver."""
    name: str
    fn: SolverFn
    description: str = ""
    tags: list[str] = field(default_factory=list)


SOLVER_REGISTRY: dict[str, SolverDefinition] = {}


def register_solver(
    name: str,
    *,
    description: str = "",
    tags: list[str] | None = None,
):
    """Decorator to register a solver function.

    Args:
        name: Unique solver identifier (e.g. "triz_layered").
        description: Human-readable description.
        tags: Optional categorization tags.
    """
    def decorator(fn: SolverFn) -> SolverFn:
        if name in SOLVER_REGISTRY:
            logger.warning(
                "Overwriting solver '%s' (was %s, now %s)",
                name,
                SOLVER_REGISTRY[name].fn.__qualname__,
                fn.__qualname__,
            )
        SOLVER_REGISTRY[name] = SolverDefinition(
            name=name,
            fn=fn,
            description=description,
            tags=tags or [],
        )
        logger.debug("Registered solver '%s': %s", name, fn.__qualname__)
        return fn
    return decorator


def dispatch(name: str, request: Any) -> Any:
    """Dispatch a request to a registered solver by name.

    Raises:
        ValueError: If the solver name is not registered.
    """
    defn = SOLVER_REGISTRY.get(name)
    if defn is None:
        registered = sorted(SOLVER_REGISTRY.keys())
        raise ValueError(
            f"Unknown solver: '{name}'. Registered: {registered}"
        )
    return defn.fn(request)


def list_solvers() -> list[SolverDefinition]:
    """Return all registered solvers, sorted by name."""
    return sorted(SOLVER_REGISTRY.values(), key=lambda s: s.name)
