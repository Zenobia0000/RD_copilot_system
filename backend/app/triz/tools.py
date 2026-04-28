"""TRIZ domain tools — expose deterministic modules as AgentLoop-callable tools.

Each tool wraps an existing module (KB, CCI, SIM, param_mapper, state_manager)
and follows the harness Tool ABC so the LLM can call them via the standard
tool-use loop. Skills (SKILL.md) reference these tools by name.
"""

from __future__ import annotations

import json
from typing import Any, ClassVar

from app.harness.tools.base import Tool, ToolResult
from app.triz.bundle import VALID_CATEGORIES, BundleError, BundleManager
from app.triz.kb.loader import KBLoader
from app.triz.kb.matrix import lookup_principles, validate_parameter_id
from app.triz.solve.param_mapper import (
    ScoredCandidate,
    needs_llm_disambiguation,
    rank_candidates,
)
from app.triz.solve.sim import build_sim_result
from app.triz.state import StepName
from app.triz.state_manager import StateError, TrizStateManager
from app.triz.verify.cci import (
    CCIInput,
    CognitiveChange,
    EnergyChange,
    StructuralChange,
    check_evidence_downgrade,
    classify_verdict,
    compute_cci,
)


# ── MatrixLookup ────────────────────────────────────────────────────


class MatrixLookupTool(Tool):
    """Query the TRIZ contradiction matrix."""

    name: ClassVar[str] = "MatrixLookup"
    description: ClassVar[str] = (
        "Look up inventive principles from the 39-parameter contradiction "
        "matrix. Given an improving parameter ID and a worsening parameter ID "
        "(both 1-39), returns the recommended principle IDs and descriptions."
    )
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "improve_id": {
                "type": "integer",
                "description": "Improving parameter ID (1-39).",
            },
            "worsen_id": {
                "type": "integer",
                "description": "Worsening parameter ID (1-39).",
            },
        },
        "required": ["improve_id", "worsen_id"],
    }

    def __init__(self, kb: KBLoader) -> None:
        self._kb = kb

    def run(self, *, improve_id: int, worsen_id: int) -> ToolResult:
        if not validate_parameter_id(self._kb, improve_id):
            return ToolResult(
                content=f"Error: Invalid improving parameter ID: {improve_id}. Must be 1-39.",
                is_error=True,
            )
        if not validate_parameter_id(self._kb, worsen_id):
            return ToolResult(
                content=f"Error: Invalid worsening parameter ID: {worsen_id}. Must be 1-39.",
                is_error=True,
            )
        if improve_id == worsen_id:
            return ToolResult(
                content=json.dumps({
                    "improve_id": improve_id,
                    "worsen_id": worsen_id,
                    "principles": [],
                    "note": "Same parameter — no self-contradiction.",
                }, ensure_ascii=False),
            )

        principle_ids = lookup_principles(self._kb, improve_id, worsen_id)
        descriptions = self._kb.inject_principles_for_prompt(principle_ids)

        improve_param = self._kb.get_parameter(improve_id)
        worsen_param = self._kb.get_parameter(worsen_id)

        result = {
            "improve": {
                "id": improve_id,
                "name_en": improve_param.name_en if improve_param else "",
                "name_zh": improve_param.name_zh if improve_param else "",
            },
            "worsen": {
                "id": worsen_id,
                "name_en": worsen_param.name_en if worsen_param else "",
                "name_zh": worsen_param.name_zh if worsen_param else "",
            },
            "principles": principle_ids,
            "principle_descriptions": descriptions,
        }
        return ToolResult(content=json.dumps(result, ensure_ascii=False))


# ── ParamMap ────────────────────────────────────────────────────────


