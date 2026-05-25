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
    socraticAnswers: list[str] = Field(default_factory=list)


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
    # Auto-TRIZ v2 (WBS 8.3.3): optional FA + OZ-OT context for enriched prompts
    fa_context: dict | None = None   # FunctionAnalysisResponse dict (optional)
    oz_ot_context: dict | None = None  # OzOtAnalysisResponse dict (optional)


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
    # Explore stage always emits TC; null = cannot map to TC.
    type: Literal["TC"] | None = "TC"
    confidence: float = Field(ge=0, le=1, default=0.7)
    # LLM explanation when type is None (cannot map to TC).
    rationale: str | None = None


# ---------------------------------------------------------------------------
# 3-Stage TC Pipeline — intermediate models (internal only, not API-exposed)
# ---------------------------------------------------------------------------

class KpiPriority(BaseModel):
    """Stage 1 sub-model: a single KPI with severity classification."""
    kpi: str
    severity: Literal["hard", "soft"] = "soft"
    failure_mode: str = ""


class InferredAction(BaseModel):
    """Stage 1 sub-model: an engineering action inferred from KPIs/constraints."""
    action: str
    driven_by: str = ""
    likely_side_effects: list[str] = Field(default_factory=list)


class ProblemFrame(BaseModel):
    """Stage 1 output: structured engineering problem framing."""
    system_boundary: str = ""
    kpi_priorities: list[KpiPriority] = Field(default_factory=list)
    inferred_engineering_actions: list[InferredAction] = Field(default_factory=list)
    critical_constraints: list[str] = Field(default_factory=list)
    design_tensions: list[str] = Field(default_factory=list)


class CandidateTC(BaseModel):
    """Stage 2 output: a single candidate TC before ranking."""
    engineering_statement: str
    type: Literal["TC"] | None = "TC"
    confidence: float = Field(ge=0, le=1, default=0.7)
    rationale: str | None = None
    improving_param: int | None = None
    worsening_param: int | None = None
    source_action: str = ""
    linked_kpis: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Multi-TC Identification (POST /contradictions/identify-multi)
# ---------------------------------------------------------------------------

class MultiTcIdentifyRequest(BaseModel):
    """Identify multiple TCs from project context in one call."""
    project_id: str
    mission: str = ""
    constraints: list[str] = Field(default_factory=list)
    kpis: list[str] = Field(default_factory=list)
    socraticAnswers: list[str] = Field(default_factory=list)
    # 已有的 contradiction descriptions，供 LLM 避免重複
    existing_descriptions: list[str] = Field(default_factory=list)


class IdentifiedTC(BaseModel):
    """A single TC item within the multi-TC response."""
    engineering_statement: str
    type: Literal["TC"] | None = "TC"
    confidence: float = Field(ge=0, le=1, default=0.7)
    rationale: str | None = None
    improving_param: int | None = None
    worsening_param: int | None = None
    # --- 3-Stage Pipeline new fields ---
    linked_kpis: list[str] = Field(default_factory=list)
    why_selected: str | None = None
    priority: int | None = None


class MultiTcIdentifyResponse(BaseModel):
    """Response containing multiple identified TCs."""
    items: list[IdentifiedTC] = Field(default_factory=list)


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
    # v8: optional concept architecture pack input for 3-step engineering spec pipeline.
    # When present, suggest_subsystems uses the pack's subsystems as seed for
    # structure expansion → AI spec generation → source strengthening.
    concept_pack: "ConceptArchitecturePack | None" = Field(
        default=None,
        description=(
            "Concept Architecture Pack from the concept step. When provided, "
            "the pipeline expands concept-level subsystems into full engineering "
            "spec drafts with DraftValue provenance."
        ),
    )


# ---- Spatial Grounding (Discovery Mode) ----------------------------------
# These types let Interface Contracts carry structured dimensional estimates
# alongside the legacy free-text fields. They are OPTIONAL — RD discovery mode
# never requires upfront spatial budgets.

GeometryArchetype = Literal[
    "cube", "cylinder", "disc", "l_bracket", "sphere", "flat_plate", "custom",
]
"""Coarse shape tag chosen by the LLM to drive proxy-geometry selection."""

LodHint = Literal["concept", "envelope", "preliminary", "detailed"]
"""Level-of-detail hint (LOD 0–3) indicating how trustworthy spatial data is
for downstream CAD consumption.  Auto-derived from *confidence* when not set
explicitly by the LLM or caller."""


COORDINATE_CONVENTION = (
    "Right-hand coordinate system: X=right, Y=up, Z=front. "
    "Origin at product geometric center. All dimensions in mm."
)
"""Global coordinate convention string for prompt injection and documentation."""


class BBox(BaseModel):
    """Axis-aligned bounding box in millimeters.

    Coordinate convention (matches USD/OpenGL right-hand rule):
      - Origin: product-level geometric center (0, 0, 0)
      - X: right (+) / left (-)
      - Y: up (+) / down (-)
      - Z: front (+) / back (-)
      - All values in millimeters

    ``origin_mm`` is the center of THIS bbox in the global frame.
    ``anchor`` names the reference point semantically (e.g. "BB_center").
    """
    x_mm: float
    y_mm: float
    z_mm: float
    origin_mm: tuple[float, float, float] = (0.0, 0.0, 0.0)
    anchor: str = ""  # e.g. "BB_center" / "downtube_top" — frame-relative anchor name
    geometry_archetype: GeometryArchetype | None = None


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
    lod_hint: LodHint = "concept"
    geometry_is_placeholder: bool = True
    rationale: str = ""                  # one-line justification when llm_estimate

    @model_validator(mode="after")
    def _derive_lod_from_confidence(self) -> "SpatialEstimate":
        """Auto-upgrade *lod_hint* when the caller leaves it at the default
        ``"concept"`` but supplies a higher-fidelity *confidence*.

        * ``rd_confirmed`` → ``preliminary`` (LOD 2)
        * ``library``      → ``envelope``    (LOD 1)
        * ``estimate``     → keep ``concept`` (LOD 0)
        """
        if self.lod_hint == "concept":
            _CONF_TO_LOD: dict[str, LodHint] = {
                "rd_confirmed": "preliminary",
                "library": "envelope",
            }
            derived = _CONF_TO_LOD.get(self.confidence)
            if derived is not None:
                object.__setattr__(self, "lod_hint", derived)
        return self

    @model_validator(mode="after")
    def _derive_placeholder_flag(self) -> "SpatialEstimate":
        """Auto-clear *geometry_is_placeholder* when *reference_source*
        indicates real-world data (learned component, RD override, or web).

        Recognised prefixes that flip the flag to ``False``:
        ``learned:``, ``rd_override:``, ``web:``.
        """
        _REAL_PREFIXES = ("learned:", "rd_override:", "web:")
        if self.reference_source and self.reference_source.startswith(_REAL_PREFIXES):
            object.__setattr__(self, "geometry_is_placeholder", False)
        return self


