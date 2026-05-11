/**
 * 結構示意圖 (Structural Schematic View) — View Model 型別定義
 *
 * 這些型別用於將原始的 SuggestedSubsystem / EngineeringSpecDraft / ConceptInterface
 * 資料轉換成純粹的「示意圖語言」，讓 ReactFlow 渲染邏輯與後端資料結構完全解耦。
 */

import type { SpecTreeNode } from "../buildSpecTree";
import type { InterfaceContract } from "@/types/generated/subsystem";

// ── 列舉型別 ─────────────────────────────────────────────

/** 區塊在示意圖中的層級 */
export type SchematicBlockLevel = "system" | "module" | "component";

/** 關係通道型別 */
export type RelationType =
  | "signal"
  | "thermal"
  | "load"
  | "envelope"
  | "hierarchy"
  | "other";

/** 基於信心度的風險分級 */
export type RiskLevel = "high" | "medium" | "low" | "none";

// ── 區塊 (Block) ────────────────────────────────────────

export interface SchematicBlock {
  /** 唯一 ID (subsystem name) */
  id: string;
  name: string;
  level: SchematicBlockLevel;
  /** system blocks → null */
  parentId: string | null;
  /** e.g. "120×80×40 mm" */
  bboxSummary: string | null;
  massG: number | null;
  /** 0-1 */
  avgConfidence: number;
  /** 基於信心度的風險分級 */
  riskLevel: RiskLevel;
  specCount: number;
  verificationCount: number;
  /** module 下的 component 數量 */
  childCount: number;
  /** 附帶完整 SpecTreeNode reference，點擊後用於 SubsystemDatasheet */
  specTreeNodeRef: SpecTreeNode;
}

// ── 關係 (Relation) ─────────────────────────────────────

export interface SchematicRelation {
  id: string;
  sourceId: string;
  targetId: string;
  /** 一個關係可能跨多種通道 */
  types: RelationType[];
  criticality: "low" | "medium" | "high";
  /** 簡短摘要 */
  label: string;
  /** 原始合約 reference */
  contractRef?: InterfaceContract;
  /** 是否跨模組 (不同 system 底下) */
  isCrossModule: boolean;
}

// ── View Model ──────────────────────────────────────────

export interface SchematicViewModel {
  blocks: SchematicBlock[];
  relations: SchematicRelation[];
  /** level=system 的子集 */
  systems: SchematicBlock[];
  /** level=module 的子集 */
  modules: SchematicBlock[];
  /** level=component 的子集 */
  components: SchematicBlock[];
  globalStats: {
    totalBlocks: number;
    totalRelations: number;
    avgConfidence: number;
    highRiskCount: number;
  };
}

// ── 篩選狀態 ────────────────────────────────────────────

export interface SchematicFilterState {
  /** 預設 false */
  showComponents: boolean;
  /** 預設 {"signal","thermal","load"} */
  relationTypes: Set<RelationType>;
  /** 預設 "all" */
  riskFilter: RiskLevel | "all";
  /** 預設 "all" */
  levelFilter: SchematicBlockLevel | "all";
  searchQuery: string;
}

/** 建立預設篩選狀態 */
export function createDefaultFilterState(): SchematicFilterState {
  return {
    showComponents: false,
    relationTypes: new Set<RelationType>(["signal", "thermal", "load"]),
    riskFilter: "all",
    levelFilter: "all",
    searchQuery: "",
  };
}

// ── 關係型別色彩映射 ────────────────────────────────────

export const RELATION_TYPE_COLORS: Record<RelationType, string> = {
  signal: "#3b82f6",   // blue-500
  thermal: "#ef4444",  // red-500
  load: "#f97316",     // orange-500
  envelope: "#8b5cf6", // violet-500
  hierarchy: "#d1d5db", // gray-300
  other: "#6b7280",    // gray-500
};

export const RELATION_TYPE_LABELS: Record<RelationType, string> = {
  signal: "信號",
  thermal: "散熱",
  load: "載荷",
  envelope: "包絡",
  hierarchy: "層級",
  other: "其他",
};

export const RISK_LEVEL_COLORS: Record<RiskLevel, string> = {
  high: "#ef4444",     // red-500
  medium: "#f59e0b",   // amber-500
  low: "#22c55e",      // green-500
  none: "#6b7280",     // gray-500
};
