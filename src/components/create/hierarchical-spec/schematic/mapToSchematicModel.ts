/**
 * mapToSchematicModel — 將 SuggestedSubsystem + EngineeringSpecDraft + ConceptInterface
 * 映射為 SchematicViewModel。
 *
 * 核心職責：
 *  1. 透過 buildSpecTree 將 drafts join 到 subsystem tree
 *  2. 遞迴走訪 tree → SchematicBlock[]
 *  3. 從 InterfaceContract + ConceptInterface 推斷 SchematicRelation[]
 *  4. 計算全域統計
 *
 * @see plans/structural-schematic-view.md §3 資料流
 */

import type { SuggestedSubsystem, InterfaceContract, PackageMap } from "@/types/generated/subsystem";
import type { EngineeringSpecDraft } from "@/types/generated/engineeringSpec";
import type { ConceptInterface } from "@/types/conceptArchitecture";
import { buildSpecTree, type SpecTreeNode } from "../buildSpecTree";
import type {
  SchematicBlock,
  SchematicBlockLevel,
  SchematicRelation,
  SchematicViewModel,
  RelationType,
  RiskLevel,
} from "./types";

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export interface MapToSchematicModelInput {
  tree: SuggestedSubsystem[];
  drafts: EngineeringSpecDraft[];
  packageMap?: PackageMap | null;
  conceptInterfaces?: ConceptInterface[];
}

/**
 * 從原始後端資料建立結構示意圖的 View Model。
 */
export function mapToSchematicModel(input: MapToSchematicModelInput): SchematicViewModel {
  const { tree, drafts, conceptInterfaces } = input;

  // Step 1: build enriched spec tree
  const specTree = buildSpecTree(tree, drafts);

  // Step 2: walk tree → flat blocks
  const blocks: SchematicBlock[] = [];
  for (const root of specTree) {
    flattenTree(root, null, blocks);
  }

  // Step 3: build relations
  const relations = buildRelations(specTree, conceptInterfaces ?? []);

  // Step 4: categorize blocks
  const systems = blocks.filter((b) => b.level === "system");
  const modules = blocks.filter((b) => b.level === "module");
  const components = blocks.filter((b) => b.level === "component");

  // Step 5: global stats
  const avgConfidence =
    blocks.length > 0
      ? blocks.reduce((s, b) => s + b.avgConfidence, 0) / blocks.length
      : 0;

  return {
    blocks,
    relations,
    systems,
    modules,
    components,
    globalStats: {
      totalBlocks: blocks.length,
      totalRelations: relations.length,
      avgConfidence,
      highRiskCount: blocks.filter((b) => b.riskLevel === "high").length,
    },
  };
}

// ---------------------------------------------------------------------------
// Internal: flatten tree to blocks
// ---------------------------------------------------------------------------

function flattenTree(
  node: SpecTreeNode,
  parentId: string | null,
  out: SchematicBlock[],
): void {
  const level = mapLevel(node.level);
  const spatial = node.draft?.specs?.find((s) => s.field_name === "bbox");

  const block: SchematicBlock = {
    id: node.name,
    name: node.name,
    level,
    parentId,
    bboxSummary: formatBboxFromNode(node),
    massG: extractMass(node),
    avgConfidence: node.aggregated.avgConfidence,
    riskLevel: confidenceToRisk(node.aggregated.avgConfidence),
    specCount: node.aggregated.totalSpecs,
    verificationCount: node.aggregated.verificationCount,
    childCount: node.children.length,
    specTreeNodeRef: node,
  };
  out.push(block);

  for (const child of node.children) {
    flattenTree(child, node.name, out);
  }
}

function mapLevel(level: SuggestedSubsystem["level"]): SchematicBlockLevel {
  switch (level) {
    case "system":
      return "system";
    case "module":
      return "module";
    case "component":
      return "component";
    default:
      return "module";
  }
}

function confidenceToRisk(avgConf: number): RiskLevel {
  if (avgConf <= 0) return "none";
  if (avgConf < 0.35) return "high";
  if (avgConf < 0.65) return "medium";
  return "low";
}

/**
 * 從 SpecTreeNode 的 interface_contracts 中的 spatial 資料
 * 或 draft specs 中提取 bbox 摘要字串。
 */
function formatBboxFromNode(node: SpecTreeNode): string | null {
  // Try from interface_contracts spatial
  if (node.interface_contracts) {
    for (const contract of Object.values(node.interface_contracts)) {
      if (contract?.spatial?.bbox) {
        const b = contract.spatial.bbox;
        return `${b.x_mm}×${b.y_mm}×${b.z_mm} mm`;
      }
    }
  }
  // Try from draft specs — look for spatial category
  if (node.draft?.specs) {
    for (const spec of node.draft.specs) {
      if (spec.category === "spatial" && spec.field_name?.toLowerCase().includes("bbox")) {
        return spec.value?.toString() ?? null;
      }
    }
  }
  return null;
}

function extractMass(node: SpecTreeNode): number | null {
  // Try from interface_contracts spatial
  if (node.interface_contracts) {
    for (const contract of Object.values(node.interface_contracts)) {
      if (contract?.spatial?.mass_g != null) {
        return contract.spatial.mass_g;
      }
    }
  }
  return null;
}

