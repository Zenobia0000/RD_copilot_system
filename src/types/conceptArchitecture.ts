/**
 * Concept Architecture Pack — 概念架構包型別定義
 *
 * Bridges TRIZ contradiction solving → Subsystem Definition
 * with a product-agnostic concept-level architecture.
 */

export interface ConceptSubsystem {
  code: string;
  name: string;
  role: string;
  mapped_contradictions: string[];
  mapped_kpis: string[];
  key_requirements: string[];
  suggested_level: "system" | "module" | "component";
}

export interface ConceptInterface {
  from_subsystem: string;
  to_subsystem: string;
  interface_type: string;
  description: string;
  criticality: "low" | "medium" | "high";
}

export interface ConceptArchitecturePack {
  subsystems: ConceptSubsystem[];
  interfaces: ConceptInterface[];
  architecture_rationale: string;
  template_id: string;
  coverage_summary: string;
}

/**
 * 單一 TC/PC/SF 解法在 concept-architecture 上下文裡的精簡引用。
 *
 * 鏡像 backend `DirectionSolutionRef`。來源為 `DirectionGroup.solutions`
 * 內的 `DirectionSolution`，僅取下游架構規劃需要看到的欄位。
 */
export interface DirectionSolutionRef {
  path: "TC" | "PC" | "SF";
  principle_number: number | null;
  principle_name: string;
  separation_principle: string;
  suggestion: string;
  affected_modules: string[];
}

/** 整併後對某條矛盾採用的方向（DirectionGroup 的精簡引用）。 */
export interface AdoptedDirectionRef {
  direction_id: string;
  direction_name: string;
  direction_summary: string;
}

/**
 * 一條矛盾 + 整併後採用的方向 + 該方向所有 TC/PC/SF solutions。
 *
 * 這是「正向分析 → 概念架構」步驟下游 LLM 看到的主要結構，取代舊版
 * 兩條無關聯的純字串 list（`contradiction_summaries` /
 * `triz_solution_summaries`）。
 */
export interface ContradictionSolutionPair {
  contradiction_id: string;    // 對應 FE [CT-N] 標籤
  contradiction_text: string;  // 矛盾完整描述（不含 [CT-N] 前綴）
  adopted_direction: AdoptedDirectionRef;
  solutions: DirectionSolutionRef[];
}

export interface UpstreamArtifactSummary {
  mission: string;
  constraints: string[];
  kpis: string[];
  socratic_insights: string[];
  /**
   * 矛盾與整併後採用之 TRIZ 解法以「成對」結構提供給 LLM。
   * 必須在 explore→consolidation 步驟跑完後才會有值。
   */
  contradiction_solution_pairs: ContradictionSolutionPair[];
  cld_summary: string[];
}

export interface ConceptArchitecturePackResponse {
  pack: ConceptArchitecturePack;
  source_badges: Record<string, boolean>;
}
