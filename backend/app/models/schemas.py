"""Pydantic models for API request/response schemas.

Maps to the AI Agent Architecture §1.1 Agent roles and §4.4 Artifact states.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Evidence Reference (shared across responses)
# ---------------------------------------------------------------------------

class EvidenceReference(BaseModel):
    """A single evidence reference attached to an AI suggestion."""
    ref_id: str          # e.g. "WEB-SEARCH-001", "DOC-001"
    ref_type: str        # "web_search" | "uploaded_doc" | "engineering_reasoning"
    title: str
    source: str          # domain, filename, or description
    url: str = ""
    snippet: str = ""


# ---------------------------------------------------------------------------
# Step 1: Brief Extraction
# ---------------------------------------------------------------------------

class BriefExtractionRequest(BaseModel):
    """Input for Analyst Agent — extract constraints, KPIs, assumptions from raw text/upload."""
    project_id: str
    raw_text: str = ""
    file_urls: list[str] = Field(default_factory=list)


class ExtractedConstraint(BaseModel):
    code: str
    description: str
    source: str
    type: str = "hard"
    feasibility: str = "unknown"


class ExtractedKpi(BaseModel):
    name: str
    target_value: str
    unit: str
    measurement_method: str = ""


class BriefExtractionResponse(BaseModel):
    constraints: list[ExtractedConstraint]
    kpis: list[ExtractedKpi]
    assumptions: list[str]
    feasibility_warnings: list[str]


# --- Constraint Feasibility Check ---

class ConstraintFeasibilityRequest(BaseModel):
    """Input for AI constraint feasibility analysis."""
    project_id: str
    mission: str
    constraints: list[str] = Field(default_factory=list)


class FeasibilityConflict(BaseModel):
    constraintA: str
    constraintB: str
    reason: str
    suggestion: str


class ConstraintFeasibilityResponse(BaseModel):
    """AI-generated constraint feasibility analysis."""
    status: str  # "pass" | "warning" | "conflict"
    conflicts: list[FeasibilityConflict] = Field(default_factory=list)


# --- Brief AI Rewrite ---

class BriefRewriteRequest(BaseModel):
    """Input for AI-powered mission rewrite."""
    project_id: str
    mission: str
    constraints: list[str] = Field(default_factory=list)
    kpis: list[str] = Field(default_factory=list)


class BriefRewriteResponse(BaseModel):
    """AI-rewritten mission statement."""
    rewritten_mission: str
    changes_summary: str  # brief explanation of what was improved
    evidence_references: list[EvidenceReference] = Field(default_factory=list)


class ConstraintSuggestRequest(BaseModel):
    """Input for AI constraint suggestions based on mission context."""
    project_id: str
    mission: str
    existing_constraints: list[str] = Field(default_factory=list)


class SuggestedConstraint(BaseModel):
    description: str
    source: str
    rationale: str = ""
    ref_ids: list[str] = Field(default_factory=list)  # which evidence refs support this


class ConstraintSuggestResponse(BaseModel):
    suggestions: list[SuggestedConstraint]
    evidence_references: list[EvidenceReference] = Field(default_factory=list)


class KpiSuggestRequest(BaseModel):
    """Input for AI KPI suggestions based on mission and constraints."""
    project_id: str
    mission: str
    constraints: list[str] = Field(default_factory=list)
    existing_kpis: list[str] = Field(default_factory=list)


class SuggestedKpi(BaseModel):
    kpi_name: str
    target_value: str
    unit: str
    measurement_method: str
    rationale: str = ""
    ref_ids: list[str] = Field(default_factory=list)  # which evidence refs support this


class KpiSuggestResponse(BaseModel):
    suggestions: list[SuggestedKpi]
    evidence_references: list[EvidenceReference] = Field(default_factory=list)


# --- 5W1H Task Definition ---

class TaskDef5W1HRequest(BaseModel):
    """Generate 5W1H task definition from mission + constraints + KPIs."""
    project_id: str
    mission: str
    constraints: list[str] = Field(default_factory=list)
    kpis: list[str] = Field(default_factory=list)


class TaskDef5W1HResponse(BaseModel):
    """AI-generated 5W1H task definition."""
    who: str
    what: str
    where: str
    when: str
    why: str
    how: str
    evidence_references: list[EvidenceReference] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Step 2: Socratic Questions
# ---------------------------------------------------------------------------

class SocraticRequest(BaseModel):
    """Generate Socratic questions based on brief + constraints."""
    project_id: str
    mission: str
    constraints: list[str] = Field(default_factory=list)
    existing_questions: list[str] = Field(default_factory=list)


class SocraticQuestion(BaseModel):
    # 內部欄位叫 category，但可接受輸入 key = type_class
    category: str = Field(validation_alias="type_class") # clarification, assumption, consequence, counter, origin, reflection, reframing
    text: str
    suggested_tag: str | None = None  # assumption, or None


class SocraticResponse(BaseModel):
    questions: list[SocraticQuestion]


# --- Socratic Follow-up (answer depth analysis) ---

class AnsweredQuestion(BaseModel):
    id: str = ""
    category: str
    question: str
    answer: str


class SocraticFollowUpRequest(BaseModel):
    """Analyze answer depth and generate targeted follow-up questions."""
    project_id: str
    mission: str
    constraints: list[str] = Field(default_factory=list)
    answered_questions: list[AnsweredQuestion]


class FollowUpItem(BaseModel):
    category: str = Field(validation_alias="type_class")
    text: str
    reason: str  # why this follow-up is needed


class SocraticFollowUpResponse(BaseModel):
    follow_ups: list[FollowUpItem] = Field(default_factory=list)
    depth_sufficient: bool = False


# --- Socratic Brief Impact Evaluation ---

class ExistingQuestionItem(BaseModel):
    id: str
    category: str
    text: str
    answer: str = ""


class SocraticBriefImpactRequest(BaseModel):
    """Evaluate which Socratic questions are affected by a Brief change."""
    project_id: str
    new_mission: str
    new_constraints: list[str] = Field(default_factory=list)
    existing_questions: list[ExistingQuestionItem]


class AffectedQuestionItem(BaseModel):
    id: str
    reason: str
    replacement: SocraticQuestion


class SocraticBriefImpactResponse(BaseModel):
    affected: list[AffectedQuestionItem] = Field(default_factory=list)
    unaffected_ids: list[str] = Field(default_factory=list)


# --- Socratic Auto-Tag (hidden assumption/contradiction detection) ---

class UntaggedQuestion(BaseModel):
    id: str
    category: str
    text: str
    answer: str = ""


class SocraticAutoTagRequest(BaseModel):
    project_id: str
    mission: str
    constraints: list[str] = Field(default_factory=list)
    existing_assumptions: list[str] = Field(default_factory=list)
    existing_contradictions: list[str] = Field(default_factory=list)
    untagged_questions: list[UntaggedQuestion]


class AutoTagSuggestion(BaseModel):
    question_id: str
    suggested_tag: str  # "assumption" | "contradiction" | "none"
    reason: str = ""


class SocraticAutoTagResponse(BaseModel):
    suggestions: list[AutoTagSuggestion] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Step 3: CLD Generation
# ---------------------------------------------------------------------------

class CldGenerationRequest(BaseModel):
    project_id: str
    contradictions: list[str]
    assumptions: list[str]
    mission: str = ""
    constraints: list[str] = Field(default_factory=list)
    kpis: list[str] = Field(default_factory=list)
    socraticAnswers: list[str] = Field(default_factory=list)


class CldNode(BaseModel):
    id: str
    label: str
    type: str = "variable"


class CldEdge(BaseModel):
    from_node: str = Field(validation_alias="from")
    to_node: str = Field(validation_alias="to")
    polarity: str = "+"
    source_id: str = ""


class CldLoop(BaseModel):
    id: str
    type: str  # "reinforcing" | "balancing"
    node_ids: list[str]


class CldBreakpoint(BaseModel):
    node_id: str
    rationale: str = ""


class CldGenerationResponse(BaseModel):
    nodes: list[CldNode]
    edges: list[CldEdge]
    loops: list[CldLoop] = Field(default_factory=list)
    breakpoints: list[CldBreakpoint]


# ---------------------------------------------------------------------------
# Step 3: Function Model (Su-Field Analysis)
# ---------------------------------------------------------------------------

class FunctionModelRequest(BaseModel):
    """Build a Function Model (Substance-Field) for a system interaction."""
    project_id: str
    system_function: str  # what the system is supposed to do
    substance_1: str = ""  # S1: tool substance (acts on S2)
    substance_2: str = ""  # S2: product substance (acted upon)
    field_type: str = ""  # mechanical / thermal / electrical / magnetic / chemical / ...
    interaction_type: str = ""  # useful / harmful / insufficient / missing
    su_field_completeness: str = ""  # complete / incomplete / harmful_complete
    related_contradiction_ids: list[str] = Field(default_factory=list)
    mission: str = ""
    constraints: list[str] = Field(default_factory=list)


class FunctionModelResponse(BaseModel):
    """AI-analysed Function Model with Su-Field classification."""
    system_function: str
    substance_1: str
    substance_2: str
    field_type: str
    interaction_type: str  # useful / harmful / insufficient / missing
    su_field_completeness: str  # complete / incomplete / harmful_complete
    problem_description: str = ""  # natural language description of the Su-Field problem
    suggested_contradiction_type: str = "SF"  # always SF for function-model derived problems
    confidence: float = Field(ge=0, le=1, default=0.7)


# ---------------------------------------------------------------------------
# Validation Passport (shared — attached to any solution hypothesis)
# ---------------------------------------------------------------------------

class ValidationPassportAssumption(BaseModel):
    """A single assumption declared by the solution itself."""
    content: str
    category: str = "physics"  # physics / material / cost / manufacturing / regulatory / integration
    evidence_level: str = "E0"  # E0 (none) → E1 (reasoning) → E2 (analogy) → E3 (test) → E4 (production)
    worst_consequence: str = ""
    worst_severity: str = "medium"  # critical / high / medium / low
    suggested_experiment: str = ""


class ValidationPassport(BaseModel):
    """Self-declared validation record for a solution hypothesis."""
    assumptions: list[ValidationPassportAssumption] = Field(default_factory=list)
    weak_points: list[str] = Field(default_factory=list)
    required_verifications: list[str] = Field(default_factory=list)
    cross_domain_source: str = ""
    confidence_level: float = Field(ge=0, le=1, default=0.5)


# ---------------------------------------------------------------------------
# Step 5-0: Anti-Anchor Routes
# ---------------------------------------------------------------------------

class AntiAnchorRequest(BaseModel):
    project_id: str
    mission: str
    current_constraints: list[str]
    existing_alternatives: list[str] = Field(default_factory=list)


class AntiAnchorRoute(BaseModel):
    name: str
    mechanism: str = ""  # core mechanism description
    description: str = ""  # LLM may omit; fallback to mechanism
    is_non_typical: bool = True
    rationale: str = ""
    why_unconventional: str = ""
    potential_advantage: str = ""
    cross_domain_source: str = ""
    validation_passport: ValidationPassport | None = None

    def model_post_init(self, __context) -> None:
        if not self.description and self.mechanism:
            self.description = self.mechanism


class AntiAnchorResponse(BaseModel):
    routes: list[AntiAnchorRoute] = Field(default_factory=list, validation_alias="alternatives")


# ---------------------------------------------------------------------------
# Validation Passport Generation (on-demand for solutions without one)
# ---------------------------------------------------------------------------

class ValidationPassportRequest(BaseModel):
    project_id: str
    solution_name: str
    mechanism: str
    source: str = ""  # triz_tc / triz_pc / scamper / anti_anchor / manual
    constraints: list[str] = Field(default_factory=list)
    kpis: list[str] = Field(default_factory=list)


class ValidationPassportResponse(BaseModel):
    validation_passport: ValidationPassport


# ---------------------------------------------------------------------------
# Step 5a: TRIZ Solver
# ---------------------------------------------------------------------------

class TrizLookupRequest(BaseModel):
    """TRIZ contradiction matrix lookup + principle instantiation.

    Routes by type:
      TC → contradiction matrix → 40 principles
      PC → separation principles
      SF → Su-Field 76 standard solutions (delegates to analyze_sufield)
    """
    project_id: str
    contradiction_id: str
    natural_description: str
    improving_param: int | None = None
    worsening_param: int | None = None
    physical_contradiction: str | None = None
    # Su-Field fields (used when type == "SF")
    sf_substance_1: str | None = None
    sf_substance_2: str | None = None
    sf_field: str | None = None
    type: str = "TC"  # TC, PC, or SF
    # Optional hint from Explore-stage PC decomposition (L2 WBS 9.1.1).
    # When provided, _solve_pc shortcircuits separation selection.
    separation_principle_id: str | None = None
    separation_category: str | None = None  # time|space|condition|whole_part
    separation_rationale: str | None = None
    derived_parameter: str | None = None


class TrizSuggestion(BaseModel):
    path: str = ""  # TC, PC, or SuField — auto-derived if missing
    principle_number: int | None = None
    principle_name: str = ""
    suggestion: str
    separation_principle: str = ""  # PC path: time/space/condition/system_level
    affected_modules: list[str] = Field(default_factory=list)
    secondary_contradictions: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def derive_path(cls, values):
        """Auto-derive `path` from LLM output when missing, and coerce bad principle_number."""
        if isinstance(values, dict):
            # LLM sometimes returns non-integer principle_number (e.g. 'SP-Time', '76-StdSol-1.2')
            # for PC/SF paths — move the value to principle_name and set number to None.
            pn = values.get("principle_number")
            if pn is not None and not isinstance(pn, int):
                try:
                    values["principle_number"] = int(pn)
                except (ValueError, TypeError):
                    # Non-numeric → treat as a name, clear the number
                    if not values.get("principle_name"):
                        values["principle_name"] = str(pn)
                    values["principle_number"] = None
            if not values.get("path"):
                if values.get("separation_principle"):
                    values["path"] = "PC"
                elif values.get("principle_number"):
                    values["path"] = "TC"
                else:
                    values["path"] = "unknown"
        return values


class TrizLookupResponse(BaseModel):
    mapped_improving: int | None = None
    mapped_worsening: int | None = None
    candidate_principles: list[int] = Field(default_factory=list)
    suggestions: list[TrizSuggestion]


# ---------------------------------------------------------------------------
# Step 5a-3: Su-Field Analysis (76 Standard Solutions)
# ---------------------------------------------------------------------------

class SuFieldRequest(BaseModel):
    """Su-Field model analysis + 76 standard solutions matching."""
    project_id: str
    system_description: str
    current_issues: list[str] = Field(default_factory=list)
    # Traceability back to Step 3 Function Model / contradiction
    contradiction_id: str | None = None
    substance_1: str | None = None  # S1 from Function Model
    substance_2: str | None = None  # S2 from Function Model
    field_type: str | None = None  # field from Function Model


class MatchedStandardSolution(BaseModel):
    standard_id: str          # e.g. "1.1.1"
    standard_name: str        # e.g. "Build Complete Su-Field"
    class_name: str           # e.g. "Class 1"
    suggestion: str
    affected_modules: list[str] = Field(default_factory=list)
    secondary_contradictions: list[str] = Field(default_factory=list)


class SuFieldResponse(BaseModel):
    su_field: dict             # {S1, S2, F}
    system_state: str          # incomplete | effective | harmful | insufficient
    matched_solutions: list[MatchedStandardSolution]


# ---------------------------------------------------------------------------
# Step 5a-X: LayeredTrizSolution — drill-down (L1 TC / L2 PC / L3 SF)
#
# Ref: docs/e2e/TRIZ_Layered_DrillDown_Optimization.md §5
#      docs/e2e/TRIZ_Multi_Solution_Adoption_Strategy.md v1.1 §2 M6
#      docs/diagrams/create-ux-spec.md v7 Tab ① 區塊 B
#
# Frozen enums (WBS 1.2):
#   LayerRole: phenomenon | root_cause | structural_lens
#   DepthIndicator: "trade-off 改良" | "根因突破" | "功能鏈缺陷修補"
#   SeparationType: time | space | condition | whole_part
# ---------------------------------------------------------------------------

LayerRole = Literal["phenomenon", "root_cause", "structural_lens"]
DepthIndicator = Literal["trade-off 改良", "根因突破", "功能鏈缺陷修補"]
SeparationType = Literal["time", "space", "condition", "whole_part"]
EvidenceLevelFloor = Literal["E0", "E1", "E2", "E3", "E4"]
LayerStatus = Literal["ran", "skipped_quick_mode", "skipped_condition", "error"]


class L1Surface(BaseModel):
    """L1 — TC 現象層（永遠跑）。"""
    layer_role: LayerRole = "phenomenon"
    type: Literal["TC"] = "TC"
    improving_param: int | None = None
    worsening_param: int | None = None
    candidate_principles: list[int] = Field(default_factory=list)
    suggestions: list[TrizSuggestion] = Field(default_factory=list)
    depth_indicator: DepthIndicator = "trade-off 改良"
    evidence_level_floor: EvidenceLevelFloor = "E1"
    # critic output (WBS 4.1)
    critic_trigger_l2: bool = False
    critic_reason: str = ""
    critic_confidence: float = 0.0
    status: LayerStatus = "ran"


class SeparationCandidate(BaseModel):
    type: SeparationType
    rationale: str = ""
    confidence: float = 0.0


class DeepenLink(BaseModel):
    """ARIZ 深挖：從 L1 TC 對推導出 L2 PC 的 (derived_parameter + separation types)."""
    from_layer: Literal["L1_surface"] = "L1_surface"
    # Pydantic 2.12 treats a bare `tuple[...] = (None, None)` literal default as
    # mutable and silently demotes later-in-class fields to required. Declare
    # explicitly through Field + default_factory to avoid that corner case.
    from_tc_pair: tuple[int | None, int | None] = Field(
        default_factory=lambda: (None, None)
    )
    derived_physical_parameter: str = ""
    contradiction_statement: str = ""
    separation_type_candidates: list[SeparationCandidate] = Field(default_factory=list)


class L2RootCause(BaseModel):
    """L2 — PC 本質層（有條件跑）。"""
    layer_role: LayerRole = "root_cause"
    type: Literal["PC"] = "PC"
    triggered: bool = False
    trigger_reason: str = ""
    deepen_link: DeepenLink | None = None
    suggestions: list[TrizSuggestion] = Field(default_factory=list)
    depth_indicator: DepthIndicator = "根因突破"
    evidence_level_floor: EvidenceLevelFloor = "E1"
    status: LayerStatus = "skipped_condition"


class SuFieldModel(BaseModel):
    S1: str = ""
    S2: str = ""
    F: str = ""
    state: Literal["incomplete", "effective", "harmful", "insufficient", "unknown"] = "unknown"


class L3StructuralCheck(BaseModel):
    """L3 — SF 結構層（永遠跑，角色=structural_lens 旁路）。"""
    layer_role: LayerRole = "structural_lens"
    type: Literal["SF"] = "SF"
    su_field_model: SuFieldModel = Field(default_factory=SuFieldModel)
    matched_standard_solutions: list[str] = Field(default_factory=list)
    suggestions: list[TrizSuggestion] = Field(default_factory=list)
    # LLM-produced bridge text (WBS 5.3)
    supports_l1: str = ""
    supports_l2: str = ""
    standalone_value: str = ""
    depth_indicator: DepthIndicator = "功能鏈缺陷修補"
    evidence_level_floor: EvidenceLevelFloor = "E1"
    status: LayerStatus = "ran"


class DifferentialPairAnalysis(BaseModel):
    on_solving_degree: str = ""
    on_effort: str = ""
    on_risk: str = ""
    orthogonality: str = ""
    synergy: str = ""


class RecommendedRoute(BaseModel):
    primary: str = ""          # e.g. "L2 + L3 組合（突破路線）"
    fallback: str = ""         # e.g. "L1 單獨（快速路線）"
    adopted_layers: list[Literal["L1", "L2", "L3"]] = Field(default_factory=list)
    rationale: str = ""


class DifferentialAnalysis(BaseModel):
    """跨層差異分析 — 由 LLM 在 orchestrator 最後一步產生。"""
    l1_vs_l2: DifferentialPairAnalysis = Field(default_factory=DifferentialPairAnalysis)
    l1_vs_l3: DifferentialPairAnalysis = Field(default_factory=DifferentialPairAnalysis)
    l2_vs_l3: DifferentialPairAnalysis = Field(default_factory=DifferentialPairAnalysis)
    recommended_route: RecommendedRoute = Field(default_factory=RecommendedRoute)


class PhaseBDirective(BaseModel):
    """指示 Phase B 掃描如何處理同一 LTS 內的多層採納。"""
    same_contradiction_intra_layer_conflict: Literal["skip", "check"] = "skip"
    cross_contradiction_conflict: Literal["skip", "check"] = "check"


class LayeredTrizSolution(BaseModel):
    """v7: 一個矛盾對應一張分層診斷卡（L1 + L2? + L3 + differential）。

    取代舊設計的「每矛盾三條 pending 候選」，改為一個堆疊診斷單元。
    Schema 對齊 TRIZ_Layered_DrillDown_Optimization.md §5。
    """
    id: str                                     # e.g. "LTS-EBIKE-012"
    project_id: str
    contradiction_id: str
    contradiction_natural_description: str = ""
    severity: Literal["fatal", "major", "minor", "unknown"] = "unknown"

    l1_surface: L1Surface
    l2_root_cause: L2RootCause | None = None    # None → 未跑（condition 未達 或 quick_mode 跳過）
    l3_structural_check: L3StructuralCheck

    differential_analysis: DifferentialAnalysis = Field(default_factory=DifferentialAnalysis)
    phase_b_directive: PhaseBDirective = Field(default_factory=PhaseBDirective)


class SolveTrizLayeredRequest(BaseModel):
    """POST /triz/solve-layered — 單矛盾版本（orchestrator 會遍歷多矛盾時呼叫 N 次）。"""
    project_id: str
    contradiction_id: str
    natural_description: str
    severity: Literal["fatal", "major", "minor", "unknown"] = "unknown"
    # TC inputs
    improving_param: int | None = None
    worsening_param: int | None = None
    # PC inputs (若 RD 手動提供，會覆寫 deepen_link 推導)
    physical_contradiction: str | None = None
    # SF inputs (直接傳遞給 _solve_sf)
    sf_substance_1: str | None = None
    sf_substance_2: str | None = None
    sf_field: str | None = None
    # Control flags (WBS 3.5 / 3.6)
    quick_mode: bool = False         # severity=minor + quick_mode=true → L2 skipped
    force_l2: bool = False           # RD 手動要求深挖，覆蓋所有條件


class SolveTrizLayeredResponse(BaseModel):
    layered_solution: LayeredTrizSolution


# ---------------------------------------------------------------------------
# Step 5c: SCAMPER
# ---------------------------------------------------------------------------

class ScamperRequest(BaseModel):
    project_id: str
    subsystem_name: str
    subsystem_description: str
    related_contradictions: list[str] = Field(default_factory=list)
    # RD-confirmed structured 6-dim contracts, keyed by neighbour. Optional
    # for backward-compat: scamper_transform degrades gracefully to the
    # contradiction-only prompt when the dict is empty. When populated, the
    # LLM is instructed to declare which contract dimension each variant
    # preserves / modifies / breaks (WBS 10.1 — F3 reads RD-confirmed
    # interface contracts so creative transformations respect boundaries).
    interface_contracts: dict[str, "InterfaceContract"] = Field(default_factory=dict)
    # Short stable fingerprint of the confirmed contract snapshot at the
    # moment RD confirmed the subsystem. Not cryptographic — FE uses a
    # djb2-style hash. If the FE later detects edits (hash mismatch) it
    # blocks SCAMPER and forces re-confirm. The backend logs any inbound
    # request whose hash is missing when contracts are present so we have
    # a paper trail of clients that need updating.
    contracts_hash: str = ""


class ScamperVariant(BaseModel):
    action: str  # Substitute, Combine, Adapt, Modify, Put to other use, Eliminate, Reverse
    description: str
    potential_benefits: str = ""
    new_contradictions: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_keys(cls, values):
        """Accept LLM output keys: benefit → potential_benefits, new_contradiction → new_contradictions."""
        if isinstance(values, dict):
            if "benefit" in values and "potential_benefits" not in values:
                values["potential_benefits"] = values.pop("benefit")
            if "new_contradiction" in values and "new_contradictions" not in values:
                nc = values.pop("new_contradiction")
                values["new_contradictions"] = [nc] if isinstance(nc, str) and nc else []
        return values


class ScamperResponse(BaseModel):
    variants: list[ScamperVariant] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_keys(cls, values):
        """Accept LLM key 'transformations' as alias for 'variants'."""
        if isinstance(values, dict):
            if "transformations" in values and "variants" not in values:
                values["variants"] = values.pop("transformations")
        return values


# ---------------------------------------------------------------------------
# Step 6: Risk Analysis
# ---------------------------------------------------------------------------

class RiskAnalysisRequest(BaseModel):
    project_id: str
    alternative_name: str
    mechanism: str
    assumptions: list[str] = Field(default_factory=list)


class RiskSuggestion(BaseModel):
    description: str
    failure_mode: str
    probability: int = Field(ge=1, le=5)
    severity: int = Field(ge=1, le=5)
    mitigation: str


class RiskAnalysisResponse(BaseModel):
    risks: list[RiskSuggestion]


# ---------------------------------------------------------------------------
# Step 7: Action Suggestions
# ---------------------------------------------------------------------------

class ActionSuggestRequest(BaseModel):
    project_id: str
    selected_alternative: str
    rationale: str
    risks: list[str] = Field(default_factory=list)


class ActionSuggestion(BaseModel):
    description: str
    assignee_role: str
    suggested_due_days: int = 14


class ActionSuggestResponse(BaseModel):
    actions: list[ActionSuggestion]


# ---------------------------------------------------------------------------
# Contradiction Convergence (Step 5a-6)
# ---------------------------------------------------------------------------

class ConvergenceAlternativeInput(BaseModel):
    """Rich alternative payload for convergence scanning."""
    id: str
    name: str
    mechanism: str
    source: str = ""  # triz_tc / triz_pc / triz_sf / scamper / manual / ai_integrated
    resolves_contradiction_ids: list[str] = Field(default_factory=list)


class ConvergenceContradictionInput(BaseModel):
    """Rich contradiction payload for convergence scanning."""
    id: str
    natural_description: str
    severity: str  # fatal / major / minor
    resolved: bool = False
    type: str | None = None  # TC, PC, or SF
    improving_param: int | None = None  # TRIZ 39-param number
    worsening_param: int | None = None
    engineering_statement: str = ""
    physical_contradiction: str = ""
    # Su-Field fields (populated when type == "SF")
    sf_substance_1: str = ""
    sf_substance_2: str = ""
    sf_field: str = ""


class LayeredAlternativeDirective(BaseModel):
    """v7 WP 10.6: Per-alternative Phase B directive carried on the scan
    request. Lets the scanner SKIP intra-LTS cross-layer pairs and WARN on
    cross-LTS redundancy without re-reading the LTS from DB.

    Ref: docs/e2e/TRIZ_Layered_DrillDown_Optimization.md §8.3
    """
    alternative_id: str
    lts_id: str
    adopted_layers: list[Literal["L1", "L2", "L3"]] = Field(default_factory=list)
    same_contradiction_intra_layer_conflict: Literal["skip", "check"] = "skip"
    cross_contradiction_conflict: Literal["skip", "check"] = "check"


class ConvergenceScanRequest(BaseModel):
    project_id: str
    alternatives: list[ConvergenceAlternativeInput] = Field(default_factory=list)
    contradictions: list[ConvergenceContradictionInput]
    mission: str = ""
    constraints: list[str] = Field(default_factory=list)
    kpis: list[str] = Field(default_factory=list)
    phase: str = "B"  # v8: always "B" — Phase A retired (L1 critic subsumes)
    # v7 WP 10.6: optional Phase B directives for layered Concept Routes.
    # Empty list → legacy behaviour (flat mode). Non-empty → scanner pairs
    # alternatives by lts_id and applies SKIP / WARN / CHECK per §8.3.
    layered_directives: list[LayeredAlternativeDirective] = Field(default_factory=list)


class SecondaryContradiction(BaseModel):
    description: str
    severity: str  # fatal, major, minor
    source_alternative: str = ""  # may be empty if no source identified
    type: str = "TC"  # TC, PC, or SF
    improving_param: int | None = None
    worsening_param: int | None = None
    reasoning: str = ""
    is_confirmatory: bool = False  # True = same causal chain as existing, doesn't count as new


class ConvergenceScanResponse(BaseModel):
    new_contradictions: list[SecondaryContradiction]
    convergence_score: float  # 0-100 integer scale
    architecture_health: str  # healthy, warning, critical
    force_pause: bool = False
    pause_reason: str = ""
    reasoning_trace: str = ""
    phase: str = "B"  # echo back which phase produced this result

    @model_validator(mode="before")
    @classmethod
    def normalize_keys(cls, values):
        # Accept LLM output key 'secondary_contradictions' -> 'new_contradictions'
        if isinstance(values, dict):
            if "secondary_contradictions" in values and "new_contradictions" not in values:
                values["new_contradictions"] = values.pop("secondary_contradictions")
            # Accept 0-1 scale and normalise to 0-100
            score = values.get("convergence_score", 0)
            if isinstance(score, (int, float)) and score <= 1.0:
                values["convergence_score"] = round(score * 100)
        return values


# ---------------------------------------------------------------------------
# MUST Evaluation (AI-assisted Go/No-Go)
# ---------------------------------------------------------------------------

class MustCriterionConfig(BaseModel):
    """A single MUST criterion derived from Brief constraints/KPIs."""
    id: str  # e.g. "M1"
    label: str  # e.g. "效率 ≥ 95%"
    source: str  # which constraint/KPI this comes from
    threshold: str = ""  # quantitative threshold if applicable


class MustEvaluationRequest(BaseModel):
    """Evaluate one alternative against project MUST criteria."""
    project_id: str
    alternative_name: str
    mechanism: str
    must_criteria: list[MustCriterionConfig]
    constraints: list[str] = Field(default_factory=list)
    kpis: list[str] = Field(default_factory=list)


class MustCriterionResult(BaseModel):
    """AI pre-judgment for a single MUST criterion."""
    id: str
    label: str
    passed: bool | None  # true=pass, false=fail, null=insufficient data
    confidence: float = Field(ge=0, le=1)  # 0~1
    reasoning: str  # why AI judged this way
    evidence_sources: list[str] = Field(default_factory=list)


class MustEvaluationResponse(BaseModel):
    """AI pre-filled MUST results for RD to confirm/override."""
    criteria_results: list[MustCriterionResult]
    overall_pass: bool | None  # null if any criterion is null
    summary: str  # brief overall assessment


# ---------------------------------------------------------------------------
# Contradiction Formalization (SOW: POST /contradictions/{cid}/formalize)
# ---------------------------------------------------------------------------

class ContradictionFormalizeRequest(BaseModel):
    """Formalize a natural-language contradiction into TRIZ sentence."""
    project_id: str
    contradiction_id: str
    natural_description: str
    mission: str = ""
    constraints: list[str] = Field(default_factory=list)
    kpis: list[str] = Field(default_factory=list)
    socraticAnswers: list[str] = Field(default_factory=list)


class ContradictionFormalizeResponse(BaseModel):
    """TRIZ-formalized contradiction — Explore stage emits TC-only (ADR-007).

    If LLM cannot map the natural description to two distinct TRIZ 39
    parameters, `type` is returned as None and `rationale` explains why,
    so the UI can present a Socratic follow-up instead of silently
    downgrading to PC/SF.
    """
    engineering_statement: str
    improving_param: int | None = None
    worsening_param: int | None = None
    # deprecated — PC/SF 改於 Create 階段自 TC 派生（ADR-007）。
    # 欄位保留以相容舊 DB row 與 Create 階段派生結果回傳。
    physical_contradiction: str | None = None
    pc_attribute_a: str | None = None
    pc_attribute_not_a: str | None = None
    # deprecated — Su-Field 於 Create 階段自 TC 派生（ADR-007）。
    sf_substance_1: str | None = None  # S1: tool substance
    sf_substance_2: str | None = None  # S2: product substance
    sf_field: str | None = None  # field type (mechanical/thermal/electrical/...)
    sf_interaction: str | None = None  # useful/harmful/insufficient/missing
    sf_completeness: str | None = None  # complete/incomplete/harmful_complete
    # ADR-007: Explore output restricted to "TC"; null = cannot map.
    type: Literal["TC"] | None = "TC"
    confidence: float = Field(ge=0, le=1, default=0.7)
    # LLM explanation when type is None (cannot map to TC).
    rationale: str | None = None


# ---------------------------------------------------------------------------
# Assumption Extraction (SOW: POST /assumptions/extract)
# ---------------------------------------------------------------------------

class AssumptionExtractRequest(BaseModel):
    """Extract assumptions from Socratic question answers."""
    project_id: str
    questions_and_answers: list[dict] = Field(default_factory=list)
    mission: str = ""
    constraints: list[str] = Field(default_factory=list)
    kpis: list[str] = Field(default_factory=list)
    existing_assumptions: list[str] = Field(default_factory=list)


class ExtractedAssumption(BaseModel):
    content: str
    source: str = ""
    worst_consequence: str = ""
    worst_severity: str = "medium"  # critical, high, medium, low
    is_falsifiable: bool = True
    evidence_level: str = "E0"  # E0 (speculation) → E4 (production-proven)
    falsification_method: str = ""  # experiment to disprove; "N/A" if not falsifiable


class AssumptionExtractResponse(BaseModel):
    assumptions: list[ExtractedAssumption]


# ---------------------------------------------------------------------------
# SCAMPER Subsystem Suggestions (SOW: GET /scamper/subsystem-suggestions)
# ---------------------------------------------------------------------------

class SubsystemSuggestRequest(BaseModel):
    """Suggest subsystems for SCAMPER analysis.

    v7 (WBS 11.1): When the new `triz_layered_mode` is on, the Create Tab ①
    passes `layered_triz_solutions` so F2 can bind subsystems to the
    adopted_route / recommended_route of a LayeredTrizSolution instead of
    scanning a flat contradiction list. The legacy `contradictions` field is
    kept for back-compat so existing consumers compile unchanged.

    Ref: docs/e2e/TRIZ_Layered_DrillDown_Optimization.md §8.1 / §8.1.1 and
         docs/e2e/module/Forward_Subsystem_Discovery_Architecture.md §3.1
    """
    project_id: str
    mission: str
    contradictions: list[str] = Field(default_factory=list)
    existing_subsystems: list[str] = Field(default_factory=list)
    # v7 M6: optional layered-TRIZ handoff. When present, F2 should prefer
    # `adopted_route` (or `recommended_route`) on each LTS as the
    # `related_contradictions` primary binding; when empty, fall back to the
    # flat `contradictions` list above.
    layered_triz_solutions: list[LayeredTrizSolution] = Field(default_factory=list)


# ---- Spatial Grounding (Discovery Mode) ----------------------------------
# These types let Interface Contracts carry structured dimensional estimates
# alongside the legacy free-text fields. They are OPTIONAL — RD discovery mode
# never requires upfront spatial budgets.

class BBox(BaseModel):
    """Axis-aligned bounding box in millimeters."""
    x_mm: float
    y_mm: float
    z_mm: float
    origin_mm: tuple[float, float, float] = (0.0, 0.0, 0.0)
    anchor: str = ""  # e.g. "BB_center" / "downtube_top" — frame-relative anchor name


class SpatialEstimate(BaseModel):
    """Per-module structured dimensional estimate. In discovery mode these are
    LLM proposals (or library lookups), not constraints."""
    bbox: BBox | None = None
    mass_g: float | None = None
    mounting_pattern: str = ""           # e.g. "M6x4 @ 50mm PCD"
    # Canonical prefixes (locked by test_reference_source_lint.py):
    #   rd_override:<key> | learned:<key> | web:<query> | seed:<key> | llm_estimate
    # The layered resolver (app/services/spatial_lookup.py) emits the first four;
    # llm_estimate is the caller-side fallback when no layer resolves. Empty
    # string is allowed at construction time but the agent always fills it.
    reference_source: str = ""
    # Strict enum — LLM / legacy callers emitting e.g. "Library" or "high"
    # will raise ValidationError (desired: drift must be loud). rd_confirmed
    # is RESERVED for RD inline override writes; see Three_Tier_Tree_Review_Checklist.md.
    confidence: Literal["library", "estimate", "rd_confirmed"] = "estimate"
    rationale: str = ""                  # one-line justification when llm_estimate


class InterfaceContract(BaseModel):
    """6-dimensional interface contract between two coupled modules.

    Wire format is camelCase (matches the LLM SUBSYSTEM_SUGGESTION prompt and
    the FE TypeScript types). Single source of truth — no aliases, no fallbacks.
    Anything sending snake_case will fail validation loudly, which is the
    desired behaviour: drift between layers should never be silent.
    """
    envelope: str = ""
    loadPath: str = ""
    thermalPath: str = ""
    signalPath: str = ""
    datumTolerance: str = ""
    serviceability: str = ""
    # Optional structured spatial estimate. None when LLM omits it; existing
    # contracts without spatial data remain valid.
    spatial: SpatialEstimate | None = None


# ---- Package Map (Discovery Validator output) ----------------------------

class PackageNode(BaseModel):
    """A single module flattened into the package map."""
    name: str
    spatial: SpatialEstimate
    clashes: list[str] = Field(default_factory=list)  # names of overlapping nodes


class RequiredEnvelope(BaseModel):
    """The minimum envelope this design REQUIRES (descriptive, not prescriptive)."""
    total_bbox_mm: tuple[float, float, float]
    total_mass_g: float
    by_anchor: dict[str, tuple[float, float, float]] = Field(default_factory=dict)


class PackageMap(BaseModel):
    """Discovery output. Tells RD what space and mass the design wants.
    overlay_* fields populated only when an optional what-if overlay is applied."""
    nodes: list[PackageNode] = Field(default_factory=list)
    required: RequiredEnvelope
    overlay_budget: dict | None = None
    overlay_violations: list[str] = Field(default_factory=list)
    svg: str = ""
    table_md: str = ""
    notes: list[str] = Field(default_factory=list)


class SuggestedSubsystem(BaseModel):
    name: str
    # Strict three-level enum — LLM emitting "sub-module" / "Component" /
    # "system-level" will raise ValidationError. Matches the TS Literal at
    # src/types/generated/subsystem.ts SubsystemLevel. See
    # Three_Tier_Tree_Review_Checklist.md § 樹階層.
    level: Literal["system", "module", "component"] = "module"
    reason: str = ""
    related_contradictions: list[str] = Field(default_factory=list)
    children: list["SuggestedSubsystem"] = Field(default_factory=list)
    interface_contracts: dict[str, InterfaceContract] = Field(default_factory=dict)


class SubsystemSuggestResponse(BaseModel):
    subsystems: list[SuggestedSubsystem]
    # Optional discovery output. None for legacy callers; populated when the
    # spatial validator successfully derives a package map from the contracts.
    package_map: PackageMap | None = None


# ---- Optional spatial overlay (what-if) ----------------------------------
# RD can POST a hypothetical frame envelope AFTER discovery to compare
# trade-offs. This is intentionally not part of the discovery flow itself,
# so creativity is not constrained upfront.

class SpatialOverlayRequest(BaseModel):
    """Stateless what-if: caller provides the subsystem tree to validate plus
    an overlay. Discovery is recomputed from the subsystems and the overlay
    is applied. Subsystems are passed in the same shape returned by
    POST /scamper/subsystem-suggestions, so the FE can simply round-trip the
    previous response back together with the new overlay."""
    project_id: str
    subsystems: list["SuggestedSubsystem"] = Field(default_factory=list)
    overlay: dict = Field(default_factory=dict)
    # Schema:
    # {
    #   "zones": {"downtube": {"x_mm": 380, ...}},
    #   "mass_budget_g": {"Battery": 4500}
    # }


class SpatialOverlayResponse(BaseModel):
    package_map: PackageMap


# ---- Layered Spatial Lookup endpoints --------------------------------------
# Backs the RD inline-override flow and the learned-component promotion flow.

class ComponentOverrideRequest(BaseModel):
    """RD says: for THIS project, this component IS this size. Authoritative."""
    project_id: str
    component_key: str          # free-form, e.g. "main_battery"
    category: str = ""
    bbox: BBox
    mass_g: float = 0.0
    note: str = ""


class ComponentOverrideResponse(BaseModel):
    saved: bool
    component_key: str


class LearnedComponentPromoteRequest(BaseModel):
    """Promote a confirmed estimate into the global learned_components table.
    Triggered when RD signs off on a Pre-CAD review whose estimate came from
    web/llm — the estimate becomes a fact for future projects."""
    key: str
    category: str
    bbox: BBox
    mass_g: float = 0.0
    origin: str = "manual"      # "rd_override" | "web" | "seed_promote" | "manual"
    origin_project_id: str = ""
    source_url: str = ""
    source_text: str = ""


class LearnedComponentPromoteResponse(BaseModel):
    saved: bool
    key: str
    confirmed_count: int


# ---------------------------------------------------------------------------
# SCAMPER Feedback Contradictions (SOW: POST /scamper/feedback-contradictions)
# ---------------------------------------------------------------------------

class ScamperFeedbackRequest(BaseModel):
    """Feed SCAMPER-generated contradictions back to contradiction management."""
    project_id: str
    new_contradictions: list[dict] = Field(default_factory=list)


class ScamperFeedbackResponse(BaseModel):
    created_count: int
    deduplicated_count: int
    contradiction_ids: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Pre-CAD AI Analysis (SOW: POST /pre-cad-reviews/{rid}/ai-analyze)
# ---------------------------------------------------------------------------

class PreCadAnalyzeRequest(BaseModel):
    """AI analysis of Pre-CAD 5D review."""
    project_id: str
    alternative_name: str
    mechanism: str
    constraints: list[str] = Field(default_factory=list)
    # OPTIONAL: pass the subsystem tree (same shape as SubsystemSuggestResponse)
    # so the spatial validator can compute a deterministic spatial_score from
    # real arithmetic instead of letting the LLM guess. When omitted, behaviour
    # is unchanged (LLM-only scoring).
    subsystems: list["SuggestedSubsystem"] = Field(default_factory=list)


class SpatialTrace(BaseModel):
    """Compact trace of WHY the Pre-CAD spatial_score has its value.

    Produced by the Pre-CAD evaluator from the deterministic spatial validator
    output (not from the LLM). Rendered by the FE in a hover-card so RD can see
    the underlying arithmetic (bbox, mass, clashes) behind the score.

    `source` encodes provenance:
      - "validator"    — score/trace came from a non-empty PackageMap
      - "empty"        — no subsystems or validator returned empty PackageMap
      - "llm_fallback" — validator raised; trace carries empty lists
    """
    total_mass_g: float = 0.0
    total_bbox_mm: tuple[float, float, float] = (0.0, 0.0, 0.0)
    clash_pairs: list[tuple[str, str]] = Field(default_factory=list)
    module_count: int = 0
    notes: list[str] = Field(default_factory=list)
    source: Literal["validator", "llm_fallback", "empty"] = "empty"


class PreCadAnalyzeResponse(BaseModel):
    """5D AI scores and analysis."""
    # Ignore any LLM-supplied `overall_pass` — it is now computed server-side
    # from the 5 scores so it cannot drift after a deterministic override.
    model_config = ConfigDict(extra="ignore")

    spatial_score: int = Field(ge=1, le=5)
    cost_score: int = Field(ge=1, le=5)
    safety_score: int = Field(ge=1, le=5)
    decoupling_score: int = Field(ge=1, le=5)
    supply_score: int = Field(ge=1, le=5)
    analysis: str
    evidence_references: list[EvidenceReference] = Field(default_factory=list)
    # Populated when the request includes subsystems with spatial estimates.
    # Lets the FE display the same package map RD already saw at F2 alongside
    # the pre-CAD scores.
    package_map: PackageMap | None = None
    # Deterministic trace of the spatial_score, built from the validator's
    # PackageMap (never from the LLM). Optional to avoid breaking legacy
    # callers that don't expect the field.
    spatial_trace: "SpatialTrace | None" = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def overall_pass(self) -> bool:
        """Derived from the 5 scores: pass iff every dimension >= 3.

        Implemented as a computed field (not stored) so that any code path
        which mutates one of the scores (e.g. the deterministic spatial
        override in `analyze_pre_cad`) automatically gets a consistent
        `overall_pass` at serialization time — no manual recompute needed.
        """
        return all(
            s >= 3
            for s in (
                self.spatial_score,
                self.cost_score,
                self.safety_score,
                self.decoupling_score,
                self.supply_score,
            )
        )


# ---------------------------------------------------------------------------
# Unknown Factor Discovery (SOW: POST /unknown-factors/discover)
# ---------------------------------------------------------------------------

class UnknownFactorDiscoverRequest(BaseModel):
    """Discover unknown factors from project context."""
    project_id: str
    mission: str
    constraints: list[str] = Field(default_factory=list)
    kpis: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    existing_assumptions: list[str] = Field(default_factory=list)
    existing_unknowns: list[str] = Field(default_factory=list)


class DiscoveredUnknownFactor(BaseModel):
    description: str
    impact: str = "medium"  # high / medium / low
    reason: str = ""


class UnknownFactorDiscoverResponse(BaseModel):
    factors: list[DiscoveredUnknownFactor]


# ---------------------------------------------------------------------------
# WANT Criteria Seed (SOW: POST /want/criteria/seed)
# ---------------------------------------------------------------------------

class WantSeedRequest(BaseModel):
    """Seed WANT criteria from mission + constraints + KPIs."""
    project_id: str
    mission: str
    constraints: list[str] = Field(default_factory=list)
    kpis: list[str] = Field(default_factory=list)


class SuggestedWantCriterion(BaseModel):
    name: str
    description: str
    weight: int = Field(ge=1, le=10, default=5)
    anchors: dict = Field(default_factory=dict)  # {1: "poor", 3: "fair", 5: "excellent"}


class WantSeedResponse(BaseModel):
    criteria: list[SuggestedWantCriterion]


# ---------------------------------------------------------------------------
# Gate Check (SOW: GET /gates/{gate_id}/check)
# ---------------------------------------------------------------------------

class GateCheckItem(BaseModel):
    label: str
    met: bool
    detail: str = ""


class AiReviewResult(BaseModel):
    """AI evaluator result attached to a gate check (optional)."""
    evaluator: str          # "must" | "pre_cad" | "convergence"
    summary: str
    confidence: float = 0.0
    details: dict = Field(default_factory=dict)


class GateCheckResponse(BaseModel):
    gate_id: str
    passed: bool
    failed_reasons: list[str] = Field(default_factory=list)
    checklist_items: list[GateCheckItem] = Field(default_factory=list)
    ai_review: AiReviewResult | None = None


# ---------------------------------------------------------------------------
# Export (SOW: POST /export)
# ---------------------------------------------------------------------------

class ExportRequest(BaseModel):
    project_id: str
    format: str = "markdown"  # markdown or json
    sections: list[str] = Field(default_factory=list)  # empty = all sections


class ExportResponse(BaseModel):
    content: str
    format: str
    filename: str


# ---------------------------------------------------------------------------
# Knowledge Writeback (SOW: POST /knowledge/writeback)
# ---------------------------------------------------------------------------

class KnowledgeWritebackRequest(BaseModel):
    project_id: str
    asset_types: list[str] = Field(default_factory=list)  # empty = all 6 types


class WrittenAsset(BaseModel):
    asset_type: str
    title: str
    id: str


class KnowledgeWritebackResponse(BaseModel):
    written_count: int
    assets: list[WrittenAsset] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Forward-reference resolution
# ---------------------------------------------------------------------------
# ScamperRequest references InterfaceContract (defined later in this file),
# so we rebuild the model here once all symbols are in scope. Without this,
# Pydantic v2 may fail to resolve the string annotation at validation time.
ScamperRequest.model_rebuild()


# NOTE: An earlier scaffold of LayeredTrizSolution / L1Surface / L2RootCause /
# L3StructuralCheck / DeepenLink / DifferentialAnalysis lived at the bottom of
# this file and was shadowing the canonical definitions above (lines 511–669,
# WBS 1.1 / 2.1 / §5 of TRIZ_Layered_DrillDown_Optimization.md). It has been
# removed in v7 — all Layered TRIZ types are authoritative in the earlier
# section. Downstream consumers import from `app.models.schemas` unchanged.


# ---------------------------------------------------------------------------
# TC → Multi-PC Decomposition (L2 WBS task 3.2)
# Ref: docs/e2e/module/Explore_TC_to_MultiPC_Decomposition_WBS.md
# ---------------------------------------------------------------------------

class DecomposedPC(BaseModel):
    """A single Physical Contradiction derived from a parent TC.

    Each DecomposedPC represents ONE dimension where the TC manifests as a
    same-property mutual exclusion (A vs ¬A). Multiple DecomposedPCs per TC
    are expected for complex engineering systems (e.g., e-Bike drive unit
    typically yields 3-5 PCs covering different subsystems).
    """
    derived_parameter: str = Field(..., description="同一物理屬性 P，例: 齒輪模數")
    subsystem_hint: str = Field(..., description="所屬子系統，例: 齒輪傳動")
    physical_contradiction: str = Field(..., description="完整 X must A and must ¬A 陳述")
    pc_attribute_a: str = Field(..., description="屬性 A 濃縮詞")
    pc_attribute_not_a: str = Field(..., description="屬性 ¬A 濃縮詞")

    separation_principle_id: str = Field(..., description="16 項 id 之一，例: space.partition_combine")
    separation_category: Literal["time", "space", "condition", "whole_part"]
    separation_rationale: str = Field(..., description="為何此分離原則適用（1-2 句）")

    confidence: float = Field(ge=0, le=1, default=0.7)

    @field_validator("separation_principle_id")
    @classmethod
    def _validate_separation_id(cls, v: str) -> str:
        """Ensure id is in the canonical 16-item list."""
        from app.tools.separation_principles import get_separation_principle
        if get_separation_principle(v) is None:
            raise ValueError(
                f"separation_principle_id '{v}' not in canonical 16-item list. "
                f"See backend/app/tools/separation_principles.py for valid ids."
            )
        return v


class ContradictionDecomposeRequest(BaseModel):
    """Request to decompose a parent TC into multiple child PCs."""
    project_id: str
    parent_contradiction_id: str
    engineering_statement: str
    improving_param: int | None = None
    worsening_param: int | None = None
    severity: str = "minor"
    mission: str = ""
    constraints: list[str] = Field(default_factory=list)
    kpis: list[str] = Field(default_factory=list)
    socraticAnswers: list[str] = Field(default_factory=list)
    # Optional: pre-fetched candidate principles from TC solver (for critic rule 2)
    candidate_principles: list[int] = Field(default_factory=list)
    # Optional: allow client to force a re-decompose even if critic would say no
    rd_manual: bool = False


class ContradictionDecomposeResponse(BaseModel):
    """Response containing critic decision + decomposed PCs."""
    triggered: bool = Field(..., description="L1 critic 是否觸發深挖")
    trigger_reason: str = Field(..., description="觸發或未觸發的理由")
    decomposed_pcs: list[DecomposedPC] = Field(default_factory=list)
    reasoning: str = Field(default="", description="LLM 產出整體分解策略說明（若有）")


# ---------------------------------------------------------------------------
# Auto-TRIZ v2 Analyst Methods (WBS 8.2.1–8.2.5)
# ---------------------------------------------------------------------------

# --- 8.2.1: Five Why Analysis ---

class FiveWhyRequest(BaseModel):
    """Input for 5-Why root-cause analysis."""
    project_id: str
    problem_statement: str
    context: str = ""


class WhyBecausePair(BaseModel):
    why: str
    because: str


class FiveWhyResponse(BaseModel):
    """5-Why analysis output with root causes and next step."""
    why_chain: list[WhyBecausePair]
    root_causes: list[str]
    recommended_next_step: str


# --- 8.2.2: KT Is/Is-Not Analysis ---

class KtIsIsNotRequest(BaseModel):
    """Input for Kepner-Tregoe Is/Is-Not analysis."""
    project_id: str
    problem_statement: str
    known_facts: list[str] = Field(default_factory=list)


class IsIsNotDimension(BaseModel):
    dimension: str  # what / where / when / extent
    is_value: str
    is_not_value: str


class KtIsIsNotResponse(BaseModel):
    """KT Is/Is-Not matrix output."""
    is_matrix: list[IsIsNotDimension]
    distinctions: list[str]
    hypotheses: list[str]


# --- 8.2.3: Function Analysis ---

class FunctionAnalysisRequest(BaseModel):
    """Input for TRIZ Function Analysis (FA)."""
    project_id: str
    system_description: str
    components: list[str]


class ComponentInteraction(BaseModel):
    from_component: str = Field(validation_alias="from")
    to_component: str = Field(validation_alias="to")
    action: str
    type: str  # useful / harmful / insufficient


class SfDiagnosis(BaseModel):
    S1: str = ""
    S2: str = ""
    F: str = ""
    state: str = "unknown"  # incomplete / effective / harmful / insufficient / unknown
    problem_summary: str = ""


class FunctionAnalysisResponse(BaseModel):
    """Function Analysis output — component interactions + SF diagnosis."""
    component_interactions: list[ComponentInteraction]
    sf_diagnosis: SfDiagnosis
    subsystem_boundary: dict = Field(default_factory=dict)


# --- 8.2.4: OZ-OT Analysis ---

class OzOtAnalysisRequest(BaseModel):
    """Input for TRIZ OZ-OT-Px analysis."""
    project_id: str
    contradiction_id: str
    tc_description: str
    improving_param: int | None = None
    worsening_param: int | None = None


class OzOtAnalysisResponse(BaseModel):
    """OZ-OT-Px analysis output."""
    oz_zone: str
    ot_time: str
    px_variable: str
    separation_hints: list[str] = Field(default_factory=list)


# --- 8.2.5: Entry Grading ---

class EntryGradingRequest(BaseModel):
    """Input for problem entry-level grading."""
    project_id: str
    problem_description: str
    available_data: dict = Field(default_factory=dict)


class EntryGradingResponse(BaseModel):
    """Entry grading output — complexity level + recommended steps."""
    level: Literal["A", "B", "C"]
    reasoning: str
    recommended_steps: list[str] = Field(default_factory=list)
