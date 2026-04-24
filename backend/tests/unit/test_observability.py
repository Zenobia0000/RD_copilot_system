"""Tests for WBS 11.4 observability primitives.

Exercises:
  * ``phase_timer`` happy-path / error / re-raise semantics.
  * ``emit_counter`` value coercion and label passthrough.
  * ``suggest_subsystems`` integration — the four phase metrics are
    emitted in the documented order with all LLM / resolver / validator
    boundaries stubbed (no external I/O).

Emission style reminder: ``metrics.py`` writes the payload as a JSON
string log *message* (not ``extra=``). Tests parse
``record.getMessage()`` back into a dict.
"""

from __future__ import annotations

import json
import logging

import pytest

from app.observability import emit_counter, phase_timer


METRICS_LOGGER = "metrics"


def _parse_metrics(caplog) -> list[dict]:
    """Return decoded metric payloads in emission order."""
    out: list[dict] = []
    for record in caplog.records:
        if record.name != METRICS_LOGGER:
            continue
        try:
            out.append(json.loads(record.getMessage()))
        except (TypeError, ValueError):
            continue
    return out


# ---------------------------------------------------------------------------
# phase_timer
# ---------------------------------------------------------------------------


def test_phase_timer_happy_path_emits_ok(caplog):
    caplog.set_level(logging.INFO, logger=METRICS_LOGGER)

    with phase_timer("unit.test_phase", project_id="p1", flavor="vanilla"):
        pass

    metrics = _parse_metrics(caplog)
    assert len(metrics) == 1
    m = metrics[0]
    assert m["metric"] == "phase"
    assert m["name"] == "unit.test_phase"
    assert m["status"] == "ok"
    assert isinstance(m["duration_ms"], float)
    assert m["duration_ms"] >= 0.0
    assert m["labels"] == {"project_id": "p1", "flavor": "vanilla"}
    assert "error_type" not in m


def test_phase_timer_on_exception_emits_error_and_reraises(caplog):
    caplog.set_level(logging.INFO, logger=METRICS_LOGGER)

    class BoomError(RuntimeError):
        pass

    with pytest.raises(BoomError):
        with phase_timer("unit.boom", attempt=3):
            raise BoomError("kaboom")

    metrics = _parse_metrics(caplog)
    assert len(metrics) == 1
    m = metrics[0]
    assert m["metric"] == "phase"
    assert m["name"] == "unit.boom"
    assert m["status"] == "error"
    assert m["error_type"] == "BoomError"
    assert m["labels"] == {"attempt": 3}
    assert isinstance(m["duration_ms"], float)


def test_phase_timer_accepts_status_override(caplog):
    caplog.set_level(logging.INFO, logger=METRICS_LOGGER)

    with phase_timer("unit.override") as state:
        state["status"] = "fallback"

    metrics = _parse_metrics(caplog)
    assert len(metrics) == 1
    assert metrics[0]["status"] == "fallback"


# ---------------------------------------------------------------------------
# emit_counter
# ---------------------------------------------------------------------------


def test_emit_counter_defaults_to_one(caplog):
    caplog.set_level(logging.INFO, logger=METRICS_LOGGER)
    emit_counter("unit.counter_default")

    metrics = _parse_metrics(caplog)
    assert len(metrics) == 1
    m = metrics[0]
    assert m["metric"] == "counter"
    assert m["name"] == "unit.counter_default"
    assert m["value"] == 1
    assert isinstance(m["value"], int)
    assert m["labels"] == {}


def test_emit_counter_with_value_and_labels(caplog):
    caplog.set_level(logging.INFO, logger=METRICS_LOGGER)
    emit_counter("unit.counter_labelled", value=7, attempt=2, project_id="p1")

    metrics = _parse_metrics(caplog)
    assert len(metrics) == 1
    m = metrics[0]
    assert m["metric"] == "counter"
    assert m["value"] == 7
    assert m["labels"] == {"attempt": 2, "project_id": "p1"}


# ---------------------------------------------------------------------------
# suggest_subsystems integration — phase ordering
# ---------------------------------------------------------------------------


def test_suggest_subsystems_emits_phase_metrics_in_order(caplog, monkeypatch):
    """End-to-end phase ordering check.

    Stubs the LLM + the spatial resolver + the package validator so no
    external I/O happens. Asserts that the four UC1 phase metrics are
    emitted in the contract-fixed order:
        summarize → llm_suggest → resolve_spatial → discover_package
    """
    from app.agents import triz_solver
    from app.models.schemas import (
        PackageMap,
        RequiredEnvelope,
        SubsystemSuggestRequest,
    )

    _empty_pkg = PackageMap(
        nodes=[],
        required=RequiredEnvelope(
            total_bbox_mm=(0.0, 0.0, 0.0),
            total_mass_g=0.0,
        ),
    )

    caplog.set_level(logging.INFO, logger=METRICS_LOGGER)

    # Stub LLM call — return a minimally valid response with no subsystems
    # so the 6-dim validator finds no violations and no retry is triggered.
    fake_json = json.dumps({"subsystems": []})
    monkeypatch.setattr(
        triz_solver,
        "call_llm_json",
        lambda system, prompt, **kwargs: fake_json,
    )

    # Stub the spatial resolver so summarize_for_prompt is fast and returns
    # a known string without hitting Supabase / seed JSON.
    class _FakeResolver:
        def summarize_for_prompt(self, project_id: str = "", max_chars: int = 2500) -> str:
            return "# stub"

        def lookup(self, query):  # pragma: no cover - unused when subsystems empty
            return None

    monkeypatch.setattr(
        triz_solver,
        "default_resolver",
        lambda include_web=False: _FakeResolver(),
    )

    # Stub spatial layer walk + validator.
    monkeypatch.setattr(
        triz_solver,
        "_resolve_spatial_via_layers",
        lambda subsystems, project_id, resolver=None: None,
    )
    monkeypatch.setattr(
        triz_solver,
        "discover_package",
        lambda subsystems: _empty_pkg,
    )

    req = SubsystemSuggestRequest(
        project_id="p-obs",
        mission="observability test",
        contradictions=[],
        existing_subsystems=[],
    )
    resp = triz_solver.suggest_subsystems(req)
    assert resp.package_map is not None

    metrics = _parse_metrics(caplog)
    phase_names = [m["name"] for m in metrics if m.get("metric") == "phase"]

    # Must contain all four in the documented order. (Other metrics from
    # deeper layers may interleave but the UC1 phases must appear in order.)
    expected_order = [
        "uc1.summarize",
        "uc1.llm_suggest",
        "uc1.resolve_spatial",
        "uc1.discover_package",
    ]
    filtered = [n for n in phase_names if n in expected_order]
    assert filtered == expected_order, (
        f"Expected UC1 phases in order {expected_order}, got {filtered} "
        f"(all phases: {phase_names})"
    )

    # All four should be status=ok in the happy path.
    uc1_metrics = [m for m in metrics if m.get("name") in expected_order]
    assert all(m["status"] == "ok" for m in uc1_metrics)
    assert all(isinstance(m["duration_ms"], float) for m in uc1_metrics)
    assert all(m["labels"].get("project_id") == "p-obs" for m in uc1_metrics)