class ParamMapTool(Tool):
    """Map natural language to TRIZ 39 parameters."""

    name: ClassVar[str] = "ParamMap"
    description: ClassVar[str] = (
        "Given a natural-language description of an engineering attribute "
        "(e.g. '馬達扭力密度', 'gear noise'), rank the 39 TRIZ parameters by "
        "relevance. Returns top-N candidates with scores and whether LLM "
        "disambiguation is needed."
    )
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "description": {
                "type": "string",
                "description": "Natural language description of the attribute.",
            },
            "top_n": {
                "type": "integer",
                "description": "Number of top candidates to return. Default 5.",
            },
        },
        "required": ["description"],
    }

    def __init__(self, kb: KBLoader) -> None:
        self._kb = kb

    def run(self, *, description: str, top_n: int = 5) -> ToolResult:
        if not description.strip():
            return ToolResult(
                content="Error: description must be non-empty.",
                is_error=True,
            )

        candidates = rank_candidates(description, self._kb, top_n=top_n)
        needs_disambiguation = needs_llm_disambiguation(candidates)

        result = {
            "query": description,
            "needs_llm_disambiguation": needs_disambiguation,
            "candidates": [
                {
                    "rank": i + 1,
                    "id": c.param.id,
                    "name_en": c.param.name_en,
                    "name_zh": c.param.name_zh,
                    "score": c.score,
                    "breakdown": c.breakdown,
                }
                for i, c in enumerate(candidates)
            ],
        }
        return ToolResult(content=json.dumps(result, ensure_ascii=False))


# ── CCICalculate ────────────────────────────────────────────────────


_STRUCTURAL_VALUES = {e.value for e in StructuralChange}
_ENERGY_VALUES = {e.value for e in EnergyChange}
_COGNITIVE_VALUES = {e.value for e in CognitiveChange}


class CCICalculateTool(Tool):
    """Compute CCI score and verdict."""

    name: ClassVar[str] = "CCICalculate"
    description: ClassVar[str] = (
        "Calculate the Composite Complexity Index (CCI) from Q1-Q4 inputs. "
        "Returns weighted score (0-1), verdict tier, and component scores.\n"
        "Q1 structural: reduced|unchanged|added_no_interface|added_with_interface|new_subsystem\n"
        "Q2 energy: reduced|unchanged|slight_increase|moderate_increase|new_source\n"
        "Q3 cognitive: simplified|unchanged|one_branch|specialist|new_model\n"
        "Q4: trends_satisfied (integer, how many evolution trends met, default total=3)"
    )
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "structural": {
                "type": "string",
                "enum": sorted(_STRUCTURAL_VALUES),
                "description": "Q1: Net structural change.",
            },
            "energy": {
                "type": "string",
                "enum": sorted(_ENERGY_VALUES),
                "description": "Q2: Energy consumption change.",
            },
            "cognitive": {
                "type": "string",
                "enum": sorted(_COGNITIVE_VALUES),
                "description": "Q3: Cognitive complexity change.",
            },
            "trends_satisfied": {
                "type": "integer",
                "description": "Q4: Number of evolution trends satisfied (0-3).",
            },
            "total_trends": {
                "type": "integer",
                "description": "Total evolution trends to check against. Default 3.",
            },
        },
        "required": ["structural", "energy", "cognitive", "trends_satisfied"],
    }

    def run(
        self,
        *,
        structural: str,
        energy: str,
        cognitive: str,
        trends_satisfied: int,
        total_trends: int = 3,
    ) -> ToolResult:
        # Validate enum values
        if structural not in _STRUCTURAL_VALUES:
            return ToolResult(
                content=f"Error: invalid structural value '{structural}'. Must be one of: {sorted(_STRUCTURAL_VALUES)}",
                is_error=True,
            )
        if energy not in _ENERGY_VALUES:
            return ToolResult(
                content=f"Error: invalid energy value '{energy}'. Must be one of: {sorted(_ENERGY_VALUES)}",
                is_error=True,
            )
        if cognitive not in _COGNITIVE_VALUES:
            return ToolResult(
                content=f"Error: invalid cognitive value '{cognitive}'. Must be one of: {sorted(_COGNITIVE_VALUES)}",
                is_error=True,
            )

        inp = CCIInput(
            q1=StructuralChange(structural),
            q2=EnergyChange(energy),
            q3=CognitiveChange(cognitive),
            trends_satisfied=trends_satisfied,
            total_trends=total_trends,
        )
        scores = compute_cci(inp)
        verdict = classify_verdict(scores.cci)

        result = {
            "cci": scores.cci,
            "verdict": verdict.value,
            "scores": {
                "structural": scores.structural,
                "energy": scores.energy,
                "cognitive": scores.cognitive,
                "evolution_aligned": scores.evolution_aligned,
            },
            "weights": "0.30*Q1 + 0.25*Q2 + 0.20*Q3 + 0.25*Q4",
        }
        return ToolResult(content=json.dumps(result, ensure_ascii=False))


