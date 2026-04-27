import type { LucideIcon } from "lucide-react";
import {
  FolderKanban,
  BookOpen,
  Settings,
  ClipboardList,
  Compass,
  ListChecks,
  Wand2,
  Search,
  Gavel,
  GraduationCap,
  ShieldCheck,
} from "lucide-react";
import type { PhaseProgress } from "@/types/project";

// ── Types ──────────────────────────────────────────────────────────

export interface GlobalNavItem {
  label: string;
  path: string;
  icon: LucideIcon;
}

export interface ProjectStep {
  id: string;
  label: string;
  zhLabel: string;
  icon: LucideIcon;
  route: string;
  phase: number;
}

export type StepStatusValue = "active" | "completed" | "not_started";

// ── Data ───────────────────────────────────────────────────────────

export const globalNavItems: GlobalNavItem[] = [
  { label: "\u5c08\u6848\u5217\u8868", path: "/projects", icon: FolderKanban },
  { label: "\u77e5\u8b58\u5eab", path: "/knowledge-base", icon: BookOpen },
  { label: "\u8a2d\u5b9a", path: "/settings", icon: Settings },
];

export const projectSteps: ProjectStep[] = [
  { id: "brief", label: "Brief", zhLabel: "\u5b9a\u7fa9\u7c21\u5831", icon: ClipboardList, route: "brief", phase: 1 },
  { id: "explore", label: "Explore", zhLabel: "\u554f\u984c\u63a2\u7d22", icon: Compass, route: "explore", phase: 1 },
  { id: "track", label: "Track", zhLabel: "\u5047\u8a2d\u8ffd\u8e64", icon: ListChecks, route: "track", phase: 2 },
  { id: "create", label: "Create", zhLabel: "\u65b9\u6848\u5275\u9020", icon: Wand2, route: "create", phase: 2 },
  { id: "pre-cad", label: "Pre-CAD", zhLabel: "Pre-CAD \u5be9\u67e5", icon: ShieldCheck, route: "pre-cad", phase: 2 },
  { id: "review", label: "Review", zhLabel: "\u8a2d\u8a08\u5be9\u67e5", icon: Search, route: "review", phase: 3 },
  { id: "decide", label: "Decide", zhLabel: "\u6700\u7d42\u6c7a\u7b56", icon: Gavel, route: "decide", phase: 3 },
  { id: "feynman", label: "Feynman", zhLabel: "\u5167\u5316\u50b3\u9054", icon: GraduationCap, route: "feynman", phase: 3 },
];

export const phaseLabels: Record<number, string> = {
  1: "Define",
  2: "Diverge",
  3: "Converge",
};

/** Map each sidebar step to the phase_progress keys it covers */
export const stepProgressKeys: Record<string, (keyof PhaseProgress)[]> = {
  brief:     ["D1"],
  explore:   ["D2", "PG-D"],
  track:     ["X1"],
  create:    ["X2"],
  "pre-cad": ["PG-X"],
  review:    ["V1"],
  decide:    ["V2"],
  feynman:   ["PG-V"],
};

// ── Helpers ────────────────────────────────────────────────────────

export function getStepStatus(
  pathname: string,
  route: string,
  projectId: string,
  progress?: PhaseProgress,
): StepStatusValue {
  const fullPath = `/projects/${projectId}/${route}`;
  if (pathname === fullPath || pathname.startsWith(fullPath + "/")) return "active";
  if (progress) {
    const keys = stepProgressKeys[route];
    if (keys && keys.every((k) => progress[k] === "passed")) return "completed";
    if (keys && keys.some((k) => progress[k] === "in_progress")) return "active";
  }
  return "not_started";
}
