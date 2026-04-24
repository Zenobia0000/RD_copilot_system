---
description: TRIZ Step 2+3 TC/PC/SF 解題。參數映射、矩陣查表、分離策略、SF 標準解。
---

# TRIZ Step 2+3: 解題管線

載入 **triz-contradict** skill，執行完整的 TC → PC → SF 解題管線。

## 使用方式

```
/triz-solve                        # 從 Step 1 產出接續
/triz-solve --sf-only              # SF-only 快速通道（功能缺失無矛盾）
/triz-solve 改善強度會惡化重量        # 直接輸入 TC
```

## 三種模式

1. **TC 主路徑**：參數映射 → 矩陣查表 → 原理具體化 → OZ-OT-Px → PC → 分離 → SF
2. **Multi-TC**：瓶頸路徑 或 SIM 路徑
3. **SF-only**：功能缺失 → 直接 SF 標準解