# ── SIMCompute ──────────────────────────────────────────────────────


class SIMComputeTool(Tool):
    """Compute SIM statistics and convergence verdict."""

    name: ClassVar[str] = "SIMCompute"
    description: ClassVar[str] = (
        "Compute Solution Interaction Matrix (SIM) summary and convergence "
        "verdict. Input is a dict of pairwise scores: "
        '{"SOL-TC1 × SOL-TC3": 0, "SOL-TC1 × SOL-TC4": 1, ...} '
        "where +1=synergy, 0=neutral, -1=conflict. "
        "Returns summary counts, verdict (converged/iterate/stop), and "
        "synergy/conflict details."
    )
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "matrix": {
                "type": "object",
                "description": (
                    "Pairwise solution interaction scores. "
                    "Keys: 'SOL-TCx × SOL-TCy', values: -1, 0, or +1."
                ),
                "additionalProperties": {"type": "integer"},
            },
            "iteration": {
                "type": "integer",
                "description": "Current SIM iteration number. Default 1.",
            },
            "synergy_reasons": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Reasons for +1 pairs.",
            },
            "conflict_reasons": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Reasons for -1 pairs.",
            },
        },
        "required": ["matrix"],
    }

    def run(
        self,
        *,
        matrix: dict[str, int],
        iteration: int = 1,
        synergy_reasons: list[str] | None = None,
        conflict_reasons: list[str] | None = None,
    ) -> ToolResult:
        # Validate scores are -1, 0, or +1
        for key, score in matrix.items():
            if score not in (-1, 0, 1):
                return ToolResult(
                    content=f"Error: invalid score {score} for '{key}'. Must be -1, 0, or +1.",
                    is_error=True,
                )

        sim_result = build_sim_result(
            matrix,
            synergy_reasons=synergy_reasons,
            conflict_reasons=conflict_reasons,
            iteration=iteration,
        )

        result = {
            "iteration": sim_result.iteration,
            "summary": sim_result.summary,
            "verdict": sim_result.verdict,
            "synergies": sim_result.synergies,
            "conflicts": sim_result.conflicts,
            "total_pairs": len(matrix),
        }
        return ToolResult(content=json.dumps(result, ensure_ascii=False))


# ── TrizStateRead ───────────────────────────────────────────────────


class TrizStateReadTool(Tool):
    """Read TRIZ session state with schema validation."""

    name: ClassVar[str] = "TrizStateRead"
    description: ClassVar[str] = (
        "Read the current TRIZ session state (.triz-state.json). "
        "Returns the full session state or a specific step's data. "
        "All data is Pydantic-validated on read."
    )
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "step": {
                "type": "string",
                "enum": ["step0", "step1", "step2", "step3", "step4", "step5"],
                "description": (
                    "If specified, return only this step's data. "
                    "Omit to get the full session state."
                ),
            },
            "field": {
                "type": "string",
                "description": (
                    "Top-level field to read (e.g. 'session_id', 'current_step', "
                    "'specs'). Omit to get all fields."
                ),
            },
        },
        "required": [],
    }

    def __init__(self, mgr: TrizStateManager) -> None:
        self._mgr = mgr

    def run(
        self,
        *,
        step: str | None = None,
        field: str | None = None,
    ) -> ToolResult:
        if not self._mgr.exists():
            return ToolResult(
                content="Error: No active TRIZ session. State file not found.",
                is_error=True,
            )

        try:
            session = self._mgr.load()
        except StateError as exc:
            return ToolResult(content=f"Error: {exc}", is_error=True)

        data = session.model_dump(mode="json")

        if step:
            if step not in data:
                return ToolResult(
                    content=f"Error: unknown step '{step}'.",
                    is_error=True,
                )
            return ToolResult(
                content=json.dumps(
                    {"step": step, "data": data[step]},
                    ensure_ascii=False,
                )
            )

        if field:
            if field not in data:
                return ToolResult(
                    content=f"Error: unknown field '{field}'. Available: {sorted(data.keys())}",
                    is_error=True,
                )
            return ToolResult(
                content=json.dumps(
                    {"field": field, "value": data[field]},
                    ensure_ascii=False,
                )
            )

        return ToolResult(content=json.dumps(data, ensure_ascii=False))


