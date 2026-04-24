import type { NavCardDef, PhaseProgress } from "@/types/project";

/**
 * Build navigation cards for the project dashboard based on gate progress.
 * Each card's lock state is derived from prerequisite gates.
 */
export function getNavCards(progress: PhaseProgress): NavCardDef[] {
  const gate11 = progress["1.1"] === "passed";
  const gate13 = progress["1.3"] === "passed";
  const gate21 = progress["2.1"] === "passed";
  const gate23 = progress["2.3"] === "passed";
  const gate32 = progress["3.2"] === "passed";

  function countPassed(...keys: (keyof PhaseProgress)[]): number {
    return keys.filter((k) => progress[k] === "passed").length;
  }

  return [
    {
      id: "brief",
      enName: "Brief",
      zhName: "定義簡報",
      phase: "Phase 1",
      icon: "ClipboardList",
      route: "brief",
      subSteps: 1,
      completedSteps: gate11 ? 1 : 0,
      locked: false,
    },
    {
      id: "explore",
      enName: "Explore",
      zhName: "問題探索",
      phase: "Phase 1",
      icon: "Compass",
      route: "explore",
      subSteps: 2,
      completedSteps: countPassed("1.2", "1.3"),
      requiredGate: "1.1",
      locked: !gate11,
      lockReason: !gate11 ? "需先完成 Brief (Gate 1.1)" : undefined,
    },
    {
      id: "track",
      enName: "Track",
      zhName: "假設追蹤",
      phase: "Phase 2",
      icon: "ListChecks",
      route: "track",
      subSteps: 1,
      completedSteps: gate21 ? 1 : 0,
      requiredGate: "1.3",
      locked: !gate13,
      lockReason: !gate13 ? "需先完成 Phase 1 所有 Gate" : undefined,
    },
    {
      id: "create",
      enName: "Create",
      zhName: "方案創造",
      phase: "Phase 2",
      icon: "Wand2",
      route: "create",
      subSteps: 2,
      completedSteps: countPassed("2.2", "2.3"),
      requiredGate: "2.1",
      locked: !gate21,
      lockReason: !gate21 ? "需先完成 Track (Gate 2.1)" : undefined,
    },
    {
      id: "cad",
      enName: "CAD",
      zhName: "CAD 繪製",
      phase: "Phase 2",
      icon: "PenTool",
      route: "cad",
      subSteps: 1,
      completedSteps: gate23 ? 1 : 0,
      requiredGate: "2.3",
      locked: !gate23,
      lockReason: !gate23 ? "需先完成 Phase 2 所有 Gate" : undefined,
    },
    {
      id: "review",
      enName: "Review",
      zhName: "設計審查",
      phase: "Phase 3",
      icon: "Search",
      route: "review",
      subSteps: 1,
      completedSteps: gate32 ? 1 : 0,
      requiredGate: "2.3",
      locked: !gate23,
      lockReason: !gate23 ? "需完成 CAD 繪製階段" : undefined,
    },
    {
      id: "decide",
      enName: "Decide",
      zhName: "最終決策",
      phase: "Phase 3",
      icon: "Gavel",
      route: "decide",
      subSteps: 2,
      completedSteps: countPassed("3.2", "3.3"),
      requiredGate: "3.2",
      locked: !gate32,
      lockReason: !gate32 ? "需先完成 Review (Gate 3.2)" : undefined,
    },
  ];
}
