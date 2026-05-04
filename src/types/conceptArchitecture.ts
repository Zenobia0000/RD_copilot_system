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

export interface UpstreamArtifactSummary {
  mission: string;
  constraints: string[];
  kpis: string[];
  socratic_insights: string[];
  contradiction_summaries: string[];
  triz_solution_summaries: string[];
  cld_summary: string[];
}

export interface ConceptArchitecturePackResponse {
  pack: ConceptArchitecturePack;
  source_badges: Record<string, boolean>;
}