# ── TrizStateWrite ──────────────────────────────────────────────────


class TrizStateWriteTool(Tool):
    """Write to TRIZ session state with schema validation."""

    name: ClassVar[str] = "TrizStateWrite"
    description: ClassVar[str] = (
        "Update a specific step's data in the TRIZ session state. "
        "The data is Pydantic-validated before writing. Uses atomic "
        "write (temp file + rename) to prevent corruption.\n"
        "To mark a step as completed, include '\"completed\": true' in data."
    )
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "step": {
                "type": "string",
                "enum": ["step0", "step1", "step2", "step3", "step4", "step5"],
                "description": "Which step to update.",
            },
            "data": {
                "type": "object",
                "description": "Step data fields to merge-update.",
            },
        },
        "required": ["step", "data"],
    }

    def __init__(self, mgr: TrizStateManager) -> None:
        self._mgr = mgr

    def run(self, *, step: str, data: dict[str, Any]) -> ToolResult:
        if not self._mgr.exists():
            return ToolResult(
                content="Error: No active TRIZ session. State file not found.",
                is_error=True,
            )

        try:
            session = self._mgr.load()
        except StateError as exc:
            return ToolResult(content=f"Error loading state: {exc}", is_error=True)

        # Get the step object and merge-update fields
        step_obj = getattr(session, step, None)
        if step_obj is None:
            return ToolResult(
                content=f"Error: unknown step '{step}'.",
                is_error=True,
            )

        # Merge data into the step object via model_validate for proper
        # Pydantic coercion (enum strings → Enum, dicts → sub-models).
        for key in data:
            if not hasattr(step_obj, key):
                return ToolResult(
                    content=f"Error: unknown field '{key}' for {step}.",
                    is_error=True,
                )
        merged = {**step_obj.model_dump(), **data}
        try:
            new_step_obj = type(step_obj).model_validate(merged)
        except Exception as exc:
            return ToolResult(
                content=f"Error validating {step} data: {exc}",
                is_error=True,
            )
        setattr(session, step, new_step_obj)

        # Re-validate and save
        try:
            self._mgr.save(session)
        except Exception as exc:
            return ToolResult(
                content=f"Error saving state: {exc}",
                is_error=True,
            )

        state_hash = self._mgr.compute_triz_state_hash()
        return ToolResult(
            content=json.dumps(
                {"ok": True, "step": step, "hash": state_hash},
                ensure_ascii=False,
            )
        )


# ── TrizStateAdvance ────────────────────────────────────────────────


class TrizStateAdvanceTool(Tool):
    """Advance to the next TRIZ step with guard rails."""

    name: ClassVar[str] = "TrizStateAdvance"
    description: ClassVar[str] = (
        "Advance the TRIZ session to the next step. Guard rails: "
        "current step must be completed, cannot skip steps. "
        "Returns the new current_step on success."
    )
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "to_step": {
                "type": "string",
                "enum": ["step1", "step2", "step3", "step4", "step5"],
                "description": "The step to advance to.",
            },
        },
        "required": ["to_step"],
    }

    def __init__(self, mgr: TrizStateManager) -> None:
        self._mgr = mgr

    def run(self, *, to_step: str) -> ToolResult:
        if not self._mgr.exists():
            return ToolResult(
                content="Error: No active TRIZ session. State file not found.",
                is_error=True,
            )

        try:
            session = self._mgr.load()
        except StateError as exc:
            return ToolResult(content=f"Error loading state: {exc}", is_error=True)

        try:
            target = StepName(to_step)
        except ValueError:
            return ToolResult(
                content=f"Error: invalid step '{to_step}'.",
                is_error=True,
            )

        try:
            session = self._mgr.advance_step(session, target)
        except StateError as exc:
            return ToolResult(content=f"Error: {exc}", is_error=True)

        return ToolResult(
            content=json.dumps(
                {
                    "ok": True,
                    "current_step": session.current_step,
                    "session_id": session.session_id,
                },
                ensure_ascii=False,
            )
        )


# ── ArtifactBundle ─────────────────────────────────────────────────