class PortLocation(BaseModel):
    """3D port location for a physical interface connection point.

    Used by CAD/harness-routing tools to place connectors, pipe stubs, or
    cable entry points on each module boundary.
    """
    position_mm: tuple[float, float, float] = Field(
        default=(0.0, 0.0, 0.0),
        description="Port center position in global coordinate frame (mm).",
    )
    normal: tuple[float, float, float] = Field(
        default=(0.0, 0.0, 1.0),
        description="Outward-facing normal vector of the port face.",
    )
    port_type: str = Field(
        default="",
        description="Port type hint: 'mechanical', 'electrical', 'thermal', 'fluid'.",
    )


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
    # Optional structured port locations for CAD pipe/harness routing.
    ports: list[PortLocation] = Field(default_factory=list)
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
    # ── Traceability fields from ConceptSubsystem ──────────────────────────
    concept_origin_code: str | None = Field(
        default=None,
        description=(
            "原始 ConceptSubsystem.code（如 'A1'）。"
            "僅系統層級節點有此欄位，子模組/元件為 None。"
        ),
    )
    mapped_kpis: list[str] = Field(
        default_factory=list,
        description="從 ConceptSubsystem 傳遞下來的 KPI IDs",
    )


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
# USDA Export (POST /export/usda)
# ---------------------------------------------------------------------------

class UsdaExportRequest(BaseModel):
    """Request body for USDA scene export."""
    project_id: str
    project_name: str = ""
    subsystems: list["SuggestedSubsystem"] = Field(
        default_factory=list,
        description="Full subsystem tree (system→module→component).",
    )
    drafts: list["EngineeringSpecDraft"] = Field(
        default_factory=list,
        description="Engineering spec drafts, indexed by subsystem_code.",
    )
    package_map: "PackageMap | None" = Field(
        default=None,
        description="Optional PackageMap for clash information.",
    )
    include_proxy_geometry: bool = Field(
        default=True,
        description="When True, emit visual proxy geometry (Cube/Cylinder) for nodes with spatial data.",
    )
    proxy_geometry_mode: Literal["none", "cube", "inferred"] = Field(
        default="inferred",
        description=(
            "Geometry mode: 'none' = no proxy, 'cube' = always Cube, "
            "'inferred' = Cylinder for shaft/housing keywords, Cube otherwise."
        ),
    )


class UsdaExportResponse(BaseModel):
    """USDA export result."""
    content: str = Field(description="Complete .usda text content.")
    filename: str = Field(description="Suggested download filename.")


class NodeUsdaLlmRequest(BaseModel):
    """Request body for per-node LLM-based USDA generation."""

    node_name: str = Field(..., description="節點名稱，如 Drive System")
    node_level: Literal["system", "module", "component"]

    # 該節點的 context — 前端從 SpecTreeNode 組裝
    node_description: str = Field(
        ...,
        description="節點 reason + 所有子節點 reason 的組合文字描述",
    )
    specs_summary: list[dict] = Field(
        default_factory=list,
        description="該節點含子節點的 DraftValue specs 摘要 — field_name, value, unit, category",
    )
    interface_contracts: dict[str, dict] = Field(
        default_factory=dict,
        description="該節點的 interface_contracts 簡化版",
    )
    children_names: list[str] = Field(
        default_factory=list,
        description="子節點名稱列表，用於 USDA 結構生成",
    )


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
# Su-Field derivation from a confirmed TC (Plan B — hierarchical TC tree)
# ---------------------------------------------------------------------------

class ContradictionDeriveSFRequest(BaseModel):
    """Derive a child Su-Field model from a parent TC at Explore stage."""
    project_id: str
    contradiction_id: str
    engineering_statement: str
    improving_param: int = Field(..., ge=1, le=39)
    worsening_param: int = Field(..., ge=1, le=39)
    natural_description: str = ""


class ContradictionDeriveSFResponse(BaseModel):
    """Su-Field derivation result — None-safe fields for graceful degradation."""
    derived: bool = Field(..., description="Whether SF derivation succeeded")
    sf_substance_1: str | None = None
    sf_substance_2: str | None = None
    sf_field: str | None = None
    sf_interaction: str | None = None
    sf_completeness: str | None = None


# ---------------------------------------------------------------------------
# Step 5a-D: Directed TRIZ Solver — Direction-centric flow
#
# Replaces the layered drill-down (L1/L2/L3) paradigm with a simpler
# "solve all three tools → cluster by implementation direction → pick best"
# approach. Ref: user flow specification §二–§四.
# ---------------------------------------------------------------------------

class DirectionSolution(BaseModel):
    """一條從 TC/PC/SF 任一路徑產出的解法。"""
    path: Literal["TC", "PC", "SF"]
    principle_number: int | None = None
    principle_name: str = ""
    suggestion: str
    separation_principle: str = ""
    affected_modules: list[str] = Field(default_factory=list)
    secondary_contradictions: list[str] = Field(default_factory=list)


class DirectionGroup(BaseModel):
    """一個實現方向（由多條解法歸群）。"""
    direction_id: str = ""              # e.g. "DIR-1"
    direction_name: str = ""            # e.g. "折疊/可變形"
    direction_summary: str = ""         # LLM 產出的方向摘要
    solutions: list[DirectionSolution] = Field(default_factory=list)
    tc_count: int = 0
    pc_count: int = 0
    sf_count: int = 0


class DirectionScore(BaseModel):
    """一個方向的評分結果。"""
    direction_id: str = ""
    tool_support: int = 0               # TC票 + PC票 + SF票
    feasibility: float = 0.0            # 0~10
    cost_difficulty: float = 0.0        # 0~10
    coverage_score: float = 0.0         # 0~10  (Step H coverage audit)
    weighted_total: float = 0.0         # 加權總分
    score_rationale: str = ""


# ---------------------------------------------------------------------------
# Brief Context Snapshot (Step H-1 / H-2 input)
# ---------------------------------------------------------------------------
# Frozen, project-level upstream context fed into _decompose_contradiction
# and _audit_coverage so the LLM judges each solution direction against the
# *original* mission / constraints / KPIs / socratic insights / CLD risks,
# not just the contradiction string in isolation.
#
# Single source of truth for the "回脈絡驗證" pipeline. Built from
# Supabase tables: briefs / constraints / kpis / socratic_questions /
# cld_nodes / cld_edges by app.services.brief_context.fetch_brief_context.
#
# All fields default to empty so partial/missing project data does not
# break the pipeline — downstream prompts already render "(未提供)"
# fallbacks for empty blocks.

class BriefConstraint(BaseModel):
    """Single hard/soft constraint from the brief stage."""
    code: str = ""          # e.g. "C1"
    description: str = ""
    type: str = "hard"      # "hard" | "soft"
    feasibility: str = "unknown"


class BriefKpi(BaseModel):
    """Single KPI with optional current value for progress-aware audit."""
    name: str = ""
    target_value: str = ""
    unit: str = ""
    current_value: str = ""
    current_status: str = "unknown"   # on_track / at_risk / off_track / unknown


class SocraticInsight(BaseModel):
    """One answered Socratic Q&A pair distilled for context injection.

    Only questions with non-empty answers reach this list; tagged
    assumptions are surfaced so the LLM can flag direction dependence
    on the same assumption.
    """
    category: str = ""
    question: str = ""
    answer: str = ""
    is_assumption: bool = False


class CldNodeSummary(BaseModel):
    """One CLD variable. `is_leverage=True` flags a breakpoint candidate."""
    label: str = ""
    node_type: str = "variable"
    is_leverage: bool = False


class CldEdgeSummary(BaseModel):
    """One causal arrow (from → to) with polarity."""
    from_label: str = ""
    to_label: str = ""
    polarity: str = "+"     # "+" reinforcing / "-" balancing


class CldSummary(BaseModel):
    """Flattened CLD view used as audit context."""
    nodes: list[CldNodeSummary] = Field(default_factory=list)
    edges: list[CldEdgeSummary] = Field(default_factory=list)
    leverage_points: list[str] = Field(default_factory=list)  # node labels


