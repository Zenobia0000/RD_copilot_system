"""Tests for harness/solver_registry.py — solver registration + dispatch."""

import pytest

from app.harness.solver_registry import (
    SOLVER_REGISTRY,
    SolverDefinition,
    dispatch,
    list_solvers,
    register_solver,
)


@pytest.fixture(autouse=True)
def _clean_registry():
    """Save and restore SOLVER_REGISTRY around each test."""
    saved = dict(SOLVER_REGISTRY)
    SOLVER_REGISTRY.clear()
    yield
    SOLVER_REGISTRY.clear()
    SOLVER_REGISTRY.update(saved)


def test_register_solver_basic():
    @register_solver("test_solver", description="A test solver")
    def my_solver(req):
        return {"result": req}

    assert "test_solver" in SOLVER_REGISTRY
    defn = SOLVER_REGISTRY["test_solver"]
    assert defn.name == "test_solver"
    assert defn.description == "A test solver"
    assert defn.fn is my_solver


def test_register_solver_with_tags():
    @register_solver("tagged", tags=["triz", "layered"])
    def solver(req):
        return req

    assert SOLVER_REGISTRY["tagged"].tags == ["triz", "layered"]


def test_dispatch_calls_solver():
    @register_solver("echo")
    def echo_solver(req):
        return f"echoed: {req}"

    result = dispatch("echo", "hello")
    assert result == "echoed: hello"


def test_dispatch_unknown_raises():
    with pytest.raises(ValueError, match="Unknown solver"):
        dispatch("nonexistent", {})


def test_list_solvers_sorted():
    @register_solver("beta")
    def s1(r): return r

    @register_solver("alpha")
    def s2(r): return r

    solvers = list_solvers()
    assert [s.name for s in solvers] == ["alpha", "beta"]


def test_overwrite_logs_warning(caplog):
    @register_solver("dup")
    def first(r): return "first"

    with caplog.at_level("WARNING"):
        @register_solver("dup")
        def second(r): return "second"

    assert "Overwriting solver 'dup'" in caplog.text
    assert dispatch("dup", None) == "second"


def test_triz_layered_solver_registered():
    """The orchestrator module auto-registers 'triz_layered' on import."""
    # Import triggers the @register_solver decorator
    import app.harness.orchestrator  # noqa: F401

    assert "triz_layered" in SOLVER_REGISTRY
    defn = SOLVER_REGISTRY["triz_layered"]
    assert "L1" in defn.description or "drill-down" in defn.description
    assert "triz" in defn.tags