class ArtifactBundleTool(Tool):
    """Manage the engineering artifact bundle (MANIFEST.json)."""

    name: ClassVar[str] = "ArtifactBundle"
    description: ClassVar[str] = (
        "Manage docs/engineering/MANIFEST.json — the SSOT for all engineering "
        "artifacts produced by the TRIZ→TR pipeline.\n\n"
        "Actions:\n"
        "  register — Register an artifact after writing it. Computes SHA-256, "
        "adds to manifest, increments version.\n"
        "  validate — Check all registered files exist and hashes match.\n"
        "  status — Return manifest summary (statistics, provenance).\n"
        "  export — Create a ZIP archive of all registered artifacts.\n\n"
        "Categories: framework, work_instructions, interface_control, "
        "material_cards, key_characteristics, gate_reviews, test_reports, "
        "dfm_reviews, fmea, control_plan, sop, spc, ppap."
    )
    input_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["register", "validate", "status", "export"],
                "description": "Operation to perform.",
            },
            "path": {
                "type": "string",
                "description": (
                    "File path relative to docs/engineering/ "
                    "(e.g. 'WI-01_motor.md'). Required for register."
                ),
            },
            "category": {
                "type": "string",
                "enum": sorted(VALID_CATEGORIES),
                "description": "Artifact category. Required for register.",
            },
            "produced_by": {
                "type": "string",
                "description": (
                    "Skill name that produced this artifact "
                    "(e.g. 'triz-wi', 'tr-gate'). Required for register."
                ),
            },
        },
        "required": ["action"],
    }

    def __init__(self, mgr: BundleManager) -> None:
        self._mgr = mgr

    def to_anthropic_schema(self) -> dict[str, Any]:
        """Override to inject valid categories from the BundleManager instance."""
        schema = super().to_anthropic_schema()
        props = schema["input_schema"]["properties"]
        if "category" in props:
            props["category"] = {
                **props["category"],
                "enum": sorted(self._mgr.valid_categories),
            }
        return schema

    def run(
        self,
        *,
        action: str,
        path: str | None = None,
        category: str | None = None,
        produced_by: str | None = None,
    ) -> ToolResult:
        if action == "register":
            return self._register(path=path, category=category, produced_by=produced_by)
        if action == "validate":
            return self._validate()
        if action == "status":
            return self._status()
        if action == "export":
            return self._export()
        return ToolResult(
            content=f"Error: unknown action '{action}'.",
            is_error=True,
        )

    def _register(
        self,
        *,
        path: str | None,
        category: str | None,
        produced_by: str | None,
    ) -> ToolResult:
        if not path:
            return ToolResult(content="Error: 'path' is required for register.", is_error=True)
        if not category:
            return ToolResult(content="Error: 'category' is required for register.", is_error=True)
        if not produced_by:
            return ToolResult(content="Error: 'produced_by' is required for register.", is_error=True)

        try:
            entry = self._mgr.register(
                relative_path=path,
                category=category,
                produced_by=produced_by,
            )
        except BundleError as exc:
            return ToolResult(content=f"Error: {exc}", is_error=True)

        return ToolResult(
            content=json.dumps(
                {
                    "ok": True,
                    "action": "register",
                    "path": entry.path,
                    "category": entry.category,
                    "sha256": entry.sha256[:16] + "...",
                    "version": entry.version,
                },
                ensure_ascii=False,
            )
        )

    def _validate(self) -> ToolResult:
        try:
            result = self._mgr.validate()
        except BundleError as exc:
            return ToolResult(content=f"Error: {exc}", is_error=True)
        return ToolResult(content=json.dumps(result, ensure_ascii=False))

    def _status(self) -> ToolResult:
        try:
            result = self._mgr.status()
        except BundleError as exc:
            return ToolResult(content=f"Error: {exc}", is_error=True)
        return ToolResult(content=json.dumps(result, ensure_ascii=False))

    def _export(self) -> ToolResult:
        try:
            zip_path = self._mgr.export_zip()
        except BundleError as exc:
            return ToolResult(content=f"Error: {exc}", is_error=True)
        return ToolResult(
            content=json.dumps(
                {"ok": True, "action": "export", "zip_path": str(zip_path)},
                ensure_ascii=False,
            )
        )
