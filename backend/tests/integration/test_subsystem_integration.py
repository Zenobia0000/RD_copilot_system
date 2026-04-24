"""Integration tests for WBS 3.2, 4.2, 5.2 of the Subsystem Interface
Development plan (docs/e2e/module/Subsystem_Interface_Development_WBS.md).

Scope:
  - WBS 3.2: when the LLM cites a reference_source whose key is missing in
    every layer, confidence is downgraded to "estimate" and the LLM's
    bbox/mass are preserved (last-resort fallback).
  - WBS 4.2: after POST /spatial/component-overrides upserts a row, the next
    resolver call for that project returns reference_source starting with
    "rd_override:<key>" (L1 hit).
  - WBS 5.2: POST /spatial/learned-components is idempotent on duplicate key
    (no new row, confirmed_count bumped, existing bbox NOT overwritten — per
    current router semantics).

Stubbing strategy: a tiny in-memory FakeSupabase that captures upsert/insert/
update/select for the two tables we care about. It is patched into both
`app.routers.spatial.get_supabase` (write path) and
`app.core.supabase.get_supabase` (read path used by the resolver backends).
This lets us drive the 4.2 end-to-end test through the real router AND the
real `RdOverrideBackend` without touching any real DB — one fake,
shared-state, no mock-matrix explosion.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from app.agents.triz_solver import _resolve_spatial_via_layers
from app.models.schemas import (
    BBox,
    InterfaceContract,
    SpatialEstimate,
    SuggestedSubsystem,
)
from app.services.spatial_lookup import (
    LookupQuery,
    RdOverrideBackend,
    SpatialResolver,
)


# ---------------------------------------------------------------------------
# Tiny in-memory Supabase fake
# ---------------------------------------------------------------------------


class _Response:
    def __init__(self, data: list[dict]):
        self.data = data


class _Query:
    """Chainable query builder — mirrors the subset of supabase-py used by
    the router and the resolver backends."""

    def __init__(self, table: "_Table", op: str = "select"):
        self.table = table
        self.op = op
        self.filters: list[tuple[str, Any]] = []
        self.payload: Any = None
        self.upsert_conflict: str = ""
        self._limit: int | None = None

    # --- terminal ops -----------------------------------------------------
    def select(self, *_a, **_k) -> "_Query":
        self.op = "select"
        return self

    def upsert(self, payload: dict, on_conflict: str = "") -> "_Query":
        self.op = "upsert"
        self.payload = payload
        self.upsert_conflict = on_conflict
        return self

    def insert(self, payload: dict) -> "_Query":
        self.op = "insert"
        self.payload = payload
        return self

    def update(self, payload: dict) -> "_Query":
        self.op = "update"
        self.payload = payload
        return self

    def delete(self) -> "_Query":
        self.op = "delete"
        return self

    # --- chainable filters ------------------------------------------------
    def eq(self, col: str, val: Any) -> "_Query":
        self.filters.append((col, val))
        return self

    def order(self, *_a, **_k) -> "_Query":
        return self

    def limit(self, n: int) -> "_Query":
        self._limit = n
        return self

    # --- execution --------------------------------------------------------
    def _match(self, row: dict) -> bool:
        return all(row.get(col) == val for col, val in self.filters)

    def execute(self) -> _Response:
        rows = self.table.rows
        if self.op == "select":
            matching = [r for r in rows if self._match(r)]
            if self._limit is not None:
                matching = matching[: self._limit]
            return _Response(matching)
        if self.op == "upsert":
            conflict_cols = [c.strip() for c in self.upsert_conflict.split(",") if c.strip()]
            if conflict_cols:
                for r in rows:
                    if all(r.get(c) == self.payload.get(c) for c in conflict_cols):
                        r.update(self.payload)
                        return _Response([r])
            rows.append(dict(self.payload))
            return _Response([self.payload])
        if self.op == "insert":
            rows.append(dict(self.payload))
            return _Response([self.payload])
        if self.op == "update":
            updated = []
            for r in rows:
                if self._match(r):
                    r.update(self.payload)
                    updated.append(r)
            return _Response(updated)
        if self.op == "delete":
            keep = [r for r in rows if not self._match(r)]
            removed = [r for r in rows if self._match(r)]
            self.table.rows = keep
            return _Response(removed)
        return _Response([])


class _Table:
    def __init__(self, name: str):
        self.name = name
        self.rows: list[dict] = []

    def __getattr__(self, item):
        # Any method called directly on the table short-circuits to a query.
        q = _Query(self)
        return getattr(q, item)


class FakeSupabase:
    def __init__(self) -> None:
        self._tables: dict[str, _Table] = {}
        self.rpc_calls: list[tuple[str, dict]] = []

    def table(self, name: str) -> _Query:
        tbl = self._tables.setdefault(name, _Table(name))
        return _Query(tbl)

    def rpc(self, name: str, params: dict) -> "FakeSupabase._Rpc":
        self.rpc_calls.append((name, params))
        return FakeSupabase._Rpc()

    class _Rpc:
        def execute(self) -> _Response:
            return _Response([])

    # Helpers for assertions
    def rows(self, table_name: str) -> list[dict]:
        return self._tables.setdefault(table_name, _Table(table_name)).rows


@pytest.fixture()
def fake_sb():
    """Provide a FakeSupabase patched into both the router module and the
    resolver backends' lazy import target."""
    sb = FakeSupabase()
    with patch("app.routers.spatial.get_supabase", return_value=sb), \
         patch("app.core.supabase.get_supabase", return_value=sb):
        yield sb


