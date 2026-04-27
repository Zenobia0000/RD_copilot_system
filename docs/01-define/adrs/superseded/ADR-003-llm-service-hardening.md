# ADR-003: LLM 服務層強化 — Retry、驗證、Token 管理、Prompt 版控

- **Status**: Superseded (2026-04-27)
- **Date**: 2026-03-13 (proposed) → 2026-04-21 (status updated) → 2026-04-27 (superseded)
- **Deciders**: Development Team
- **Superseded By**: ADR-006 (Harness 架構 — model_adapter + prompt_assembler)

> **Superseded Notice (2026-04-27)**:
>
> 本 ADR 已封存。封存原因：
>
> 1. **Phase 1 已實作並保留於程式碼中** — retry decorator、Pydantic validation、prompt 分離仍有效，但已被 Harness 層包裝。
> 2. **Phase 2 被 ADR-006 取代** — Prompt 外部化原計劃為 `prompts/templates/*.md`，現由 `backend/app/harness/prompt_assembler.py` (context engineering + cache budget) 實現；Token tracking 由 `backend/app/observability/` 處理。
> 3. **Phase 3 被 ADR-006 取代** — Model routing 原計劃為 sonnet/haiku 按複雜度切換，現由 `backend/app/harness/model_adapter.py` 封裝 `_call_provider` 實現。
>
> 歷史參考價值：Phase 1 的設計決策（retry 策略、Pydantic 驗證模式）仍是現行 Harness 層的基礎。

---

> **Implementation Note (2026-04-21)** *(歷史記錄)*:
> - ✅ Phase 1 — Retry: `backend/app/agents/base.py` (`retry_on_transient` decorator, exponential backoff)
> - ✅ Phase 1 — Output validation: `call_llm_structured()` with Pydantic model validation
> - ✅ Phase 1 — Prompt separation: `backend/app/prompts/` (4 files: analyst, triz_solver, evaluator, knowledge)
> - ⏳ Phase 2 — Token budget tracking: Not implemented → **Superseded by ADR-006 prompt_assembler**
> - ⏳ Phase 2 — External `.md` prompt files: **Superseded by ADR-006 prompt_assembler**
> - ⏳ Phase 3 — Model routing / A-B testing: **Superseded by ADR-006 model_adapter**

## Context

SOW v1.0 規劃了統一的 `LLMService` 入口，包含：
- Retry 機制（指數退避重試）
- Token 計數與預算管理
- 10 個 Prompt 模板（PM-1 至 PM-10），外部檔案載入、獨立版控
- Pydantic 2.0+ 結構化輸出驗證

### 現況（`backend/app/agents/base.py`）

```python
def call_llm_json(system, user_message, *, model=None, max_tokens=4096, temperature=0.2):
    client = get_llm()
    response = client.messages.create(...)
    return response.content[0].text  # 原始文字，無驗證
```

| 項目 | SOW 規格 | 現況 | 缺口嚴重度 |
|------|----------|------|-----------|
| Retry | 指數退避重試 | 單次呼叫，失敗即拋錯 | **高** — API 暫時性錯誤直接傳遞至使用者 |
| Token 管理 | 計數 + 預算追蹤 | 無任何 token 追蹤 | 中 — 無法監控成本 |
| Prompt 載入 | 外部 `.md`/`.yaml` 檔案 | 硬編碼於 Python 模組（`prompts/analyst.py` 等） | 中 — 修改 prompt 需改 code |
| 輸出驗證 | Pydantic 模型驗證 | `json.loads()` 直接解析，無結構驗證 | **高** — LLM 輸出異常將導致前端崩潰 |
| 模型路由 | 依任務複雜度選擇 sonnet/haiku | 固定 default_model，僅 knowledge agent 用 fast_model | 低 — 目前可接受 |

### 現有 Prompt 模板（對應 SOW PM-1 ~ PM-10）