class BriefContextSnapshot(BaseModel):
    """Project-level upstream context for context-aware coverage audit.

    Built once per /triz/solve-directed call by `fetch_brief_context`,
    passed as a single object down to Step H-1 (decompose) and Step H-2
    (audit) so the same context surface is visible to both stages.

    Any field may be empty — the pipeline falls back to "(未提供)" in
    prompts so the LLM is told explicitly when a context channel is
    missing rather than silently degrading.
    """
    project_id: str = ""
    mission: str = ""
    constraints: list[BriefConstraint] = Field(default_factory=list)
    kpis: list[BriefKpi] = Field(default_factory=list)
    socratic_summary: list[SocraticInsight] = Field(default_factory=list)
    cld_summary: CldSummary = Field(default_factory=CldSummary)


# ---------------------------------------------------------------------------
# Step H / Step I: Resolution Coverage models
# ---------------------------------------------------------------------------

# Resolution status: 5-state semantic verdict for whether a direction
# actually resolves its contradiction *in the original problem context*.
# Pure rendering label is the FE concern — backend uses this for sort
# de-prioritisation (see _apply_coverage_to_scores).
ResolutionStatus = Literal[
    "directly_resolves",        # improves desired + suppresses undesired + within boundary
    "partially_resolves",       # only one of the two sides; or symptom-only
    "conditionally_resolves",   # theoretically yes IF key_assumptions hold
    "does_not_resolve",         # weak link to contradiction; no real fix
    "unclear",                  # not enough info to decide; do not over-confidently judge
]

# Layer the direction touches in the causal chain. Surfaced so RD can
# spot "all top picks are symptom-level" failure modes early.
AddressesLayer = Literal[
    "root_cause",
    "mechanism",
    "symptom",
    "unclear",
]

# SubRequirement kind: maps to the user's Step 1 contradiction split.
# `mission_outcome` is an extra kind for KPI-level goals that are not
# inside the contradiction text but must still be satisfied by any
# direction that claims to "really" resolve it.
SubRequirementKind = Literal[
    "desired_improvement",
    "undesired_effect",
    "boundary_condition",
    "mission_outcome",
]


class SubRequirement(BaseModel):
    """矛盾分解出的單一子需求 (Step H-1, context-aware).

    v2 fields (kind, source_ref) are additive — legacy payloads without
    them deserialize to safe defaults so this model stays backward
    compatible with rows persisted before the context-aware refactor.

    v3 fields (raw_text, candidate_id, relevance_score) added by Phase 1
    (S0 演算法為骨重構) for traceability back to the enumerated candidate
    pool. They default to empty so older rows stay valid.
    """
    id: str = ""            # e.g. "SR-1"
    domain: str = ""        # e.g. "thermal", "electromagnetic", "mechanical"
    description: str = ""
    why_necessary: str = ""
    # --- v2 additions (context-aware decomposition) ---
    kind: SubRequirementKind = "desired_improvement"
    source_ref: str = ""    # e.g. "mission" | "constraint:C1" | "kpi:K2" |
                            #      "contradiction" | "socratic" | "cld"
    # --- v3 additions (S0 演算法為骨重構) ---
    raw_text: str = ""              # 原始 candidate.raw_text 保留為 ground truth
    candidate_id: int = 0           # 對應 _enumerate_sr_candidates 的 candidate_id
    relevance_score: int = 0        # LLM 給的 0-3 相關性分


class SrWeakWarning(BaseModel):
    """A candidate with score==1 — surfaced as ⚠️ tooltip in UI, not as a proper SR."""
    candidate_id: int = 0
    kind: SubRequirementKind = "desired_improvement"
    source_ref: str = ""
    raw_text: str = ""
    relevance_score: int = 1
    why_weak: str = ""


# Per-SR verdict — UI-friendly 5-state label describing what the
# direction does for ONE sub-requirement. Derived primarily from the
# LLM's coverage_matrix score, then upgraded/downgraded by key
# assumptions / mission violations / unresolved flags so the UI does
# not need to cross-reference three sections to understand a row.
#
#   "directly_solves"  — score=2, no assumption blocks this SR
#   "partially_solves" — score=1, partial / indirect support
#   "needs_verify"     — score=2 but an unverified assumption gates it
#   "violates"         — direction directly breaks this SR (e.g. mass
#                         cap broken). Emitted when mission_violations
#                         enumerates this SR.
#   "not_addressed"    — score=0, the direction does nothing for this
#   "unclear"          — no audit info available (legacy fallback)
PerSrVerdict = Literal[
    "directly_solves",
    "partially_solves",
    "needs_verify",
    "violates",
    "not_addressed",
    "unclear",
]


class CoverageEntry(BaseModel):
    """單一 (方向, 子需求) 配對的覆蓋評分。

    v2 fields (verdict / verdict_zh) carry the human-friendly per-SR
    state for the new SR-grouped UI. Legacy rows lacking these fields
    fall back to ``verdict="unclear"`` and the frontend re-derives a
    label from ``score`` + audit-level assumptions.
    """
    sub_requirement_id: str = ""
    score: int = 0          # 0 / 1 / 2
    rationale: str = ""
    # v2 additions for SR-grouped UI
    verdict: PerSrVerdict = "unclear"
    verdict_zh: str = ""    # single-sentence plain-language explanation


class DirectionCoverageAudit(BaseModel):
    """單一方向的覆蓋率審計結果 (Step H-2, context-aware).

    v2 fields express the 5-state verdict + boundary/CLD violations so
    the FE can render a meaningful status badge and so the ranker can
    push "does_not_resolve" / "unclear" to the bottom regardless of
    raw coverage_score. Legacy rows missing these fields parse with
    safe defaults (resolution_status="unclear").
    """
    direction_id: str = ""
    coverage_matrix: list[CoverageEntry] = Field(default_factory=list)
    coverage_score: float = 0.0   # 0.0–10.0
    unresolved_gaps: list[str] = Field(default_factory=list)
    # --- v2 additions (context-aware audit) ---
    resolution_status: ResolutionStatus = "unclear"
    key_assumptions: list[str] = Field(default_factory=list)
    # Required when resolution_status == "conditionally_resolves";
    # validator below auto-promotes that case if assumptions present.
    mission_violations: list[str] = Field(default_factory=list)
    # Lines like "violates constraint C2: total weight > 5kg"
    cld_side_effects: list[str] = Field(default_factory=list)
    # Lines like "amplifies feedback loop A→B→A via shared node X"
    addresses_layer: AddressesLayer = "unclear"
    gap_summary: str = ""

    @model_validator(mode="after")
    def _promote_conditional_when_assumptions_present(self):
        """If RD-overridden audit lists key_assumptions but left status
        as 'directly_resolves', downgrade to 'conditionally_resolves'.

        Prevents the common LLM tic of claiming full resolution while
        also enumerating prerequisites — those are conditions, not
        guarantees.
        """
        if (
            self.resolution_status == "directly_resolves"
            and len(self.key_assumptions) > 0
        ):
            self.resolution_status = "conditionally_resolves"
        return self


class CombinedDirection(BaseModel):
    """互補方向組合結果 (Step I)。"""
    selected_direction_ids: list[str] = Field(default_factory=list)
    total_coverage_score: float = 0.0
    coverage_matrix: list[dict] = Field(default_factory=list)
    unresolved_gaps: list[str] = Field(default_factory=list)
    synergies: str = ""
    potential_conflicts: str = ""
    integration_strategy: str = ""