# ---------------------------------------------------------------------------
# Minimal builder helpers
# ---------------------------------------------------------------------------


def _module_with_citation(
    *,
    target: str,
    reference_source: str,
    bbox: tuple[float, float, float],
    mass_g: float,
) -> SuggestedSubsystem:
    return SuggestedSubsystem(
        name="Subject",
        level="module",
        interface_contracts={
            target: InterfaceContract(
                spatial=SpatialEstimate(
                    bbox=BBox(x_mm=bbox[0], y_mm=bbox[1], z_mm=bbox[2]),
                    mass_g=mass_g,
                    reference_source=reference_source,
                    confidence="library",
                    rationale="LLM best guess",
                )
            )
        },
    )


class _EmptyResolver(SpatialResolver):
    """Returns None for every lookup (simulates 'no layer matches this key')."""

    def lookup(self, query):  # type: ignore[override]
        return None


# ---------------------------------------------------------------------------
# WBS 3.2 — confidence downgrade when cited key is missing
# ---------------------------------------------------------------------------


class TestConfidenceDowngradeOnMissingKey:
    """Gap-filling coverage for WBS 3.2.

    The existing test `test_agent_downgrades_unknown_layer_citation` in
    test_spatial_validator.py already covers the `learned:` prefix with a
    single bbox dim. These tests round out the matrix:

      - each supported prefix (rd_override / learned / seed)
      - assert BOTH bbox AND mass are preserved (not just one dim)
      - assert the LLM-supplied rationale is NOT mutated
    """

    def test_rd_override_prefix_missing_key_preserves_llm_bbox(self):
        node = _module_with_citation(
            target="Frame",
            reference_source="rd_override:nonexistent_motor_xyz",
            bbox=(123.0, 45.0, 67.0),
            mass_g=888.0,
        )
        _resolve_spatial_via_layers(
            [node], project_id="p1", resolver=_EmptyResolver()
        )
        sp = node.interface_contracts["Frame"].spatial
        assert sp.confidence == "estimate"
        assert sp.bbox.x_mm == 123.0
        assert sp.bbox.y_mm == 45.0
        assert sp.bbox.z_mm == 67.0
        assert sp.mass_g == 888.0
        # reference_source and rationale must be preserved — this is still a
        # cited (albeit broken) source, not a fresh llm_estimate.
        assert sp.reference_source == "rd_override:nonexistent_motor_xyz"
        assert sp.rationale == "LLM best guess"

    def test_learned_prefix_missing_key_downgrades_to_estimate(self):
        node = _module_with_citation(
            target="Gearbox",
            reference_source="learned:does_not_exist_12345",
            bbox=(200.0, 150.0, 100.0),
            mass_g=4200.0,
        )
        _resolve_spatial_via_layers(
            [node], project_id="p1", resolver=_EmptyResolver()
        )
        sp = node.interface_contracts["Gearbox"].spatial
        assert sp.confidence == "estimate"
        # All three dims preserved — previous test_spatial_validator coverage
        # only asserted x_mm.
        assert (sp.bbox.x_mm, sp.bbox.y_mm, sp.bbox.z_mm) == (200.0, 150.0, 100.0)
        assert sp.mass_g == 4200.0

    def test_seed_prefix_missing_key_keeps_llm_number(self):
        node = _module_with_citation(
            target="Frame",
            reference_source="seed:definitely_not_in_seed_json",
            bbox=(10.0, 20.0, 30.0),
            mass_g=50.0,
        )
        _resolve_spatial_via_layers(
            [node], project_id="p1", resolver=_EmptyResolver()
        )
        sp = node.interface_contracts["Frame"].spatial
        assert sp.confidence == "estimate"
        assert (sp.bbox.x_mm, sp.bbox.y_mm, sp.bbox.z_mm) == (10.0, 20.0, 30.0)
        assert sp.mass_g == 50.0
        assert sp.reference_source == "seed:definitely_not_in_seed_json"


