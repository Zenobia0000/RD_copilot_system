---
description: TRIZ 主入口。自動偵測問題類型並路由到適當步驟。
---

# TRIZ 主入口

載入 **triz-router** skill，分析使用者的問題描述並路由到適當的 TRIZ 步驟。

## 使用方式

```
/triz                              # 互動式引導
/triz 馬達散熱不足但不能加大體積      # 直接描述矛盾
/triz resume                       # 恢復上次 session
```

## 路由邏輯

- 有明確矛盾 → `/triz-solve`
- 功能缺失無副作用 → `/triz-solve --sf-only`
- 問題症狀描述 → `/triz-scope`
- 需要功能建模 → `/triz-model`
- 無法判斷 → 引導式問答