| SOW ID | 用途 | 實際位置 |
|--------|------|----------|
| PM-1 | Task Definition | `prompts/analyst.py::BRIEF_EXTRACTION` |
| PM-2 | Socratic Questions | `prompts/analyst.py::SOCRATIC_QUESTIONS` |
| PM-3 | Contradiction Identify | `prompts/analyst.py::CLD_GENERATION` |
| PM-4 | TRIZ Solution | `prompts/triz_solver.py::TRIZ_TC_INSTANTIATION` |
| ~~PM-5~~ | ~~SCAMPER Variant~~ | ~~`prompts/triz_solver.py::SCAMPER_TRANSFORM`~~ **(v9 移除)** |
| ~~PM-6~~ | ~~Alternative Generate~~ | ~~`prompts/analyst.py::ANTI_ANCHOR_GENERATION`~~ **(已退役，AA 併入 TRIZ L1 跨域去錨定)** |
| PM-7 | Decision Record | `prompts/evaluator.py::MUST_EVALUATION` |
| PM-8 | Black Hat Review | `prompts/evaluator.py::RISK_ANALYSIS` |
| ~~PM-9~~ | ~~Anti-Anchor~~ | ~~`prompts/analyst.py::ANTI_ANCHOR_GENERATION`~~ **(已退役，AA 併入 TRIZ L1 跨域去錨定)** |
| PM-10 | Assumption Extract | `prompts/analyst.py::CONSTRAINT_SUGGESTION` |

## Decision

分三階段漸進強化 LLM 服務層：

### Phase 1 — v1.0 Release（P0）

1. **Retry 機制**：使用 `tenacity` 函式庫，裝飾 `call_llm_json` 和 `call_llm_structured`：
   - 最多 3 次重試
   - 指數退避（min=1s, max=10s）
   - 僅對 `APIStatusError(status_code >= 500)` 和 `APIConnectionError` 重試

2. **Pydantic 輸出驗證**：在每個 agent function 中，`json.loads()` 後加入 Pydantic model 驗證：
   ```python
   raw = call_llm_json(system, prompt)
   data = json.loads(raw)
   return ConstraintSuggestResponse.model_validate(data)  # 取代直接 **data 展開
   ```

3. **JSON 解析容錯**：處理 LLM 回傳 markdown code block 的情況：
   ```python
   text = raw.strip()
   if text.startswith("```"):
       text = text.split("\n", 1)[1].rsplit("```", 1)[0]
   ```

### Phase 2 — v1.0 Hardening（P1）

4. **Token 使用記錄**：從 Anthropic API response 的 `usage` 欄位提取 `input_tokens` / `output_tokens`，寫入 `llm_usage_logs` Supabase 表。

5. **Prompt 外部化**：將 prompt 模板移至 `backend/app/prompts/templates/*.md`，Python 模組改為載入器：
   ```python
   CONSTRAINT_SUGGESTION = load_template("constraint_suggestion.md")
   ```

### Phase 3 — v1.1（P2）

6. Prompt 版控（A/B 測試支援）
7. Per-project token 預算追蹤與告警
8. 智慧模型路由（依 prompt 長度/任務類型選擇 sonnet vs haiku）

## Consequences

### 正面

- Retry 可覆蓋 Anthropic API 的暫時性錯誤（rate limit、server error），減少使用者看到「AI 建議失敗」的頻率。
- Pydantic 驗證在 LLM 輸出異常時提供明確錯誤訊息，而非前端不可預期的 crash。
- Token logging 為成本監控和 prompt 優化提供數據基礎。

### 負面

- Retry 增加最差情況延遲（3 次重試 ≈ 額外 ~15s）。
- Pydantic 驗證可能拒絕 LLM 的合理但格式略有偏差的回應（需要 permissive schema 設計）。
- Phase 2 的 prompt 外部化需要一次性遷移所有 16 個 prompt，有短期工作量。

## Action Items

- [ ] 安裝 `tenacity`：加入 `pyproject.toml` dependencies
- [ ] 修改 `backend/app/agents/base.py`：加入 retry 裝飾器 + JSON 容錯
- [ ] 修改所有 agent functions（`analyst.py`, `triz_solver.py`, `evaluator.py`, `knowledge.py`）：加入 `.model_validate()` 驗證
- [ ] 建立 `llm_usage_logs` Supabase 表（Phase 2）
- [ ] 建立 `backend/app/prompts/templates/` 目錄並遷移 prompt（Phase 2）

## Related

- `backend/app/agents/base.py`: 現有 LLM client 實作
- `backend/app/models/schemas.py`: 已定義的 Pydantic response models
- `backend/app/prompts/`: 現有 prompt 模板
