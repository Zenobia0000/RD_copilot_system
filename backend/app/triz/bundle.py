"""Artifact bundle manager — MANIFEST.json SSOT for engineering deliverables.

Tracks all artifacts produced by the TRIZ→TR pipeline (WI, ICD, MC, Gate
Reviews, Test Reports, DFM, SOP, PPAP, etc.) in a single manifest file.
Provides registration (with SHA-256 hashing), validation (file existence +
hash integrity), and status summary.

The manifest lives at ``docs/engineering/MANIFEST.json`` — next to the
artifacts it indexes — because it's a human-readable deliverable, not
internal Skill state.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


# ── Pydantic models ──────────────────────────────────────────────────

VALID_CATEGORIES = frozenset({
    "framework",
    "work_instructions",
    "interface_control",
    "material_cards",
    "key_characteristics",
    "gate_reviews",
    "test_reports",
    "dfm_reviews",
    "fmea",
    "control_plan",
    "sop",
    "spc",
    "ppap",
})


class ArtifactEntry(BaseModel):
    """One registered artifact file."""

    path: str = Field(description="Path relative to engineering root.")
    category: str
    sha256: str
    produced_by: str = Field(description="Skill name that produced this artifact.")
    registered_at: str
    version: int = 1


class BundleSource(BaseModel):
    """Provenance: links bundle back to TRIZ/TR session."""

    triz_session: str | None = None
    triz_state_hash: str | None = None
    tr_state_hash: str | None = None


class BundleManifest(BaseModel):
    """Root model for MANIFEST.json."""

    bundle_id: str = ""
    bundle_version: int = 0
    created_at: str = ""
    updated_at: str = ""
    source: BundleSource = Field(default_factory=BundleSource)
    artifacts: dict[str, list[ArtifactEntry]] = Field(default_factory=dict)
    statistics: dict[str, int] = Field(default_factory=dict)


# ── Manager ──────────────────────────────────────────────────────────


class BundleError(Exception):
    """Non-recoverable bundle operation error."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


