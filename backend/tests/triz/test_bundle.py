"""Tests for ArtifactBundleTool and BundleManager."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.triz.bundle import BundleError, BundleManager, _sha256
from app.triz.tools import ArtifactBundleTool


@pytest.fixture()
def eng_root(tmp_path: Path) -> Path:
    """Create a temporary engineering root with sample artifacts."""
    root = tmp_path / "docs" / "engineering"
    root.mkdir(parents=True)
    return root


@pytest.fixture()
def state_dir(tmp_path: Path) -> Path:
    """Create a temporary state dir with a .triz-state.json."""
    d = tmp_path / ".claude" / "context" / "triz"
    d.mkdir(parents=True)
    state = {
        "session_id": "test-session-001",
        "current_step": "step5",
    }
    (d / ".triz-state.json").write_text(json.dumps(state), encoding="utf-8")
    return d


@pytest.fixture()
def mgr(eng_root: Path, state_dir: Path) -> BundleManager:
    return BundleManager(eng_root, state_dir=state_dir)


@pytest.fixture()
def tool(mgr: BundleManager) -> ArtifactBundleTool:
    return ArtifactBundleTool(mgr)


def _write_artifact(eng_root: Path, name: str, content: str = "test content") -> Path:
    """Helper: write a file into engineering root."""
    p = eng_root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


# ── BundleManager unit tests ──────────────────────────────────────


class TestBundleManagerRegister:
    def test_register_new_artifact(self, mgr: BundleManager, eng_root: Path) -> None:
        _write_artifact(eng_root, "WI-01_motor.md", "motor work instruction")
        entry = mgr.register(
            relative_path="WI-01_motor.md",
            category="work_instructions",
            produced_by="triz-wi",
        )
        assert entry.path == "WI-01_motor.md"
        assert entry.category == "work_instructions"
        assert entry.version == 1
        assert entry.produced_by == "triz-wi"
        assert len(entry.sha256) == 64  # SHA-256 hex

    def test_register_updates_manifest(self, mgr: BundleManager, eng_root: Path) -> None:
        _write_artifact(eng_root, "README.md", "# System")
        mgr.register(relative_path="README.md", category="framework", produced_by="triz-wi")

        manifest = mgr.load_or_create()
        assert manifest.bundle_version == 1
        assert "framework" in manifest.artifacts
        assert len(manifest.artifacts["framework"]) == 1
        assert manifest.statistics["total"] == 1

    def test_register_same_file_no_change(self, mgr: BundleManager, eng_root: Path) -> None:
        _write_artifact(eng_root, "WI-01.md", "content")
        mgr.register(relative_path="WI-01.md", category="work_instructions", produced_by="triz-wi")
        entry = mgr.register(relative_path="WI-01.md", category="work_instructions", produced_by="triz-wi")
        assert entry.version == 1  # no version bump for unchanged file

    def test_register_file_changed_bumps_version(self, mgr: BundleManager, eng_root: Path) -> None:
        _write_artifact(eng_root, "WI-01.md", "v1 content")
        mgr.register(relative_path="WI-01.md", category="work_instructions", produced_by="triz-wi")

        _write_artifact(eng_root, "WI-01.md", "v2 content updated")
        entry = mgr.register(relative_path="WI-01.md", category="work_instructions", produced_by="triz-wi")
        assert entry.version == 2

    def test_register_invalid_category(self, mgr: BundleManager, eng_root: Path) -> None:
        _write_artifact(eng_root, "foo.md")
        with pytest.raises(BundleError, match="invalid category"):
            mgr.register(relative_path="foo.md", category="invalid_cat", produced_by="x")

    def test_register_missing_file(self, mgr: BundleManager) -> None:
        with pytest.raises(BundleError, match="file not found"):
            mgr.register(relative_path="nonexistent.md", category="framework", produced_by="x")

    def test_register_saves_history(self, mgr: BundleManager, eng_root: Path) -> None:
        _write_artifact(eng_root, "WI-01.md", "content")
        mgr.register(relative_path="WI-01.md", category="work_instructions", produced_by="triz-wi")

        history_dir = eng_root / ".bundle_history"
        assert history_dir.is_dir()
        history_files = list(history_dir.glob("v1_*.json"))
        assert len(history_files) == 1

    def test_register_multiple_categories(self, mgr: BundleManager, eng_root: Path) -> None:
        _write_artifact(eng_root, "WI-01.md", "wi")
        _write_artifact(eng_root, "ICD-01.md", "icd")
        _write_artifact(eng_root, "MC-01.md", "mc")

        mgr.register(relative_path="WI-01.md", category="work_instructions", produced_by="triz-wi")
        mgr.register(relative_path="ICD-01.md", category="interface_control", produced_by="triz-wi")
        mgr.register(relative_path="MC-01.md", category="material_cards", produced_by="triz-wi")

        manifest = mgr.load_or_create()
        assert manifest.statistics["total"] == 3
        assert manifest.statistics["work_instructions"] == 1
        assert manifest.statistics["interface_control"] == 1
        assert manifest.statistics["material_cards"] == 1

    def test_register_provenance_from_state(self, mgr: BundleManager, eng_root: Path) -> None:
        _write_artifact(eng_root, "README.md", "content")
        mgr.register(relative_path="README.md", category="framework", produced_by="triz-wi")

        manifest = mgr.load_or_create()
        assert manifest.source.triz_session == "test-session-001"
        assert manifest.source.triz_state_hash is not None
        assert len(manifest.source.triz_state_hash) == 64

    def test_register_subdirectory_artifact(self, mgr: BundleManager, eng_root: Path) -> None:
        _write_artifact(eng_root, "gate_reviews/TR1_review.md", "gate review content")
        entry = mgr.register(
            relative_path="gate_reviews/TR1_review.md",
            category="gate_reviews",
            produced_by="tr-gate",
        )
        assert entry.path == "gate_reviews/TR1_review.md"


class TestBundleManagerValidate:
    def test_validate_empty_manifest(self, mgr: BundleManager) -> None:
        result = mgr.validate()
        assert result["status"] == "ok"
        assert result["total_registered"] == 0

    def test_validate_all_good(self, mgr: BundleManager, eng_root: Path) -> None:
        _write_artifact(eng_root, "WI-01.md", "content")
        mgr.register(relative_path="WI-01.md", category="work_instructions", produced_by="triz-wi")

        result = mgr.validate()
        assert result["status"] == "ok"
        assert result["valid"] == 1
        assert result["missing"] == []
        assert result["hash_mismatches"] == []

    def test_validate_missing_file(self, mgr: BundleManager, eng_root: Path) -> None:
        _write_artifact(eng_root, "WI-01.md", "content")
        mgr.register(relative_path="WI-01.md", category="work_instructions", produced_by="triz-wi")

        # Delete the file after registration
        (eng_root / "WI-01.md").unlink()

        result = mgr.validate()
        assert result["status"] == "issues_found"
        assert "WI-01.md" in result["missing"]

    def test_validate_hash_mismatch(self, mgr: BundleManager, eng_root: Path) -> None:
        _write_artifact(eng_root, "WI-01.md", "original content")
        mgr.register(relative_path="WI-01.md", category="work_instructions", produced_by="triz-wi")

        # Modify file after registration
        _write_artifact(eng_root, "WI-01.md", "tampered content!")

        result = mgr.validate()
        assert result["status"] == "issues_found"
        assert len(result["hash_mismatches"]) == 1
        assert result["hash_mismatches"][0]["path"] == "WI-01.md"


class TestBundleManagerStatus:
    def test_status_empty(self, mgr: BundleManager) -> None:
        result = mgr.status()
        assert result["bundle_version"] == 0
        assert result["statistics"] == {}

    def test_status_after_register(self, mgr: BundleManager, eng_root: Path) -> None:
        _write_artifact(eng_root, "WI-01.md", "content")
        mgr.register(relative_path="WI-01.md", category="work_instructions", produced_by="triz-wi")

        result = mgr.status()
        assert result["bundle_version"] == 1
        assert result["statistics"]["total"] == 1


class TestBundleManagerExport:
    def test_export_empty_raises(self, mgr: BundleManager) -> None:
        with pytest.raises(BundleError, match="nothing to export"):
            mgr.export_zip()

    def test_export_creates_zip(self, mgr: BundleManager, eng_root: Path) -> None:
        _write_artifact(eng_root, "WI-01.md", "motor wi")
        _write_artifact(eng_root, "MC-01.md", "material card")
        mgr.register(relative_path="WI-01.md", category="work_instructions", produced_by="triz-wi")
        mgr.register(relative_path="MC-01.md", category="material_cards", produced_by="triz-wi")

        zip_path = mgr.export_zip()
        assert zip_path.suffix == ".zip"
        assert zip_path.is_file()

        import zipfile
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            assert "MANIFEST.json" in names
            assert "WI-01.md" in names
            assert "MC-01.md" in names


# ── ArtifactBundleTool tests ──────────────────────────────────────


class TestArtifactBundleTool:
    def test_register_via_tool(self, tool: ArtifactBundleTool, eng_root: Path) -> None:
        _write_artifact(eng_root, "WI-01_motor.md", "motor content")
        result = tool.run(
            action="register",
            path="WI-01_motor.md",
            category="work_instructions",
            produced_by="triz-wi",
        )
        assert not result.is_error
        data = json.loads(result.content)
        assert data["ok"] is True
        assert data["version"] == 1

    def test_register_missing_path(self, tool: ArtifactBundleTool) -> None:
        result = tool.run(action="register", category="framework", produced_by="x")
        assert result.is_error
        assert "path" in result.content

    def test_register_missing_category(self, tool: ArtifactBundleTool) -> None:
        result = tool.run(action="register", path="foo.md", produced_by="x")
        assert result.is_error
        assert "category" in result.content

    def test_register_missing_produced_by(self, tool: ArtifactBundleTool) -> None:
        result = tool.run(action="register", path="foo.md", category="framework")
        assert result.is_error
        assert "produced_by" in result.content

    def test_validate_via_tool(self, tool: ArtifactBundleTool) -> None:
        result = tool.run(action="validate")
        assert not result.is_error
        data = json.loads(result.content)
        assert data["status"] == "ok"

    def test_status_via_tool(self, tool: ArtifactBundleTool) -> None:
        result = tool.run(action="status")
        assert not result.is_error
        data = json.loads(result.content)
        assert "bundle_version" in data

    def test_export_via_tool_empty(self, tool: ArtifactBundleTool) -> None:
        result = tool.run(action="export")
        assert result.is_error
        assert "nothing to export" in result.content

    def test_export_via_tool(self, tool: ArtifactBundleTool, eng_root: Path) -> None:
        _write_artifact(eng_root, "README.md", "system readme")
        tool.run(action="register", path="README.md", category="framework", produced_by="triz-wi")

        result = tool.run(action="export")
        assert not result.is_error
        data = json.loads(result.content)
        assert data["ok"] is True
        assert data["zip_path"].endswith(".zip")

    def test_unknown_action(self, tool: ArtifactBundleTool) -> None:
        result = tool.run(action="unknown")
        assert result.is_error
        assert "unknown action" in result.content

    def test_schema_present(self, tool: ArtifactBundleTool) -> None:
        schema = tool.to_anthropic_schema()
        assert schema["name"] == "ArtifactBundle"
        assert "register" in schema["description"]
        assert "properties" in schema["input_schema"]


class TestTrizRegistryWithBundle:
    def test_registry_includes_artifact_bundle(self, tmp_path: Path) -> None:
        """triz_tools() now returns 8 tools including ArtifactBundle."""
        from app.triz.registry import triz_tools

        # Create minimal KB structure
        kb_root = tmp_path / "kb"
        kb_root.mkdir()
        (kb_root / "01_39_parameters.md").write_text("# Parameters\n| ID | EN | ZH |\n|---|---|---|\n| 1 | Weight | 重量 |")
        (kb_root / "02_contradiction_matrix.md").write_text("# Matrix\n")
        (kb_root / "03_40_principles.md").write_text("# Principles\n")
        (kb_root / "04_separation_principles.md").write_text("# Separation\n")

        state_dir = tmp_path / "state"
        state_dir.mkdir()

        tools = triz_tools(kb_root=kb_root, state_dir=state_dir)
        names = {t.name for t in tools}
        assert "ArtifactBundle" in names
        assert len(tools) == 8
