# Critical Path — WI 依賴與關鍵路徑

> **TRIZ Session**: 2026-04-28-1500-eBike-MidDrive-Coaxial
> **總工時估算**: ~32-46 週（TR0 → TR10）

---

## WI 依賴 DAG

```
TR0 ────┐
        ├─→ WI-01 (Halbach 馬達, ~6w) ──┬─→ ICD-01 ─┐
        ├─→ WI-02 (雙級齒輪, ~6w)    ──┼─→ ICD-02 ─┤
        ├─→ WI-03 (PCM 熱管理, ~5w)  ──┼─→ ICD-01 ─┤  (馬達 loss → 熱)
        ├─→ WI-05 (Drive Board, ~4w) ──┼─→ ICD-03 ─┤
        │                               │            │
        │                               ▼            ▼
        │                         WI-04 (Coaxial Housing 整合, ~4w)
        │                                    │
        │                                    ▼
        │                              ICD-04 + 完整 3D CAD ─→ TR3 凍結
        │                                    │
        ├─→ WI-07 (採購, 並行 +6-12w 長交期) ──→ TR4
        │                                    │
        │                                    ▼
        ▼                              Alpha 原型組裝 (TR5, ~4-6w)
   WI-06 (測試計畫, 並行)                     │
        │                                    ▼
        └────────────────────────────→ V1-V14 實測 (TR6, ~4-6w)
                                              │
                                              ▼
                                        DFM (TR7, ~4w)
                                              │
                                              ▼
                                        Beta (TR8, ~6w)
                                              │
                                              ▼
                                        DVP&R (TR9, ~8-12w)
                                              │
                                              ▼
                                        PPAP (TR10, ~4w)
```

---

## 關鍵路徑（Longest Path）

```
TR0 → WI-01 (6w) → ICD-01 (1w) → WI-04 (4w) → TR3 → 治工具 (TR4 並行) →
TR5 (5w) → TR6 (5w) → TR7 (4w) → TR8 (6w) → TR9 (10w) → TR10 (4w)
                                                = ~45 週（理想最短）
```

**主要瓶頸**：
1. **WI-01 Halbach FEA**：Halbach 增益估計需 3D EM FEA 驗證（C-B002），佔關鍵路徑首段
2. **WI-04 Coaxial 整合**：6 份 MC 必須先到位才能完整 3D CAD
3. **TR9 DVP&R**：耐久測試（10 萬次 125Nm 循環）天然慢

---

## 並行機會

| WI 群組 | 可並行條件 | 預期省時 |
|:--------|:-----------|:---------|
| WI-01, WI-02, WI-03, WI-05 | TR0→TR1 期間，4 個域獨立 FEA/設計 | ~6 週（vs 序列 ~21 週） |
| WI-07 採購 vs WI-04 結構整合 | 長交期下單可在 BOM 凍結前先發 | ~4-8 週 |
| WI-06 測試治具 vs 原型製作 | TR4 期間並行 | ~3 週 |

---

## 里程碑時程（樂觀版）

| 週次 | 里程碑 | Gate |
|:-----|:-------|:-----|
| W0 | TRIZ Step 5 完成（now） | TR0 ✓ |
| W6-8 | 4 子系統 FEA 全 PASS | TR1 |
| W10 | ICD 4 份簽核、軸承選定 | TR2 |
| W14-16 | 完整 3D CAD + DFMEA | TR3 |
| W14-22 | 長交期物料到貨（並行） | TR4 |
| W20-22 | Alpha 原型組裝 | TR5 |
| W25-28 | V1-V14 測試 | TR6 |
| W32 | DFM review + PFMEA | TR7 |
| W38 | Beta 原型 | TR8 |
| W46-50 | DVP&R | TR9 |
| W50-54 | PPAP + 量產 SOP | TR10 |
