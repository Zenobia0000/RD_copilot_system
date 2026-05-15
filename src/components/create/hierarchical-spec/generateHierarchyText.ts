/**
 * generateHierarchyText — pure function that serialises the SpecTreeNode[]
 * hierarchy into a structured plain-text file suitable for guiding USDA
 * generation.
 *
 * Output has two sections:
 *   1. Hierarchy tree (System → Module → Component) — name + description only
 *   2. Per-node interface contracts (6 dimensions)
 *
 * @see plans/hierarchy-text-export.md
 */

import type { SpecTreeNode } from "./buildSpecTree";
import type { ConceptInterface } from "@/types/conceptArchitecture";
import { INTERFACE_CONTRACT_DIMS } from "@/types/generated/subsystem";

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export interface HierarchyTextOptions {
  specTree: SpecTreeNode[];
  conceptInterfaces?: ConceptInterface[];
}

/**
 * Generate a structured plain-text representation of the subsystem hierarchy.
 * Pure & synchronous — no side-effects.
 */
export function generateHierarchyText(options: HierarchyTextOptions): string {
  const { specTree } = options;
  const lines: string[] = [];

  // ---- File header --------------------------------------------------------
  const now = new Date();
  const timestamp = now.toLocaleString("zh-TW", {
    timeZone: "Asia/Taipei",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });

  lines.push("# 系統階層結構與介面關係");
  lines.push(`# 生成時間: ${timestamp}`);
  lines.push(`# ${"=".repeat(64)}`);
  lines.push("");

  // ---- Section 1: Hierarchy tree (name + description only) ----------------
  lines.push(sectionBanner("SECTION 1: 階層結構  System → Module → Component"));
  lines.push("");

  for (const root of specTree) {
    renderNode(lines, root, "", true);
    lines.push("");
  }

  // ---- Section 2: Interface contracts -------------------------------------
  const contractEntries = collectAllContracts(specTree);
  if (contractEntries.length > 0) {
    lines.push(
      sectionBanner("SECTION 2: 組件間介面合約  Interface Contracts"),
    );
    lines.push("");

    for (const entry of contractEntries) {
      lines.push(`  ${entry.fromName} ↔ ${entry.toName}`);
      for (const dim of INTERFACE_CONTRACT_DIMS) {
        const value = entry.contract[dim.key];
        if (value) {
          lines.push(`    ${dim.labelZh.padEnd(8, "　")} ${value}`);
        }
      }
      lines.push("");
    }
  }

  return lines.join("\n");
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

/** Build a section separator banner. */
function sectionBanner(title: string): string {
  const bar = "═".repeat(65);
  return `${bar}\n  ${title}\n${bar}`;
}

/** Map SubsystemLevel to display tag. */
function levelTag(level: string): string {
  switch (level) {
    case "system":
      return "SYSTEM";
    case "module":
      return "MODULE";
    case "component":
      return "COMPONENT";
    default:
      return level.toUpperCase();
  }
}

/**
 * Recursively render a SpecTreeNode with tree-drawing characters.
 * Only outputs name + description (reason) — no contradictions, KPIs, or specs.
 *
 * @param lines  - mutable output array
 * @param node   - current node
 * @param prefix - accumulated prefix for indentation (e.g. "│   ")
 * @param isRoot - true for top-level system nodes (no connector)
 */
function renderNode(
  lines: string[],
  node: SpecTreeNode,
  prefix: string,
  isRoot: boolean,
): void {
  // Node header
  if (isRoot) {
    lines.push(`[${levelTag(node.level)}] ${node.name}`);
  } else {
    lines.push(`${prefix}[${levelTag(node.level)}] ${node.name}`);
  }

  // Indentation for details under this node
  const detailPrefix = isRoot ? "  " : `${prefix}    `;

  // Description only
  if (node.reason) {
    lines.push(`${detailPrefix}描述: ${node.reason}`);
  }

  // Children
  if (node.children.length > 0) {
    const childIndentBase = isRoot ? "  " : prefix + "    ";
    lines.push(`${childIndentBase}│`);

    node.children.forEach((child, idx) => {
      const isLast = idx === node.children.length - 1;
      const connector = isLast ? "└── " : "├── ";
      const childPrefix = isLast
        ? childIndentBase + "    "
        : childIndentBase + "│   ";

      renderNodeWithConnector(lines, child, childIndentBase, connector, childPrefix);
    });
  }
}

/**
 * Render a child node with a tree connector prefix.
 * Only outputs name + description (reason).
 */
function renderNodeWithConnector(
  lines: string[],
  node: SpecTreeNode,
  parentPrefix: string,
  connector: string,
  childPrefix: string,
): void {
  // First line with connector
  lines.push(
    `${parentPrefix}${connector}[${levelTag(node.level)}] ${node.name}`,
  );

  // Description only
  if (node.reason) {
    lines.push(`${childPrefix}描述: ${node.reason}`);
  }

  // Nested children
  if (node.children.length > 0) {
    lines.push(`${childPrefix}│`);

    node.children.forEach((child, idx) => {
      const isLast = idx === node.children.length - 1;
      const conn = isLast ? "└── " : "├── ";
      const nextPrefix = isLast
        ? childPrefix + "    "
        : childPrefix + "│   ";

      renderNodeWithConnector(lines, child, childPrefix, conn, nextPrefix);
    });
  }
}

// ---------------------------------------------------------------------------
// Contract collector
// ---------------------------------------------------------------------------

interface ContractEntry {
  fromName: string;
  toName: string;
  contract: Record<string, string>;
}

/**
 * Walk the entire tree and collect all interface_contracts into a flat list.
 * De-duplicates symmetric pairs (A↔B and B↔A count as one).
 */
function collectAllContracts(roots: SpecTreeNode[]): ContractEntry[] {
  const entries: ContractEntry[] = [];
  const seen = new Set<string>();

  function walk(node: SpecTreeNode): void {
    if (node.interface_contracts) {
      for (const [neighbourName, contract] of Object.entries(
        node.interface_contracts,
      )) {
        // De-duplicate symmetric pairs
        const pairKey = [node.name, neighbourName].sort().join("↔");
        if (seen.has(pairKey)) continue;
        seen.add(pairKey);

        entries.push({
          fromName: node.name,
          toName: neighbourName,
          contract: contract as unknown as Record<string, string>,
        });
      }
    }

    for (const child of node.children) {
      walk(child);
    }
  }

  for (const root of roots) {
    walk(root);
  }

  return entries;
}