// ---------------------------------------------------------------------------
// Internal: build relations
// ---------------------------------------------------------------------------

/**
 * 建構關係清單：
 *  1. 優先使用 ConceptInterface（包含 interface_type + criticality）
 *  2. 回退使用 InterfaceContract（從 6 個文字維度推斷通道型別）
 *
 * @see plans/structural-schematic-view.md §3.3 關係型別推斷
 */
function buildRelations(
  specTree: SpecTreeNode[],
  conceptInterfaces: ConceptInterface[],
): SchematicRelation[] {
  const relations: SchematicRelation[] = [];
  const seen = new Set<string>();

  // --- Source 1: ConceptInterface (higher priority) ---
  for (const ci of conceptInterfaces) {
    const key = pairKey(ci.from_subsystem, ci.to_subsystem);
    if (seen.has(key)) continue;
    seen.add(key);

    relations.push({
      id: `ci-${key}`,
      sourceId: ci.from_subsystem,
      targetId: ci.to_subsystem,
      types: inferTypesFromInterfaceType(ci.interface_type),
      criticality: ci.criticality,
      label: ci.description?.slice(0, 60) || ci.interface_type,
      isCrossModule: true, // ConceptInterface 通常是跨模組
    });
  }

  // --- Source 2: InterfaceContract from tree nodes ---
  const blockNameToParent = new Map<string, string | null>();
  collectParentMap(specTree, null, blockNameToParent);

  for (const root of specTree) {
    collectContractRelations(root, relations, seen, blockNameToParent);
  }

  return relations;
}

function collectParentMap(
  nodes: SpecTreeNode[],
  parentName: string | null,
  out: Map<string, string | null>,
): void {
  for (const node of nodes) {
    out.set(node.name, parentName);
    collectParentMap(node.children, node.name, out);
  }
}

function collectContractRelations(
  node: SpecTreeNode,
  out: SchematicRelation[],
  seen: Set<string>,
  parentMap: Map<string, string | null>,
): void {
  if (node.interface_contracts) {
    for (const [neighbourName, contract] of Object.entries(node.interface_contracts)) {
      const key = pairKey(node.name, neighbourName);
      if (seen.has(key)) continue;
      seen.add(key);

      const types = inferTypesFromContract(contract);
      const nodeParent = findSystemAncestor(node.name, parentMap);
      const neighbourParent = findSystemAncestor(neighbourName, parentMap);

      out.push({
        id: `ic-${key}`,
        sourceId: node.name,
        targetId: neighbourName,
        types,
        criticality: guessCriticality(types),
        label: contractSummaryLabel(contract),
        contractRef: contract,
        isCrossModule: nodeParent !== neighbourParent,
      });
    }
  }

  for (const child of node.children) {
    collectContractRelations(child, out, seen, parentMap);
  }
}

/**
 * 從 InterfaceContract 的 6 個文字維度推斷關係通道型別。
 * 如果某個維度的文字非空，表示該通道存在。
 */
function inferTypesFromContract(contract: InterfaceContract): RelationType[] {
  const types: RelationType[] = [];
  if (contract.signalPath?.trim()) types.push("signal");
  if (contract.thermalPath?.trim()) types.push("thermal");
  if (contract.loadPath?.trim()) types.push("load");
  if (contract.envelope?.trim()) types.push("envelope");
  if (types.length === 0) types.push("other");
  return types;
}

/**
 * 從 ConceptInterface.interface_type 字串推斷 RelationType。
 */
function inferTypesFromInterfaceType(interfaceType: string): RelationType[] {
  const lower = interfaceType.toLowerCase();
  const types: RelationType[] = [];
  if (/signal|data|communi|i2c|spi|uart|can|serial|digital|analog/i.test(lower)) types.push("signal");
  if (/thermal|heat|cool|temp/i.test(lower)) types.push("thermal");
  if (/load|force|torque|stress|struct|mount|mech/i.test(lower)) types.push("load");
  if (/envelope|spatial|geom|fit|clear/i.test(lower)) types.push("envelope");
  if (types.length === 0) types.push("other");
  return types;
}

function guessCriticality(types: RelationType[]): "low" | "medium" | "high" {
  // If there are signal or thermal paths, likely higher criticality
  if (types.includes("signal") || types.includes("thermal")) return "high";
  if (types.includes("load")) return "medium";
  return "low";
}

function contractSummaryLabel(contract: InterfaceContract): string {
  const parts: string[] = [];
  if (contract.signalPath?.trim()) parts.push("信號");
  if (contract.thermalPath?.trim()) parts.push("散熱");
  if (contract.loadPath?.trim()) parts.push("載荷");
  if (contract.envelope?.trim()) parts.push("包絡");
  return parts.length > 0 ? parts.join(" + ") : "介面";
}

function pairKey(a: string, b: string): string {
  return a < b ? `${a}|${b}` : `${b}|${a}`;
}

function findSystemAncestor(
  name: string,
  parentMap: Map<string, string | null>,
): string | null {
  let current = name;
  let parent = parentMap.get(current) ?? null;
  while (parent != null) {
    current = parent;
    parent = parentMap.get(current) ?? null;
  }
  return current;
}
