# ADR-005：LLM 抽象層（多 provider 支援）

---

**狀態 (Status)**：`Proposed`
**決策者 (Deciders)**：TL, AI, ARCH, SEC
**決策日期 (Date)**：2026-04-28

---

## Context & Problem Statement

TRIZ skill 重度依賴 LLM。需考慮：
- 多 provider 支援（Anthropic / OpenAI / Azure OpenAI / 自建）
- Cost 控制
- Fallback（一家失效時切換）
- 企業合規（部分客戶要求自建）

---

## Considered Options

| Option | Pros | Cons |
|:-------|:-----|:-----|
| 直接呼叫 Anthropic SDK | 簡單 | 鎖定供應商 |
| 直接呼叫 OpenAI SDK | 同上 | 同上 |
| **LangChain（多 provider 抽象）** | 生態最大、provider 切換容易 | 抽象層 overhead、版本變動快 |
| 自建 adapter | 完全可控 | 工作量大 |

---

## Decision Outcome

**選擇**：LangChain v0.3+ 為主 + 自建薄抽象層（含 timeout / retry / cost tracking）

**架構**：
```
TRIZ Skill
    ↓
LLMProvider (interface)
    ├── AnthropicAdapter (LangChain)
    ├── OpenAIAdapter (LangChain)
    ├── AzureOpenAIAdapter (LangChain)
    └── LocalLLMAdapter (vLLM / Ollama)
```

**配置**：每個 skill 在 `SKILL.md` 宣告偏好 model（如 `claude-opus-4-7`），允許 admin 全域 override。

---

## Consequences

### Positive
- 客戶可選擇 provider
- 失效自動 fallback（先試主、失敗試備）
- Cost 集中追蹤（透過 LangSmith）

### Risks
- LangChain 版本不穩 → 鎖定 minor version、嚴格 changelog 檢查
- 抽象層性能損耗 < 5%（可接受）
- prompt 在不同 model 表現差異 → 對 P0 skill 做雙 provider 對標

---

## References

- LangChain：https://python.langchain.com/
- 既有 Skill 規格：`.claude/skills/triz-*/SKILL.md`
- 內容位置邊界：`.claude/CLAUDE.md`