# ---------------------------------------------------------------------------
# Phase 2 — DecisionCard：每條 direction 1 張，給 RD 選購用
# ---------------------------------------------------------------------------
# 設計理念見 plans/triz-redesign.md §3。產出時機：solve_triz_directed
# 跑完 all_directions 之後（在 _persist_directed_solution 之前），對每條
# direction 跑一輪輕量 LLM call 產出。
#
# 對使用者的承諾：「5 秒判斷不適合 / 30 秒判斷值得細看 / 看到組合衝突提示」。
# 真正的工程審判由整併後的 VerdictCard (Phase 3) 提供。

ContradictionFace = Literal[
    "improving_side",   # 主要解決矛盾的 improving 那一面
    "worsening_side",   # 主要抑制 worsening 那一面
    "both",             # 同時解到兩面
    "side_effect",      # 主要在處理次生副作用
]

EffortLevel = Literal["low", "medium", "high"]


class DecisionCardQuickTags(BaseModel):
    """採用成本 / 風險速覽。"""
    effort: EffortLevel = "medium"
    evidence_level: Literal["E0", "E1", "E2", "E3", "E4"] = "E2"
    affects_modules: list[str] = Field(default_factory=list)


class DecisionCardCombinationHints(BaseModel):
    """跨矛盾整併相容性提示（服務後續整併工作流的關鍵欄位）。"""
    synergy_with: list[str] = Field(default_factory=list)
    conflict_with: list[str] = Field(default_factory=list)
    best_paired_with: list[str] = Field(default_factory=list)


class DecisionCard(BaseModel):
    """每條 TRIZ direction 產出 1 張，給 RD 選購用。

    5 欄結構，對應 plans/triz-redesign.md §3.1：
      1. one_liner            — ≤40 字一句話機制
      2. contradiction_face   — 解矛盾的哪一面 + 中文 emoji badge
      3. resolution_*         — 對「此矛盾」的解決度（沿用 5-state）
      4. quick_tags           — 採用成本 / 證據 / 受影響模組
      5. combination_hints    — 跨矛盾整併線索（synergy / conflict / best_pair）
    """
    direction_id: str
    direction_name: str

    # 第 1 欄
    one_liner: str = ""

    # 第 2 欄
    contradiction_face: ContradictionFace = "both"
    face_badge: str = ""   # 例如 "🌡️ 降熱不擴體積"

    # 第 3 欄 — 沿用 ResolutionStatus（已有定義）
    resolution_status: ResolutionStatus = "unclear"
    resolution_one_line: str = ""

    # 第 4 欄
    quick_tags: DecisionCardQuickTags = Field(default_factory=DecisionCardQuickTags)

    # 第 5 欄
    combination_hints: DecisionCardCombinationHints = Field(
        default_factory=DecisionCardCombinationHints
    )

    # 中介資訊 — RD 勾選狀態（前端會直接 mutate 這個欄位）
    picked: bool = False


class ContradictionDirectionResult(BaseModel):
    """單一矛盾的完整方向分析結果（§二 輸出）。"""
    contradiction_id: str
    natural_description: str = ""
    severity: Literal["fatal", "major", "minor", "unknown"] = "unknown"
    all_solutions: list[DirectionSolution] = Field(default_factory=list)
    all_directions: list[DirectionGroup] = Field(default_factory=list)
    scored_directions: list[DirectionScore] = Field(default_factory=list)
    top1: DirectionGroup | None = None
    top2: DirectionGroup | None = None
    top1_score: DirectionScore | None = None
    top2_score: DirectionScore | None = None
    # Step H/I: Resolution Coverage
    sub_requirements: list[SubRequirement] = Field(default_factory=list)
    sr_weak_warnings: list["SrWeakWarning"] = Field(default_factory=list)
    coverage_audits: list[DirectionCoverageAudit] = Field(default_factory=list)
    combined_direction: CombinedDirection | None = None
    # Phase 2: DecisionCard per direction（每條 direction 1 張）
    decision_cards: list[DecisionCard] = Field(default_factory=list)


# ---- Conflict type enum (locked vocabulary for compat check) ----
# "none" is valid for the compatible case so every pair carries a tag,
# which keeps FE rendering logic uniform (no null-branch).
ConflictType = Literal[
    "physical_state",
    "intervention_clash",
    "module_overlap",
    "secondary_loop",
    "none",
]

# ---- Structured conflict-resolution suggestion types ----
ConflictSuggestionType = Literal[
    "relax_constraint",
    "hybrid",
    "rd_manual_choice",
    "architectural_reset",
]
ConflictSuggestionCost = Literal["low", "medium", "high"]


class CompatibilityResult(BaseModel):
    """兩個方向之間的相容性檢查結果。

    WBS v2: adds `conflict_type` so FE / reports can group and visualise
    conflicts by kind. Default "none" keeps construction ergonomic for
    the compatible path.
    """
    direction_a: str = ""
    direction_b: str = ""
    contradiction_a_id: str = ""
    contradiction_b_id: str = ""
    compatible: bool = True
    reason: str = ""
    conflict_type: ConflictType = "none"

    @model_validator(mode="before")
    @classmethod
    def _coerce_legacy(cls, values):
        """Backfill `conflict_type` for rows persisted before this field existed.

        Older `directed_triz_solutions` rows carry {compatible, reason} but no
        conflict_type. Deriving on read keeps analytics clean without a DB
        migration: compatible → "none", otherwise "intervention_clash" as a
        neutral placeholder until RD re-runs the check.
        """
        if isinstance(values, dict) and "conflict_type" not in values:
            values["conflict_type"] = (
                "none" if values.get("compatible", True) else "intervention_clash"
            )
        return values


class ConflictSuggestion(BaseModel):
    """One structured suggestion the LLM emits when directions conflict.

    Replaces the old `list[str]` shape. Each suggestion carries enough
    metadata that FE can render decision-oriented UI (filter by type,
    sort by cost, highlight which contradictions it targets).
    """
    type: ConflictSuggestionType = "rd_manual_choice"
    target_contradictions: list[str] = Field(default_factory=list)
    description: str = ""
    cost: ConflictSuggestionCost = "medium"


class ConflictReport(BaseModel):
    """衝突報告。

    WBS v2: `suggestions` upgraded from `list[str]` to `list[ConflictSuggestion]`.
    A validator accepts both shapes so persisted rows / older clients do
    not break — plain strings are coerced to a minimal ConflictSuggestion
    with type="rd_manual_choice" and cost="medium".
    """
    conflicting_pairs: list[CompatibilityResult] = Field(default_factory=list)
    suggestions: list[ConflictSuggestion] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _coerce_legacy_suggestions(cls, values):
        """Back-compat for rows where suggestions was stored as list[str]."""
        if not isinstance(values, dict):
            return values
        raw = values.get("suggestions")
        if not isinstance(raw, list):
            return values
        coerced: list = []
        for item in raw:
            if isinstance(item, str):
                coerced.append({
                    "type": "rd_manual_choice",
                    "target_contradictions": [],
                    "description": item,
                    "cost": "medium",
                })
            else:
                coerced.append(item)
        values["suggestions"] = coerced
        return values


