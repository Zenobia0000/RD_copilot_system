import type {
  TrizSolution, Subsystem, ScamperVariant, Alternative
} from "@/types/create";

export const mockTrizSolutions: Record<string, TrizSolution[]> = {
  "proj-001": [
    { id: "ts-001", contradictionId: "ec-001", path: "TC", principleNumber: 1, principleName: "分割", suggestion: "將馬達繞組分為高效區與低效區，在不同轉速下切換使用不同繞組，兼顧效能與噪音。", status: "adopted" },
    { id: "ts-002", contradictionId: "ec-001", path: "TC", principleNumber: 18, principleName: "機械振動", suggestion: "利用共振頻率設計阻尼系統，將噪音能量轉化為可控振動。", status: "pending" },
    { id: "ts-003", contradictionId: "ec-001", path: "PC", principleNumber: null, principleName: "時間分離", suggestion: "在不同使用場景（城市/郊外）切換高轉速/低轉速模式，時間上分離矛盾。", status: "adopted" },
    { id: "ts-004", contradictionId: "ec-001", path: "PC", principleNumber: null, principleName: "空間分離", suggestion: "將噪音產生區域與用戶感知區域空間隔離，增加隔音層。", status: "pending" },
    { id: "ts-005", contradictionId: "ec-002", path: "TC", principleNumber: 40, principleName: "複合材料", suggestion: "使用碳纖維增強塑膠替代金屬，在相同強度下減輕重量。", status: "adopted" },
    { id: "ts-006", contradictionId: "ec-002", path: "SF", principleNumber: null, principleName: "標準解 #2.1", suggestion: "引入中介物質（泡沫金屬填充）提升結構剛性而不增加顯著重量。", status: "pending" },
  ],
};

export const mockSubsystems: Record<string, Subsystem[]> = {
  "proj-001": [
    { id: "ss-001", name: "動力傳動模組", reason: "與馬達轉速、傳動效率直接相關", relatedContradictions: ["ec-001"], confirmed: true, interfaces: ["馬達安裝座介面", "熱傳導介面"], source: "ai" },
    { id: "ss-002", name: "殼體結構模組", reason: "與材料強度、重量直接相關", relatedContradictions: ["ec-002"], confirmed: true, interfaces: ["馬達安裝座介面", "密封面介面"], source: "ai" },
    { id: "ss-003", name: "散熱模組", reason: "馬達轉速提高將增加散熱需求", relatedContradictions: ["ec-001"], confirmed: false, interfaces: ["熱傳導介面"], source: "ai" },
    { id: "ss-004", name: "密封模組", reason: "IP55 防護等級涉及密封設計", relatedContradictions: [], confirmed: false, interfaces: ["密封面介面"], source: "ai" },
  ],
};

export const mockScamperVariants: Record<string, ScamperVariant[]> = {
  "proj-001": [
    { id: "sv-001", subsystemId: "ss-001", action: "S", description: "以磁力耦合器替代機械齒輪傳動，消除接觸磨耗與噪音。", adopted: true, newContradictions: [
      { id: "snc-001", description: "替代為磁力耦合後，扭矩傳遞效率在高溫下可能降低（效率 vs 溫度穩定性）", severity: "major", fedBack: false },
    ] },
    { id: "sv-002", subsystemId: "ss-001", action: "C", description: "將馬達與減速機整合為一體式模組，減少零件數量與組裝誤差。", adopted: false },
    { id: "sv-003", subsystemId: "ss-001", action: "E", description: "消除中間傳動軸，改用同軸直連結構。", adopted: true, newContradictions: [
      { id: "snc-002", description: "同軸直連移除緩衝機構，瞬間衝擊負載直接傳至馬達軸承", severity: "fatal", fedBack: false },
      { id: "snc-003", description: "組裝公差要求從 0.1mm 提升至 0.03mm，製造成本微增", severity: "minor", fedBack: false },
    ] },
    { id: "sv-004", subsystemId: "ss-002", action: "S", description: "以拓撲優化結構替代實心殼體，在關鍵應力路徑保留材料。", adopted: false },
    { id: "sv-005", subsystemId: "ss-002", action: "M", description: "將殼體壁厚從均勻改為漸變設計，高應力區加厚、低應力區減薄。", adopted: true },
    { id: "sv-006", subsystemId: "ss-002", action: "A", description: "借鑑航太蜂巢結構，以蜂巢夾層提升剛度重量比。", adopted: false },
  ],
};

export const mockAlternatives: Record<string, Alternative[]> = {
  "proj-001": [
    {
      id: "alt-001",
      name: "磁力耦合 + 可變轉速方案",
      mechanism: "採用磁力耦合器替代機械傳動，搭配雙繞組馬達實現高低轉速切換。城市模式低轉速低噪音，郊區模式高轉速高效能。殼體採用碳纖維增強材料減重。",
      source: "ai_integrated",
      keyAssumptionIds: ["ta-001", "ta-002"],
      mustScores: { M1: "pass", M2: "pass", M3: "pass", M4: "pass", M5: "marginal", M6: "pass" },
      interfaceContract: { envelope: "Φ120×180mm", loadPath: "磁力耦合→輪軸", signalPath: "CAN Bus", thermalPath: "鋁殼散熱鰭片", datumTolerance: "同軸度 0.05mm", serviceability: "側蓋可拆" },
      preCadScores: { must: 4, decoupling: 5, testability: 4, failureMech: 3, mvpCadEffort: 3 },
      overallPass: true,
    },
    {
      id: "alt-002",
      name: "同軸直連 + 漸變壁厚方案",
      mechanism: "消除中間傳動軸改用同軸直連，殼體採用漸變壁厚設計。高應力區使用 PA66+GF30 加厚至 4mm，低應力區減至 2mm，兼顧強度與重量。搭配橡膠阻尼墊降低振動傳遞。",
      source: "triz_tc",
      keyAssumptionIds: ["ta-003", "ta-005"],
      mustScores: { M1: "pass", M2: "pass", M3: "marginal", M4: "pass", M5: "pass", M6: "pass" },
      interfaceContract: { envelope: "Φ110×160mm", loadPath: "同軸直連→花鍵", signalPath: "模擬信號", thermalPath: "自然對流", datumTolerance: "同軸度 0.08mm", serviceability: "需拆馬達" },
      preCadScores: { must: 3, decoupling: 3, testability: 4, failureMech: 3, mvpCadEffort: 4 },
      overallPass: true,
    },
    {
      id: "alt-003",
      name: "輪轂直驅方案",
      mechanism: "完全捨棄傳統中驅+傳動系統，改用輪轂馬達直接驅動。消除傳動損失、噪音與重量。但需解決簧下質量增加的問題。",
      source: "manual",
      keyAssumptionIds: ["ta-001"],
      mustScores: { M1: "pass", M2: "fail", M3: "pass", M4: "pass", M5: "fail", M6: "fail" },
      interfaceContract: { envelope: "", loadPath: "", signalPath: "", thermalPath: "", datumTolerance: "", serviceability: "" },
      preCadScores: { must: null, decoupling: null, testability: null, failureMech: null, mvpCadEffort: null },
      overallPass: null,
    },
  ],
};