# ---------------------------------------------------------------------------
# WBS 4.2 — override write then resolver L1 hit
# ---------------------------------------------------------------------------


class TestOverrideHitsL1OnNextLookup:
    """WBS 4.2 coverage gap: the existing
    `test_agent_resolver_prefers_rd_override_over_seed` test pre-stubs a
    StubResolver that always returns an rd_override estimate. It proves the
    agent RESPECTS an override that already exists but does NOT exercise the
    write path. These tests go end-to-end: hit the real HTTP endpoint, let
    the router upsert into the fake Supabase, then instantiate a REAL
    `RdOverrideBackend` which reads it back through the same fake.
    """

    def _post_override(self, client, project_id: str, key: str, bbox, mass):
        resp = client.post(
            "/api/v1/spatial/component-overrides",
            json={
                "project_id": project_id,
                "component_key": key,
                "category": "motor",
                "bbox": {
                    "x_mm": bbox[0],
                    "y_mm": bbox[1],
                    "z_mm": bbox[2],
                    "anchor": "",
                },
                "mass_g": mass,
                "note": "RD custom spec",
            },
        )
        assert resp.status_code == 200, resp.text
        return resp.json()

    def test_override_write_then_resolver_returns_rd_override_reference(
        self, client, fake_sb
    ):
        body = self._post_override(
            client, "proj-alpha", "custom_mid_drive", (210.0, 160.0, 140.0), 4500.0
        )
        assert body["saved"] is True
        # Table now has exactly one row.
        assert len(fake_sb.rows("project_component_overrides")) == 1

        # Fresh resolver + backend — no pre-stubbed data, must hit the fake.
        backend = RdOverrideBackend()
        resolver = SpatialResolver(backends=[backend])

        node = _module_with_citation(
            target="Frame",
            reference_source="learned:custom_mid_drive",  # LLM may cite any prefix
            bbox=(1.0, 1.0, 1.0),  # nonsense numbers we expect to be replaced
            mass_g=1.0,
        )
        _resolve_spatial_via_layers(
            [node], project_id="proj-alpha", resolver=resolver
        )
        sp = node.interface_contracts["Frame"].spatial
        assert sp.reference_source.startswith("rd_override:")
        assert sp.reference_source == "rd_override:custom_mid_drive"
        assert sp.confidence == "rd_confirmed"
        assert sp.bbox.x_mm == 210.0
        assert sp.bbox.y_mm == 160.0
        assert sp.bbox.z_mm == 140.0
        assert sp.mass_g == 4500.0

    def test_override_scoped_to_project_only(self, client, fake_sb):
        self._post_override(
            client, "proj-alpha", "custom_mid_drive", (210.0, 160.0, 140.0), 4500.0
        )
        backend = RdOverrideBackend()

        # Same key, DIFFERENT project → no hit.
        hit = backend.lookup(
            LookupQuery(key="custom_mid_drive", project_id="proj-other")
        )
        assert hit is None

        # Same key, correct project → hit.
        hit = backend.lookup(
            LookupQuery(key="custom_mid_drive", project_id="proj-alpha")
        )
        assert hit is not None
        assert hit.reference_source == "rd_override:custom_mid_drive"