class ConsolidationResult(BaseModel):
    """跨矛盾整併結果(§三 輸出)。

    Phase 3 bugfix: 加入 `was_user_picked` 區分「RD 直接勾選」與「系統 swap Top2」。

    PR2-Lite (語意 3 — 分數損失最小化候選池演算法)：
      - 使用者在 DecisionCard 勾的多個方向 = 該矛盾的「候選池」（依分數降冪）
      - 演算法從各池首位開始，衝突時換池內下一名（單條換、損失最小者優先）
      - `adopted_directions[cid]` 仍只記**一個**最終代表方向
      - `candidate_pools[cid]` 是這條矛盾的整池（含未被採用的 fallback）
      - `exhausted_contradictions` 是「候選池已用盡仍卡住」的矛盾 ID list
      - `total_rounds` 是演算法跑了幾輪（含初始檢查）

    Status 語意（重要）：
      - "compatible"          → 採用方向（不論是 Top1 還是 RD 勾的）兩兩相容，無需 swap。
      - "resolved_with_swap"  → 「至少一條非 pinned 矛盾被系統從 Top1 → Top2 swap」
                                才會回此 status。RD 勾的方向「剛好不是 Top1」**不算**
                                swap，那是 user_picked。
      - "conflict"            → 衝突無法靠 swap 解掉。
    """
    status: Literal["compatible", "resolved_with_swap", "conflict"] = "compatible"
    adopted_directions: dict[str, DirectionGroup] = Field(default_factory=dict)
    conflict_report: ConflictReport | None = None
    integration_advice: str = ""
    # Phase 3 bugfix: contradiction_id → direction_id where RD explicitly picked it
    # (vs system-chosen Top1 or system-swapped Top2). Frontend uses this to label
    # the badge as「使用您勾選的方向」rather than「Top2 替換」.
    was_user_picked: dict[str, str] = Field(default_factory=dict)
    # PR2-Lite 新增欄位 ────────────────────────────────────────────
    # contradiction_id → list[DirectionGroup]（依分數降冪），可選；
    # 舊資料 / 單矛盾 fallback / 還沒勾選的場景可能為 {}。
    candidate_pools: dict[str, list[DirectionGroup]] = Field(default_factory=dict)
    # 演算法跑完後仍卡住、池已用盡的矛盾 IDs。conflict 時才會有值；
    # 用於前端 PR1-8 conflict UI 的「卡點分析」區塊。
    exhausted_contradictions: list[str] = Field(default_factory=list)
    # 演算法執行的輪次數（含初始 LLM 檢查）。0 = 沒跑演算法（如單矛盾 fallback）。
    total_rounds: int = 0


class SolveDirectedRequest(BaseModel):
    """POST /triz/solve-directed — 單一矛盾方向導向求解。

    Context-aware refactor: the request may optionally carry a
    pre-built `BriefContextSnapshot`. When omitted (None), the
    pipeline lazily calls `fetch_brief_context(project_id)` so the
    same /triz/solve-directed contract works for both:
      • production UI flow (loads project context from Supabase)
      • harness / unit tests (injects synthetic context directly)
    """
    project_id: str
    contradiction_id: str
    natural_description: str
    severity: Literal["fatal", "major", "minor", "unknown"] = "unknown"
    improving_param: int | None = None
    worsening_param: int | None = None
    # Optional override for tests / harness. Production callers may omit.
    brief_context: BriefContextSnapshot | None = None


class SolveDirectedResponse(BaseModel):
    """POST /triz/solve-directed — 回傳。"""
    result: ContradictionDirectionResult


# ---------------------------------------------------------------------------
# Phase 3 — Picked selections + intra-contradiction compatibility
# ---------------------------------------------------------------------------
# 設計理念見 plans/triz-redesign.md §A：使用者可在同一條矛盾下勾選多個方向，
# 我們對同矛盾多選跑兩兩相容性檢查，再用 max independent set 推薦最大相容子集；
# 跨矛盾整併則保留勾選方向，僅 swap「未被勾的 Top1」以解衝突。


class PickedSelection(BaseModel):
    """前端傳來的單一矛盾使用者勾選結果。

    `picked_direction_ids` 來自 DecisionCard checkbox。為避免 LLM 兩兩比對爆炸，
    後端在處理時對單一矛盾的多選數量上限 = 6（超過會回 422）。
    """
    contradiction_id: str
    picked_direction_ids: list[str] = Field(default_factory=list)

    @field_validator("picked_direction_ids")
    @classmethod
    def _enforce_max_six(cls, v: list[str]) -> list[str]:
        if len(v) > 6:
            raise ValueError(
                f"同一條矛盾最多可勾選 6 個方向；目前勾了 {len(v)} 個，請收斂到 6 個以內"
            )
        return v


class IntraContradictionCompatibility(BaseModel):
    """同一條矛盾下多選方向的相容性報告。

    pairwise_results: N×(N-1)/2 個兩兩比較
    max_compatible_subsets: 排序後的最大相容子集，最大優先 (用 max independent set 找出)
    has_conflict: 是否存在 ≥1 對衝突 pair
    recommendation: ≤80 字推薦組合一句話
    """
    contradiction_id: str
    picked_direction_ids: list[str] = Field(default_factory=list)
    pairwise_results: list[CompatibilityResult] = Field(default_factory=list)
    max_compatible_subsets: list[list[str]] = Field(default_factory=list)
    has_conflict: bool = False
    recommendation: str = ""


# ---------------------------------------------------------------------------
# Phase 3 — EngineeringVerdictCard Q1–Q8
# ---------------------------------------------------------------------------
# 設計理念見 plans/triz-redesign.md §4。對整併方案做 8 節完整工程審判：
#   Q1 contradiction_face_per_picked  每條被勾的 direction 解的是哪一面
#   Q2 mechanism_trace                整體機制因果鏈
#   Q3 feasibility_matrix             逐軸可行性判定
#   Q4 side_effects_via_cld           CLD multi-hop 副作用
#   Q5 coverage_completeness          對所有 SR 的涵蓋率
#   Q6 verification_plan              採用前必要驗證
#   Q7 duty_cycle_verdict             peak/continuous/startup/steady_state
#   Q8 boundary_collapse              ≥5 條失效條件


class ContradictionFacePerPicked(BaseModel):
    """Q1：每條被勾的方向解的是哪一面 (improving / worsening)。"""
    contradiction_id: str
    picked_direction_id: str
    picked_direction_name: str
    improving_side: Literal["yes", "partial", "no"] = "no"
    worsening_side: Literal["yes", "partial", "no"] = "no"
    introduces_new_side_effect: list[str] = Field(default_factory=list)


class MechanismTrace(BaseModel):
    """Q2：整併方案的整體機制因果鏈。"""
    technology_mix: list[Literal["control", "structure", "material", "topology"]] = Field(
        default_factory=list
    )
    delta_chain: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    evidence_level: Literal["E0", "E1", "E2", "E3", "E4"] = "E2"


class FeasibilityVerdict(BaseModel):
    """Q3：對單一軸 (constraint / KPI / mission spec) 的可行性判定。"""
    axis: str
    source_ref: str = ""
    verdict: Literal[
        "pass", "marginal_pass", "bottleneck",
        "not_addressed", "not_affected", "fail",
    ] = "not_addressed"
    rationale: str = ""
    quantitative_estimate: str = ""


class FeasibilityMatrix(BaseModel):
    """Q3：整併方案對每個 relevant axis 的逐項判定。"""
    axes: list[FeasibilityVerdict] = Field(default_factory=list)
    overall_verdict: Literal["pass", "marginal", "fail"] = "marginal"
    bottleneck_axes: list[str] = Field(default_factory=list)


