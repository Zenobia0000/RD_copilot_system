import type { NavCardDef, PhaseProgress } from "@/types/project";

export function getMockNavCards(progress: PhaseProgress): NavCardDef[] {
  const gateD1 = progress["D1"] === "passed";
  const gateD2 = progress["D2"] === "passed";
  const gatePGD = progress["PG-D"] === "passed";
  const gateX1 = progress["X1"] === "passed";
  const gateX2 = progress["X2"] === "passed";
  const gatePGX = progress["PG-X"] === "passed";
  const gateV2 = progress["V2"] === "passed";

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
      completedSteps: gateD1 ? 1 : 0,
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
      completedSteps: countPassed("D2", "PG-D"),
      requiredGate: "D1",
      locked: !gateD1,
      lockReason: !gateD1 ? "需先完成 Brief (Gate D1)" : undefined,
    },
    {
      id: "track",
      enName: "Track",
      zhName: "假設追蹤",
      phase: "Phase 2",
      icon: "ListChecks",
      route: "track",
      subSteps: 1,
      completedSteps: gateX1 ? 1 : 0,
      requiredGate: "PG-D",
      locked: !gatePGD,
      lockReason: !gatePGD ? "需先完成 Phase 1 所有 Gate" : undefined,
    },
    {
      id: "create",
      enName: "Create",
      zhName: "方案創造",
      phase: "Phase 2",
      icon: "Wand2",
      route: "create",
      subSteps: 2,
      completedSteps: countPassed("X2", "PG-X"),
      requiredGate: "X1",
      locked: !gateX1,
      lockReason: !gateX1 ? "需先完成 Track (Gate X1)" : undefined,
    },
    {
      id: "cad",
      enName: "CAD",
      zhName: "CAD 繪製",
      phase: "Phase 2",
      icon: "PenTool",
      route: "cad",
      subSteps: 1,
      completedSteps: gatePGX ? 1 : 0,
      requiredGate: "PG-X",
      locked: !gatePGX,
      lockReason: !gatePGX ? "需先完成 Phase 2 所有 Gate" : undefined,
    },
    {
      id: "review",
      enName: "Review",
      zhName: "設計審查",
      phase: "Phase 3",
      icon: "Search",
      route: "review",
      subSteps: 1,
      completedSteps: gateV2 ? 1 : 0,
      requiredGate: "PG-X",
      locked: !gatePGX,
      lockReason: !gatePGX ? "需完成 CAD 繪製階段" : undefined,
    },
    {
      id: "decide",
      enName: "Decide",
      zhName: "最終決策",
      phase: "Phase 3",
      icon: "Gavel",
      route: "decide",
      subSteps: 2,
      completedSteps: countPassed("V2", "PG-V"),
      requiredGate: "V2",
      locked: !gateV2,
      lockReason: !gateV2 ? "需先完成 Review (Gate V2)" : undefined,
    },
  ];
}
