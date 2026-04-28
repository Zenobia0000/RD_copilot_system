"""Pydantic v2 models for TRIZ session state (.triz-state.json).

These models are the single source of truth for state structure.
All step orchestrators and the state manager import from here.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


# ── Enums ────────────────────────────────────────────────────────────

class StepName(str, Enum):
    step0 = "step0"
    step1 = "step1"
    step2 = "step2"
    step3 = "step3"
    step4 = "step4"
    step5 = "step5"


class PathType(str, Enum):
    tc_main = "tc-main"
    sf_only = "sf-only"
    multi_tc = "multi-tc"
    multi_tc_bottleneck = "multi-tc-bottleneck"
    multi_tc_sim = "multi-tc-sim"


class Step0Routing(str, Enum):
    step1 = "step1"
    step2 = "step2"
    sf_only = "sf-only"
    ceca = "ceca"


class Step1Routing(str, Enum):
    tc_main = "tc-main"
    tc_main_multi = "tc-main-multi"
    sf_only = "sf-only"


class FAType(str, Enum):
    useful = "useful"
    harmful = "harmful"
    insufficient = "insufficient"
    excessive = "excessive"
    missing = "missing"


class SFStatus(str, Enum):
    harmful = "harmful"
    insufficient = "insufficient"
    missing = "missing"
    excessive = "excessive"
    ineffective = "ineffective"


class CCIVerdict(str, Enum):
    strong_evolution = "Strong Evolution"
    weak_evolution = "Weak Evolution"
    conscious_patch = "Conscious Patch"
    hard_patch = "Hard Patch"


class Step4Verdict(str, Enum):
    evolution = "evolution"
    weak_evolution = "weak-evolution"
    patch = "patch"
    strong_patch = "strong-patch"


class SeparationType(str, Enum):
    time = "time"
    space = "space"
    condition = "condition"
    whole_part = "whole-part"


# ── Sub-models ───────────────────────────────────────────────────────

class TCBrief(BaseModel):
    id: str
    improve: str
    worsen: str


class FAEntry(BaseModel):
    source: str
    function: str
    target: str
    type: FAType
    id: str = ""
    name: str = ""
    role: str = ""
    note: str = ""


class SFEntry(BaseModel):
    id: str
    s1: str
    f: str
    s2: str
    status: SFStatus
    tc: str = ""
    routing: str = ""


class ImproveWorsen(BaseModel):
    improve: str
    worsen: str


class ParameterRef(BaseModel):
    id: int
    name: str
    mapping: str = ""


class TCDefinition(BaseModel):
    """Full TC definition with parameter mapping and matrix results."""
    id: str
    improve_param: ParameterRef
    worsen_param: ParameterRef
    matrix_principles: list[int] = Field(default_factory=list)
    selected_principle: int | None = None
    principle_name: str = ""
    concretization: str = ""
    control_equation: str = ""
    claim_id: str = ""
    secondary_principle: dict[str, Any] | None = None
    note: str = ""


class EvidenceClaim(BaseModel):
    id: str
    claim: str
    has_equation: bool = False
    value: str = ""
    source_type: str = ""
    source: str = ""
    confidence: str = "LOW"  # HIGH / MEDIUM / LOW
    accessed: str = ""


class EvidenceGate(BaseModel):
    status: str  # PASS / FAIL
    claims: list[EvidenceClaim] = Field(default_factory=list)


class PCDefinition(BaseModel):
    parameter: str
    required_A: str
    required_notA: str
    separation: SeparationType
    separation_detail: str = ""


class SolutionEntry(BaseModel):
    id: str
    tc_id: str
    pc: PCDefinition | None = None
    description: str = ""
    sf_standard: str | None = None
    claim_ids: list[str] = Field(default_factory=list)


class SIMResult(BaseModel):
    iteration: int = 1
    matrix: dict[str, int] = Field(default_factory=dict)
    summary: dict[str, int] = Field(default_factory=dict)
    verdict: str = ""
    synergies: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)


class CCIScores(BaseModel):
    structural: float = Field(ge=0.0, le=1.0)
    energy: float = Field(ge=0.0, le=1.0)
    cognitive: float = Field(ge=0.0, le=1.0)
    evolution_aligned: float = Field(ge=0.0, le=1.0)
    cci: float = Field(ge=0.0, le=1.0)


class EvidenceRegistry(BaseModel):
    total_claims: int = 0
    high_confidence: int = 0
    medium_confidence: int = 0
    low_confidence: int = 0
    coverage_pct: float = 0.0
    evolution_sustained: bool = True
    corrections: list[str] = Field(default_factory=list)


# ── Step States ──────────────────────────────────────────────────────

class Step0State(BaseModel):
    completed: bool = False
    routing: Step0Routing | None = None
    root_causes: list[str] = Field(default_factory=list)
    tc_hypothesis: list[str] = Field(default_factory=list)
    ceca_nodes: list[dict[str, Any]] = Field(default_factory=list)
    ceca_key_nodes: list[str] = Field(default_factory=list)
    note: str = ""


class Step1State(BaseModel):
    completed: bool = False
    fa_components: list[FAEntry] = Field(default_factory=list)
    sf_diagnosis: list[SFEntry] = Field(default_factory=list)
    improve_worsen_nl: dict[str, ImproveWorsen] = Field(default_factory=dict)
    routing: Step1Routing | None = None


class Step2State(BaseModel):
    completed: bool = False
    tc_definitions: list[TCDefinition] = Field(default_factory=list)
    bottleneck_tc: str = ""
    dependent_tcs: list[str] = Field(default_factory=list)
    evidence_gate: EvidenceGate | None = None


class Step3State(BaseModel):
    completed: bool = False
    refinement_round: int = 0
    solutions: list[SolutionEntry] = Field(default_factory=list)
    sim: SIMResult | None = None
    sim_iteration_count: int = 0
    sim_minus1_history: list[int] = Field(default_factory=list)


class Step4State(BaseModel):
    completed: bool = False
    px_separation_verified: bool = False
    px_results: dict[str, str] = Field(default_factory=dict)
    verdict: Step4Verdict | None = None
    complexity_scores: dict[str, CCIScores] | CCIScores | None = None
    cci_verdict: str = ""
    evidence_registry: EvidenceRegistry | None = None
    new_tc_detected: bool = False
    new_tc_description: str = ""
    observation_items: list[str] = Field(default_factory=list)
    deliverables: list[str] = Field(default_factory=list)


class Step5State(BaseModel):
    completed: bool = False
    subsystems_identified: list[str] = Field(default_factory=list)
    wi_files: list[str] = Field(default_factory=list)
    icd_files: list[str] = Field(default_factory=list)
    mc_files: list[str] = Field(default_factory=list)
    framework_files: list[str] = Field(default_factory=list)
    total_files: int = 0
    output_dir: str = "docs/engineering/"


# ── Root Model ───────────────────────────────────────────────────────

class TrizSession(BaseModel):
    """Root model for .triz-state.json."""

    session_id: str
    created_at: datetime
    current_step: StepName
    path: PathType
    problem_description: str
    report_file: str
    specs: dict[str, Any] = Field(default_factory=dict)
    preliminary_tcs: list[TCBrief] = Field(default_factory=list)
    spiral_iteration: int = 0

    step0: Step0State = Field(default_factory=Step0State)
    step1: Step1State = Field(default_factory=Step1State)
    step2: Step2State = Field(default_factory=Step2State)
    step3: Step3State = Field(default_factory=Step3State)
    step4: Step4State = Field(default_factory=Step4State)
    step5: Step5State = Field(default_factory=Step5State)

    model_config = {"use_enum_values": True}


# ── Step transition order ────────────────────────────────────────────

STEP_ORDER: list[StepName] = [
    StepName.step0,
    StepName.step1,
    StepName.step2,
    StepName.step3,
    StepName.step4,
    StepName.step5,
]


def next_step(current: StepName) -> StepName | None:
    """Return the next step, or None if at final step."""
    idx = STEP_ORDER.index(current)
    if idx + 1 < len(STEP_ORDER):
        return STEP_ORDER[idx + 1]
    return None


def step_completed(session: TrizSession, step: StepName) -> bool:
    """Check if a given step is marked completed."""
    state = getattr(session, step.value, None)
    return state is not None and getattr(state, "completed", False)


# ── TR State Models ──────────────────────────────────────────────────

class SubsystemTR(BaseModel):
    current: str = "TR0"
    target: str = "TR1"
    blockers: list[str] = Field(default_factory=list)
    responsible_wi: list[str] = Field(default_factory=list)


class WIStatus(BaseModel):
    status: str = "not_started"  # not_started | in_progress | completed
    steps_completed: list[str] = Field(default_factory=list)
    deliverables: dict[str, Any] = Field(default_factory=dict)


class GateReview(BaseModel):
    gate: str
    date: str
    verdict: str  # GO | CONDITIONAL | NO-GO
    report_file: str = ""
    conditions: list[str] = Field(default_factory=list)


class VTest(BaseModel):
    status: str = "not_tested"  # not_tested | pass | fail | conditional
    result: str | None = None
    phase: str = ""  # A | B | C | D
    subsystem: str = ""


class TRState(BaseModel):
    """Root model for .tr-state.json."""

    project_id: str
    triz_session_ref: str
    triz_state_hash: str = ""
    created_at: datetime
    subsystem_tr: dict[str, SubsystemTR] = Field(default_factory=dict)
    wi_status: dict[str, WIStatus] = Field(default_factory=dict)
    gate_reviews: list[GateReview] = Field(default_factory=list)
    v_tests: dict[str, VTest] = Field(default_factory=dict)
    risk_status: dict[str, str] = Field(default_factory=dict)

    model_config = {"use_enum_values": True}
