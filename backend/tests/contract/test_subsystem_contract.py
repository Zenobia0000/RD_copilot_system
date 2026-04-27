"""Contract / schema snapshot tests for WBS 11.2.

Locks the wire contract for four FastAPI endpoints that the FE depends on:

    POST /subsystems/suggest             (migrated from /scamper/subsystem-suggestions)
    POST /subsystems/spatial-overlay     (migrated from /scamper/spatial-overlay)
    POST /spatial/component-overrides
    POST /spatial/learned-components

The goal is NOT to re-test business logic — that belongs in
``test_spatial_validator.py`` and ``test_triz_solver.py``. The goal is:

1. If anyone renames a request/response field (e.g. ``component_key`` →
   ``componentKey``) the schema snapshot will fail loudly.
2. If the response envelope shape changes (e.g. someone returns a bare
   ``PackageMap`` from ``/subsystems/spatial-overlay`` instead of
   ``{package_map: PackageMap}``) the field-level guard will fail.
3. The router happy-path must remain callable with a realistic payload and
   the body must parse cleanly back into the declared response model.

All LLM / Supabase / resolver boundaries are stubbed — no external I/O.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.models.schemas import (
    BBox,
    ComponentOverrideRequest,
    ComponentOverrideResponse,
    InterfaceContract,
    LearnedComponentPromoteRequest,
    LearnedComponentPromoteResponse,
    PackageMap,
    PackageNode,
    RequiredEnvelope,
    SpatialEstimate,
    SpatialOverlayRequest,
    SpatialOverlayResponse,
    SubsystemSuggestRequest,
    SubsystemSuggestResponse,
    SuggestedSubsystem,
)


API = "/api/v1"


# ---------------------------------------------------------------------------
# Helpers: build canned response payloads the stubs return
# ---------------------------------------------------------------------------


def _canned_package_map() -> PackageMap:
    """A PackageMap with every FE-critical field populated so the guards
    have something non-default to look at."""
    return PackageMap(
        nodes=[
            PackageNode(
                name="Motor → Gearbox",
                spatial=SpatialEstimate(
                    bbox=BBox(x_mm=180, y_mm=140, z_mm=120, anchor="BB_center"),
                    mass_g=3900,
                    reference_source="seed:bafang_m600_mid_drive",
                    confidence="library",
                    rationale="vendor datasheet",
                ),
                clashes=[],
            ),
        ],
        required=RequiredEnvelope(
            total_bbox_mm=(180.0, 140.0, 120.0),
            total_mass_g=3900.0,
            by_anchor={"BB_center": (180.0, 140.0, 120.0)},
        ),
        overlay_budget=None,
        overlay_violations=[],
        svg="<svg>stub</svg>",
        table_md="| Module | x | y | z |\n|---|---|---|---|\n| Motor → Gearbox | 180 | 140 | 120 |",
        notes=["stub"],
    )


def _canned_suggestion_response() -> SubsystemSuggestResponse:
    return SubsystemSuggestResponse(
        subsystems=[
            SuggestedSubsystem(
                name="Motor",
                level="module",
                reason="mid-drive propulsion",
                related_contradictions=["weight vs range"],
                children=[],
                interface_contracts={
                    "Gearbox": InterfaceContract(
                        envelope="180x140x120mm",
                        loadPath="bottom bracket → crank",
                        thermalPath="case → frame",
                        signalPath="CAN bus to controller",
                        datumTolerance="±0.1mm",
                        serviceability="removable cover",
                        spatial=SpatialEstimate(
                            bbox=BBox(x_mm=180, y_mm=140, z_mm=120, anchor="BB_center"),
                            mass_g=3900,
                            reference_source="seed:bafang_m600_mid_drive",
                            confidence="library",
                        ),
                    ),
                },
            ),
        ],
        package_map=_canned_package_map(),
    )


# ---------------------------------------------------------------------------
# Supabase chain stub: returns a fluent mock that satisfies the spatial router
# ---------------------------------------------------------------------------


def _make_supabase_stub(existing_learned_rows=None):
    """Return a Supabase-client-shaped mock where every fluent call returns
    another mock whose ``.execute()`` yields a SimpleNamespace(data=...).

    ``existing_learned_rows`` lets a test pre-populate the
    ``learned_components`` select result so the router exercises the
    "bump existing" path or the "insert new" path.
    """
    existing_learned_rows = existing_learned_rows or []

    # Chain terminus
    exec_insert = MagicMock(return_value=SimpleNamespace(data=[{"ok": True}]))
    exec_upsert = MagicMock(return_value=SimpleNamespace(data=[{"ok": True}]))
    exec_select = MagicMock(return_value=SimpleNamespace(data=existing_learned_rows))
    exec_update = MagicMock(return_value=SimpleNamespace(data=[{"ok": True}]))
    exec_rpc = MagicMock(return_value=SimpleNamespace(data=None))

    table_mock = MagicMock()
    # .upsert(...).execute()
    table_mock.upsert.return_value.execute = exec_upsert
    # .insert(...).execute()
    table_mock.insert.return_value.execute = exec_insert
    # .update(...).eq(...).execute()
    table_mock.update.return_value.eq.return_value.execute = exec_update
    # .select(...).eq(...).limit(...).execute()
    table_mock.select.return_value.eq.return_value.limit.return_value.execute = exec_select

    sb = MagicMock()
    sb.table.return_value = table_mock
    sb.rpc.return_value.execute = exec_rpc
    return sb


# ---------------------------------------------------------------------------
# TestSubsystemSuggestionsContract  — POST /scamper/subsystem-suggestions
# ---------------------------------------------------------------------------


class TestSubsystemSuggestionsContract:
    """Lock the wire contract for POST /subsystems/suggest."""

    # v7 (WBS 11.1): added optional `layered_triz_solutions` field on top of
    # the legacy shape. Default value is an empty list, so legacy callers stay
    # byte-identical on the wire after serialisation.
    EXPECTED_REQUEST = {
        "project_id": "p1",
        "mission": "lightweight commuter e-bike",
        "contradictions": ["weight vs range"],
        "existing_subsystems": ["Motor"],
        "layered_triz_solutions": [],
    }

    def test_request_schema_is_frozen(self):
        req = SubsystemSuggestRequest(**self.EXPECTED_REQUEST)
        assert req.model_dump() == self.EXPECTED_REQUEST
        # Defaults: empty lists for both list fields when omitted
        minimal = SubsystemSuggestRequest(project_id="p1", mission="m")
        assert minimal.model_dump() == {
            "project_id": "p1",
            "mission": "m",
            "contradictions": [],
            "existing_subsystems": [],
            "layered_triz_solutions": [],
        }

    def test_response_schema_top_level_keys(self):
        resp = _canned_suggestion_response()
        dumped = resp.model_dump()
        # Top-level envelope must be exactly {subsystems, package_map}
        assert set(dumped.keys()) == {"subsystems", "package_map"}
        # Subsystem entry keys — FE relies on this exact set
        sub0 = dumped["subsystems"][0]
        assert set(sub0.keys()) == {
            "name",
            "level",
            "reason",
            "related_contradictions",
            "children",
            "interface_contracts",
        }
        # Interface contract must expose ALL six camelCase dims + spatial
        contract = sub0["interface_contracts"]["Gearbox"]
        assert set(contract.keys()) == {
            "envelope",
            "loadPath",
            "thermalPath",
            "signalPath",
            "datumTolerance",
            "serviceability",
            "spatial",
        }

    def test_happy_path_round_trip(self, client):
        canned = _canned_suggestion_response()
        with patch(
            "app.routers.subsystems.suggest_subsystems",
            return_value=canned,
        ) as stub:
            r = client.post(
                f"{API}/subsystems/suggest",
                json=self.EXPECTED_REQUEST,
            )
        assert r.status_code == 200, r.text
        stub.assert_called_once()
        # Must parse back into the declared response model without loss
        parsed = SubsystemSuggestResponse.model_validate(r.json())
        assert parsed.subsystems[0].name == "Motor"
        assert parsed.package_map is not None

    def test_regression_guards_package_map_and_contracts(self, client):
        """Fields the FE reads directly — any rename breaks the UI."""
        canned = _canned_suggestion_response()
        with patch(
            "app.routers.subsystems.suggest_subsystems",
            return_value=canned,
        ):
            body = client.post(
                f"{API}/subsystems/suggest",
                json=self.EXPECTED_REQUEST,
            ).json()

        pm = body["package_map"]
        # nodes[].clashes must exist (even empty) and be a list
        assert "clashes" in pm["nodes"][0]
        assert isinstance(pm["nodes"][0]["clashes"], list)
        # required.total_bbox_mm is a 3-tuple serialized as a list
        assert len(pm["required"]["total_bbox_mm"]) == 3
        # svg is str or None — never missing
        assert "svg" in pm and isinstance(pm["svg"], (str, type(None)))
        # Neighbour-keyed contracts dict — "Gearbox" is the neighbour name
        contracts = body["subsystems"][0]["interface_contracts"]
        assert isinstance(contracts, dict)
        assert "Gearbox" in contracts


# ---------------------------------------------------------------------------
# TestSpatialOverlayContract  — POST /scamper/spatial-overlay
# ---------------------------------------------------------------------------


class TestSpatialOverlayContract:
    """Lock the wire contract for POST /subsystems/spatial-overlay.

    Critical: the response MUST be wrapped as ``{package_map: PackageMap}``,
    not a bare ``PackageMap``.
    """

    def test_request_schema_is_frozen(self):
        req = SpatialOverlayRequest(
            project_id="p1",
            subsystems=[],
            overlay={"zones": {"downtube": {"x_mm": 400}}},
        )
        assert req.model_dump() == {
            "project_id": "p1",
            "subsystems": [],
            "overlay": {"zones": {"downtube": {"x_mm": 400}}},
        }
        # Defaults: empty list + empty dict when omitted
        minimal = SpatialOverlayRequest(project_id="p1")
        assert minimal.model_dump() == {
            "project_id": "p1",
            "subsystems": [],
            "overlay": {},
        }

    def test_response_schema_is_wrapped(self):
        """The single top-level key MUST be ``package_map`` — locking the
        envelope shape so nobody ever flattens it."""
        resp = SpatialOverlayResponse(package_map=_canned_package_map())
        dumped = resp.model_dump()
        assert set(dumped.keys()) == {"package_map"}
        pm = dumped["package_map"]
        # PackageMap keys
        assert set(pm.keys()) == {
            "nodes",
            "required",
            "overlay_budget",
            "overlay_violations",
            "svg",
            "table_md",
            "notes",
        }

    def test_happy_path_round_trip(self, client):
        canned_pkg = _canned_package_map()
        with patch(
            "app.routers.subsystems.discover_package",
            return_value=canned_pkg,
        ) as discover_stub, patch(
            "app.routers.subsystems.apply_overlay",
            return_value=canned_pkg,
        ) as overlay_stub:
            r = client.post(
                f"{API}/subsystems/spatial-overlay",
                json={
                    "project_id": "p1",
                    "subsystems": [],
                    "overlay": {"zones": {"downtube": {"x_mm": 400}}},
                },
            )
        assert r.status_code == 200, r.text
        discover_stub.assert_called_once()
        overlay_stub.assert_called_once()
        parsed = SpatialOverlayResponse.model_validate(r.json())
        assert parsed.package_map is not None

    def test_regression_guard_wrapped_not_bare(self, client):
        """If someone ever returns the PackageMap unwrapped this blows up."""
        with patch(
            "app.routers.subsystems.discover_package",
            return_value=_canned_package_map(),
        ), patch(
            "app.routers.subsystems.apply_overlay",
            return_value=_canned_package_map(),
        ):
            body = client.post(
                f"{API}/subsystems/spatial-overlay",
                json={"project_id": "p1", "subsystems": [], "overlay": {}},
            ).json()
        # Top-level must have exactly "package_map" — no bare "nodes" leak
        assert "package_map" in body
        assert "nodes" not in body
        assert "overlay_violations" in body["package_map"]


# ---------------------------------------------------------------------------
# TestSpatialComponentOverrideContract  — POST /spatial/component-overrides
# ---------------------------------------------------------------------------


class TestSpatialComponentOverrideContract:
    """Lock the wire contract for POST /spatial/component-overrides."""

    REQUEST = {
        "project_id": "p1",
        "component_key": "main_battery",
        "category": "battery",
        "bbox": {
            "x_mm": 380.0,
            "y_mm": 75.0,
            "z_mm": 65.0,
            "origin_mm": [0.0, 0.0, 0.0],
            "anchor": "downtube",
        },
        "mass_g": 3100.0,
        "note": "custom pack",
    }

    def test_request_schema_is_frozen(self):
        req = ComponentOverrideRequest(**self.REQUEST)
        dumped = req.model_dump()
        # BBox.origin_mm round-trips as a tuple via pydantic
        assert dumped == {
            "project_id": "p1",
            "component_key": "main_battery",
            "category": "battery",
            "bbox": {
                "x_mm": 380.0,
                "y_mm": 75.0,
                "z_mm": 65.0,
                "origin_mm": (0.0, 0.0, 0.0),
                "anchor": "downtube",
            },
            "mass_g": 3100.0,
            "note": "custom pack",
        }

    def test_response_schema_is_frozen(self):
        resp = ComponentOverrideResponse(saved=True, component_key="main_battery")
        assert resp.model_dump() == {
            "saved": True,
            "component_key": "main_battery",
        }

    def test_happy_path_round_trip(self, client):
        sb = _make_supabase_stub()
        with patch("app.routers.spatial.get_supabase", return_value=sb):
            r = client.post(
                f"{API}/spatial/component-overrides",
                json=self.REQUEST,
            )
        assert r.status_code == 200, r.text
        # Supabase table().upsert() called once on the right table
        sb.table.assert_any_call("project_component_overrides")
        parsed = ComponentOverrideResponse.model_validate(r.json())
        assert parsed.saved is True
        assert parsed.component_key == "main_battery"

    def test_regression_guard_required_fields_present(self, client):
        """FE reads {saved, component_key} — both MUST be present and
        correctly typed, even on a 'trivially saved' happy path."""
        sb = _make_supabase_stub()
        with patch("app.routers.spatial.get_supabase", return_value=sb):
            body = client.post(
                f"{API}/spatial/component-overrides",
                json=self.REQUEST,
            ).json()
        assert set(body.keys()) == {"saved", "component_key"}
        assert isinstance(body["saved"], bool)
        assert isinstance(body["component_key"], str)
        assert body["saved"] is True


# ---------------------------------------------------------------------------
# TestSpatialLearnedComponentContract  — POST /spatial/learned-components
# ---------------------------------------------------------------------------


class TestSpatialLearnedComponentContract:
    """Lock the wire contract for POST /spatial/learned-components."""

    REQUEST = {
        "key": "bafang_m600_mid_drive",
        "category": "motor",
        "bbox": {
            "x_mm": 180.0,
            "y_mm": 140.0,
            "z_mm": 120.0,
            "origin_mm": [0.0, 0.0, 0.0],
            "anchor": "BB_center",
        },
        "mass_g": 3900.0,
        "origin": "rd_override",
        "origin_project_id": "p1",
        "source_url": "https://bafang-e.com/m600",
        "source_text": "vendor datasheet",
    }

    def test_request_schema_is_frozen(self):
        req = LearnedComponentPromoteRequest(**self.REQUEST)
        dumped = req.model_dump()
        assert dumped == {
            "key": "bafang_m600_mid_drive",
            "category": "motor",
            "bbox": {
                "x_mm": 180.0,
                "y_mm": 140.0,
                "z_mm": 120.0,
                "origin_mm": (0.0, 0.0, 0.0),
                "anchor": "BB_center",
            },
            "mass_g": 3900.0,
            "origin": "rd_override",
            "origin_project_id": "p1",
            "source_url": "https://bafang-e.com/m600",
            "source_text": "vendor datasheet",
        }

    def test_response_schema_is_frozen(self):
        resp = LearnedComponentPromoteResponse(
            saved=True, key="bafang_m600_mid_drive", confirmed_count=1
        )
        assert resp.model_dump() == {
            "saved": True,
            "key": "bafang_m600_mid_drive",
            "confirmed_count": 1,
        }

    def test_happy_path_insert_new(self, client):
        """Key does not exist → insert path, confirmed_count = 1."""
        sb = _make_supabase_stub(existing_learned_rows=[])
        with patch("app.routers.spatial.get_supabase", return_value=sb):
            r = client.post(
                f"{API}/spatial/learned-components",
                json=self.REQUEST,
            )
        assert r.status_code == 200, r.text
        body = r.json()
        parsed = LearnedComponentPromoteResponse.model_validate(body)
        assert parsed.saved is True
        assert parsed.key == "bafang_m600_mid_drive"
        assert parsed.confirmed_count == 1
        sb.table.assert_any_call("learned_components")

    def test_happy_path_bumps_existing(self, client):
        """Key already exists → bump path, confirmed_count increments."""
        sb = _make_supabase_stub(
            existing_learned_rows=[{"id": "abc", "confirmed_count": 4}]
        )
        with patch("app.routers.spatial.get_supabase", return_value=sb):
            r = client.post(
                f"{API}/spatial/learned-components",
                json=self.REQUEST,
            )
        assert r.status_code == 200, r.text
        parsed = LearnedComponentPromoteResponse.model_validate(r.json())
        assert parsed.confirmed_count == 5

    def test_regression_guard_required_fields_present(self, client):
        sb = _make_supabase_stub(existing_learned_rows=[])
        with patch("app.routers.spatial.get_supabase", return_value=sb):
            body = client.post(
                f"{API}/spatial/learned-components",
                json=self.REQUEST,
            ).json()
        assert set(body.keys()) == {"saved", "key", "confirmed_count"}
        assert isinstance(body["saved"], bool)
        assert isinstance(body["key"], str)
        assert isinstance(body["confirmed_count"], int)