class CldSideEffect(BaseModel):
    """Q4：沿 CLD edges traversal 找出的單條副作用鏈。"""
    cld_path: list[str] = Field(default_factory=list)
    polarity_chain: list[Literal["positive", "negative"]] = Field(default_factory=list)
    direction_impact: str = ""
    risk_level: Literal["low", "medium", "high"] = "low"


class SideEffectsViaCld(BaseModel):
    """Q4：CLD multi-hop side-effect paths + socratic counter warnings。"""
    paths: list[CldSideEffect] = Field(default_factory=list)
    socratic_warnings: list[str] = Field(default_factory=list)


class CoverageCompleteness(BaseModel):
    """Q5：整併方案對「所有 relevant SR + 弱相關」的涵蓋率。"""
    resolves_fully: list[str] = Field(default_factory=list)
    resolves_partial: list[str] = Field(default_factory=list)
    resolves_conditional: list[str] = Field(default_factory=list)
    does_not_address: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class VerificationStep(BaseModel):
    """Q6：採用前必須跑的驗證實驗單步驟。"""
    phase: Literal[
        "simulation", "bench", "thermal_soak", "prototype", "pilot", "field"
    ] = "simulation"
    test_description: str = ""
    expected_outcome: str = ""
    effort_hours: int = 0
    blocking: bool = False


class VerificationPlan(BaseModel):
    """Q6：完整驗證計畫，含對應 socratic.action 的引用。"""
    steps: list[VerificationStep] = Field(default_factory=list)
    socratic_action_links: list[str] = Field(default_factory=list)


class DutyCycleVerdict(BaseModel):
    """Q7：在 peak / continuous / startup / steady_state 四工況下成立度。"""
    peak: Literal["addressed", "marginal", "not_addressed"] = "not_addressed"
    continuous: Literal["addressed", "marginal", "not_addressed"] = "not_addressed"
    startup: Literal["addressed", "marginal", "not_addressed"] = "not_addressed"
    steady_state: Literal["addressed", "marginal", "not_addressed"] = "not_addressed"
    cycle_specific_notes: str = ""


class BoundaryCollapse(BaseModel):
    """Q8：失效條件 (至少 5 條)。"""
    condition: str
    failure_mode: str = ""
    severity: Literal["mild", "moderate", "catastrophic"] = "moderate"


class EngineeringVerdictCard(BaseModel):
    """對整併方案做 Q1–Q8 完整工程審判 (Phase 3 核心輸出)。"""
    project_id: str
    consolidation_id: str = ""

    contradiction_face_per_picked: list[ContradictionFacePerPicked] = Field(
        default_factory=list
    )
    mechanism_trace: MechanismTrace = Field(default_factory=MechanismTrace)
    feasibility_matrix: FeasibilityMatrix = Field(default_factory=FeasibilityMatrix)
    side_effects_via_cld: SideEffectsViaCld = Field(default_factory=SideEffectsViaCld)
    coverage_completeness: CoverageCompleteness = Field(default_factory=CoverageCompleteness)
    verification_plan: VerificationPlan = Field(default_factory=VerificationPlan)
    duty_cycle_verdict: DutyCycleVerdict = Field(default_factory=DutyCycleVerdict)
    boundary_collapse: list[BoundaryCollapse] = Field(default_factory=list)

    final_verdict: Literal[
        "adopt", "adopt_with_conditions", "needs_revision", "reject"
    ] = "needs_revision"
    final_rationale: str = ""
    confidence: float = 0.5


class ConsolidateRequest(BaseModel):
    """POST /triz/consolidate — 跨矛盾整併。

    Phase 3 新增 `picks` 欄位：若提供，後端會：
      1. 對每條 PickedSelection 做同矛盾相容性檢查 → intra_compatibility
      2. 跨矛盾整併時尊重勾選方向 (而非 fallback 到 Top1)
      3. _try_swap_to_top2 只能 swap 未被勾的方向
    若未提供 picks 則 fallback 到「每條矛盾用 top1」(向後相容)。
    """
    project_id: str
    results: list[ContradictionDirectionResult]
    picks: list[PickedSelection] = Field(default_factory=list)


class PersistenceOutcome(BaseModel):
    """Backend → FE persistence reporting (2026-05 hardening).

    `_persist_consolidation_result` 把寫 DB 的結果用此結構回報，避免「靜默吞掉
    例外」導致前端誤以為 DB 也寫成功、但其實只有 in-memory response 有完整資料、
    DB 卻是殘缺的 row（這正是 Phase 3 / PR2-Lite 欄位漏寫的根因）。

    狀態語意：
      - "ok"      → 完整 payload（含 verdict_card / was_user_picked /
                    intra_compatibility / candidate_pools / ...）寫入成功
      - "partial" → 偵測到 column 不存在（migration 未套用），退回 legacy
                    schema 只寫舊欄位。FE 必須警告使用者：重整後會丟失 Phase 3 資料
      - "failed"  → 寫入完全失敗（network / RLS / 其他）。FE 必須提示「請重試」
                    且**不能**把 in-memory response 寫進 React Query cache，
                    否則 stale 會被當成 truth、後續 refetch 又會被舊 DB row 覆蓋

    `columns_written` 紀錄實際寫入 DB 的欄位名單，用於 debug / observability。
    """
    status: Literal["ok", "partial", "failed"] = "ok"
    reason: str | None = None
    columns_written: list[str] = Field(default_factory=list)


class ConsolidateResponse(BaseModel):
    """POST /triz/consolidate — 回傳。"""
    consolidation: ConsolidationResult
    # Phase 3 新增
    intra_compatibility: list[IntraContradictionCompatibility] = Field(default_factory=list)
    verdict_card: EngineeringVerdictCard | None = None
    # 2026-05 hardening：DB persist 狀態回報。預設 "ok" 兼容老測試。
    persistence: PersistenceOutcome = Field(default_factory=PersistenceOutcome)


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


# ---------------------------------------------------------------------------
# Evidence Registry (WBS 8.4)
# ---------------------------------------------------------------------------

class RegisterClaimRequest(BaseModel):
    """Register a new evidence claim."""
    project_id: str
    claim_text: str
    claim_type: Literal["assumption", "hypothesis", "result", "constraint"]
    linked_artifact_id: str | None = None
    linked_artifact_type: str | None = None


class RegisterClaimResponse(BaseModel):
    """Registered claim record."""
    id: str
    project_id: str
    claim_text: str
    claim_type: str
    status: str = "unverified"
    verification_sources: list = Field(default_factory=list)
    confidence_score: float = 0.0
    linked_artifact_id: str | None = None
    linked_artifact_type: str | None = None


class VerifyClaimRequest(BaseModel):
    """Verify / update a claim's status."""
    verification_source: dict
    new_status: Literal["unverified", "verified", "refuted", "partial"]
    confidence_score: float | None = Field(default=None, ge=0, le=1)


class VerifyClaimResponse(BaseModel):
    """Updated claim record after verification."""
    id: str
    status: str
    verification_sources: list = Field(default_factory=list)
    confidence_score: float | None = None
    updated_at: str | None = None


class ClaimTypeCoverage(BaseModel):
    """Per-type coverage breakdown."""
    total: int = 0
    verified: int = 0
    refuted: int = 0
    partial: int = 0
    unverified: int = 0