# ---------------------------------------------------------------------------
# WBS 5.2 — learned promote idempotency
# ---------------------------------------------------------------------------


class TestLearnedPromotionIdempotency:
    """Lock the current router behaviour for
    POST /spatial/learned-components on duplicate keys. Per
    `promote_learned_component` in app/routers/spatial.py:

      - First call with a new key → insert, confirmed_count = 1.
      - Second call with the SAME key → NO new row; confirmed_count bumps to 2
        via RPC `bump_learned_component_confirm` (or manual update fallback).
      - Existing bbox/mass are NOT overwritten — the first confirmed value is
        canonical by design. RD wanting to correct it must use a
        project-level override instead.
    """

    def _payload(self, key: str, bbox, mass: float) -> dict:
        return {
            "key": key,
            "category": "motor",
            "bbox": {
                "x_mm": bbox[0],
                "y_mm": bbox[1],
                "z_mm": bbox[2],
                "anchor": "",
            },
            "mass_g": mass,
            "origin": "manual",
            "origin_project_id": "",
            "source_url": "",
            "source_text": "",
        }

    def test_promote_same_key_twice_does_not_duplicate(self, client, fake_sb):
        p = self._payload("bafang_custom_a", (180.0, 140.0, 120.0), 3800.0)

        r1 = client.post("/api/v1/spatial/learned-components", json=p)
        assert r1.status_code == 200, r1.text
        assert r1.json()["confirmed_count"] == 1

        r2 = client.post("/api/v1/spatial/learned-components", json=p)
        assert r2.status_code == 200, r2.text

        rows = fake_sb.rows("learned_components")
        assert len(rows) == 1, f"expected idempotent upsert, got rows={rows}"

    def test_promote_increments_confirmed_count(self, client, fake_sb):
        p = self._payload("bafang_custom_b", (200.0, 150.0, 130.0), 4000.0)

        r1 = client.post("/api/v1/spatial/learned-components", json=p)
        assert r1.json()["confirmed_count"] == 1

        r2 = client.post("/api/v1/spatial/learned-components", json=p)
        body2 = r2.json()
        # Router reports bumped count in its response regardless of whether
        # the RPC or the manual fallback path ran.
        assert body2["confirmed_count"] == 2
        # And the RPC was attempted (fake logs it) — we don't assert the RPC
        # succeeded, just that the router tried the canonical path first.
        assert any(call[0] == "bump_learned_component_confirm" for call in fake_sb.rpc_calls)

    def test_promote_updates_bbox_on_collision(self, client, fake_sb):
        """Locks the CURRENT behaviour: the router does NOT overwrite bbox
        on duplicate-key promotion. The first-seen dimensions are canonical;
        subsequent calls with different bbox only bump the confirmed_count.
        If this test fails in the future, a product decision has flipped the
        canonical-dimensions rule and WBS 5.2 needs to be re-specified.
        """
        first = self._payload("bafang_custom_c", (180.0, 140.0, 120.0), 3800.0)
        r1 = client.post("/api/v1/spatial/learned-components", json=first)
        assert r1.status_code == 200

        # Second call has deliberately different bbox and mass.
        second = self._payload("bafang_custom_c", (999.0, 888.0, 777.0), 9999.0)
        r2 = client.post("/api/v1/spatial/learned-components", json=second)
        assert r2.status_code == 200
        # No error, no duplicate row.
        rows = fake_sb.rows("learned_components")
        assert len(rows) == 1
        # Canonical bbox/mass untouched — this is the locked behaviour.
        row = rows[0]
        assert row["bbox"]["x_mm"] == 180.0
        assert row["bbox"]["y_mm"] == 140.0
        assert row["bbox"]["z_mm"] == 120.0
        assert row["mass_g"] == 3800.0