class BundleManager:
    """Manages MANIFEST.json and artifact registration.

    Args:
        engineering_root: Path to ``docs/engineering/`` directory.
        state_dir: Optional path to ``.claude/context/triz/`` for provenance.
    """

    def __init__(
        self,
        engineering_root: Path,
        state_dir: Path | None = None,
        valid_categories: frozenset[str] | None = None,
    ) -> None:
        self._root = engineering_root
        self._state_dir = state_dir
        self._manifest_path = engineering_root / "MANIFEST.json"
        self._history_dir = engineering_root / ".bundle_history"
        self.valid_categories = valid_categories or VALID_CATEGORIES

    @property
    def manifest_path(self) -> Path:
        return self._manifest_path

    # ── Load / save ──────────────────────────────────────────────

    def load_or_create(self) -> BundleManifest:
        """Load existing manifest or create a new empty one."""
        if self._manifest_path.is_file():
            try:
                raw = json.loads(self._manifest_path.read_text(encoding="utf-8"))
                return BundleManifest.model_validate(raw)
            except (json.JSONDecodeError, Exception) as exc:
                raise BundleError(f"corrupt MANIFEST.json: {exc}") from exc
        return BundleManifest(created_at=_now_iso(), updated_at=_now_iso())

    def save(self, manifest: BundleManifest) -> None:
        """Atomic save: write to temp, then rename."""
        self._root.mkdir(parents=True, exist_ok=True)
        manifest.updated_at = _now_iso()
        manifest.statistics = self._compute_statistics(manifest)

        tmp = self._manifest_path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(
                manifest.model_dump(mode="json"),
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        tmp.rename(self._manifest_path)

    def _save_history(self, manifest: BundleManifest) -> None:
        """Snapshot current manifest version to .bundle_history/."""
        self._history_dir.mkdir(parents=True, exist_ok=True)
        filename = f"v{manifest.bundle_version}_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"
        dest = self._history_dir / filename
        dest.write_text(
            json.dumps(manifest.model_dump(mode="json"), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # ── Register ─────────────────────────────────────────────────

    def register(
        self,
        *,
        relative_path: str,
        category: str,
        produced_by: str,
    ) -> ArtifactEntry:
        """Register (or update) an artifact in the manifest.

        Args:
            relative_path: Path relative to engineering_root (e.g. "WI-01_motor.md").
            category: One of VALID_CATEGORIES.
            produced_by: Skill name that produced this artifact.

        Returns:
            The created/updated ArtifactEntry.

        Raises:
            BundleError: If the file doesn't exist or category is invalid.
        """
        if category not in self.valid_categories:
            raise BundleError(
                f"invalid category '{category}'. Must be one of: {sorted(self.valid_categories)}"
            )

        abs_path = self._root / relative_path
        if not abs_path.is_file():
            raise BundleError(f"file not found: {abs_path}")

        file_hash = _sha256(abs_path)
        manifest = self.load_or_create()

        # Check if already registered — update if hash changed
        entries = manifest.artifacts.setdefault(category, [])
        existing = next((e for e in entries if e.path == relative_path), None)

        if existing:
            if existing.sha256 == file_hash:
                return existing  # no change
            existing.sha256 = file_hash
            existing.version += 1
            existing.registered_at = _now_iso()
            entry = existing
        else:
            entry = ArtifactEntry(
                path=relative_path,
                category=category,
                sha256=file_hash,
                produced_by=produced_by,
                registered_at=_now_iso(),
            )
            entries.append(entry)

        # Update provenance from state files
        self._update_source(manifest)

        manifest.bundle_version += 1
        self.save(manifest)
        self._save_history(manifest)

        return entry

    def _update_source(self, manifest: BundleManifest) -> None:
        """Pull provenance from state files if available."""
        if self._state_dir is None:
            return

        triz_path = self._state_dir / ".triz-state.json"
        if triz_path.is_file():
            try:
                raw = json.loads(triz_path.read_text(encoding="utf-8"))
                manifest.source.triz_session = raw.get("session_id", "")
                manifest.source.triz_state_hash = _sha256(triz_path)
            except (json.JSONDecodeError, OSError):
                pass

        tr_path = self._state_dir / ".tr-state.json"
        if tr_path.is_file():
            try:
                manifest.source.tr_state_hash = _sha256(tr_path)
            except OSError:
                pass

    # ── Validate ─────────────────────────────────────────────────

    def validate(self) -> dict[str, Any]:
        """Validate all registered artifacts: existence + hash integrity.

        Returns:
            Dict with missing files, hash mismatches, and overall status.
        """
        manifest = self.load_or_create()
        missing: list[str] = []
        mismatched: list[dict[str, str]] = []
        valid_count = 0

        for _category, entries in manifest.artifacts.items():
            for entry in entries:
                abs_path = self._root / entry.path
                if not abs_path.is_file():
                    missing.append(entry.path)
                    continue
                current_hash = _sha256(abs_path)
                if current_hash != entry.sha256:
                    mismatched.append({
                        "path": entry.path,
                        "expected": entry.sha256[:12] + "...",
                        "actual": current_hash[:12] + "...",
                    })
                else:
                    valid_count += 1

        total = sum(len(entries) for entries in manifest.artifacts.values())
        return {
            "total_registered": total,
            "valid": valid_count,
            "missing": missing,
            "hash_mismatches": mismatched,
            "status": "ok" if not missing and not mismatched else "issues_found",
            "validated_at": _now_iso(),
        }

    # ── Status ───────────────────────────────────────────────────

    def status(self) -> dict[str, Any]:
        """Return manifest summary without running validation."""
        manifest = self.load_or_create()
        return {
            "bundle_id": manifest.bundle_id,
            "bundle_version": manifest.bundle_version,
            "created_at": manifest.created_at,
            "updated_at": manifest.updated_at,
            "source": manifest.source.model_dump(mode="json"),
            "statistics": manifest.statistics,
        }

    # ── Export ────────────────────────────────────────────────────

    def export_zip(self) -> Path:
        """Create a ZIP archive of all registered artifacts + MANIFEST.json.

        Returns:
            Path to the created ZIP file.

        Raises:
            BundleError: If manifest is empty or engineering_root missing.
        """
        manifest = self.load_or_create()
        if not manifest.artifacts:
            raise BundleError("nothing to export: manifest has no artifacts")

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        zip_stem = f"bundle_{manifest.bundle_id or 'unnamed'}_{timestamp}"
        zip_path = self._root / zip_stem

        # Collect files to include
        files_to_include: list[Path] = [self._manifest_path]
        for entries in manifest.artifacts.values():
            for entry in entries:
                abs_path = self._root / entry.path
                if abs_path.is_file():
                    files_to_include.append(abs_path)

        # Create ZIP (shutil makes a .zip from directory, but we want selective)
        import zipfile

        final_zip = zip_path.with_suffix(".zip")
        with zipfile.ZipFile(final_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for fp in files_to_include:
                arcname = fp.relative_to(self._root)
                zf.write(fp, arcname)

        return final_zip

    # ── Helpers ───────────────────────────────────────────────────

    @staticmethod
    def _compute_statistics(manifest: BundleManifest) -> dict[str, int]:
        stats: dict[str, int] = {}
        total = 0
        for category, entries in manifest.artifacts.items():
            count = len(entries)
            stats[category] = count
            total += count
        stats["total"] = total
        return stats