class CoverageResponse(BaseModel):
    """Project-level evidence coverage statistics."""
    total_claims: int = 0
    verified_count: int = 0
    refuted_count: int = 0
    partial_count: int = 0
    unverified_count: int = 0
    coverage_ratio: float = 0.0
    by_type: dict[str, ClaimTypeCoverage] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Auto-TRIZ v2 — SIM Matrix (WBS 8.3.1)
# ---------------------------------------------------------------------------

class SIMMatrixRequest(BaseModel):
    """Evaluate solution interactions across multiple contradictions."""
    project_id: str
    contradiction_ids: list[str] = Field(..., min_length=2)
    solutions_per_contradiction: dict[str, list[str]] = Field(
        ...,
        description="Mapping contradiction_id → list of solution summary strings",
    )


class SolutionInteraction(BaseModel):
    """A single cell in the SIM matrix."""
    solution_a: str
    contradiction_a: str
    solution_b: str
    contradiction_b: str
    score: Literal[-1, 0, 1]  # -1 conflict, 0 neutral, +1 synergy
    reasoning: str = ""


class SIMMatrixResponse(BaseModel):
    """SIM matrix output with optimal combination and conflict/synergy pairs."""
    project_id: str
    contradiction_ids: list[str]
    matrix: list[SolutionInteraction] = Field(default_factory=list)
    optimal_combination: list[str] = Field(
        default_factory=list,
        description="Best non-conflicting solution combination (list of solution summaries)",
    )
    conflicts: list[dict] = Field(
        default_factory=list,
        description="Pairs of solutions that conflict (-1)",
    )
    synergies: list[dict] = Field(
        default_factory=list,
        description="Pairs of solutions that synergise (+1)",
    )


# ---------------------------------------------------------------------------
# Auto-TRIZ v2 — Complexity Check / CCI (WBS 8.3.2)
# ---------------------------------------------------------------------------

class ComplexityCheckRequest(BaseModel):
    """Evaluate whether a solution is an evolution or a patch."""
    project_id: str
    solution_description: str
    original_contradiction: str
    affected_subsystems: list[str] = Field(default_factory=list)


class ComplexityCheckResponse(BaseModel):
    """CCI (Concept Complexity Index) evaluation result."""
    cci_level: Literal["evolution", "weak_evolution", "patch"]
    score: int = Field(ge=0, le=100, description="0=pure patch, 100=ideal evolution")
    reasoning: str = ""
    four_questions: dict = Field(
        default_factory=dict,
        description=(
            "Answers to: is_new_function_needed, introduces_new_contradiction, "
            "increases_control_complexity, reduces_resource_efficiency"
        ),
    )


# ── Concept Architecture Pack ────────────────────────────────────────


class ConceptSubsystemTemplate(BaseModel):
    """子系統模板條目 — G1-G12 or S1-S10."""
    code: str            # e.g. "G1", "S3"
    name_zh: str
    name_en: str
    description: str
    typical_functions: list[str] = Field(default_factory=list)
    typical_interfaces: list[str] = Field(default_factory=list)


class ConceptInterface(BaseModel):
    """概念級介面定義."""
    from_subsystem: str  # code ref, e.g. "G1"
    to_subsystem: str
    interface_type: str  # mechanical, electrical, thermal, signal, material
    description: str
    criticality: str = "medium"  # low, medium, high


class ConceptSubsystem(BaseModel):
    """概念架構包中的一個子系統."""
    code: str
    name: str
    role: str            # 功能角色描述
    mapped_contradictions: list[str] = Field(default_factory=list)  # contradiction IDs
    mapped_kpis: list[str] = Field(default_factory=list)            # KPI IDs
    key_requirements: list[str] = Field(default_factory=list)
    suggested_level: str = "module"  # system, module, component


class ConceptArchitecturePack(BaseModel):
    """完整的概念架構包."""
    subsystems: list[ConceptSubsystem]
    interfaces: list[ConceptInterface]
    architecture_rationale: str  # 架構選擇理由
    template_id: str = "generic"
    coverage_summary: str = ""   # 對上游產出物的覆蓋摘要


class UpstreamArtifactSummary(BaseModel):
    """上游產出物快照 — 送入 LLM 的上下文."""
    mission: str = ""
    constraints: list[str] = Field(default_factory=list)
    kpis: list[str] = Field(default_factory=list)
    socratic_insights: list[str] = Field(default_factory=list)
    contradiction_summaries: list[str] = Field(default_factory=list)
    triz_solution_summaries: list[str] = Field(default_factory=list)
    cld_summary: list[str] = Field(default_factory=list)


class ConceptArchitecturePackRequest(BaseModel):
    project_id: str
    template_id: str = "generic"  # generic | ebike_mid_drive
    upstream: UpstreamArtifactSummary


class ConceptArchitecturePackResponse(BaseModel):
    pack: ConceptArchitecturePack
    source_badges: dict[str, bool] = Field(default_factory=dict)
    # e.g. {"brief": true, "explore": true, "triz": false}


# ---------------------------------------------------------------------------
# Engineering Spec Draft — DraftValue with full provenance (v3 dynamic fields)
# ---------------------------------------------------------------------------

class DraftValue(BaseModel):
    """Single AI-generated spec value with full provenance.

    Dynamic field design: AI decides field_name and category per subsystem type.
    Every value carries source, confidence, and needs_verification — ensuring
    no AI-generated number masquerades as engineering truth.
    """

    # --- Dynamic field identification ---
    field_name: str = Field(
        ...,
        description=(
            "AI-decided field name, e.g. 'dimensions', 'thermal_budget', "
            "'gear_ratio', 'waterproof_rating', 'max_current'."
        ),
    )
    category: Literal[
        "spatial",
        "material",
        "thermal",
        "electrical",
        "mechanical",
        "manufacturing",
    ] = Field(
        ...,
        description="Spec category for UI grouping and filtering.",
    )

    # --- Value ---
    value: bool | str | float | int | dict | list = Field(
        ...,
        description=(
            "Spec value. Can be numeric (250.0), string ('IP67'), "
            "or structured dict ({'min': 10, 'max': 25, 'typical': 18})."
        ),
    )
    unit: str | None = Field(
        default=None,
        description="Unit, e.g. 'mm', 'kg', 'W', '°C', 'N·m'.",
    )

    # --- Provenance triple (user's core requirement) ---
    source: str = Field(
        default="llm_estimate",
        description=(
            "Origin of this value. Canonical prefixes: "
            "rd_override, learned, web, seed, llm_estimate, datasheet, standard."
        ),
    )
    confidence: Literal["confirmed", "library", "estimate", "speculative"] = Field(
        default="speculative",
        description=(
            "Confidence level. confirmed=RD verified, library=reliable ref, "
            "estimate=reasonable but unverified, speculative=LLM guess."
        ),
    )
    needs_verification: bool = Field(
        default=True,
        description="Whether human verification is required. Default True.",
    )

    # --- Supplementary ---
    rationale: str | None = Field(
        default=None,
        description="Explanation of why this value was chosen.",
    )
    alternatives: list[dict] | None = Field(
        default=None,
        description=(
            "Alternative options, e.g. "
            "[{'value': 'ABS', 'reason': 'lower cost'}, {'value': 'PC', 'reason': 'higher temp'}]."
        ),
    )


# Confidence-to-score mapping for overall_confidence calculation
_CONFIDENCE_SCORES: dict[str, float] = {
    "confirmed": 1.0,
    "library": 0.75,
    "estimate": 0.5,
    "speculative": 0.25,
}


class EngineeringSpecDraft(BaseModel):
    """Complete engineering spec draft for one subsystem.

    Uses dynamic ``specs: list[DraftValue]`` instead of fixed fields —
    AI decides which spec fields to generate based on subsystem type.
    """

    subsystem_code: str = Field(
        ...,
        description="Corresponding subsystem code (from ConceptSubsystem.code).",
    )

    component_type_hint: str | None = Field(
        default=None,
        description=(
            "CAD-oriented type hint from Stage 2a field planning. "
            "e.g. 'motor', 'housing', 'pcb', 'gear', 'sensor', 'battery'. "
            "Used downstream for proxy-geometry archetype selection and "
            "USDA metadata."
        ),
    )

    specs: list[DraftValue] = Field(
        default_factory=list,
        description=(
            "Dynamic spec list. AI produces appropriate fields per subsystem role. "
            "E.g. motor → dimensions, mass, max_torque, rated_power, thermal_budget; "
            "housing → dimensions, primary_material, waterproof_rating, surface_finish; "
            "PCB → dimensions, layer_count, max_current, operating_temp_range."
        ),
    )

    overall_confidence: float = Field(
        default=0.0,
        description="Weighted average confidence score (0.0–1.0) across all specs.",
    )

    verification_count: int = Field(
        default=0,
        description="Number of specs with needs_verification=True. Shown as red badge in UI.",
    )

    def recompute_stats(self) -> None:
        """Recompute overall_confidence and verification_count from specs."""
        if not self.specs:
            self.overall_confidence = 0.0
            self.verification_count = 0
            return
        total = sum(_CONFIDENCE_SCORES.get(s.confidence, 0.25) for s in self.specs)
        self.overall_confidence = round(total / len(self.specs), 3)
        self.verification_count = sum(1 for s in self.specs if s.needs_verification)


class EngineeringSpecDraftResponse(BaseModel):
    """Response wrapper for the engineering spec generation pipeline."""
    drafts: list[EngineeringSpecDraft] = Field(default_factory=list)
    subsystem_tree: list[SuggestedSubsystem] = Field(default_factory=list)
    package_map: PackageMap | None = None


# ── Split API: Engineering Spec Drafts Pipeline ──────────────────────────────
# These schemas support the 3-step split pipeline that avoids the 300s Nginx
# timeout by breaking one long request into three shorter HTTP round-trips.
# See plans/split-api-engineering-spec-drafts.md for full design rationale.


class EngSpecStep1Response(BaseModel):
    """Step 1 result: expanded subsystem tree with spatial estimates,
    interface contracts, and package map."""
    subsystems: list[SuggestedSubsystem] = Field(default_factory=list)
    package_map: PackageMap | None = None


# ── Step 1a / 1b sub-step schemas ───────────────────────────────────────
# Step 1 was split into 1a (LLM expansion only, ≤150 s) and 1b (spatial
# resolution + package map, ≤80 s) to stay within the frontend 180 s
# fetch timeout.  See plans/fix-step1-timeout-split.md.


class EngSpecStep1aResponse(BaseModel):
    """Step 1a result: LLM-expanded subsystem tree *without* resolved
    spatial estimates or package map.  Spatial fields may contain raw
    LLM guesses that have not been cross-checked against web data."""
    subsystems: list[SuggestedSubsystem] = Field(default_factory=list)


class EngSpecStep1bRequest(BaseModel):
    """Input for Step 1b (Spatial Enrichment + Package Map).

    Accepts the subsystem tree produced by Step 1a and enriches it with
    web-based spatial resolution and package-map discovery.
    """
    project_id: str = Field(..., description="Project identifier")
    subsystems: list[SuggestedSubsystem] = Field(
        ..., description="Subsystem tree from Step 1a (pre-spatial)",
    )


class EngSpecStep1bResponse(BaseModel):
    """Step 1b result: subsystems with resolved spatial estimates and
    a package map.  Same shape as EngSpecStep1Response for downstream
    compatibility."""
    subsystems: list[SuggestedSubsystem] = Field(default_factory=list)
    package_map: PackageMap | None = None


class EngSpecStep2Request(BaseModel):
    """Input for Step 2 (AI Spec Generation).

    Requires the expanded subsystem tree produced by Step 1.
    ``library_summary`` is re-resolved server-side (< 1 s) to avoid
    passing large strings across the wire.
    """
    project_id: str = Field(..., description="Project identifier")
    mission: str = Field(..., description="Design mission / objective")
    subsystems: list[SuggestedSubsystem] = Field(
        ..., description="Expanded subsystem tree from Step 1",
    )


class EngSpecStep2Response(BaseModel):
    """Step 2 result: raw AI-generated engineering spec drafts."""
    drafts: list[EngineeringSpecDraft] = Field(default_factory=list)


class EngSpecStep2ModuleRequest(BaseModel):
    """Input for Step 2 — single-module spec generation.

    The frontend calls this endpoint once per module to avoid the
    Nginx 300 s gateway timeout.
    """
    project_id: str = Field(..., description="Project identifier")
    mission: str = Field(..., description="Design mission / objective")
    module_name: str = Field(
        ..., description="Name of the module-level node to process",
    )
    module_node: SuggestedSubsystem = Field(
        ..., description="The module-level subsystem node (with children)",
    )
    subsystems: list[SuggestedSubsystem] = Field(
        ..., description="Full subsystem tree (for context in prompts)",
    )


class EngSpecStep2ModuleResponse(BaseModel):
    """Step 2 result for a single module."""
    module_name: str = Field(..., description="Module name that was processed")
    drafts: list[EngineeringSpecDraft] = Field(default_factory=list)


class EngSpecStep2SystemRequest(BaseModel):
    """Input for Step 2 — system-level node spec generation.

    Generates specs for system-level (non-module) nodes only.
    """
    project_id: str = Field(..., description="Project identifier")
    mission: str = Field(..., description="Design mission / objective")
    subsystems: list[SuggestedSubsystem] = Field(
        ..., description="Full subsystem tree from Step 1",
    )


class EngSpecStep2SystemResponse(BaseModel):
    """Step 2 result for system-level nodes."""
    drafts: list[EngineeringSpecDraft] = Field(default_factory=list)


class EngSpecStep3Request(BaseModel):
    """Input for Step 3 (Source Strengthening).

    Requires raw drafts from Step 2 **and** the expanded subsystem tree
    from Step 1 (needed by the strengthening prompt as ``subsystem_tree_json``).
    ``library_summary`` is re-resolved server-side.
    """
    project_id: str = Field(..., description="Project identifier")
    mission: str = Field(..., description="Design mission / objective")
    drafts: list[EngineeringSpecDraft] = Field(
        ..., description="Raw drafts from Step 2",
    )
    subsystems: list[SuggestedSubsystem] = Field(
        ..., description="Expanded subsystem tree from Step 1 (for prompt context)",
    )


class EngSpecStep3Response(BaseModel):
    """Step 3 result: strengthened drafts with improved provenance."""
    drafts: list[EngineeringSpecDraft] = Field(default_factory=list)


class EngSpecPersistRequest(BaseModel):
    """Request to persist an engineering-spec draft pack without running Step 3."""
    project_id: str = Field(..., description="Project identifier")
    drafts: list[EngineeringSpecDraft] = Field(
        ..., description="Drafts from Step 2 (or any stage)",
    )
    subsystem_tree: list[SuggestedSubsystem] = Field(
        ..., description="Expanded subsystem tree from Step 1",
    )
    package_map: "PackageMap | None" = Field(
        default=None, description="Optional package map from Step 1b",
    )
