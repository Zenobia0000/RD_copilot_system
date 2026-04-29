# UAT SOP — e-Bike Mid-Drive Unit 全功能驗證

**版本**：v1.0
**日期**：2026-04-28
**測試案例**：e-Bike coaxial mid-mounted drive unit (OD111mm / 92mm axial / 2500g / 125Nm peak)
**預計時間**：60-90 分鐘（含 LLM 等待時間）
**LLM 成本**：~$0.50-1.00（Azure Claude Sonnet 4.6）

---

## 前置準備

### P1. 環境確認

```bash
# 1. 切到專案根目錄
cd /home/os-sunnie.gd.weng/python_workstation/sunny_01/RD_copilot_system

# 2. 確認 .env 存在且 LLM provider 可用
cat .env | grep LLM_PROVIDER
# 預期：LLM_PROVIDER=azure_openai

# 3. 確認 CLI 可運行
cd backend && python3 -m app.harness --help
# 預期：顯示 usage 說明

# 4. 確認 LLM 連線
python3 -c "
from app.harness.config import build_client, load_env
from pathlib import Path
load_env(Path('../.env'))
hc = build_client()
print(f'OK: provider={hc.provider} model={hc.default_model}')
"
# 預期：OK: provider=azure model=claude-sonnet-4-6

# 5. 確認 KB 檔案完整
ls ../knowledge/triz/
# 預期：01_39_parameters.md ~ 07_tc_pc_sf_differences.md + README.md（8 個檔案）

# 6. 確認自動化測試全過
python3 -m pytest --tb=short -q
# 預期：463 passed（數字可能隨版本增加）
```

**判定**：6 項全 PASS → 進入測試。任一 FAIL → 先修復再繼續。

### P2. 備份現有 session（保護既有資料）

```bash
cd /home/os-sunnie.gd.weng/python_workstation/sunny_01/RD_copilot_system

# 備份 TRIZ state
cp .claude/context/triz/.triz-state.json \
   .claude/context/triz/.triz-state.json.bak-uat

# 備份 TR state（如存在）
[ -f .claude/context/triz/.tr-state.json ] && \
  cp .claude/context/triz/.tr-state.json \
     .claude/context/triz/.tr-state.json.bak-uat

echo "備份完成"
```

---

## 測試區段一覽

| # | 區段 | 測試項目數 | 預估時間 | LLM 呼叫 |
|:-:|:-----|:---------:|:--------:|:---------:|
| A | CLI 基礎設施 | 5 | 5 min | 0 |
| B | HTTP API 基礎設施 | 4 | 5 min | 0 |
| C | Domain Config 解耦 | 3 | 3 min | 0 |
| D | TRIZ 完整流程（CLI） | 7 | 40 min | 7 |
| E | TR 工程執行（CLI） | 4 | 15 min | 4 |
| F | HTTP SSE 串流 | 2 | 10 min | 2 |
| G | 狀態持久化與恢復 | 3 | 5 min | 1 |
| H | 邊界條件與錯誤處理 | 5 | 5 min | 0 |
|   | **合計** | **33** | **~88 min** | **14** |

---

## A. CLI 基礎設施（無 LLM 呼叫）

### A1. Project Root 探測

```bash
cd /home/os-sunnie.gd.weng/python_workstation/sunny_01/RD_copilot_system/backend
python3 -c "
from app.harness.cli import find_project_root
print(find_project_root())
"
```

| 項目 | 預期 |
|:-----|:-----|
| 輸出 | `/home/os-sunnie.gd.weng/python_workstation/sunny_01/RD_copilot_system` |

**PASS / FAIL**：______

### A2. Command 解析 — 存在的指令

```bash
python3 -c "
from pathlib import Path
from app.harness.command import resolve_command
root = Path('../')
r = resolve_command(
    commands_root=root / '.claude/commands',
    skills_root=root / '.claude/skills',
    name='triz-solve',
)
print(f'name={r.name} label={r.label}')
print(f'allowed_tools count: {len(r.allowed_tools) if r.allowed_tools else \"all\"}')
print(f'body length: {len(r.body)} chars')
"
```

| 項目 | 預期 |
|:-----|:-----|
| name | `triz-solve` 或 `triz-contradict` |
| label | 包含 `triz-contradict` |
| body length | > 1000 chars |

**PASS / FAIL**：______

### A3. Command 解析 — 不存在的指令

```bash
python3 -c "
from pathlib import Path
from app.harness.command import resolve_command
try:
    resolve_command(
        commands_root=Path('../.claude/commands'),
        skills_root=Path('../.claude/skills'),
        name='nonexistent-command',
    )
    print('ERROR: should have raised')
except FileNotFoundError as e:
    print(f'OK: {e}')
"
```

| 項目 | 預期 |
|:-----|:-----|
| 輸出 | `OK: ...` (FileNotFoundError 被正確拋出) |

**PASS / FAIL**：______

### A4. Skill 載入 — frontmatter 解析

```bash
python3 -c "
from pathlib import Path
from app.harness.skill import load_skill
skill = load_skill(Path('../.claude/skills/triz-contradict'))
print(f'name={skill.name}')
print(f'description={skill.description[:60]}...')
print(f'allowed_tools={skill.allowed_tools}')
print(f'body length: {len(skill.body)} chars')
"
```

| 項目 | 預期 |
|:-----|:-----|
| name | `triz-contradict` |
| body | > 5000 chars（含 KB 內嵌） |

**PASS / FAIL**：______

### A5. KB Loader 驗證

```bash
python3 -c "
from pathlib import Path
from app.triz.kb.loader import KBLoader
kb = KBLoader(Path('../knowledge/triz'))
params = kb.parameters()
matrix = kb.matrix()
principles = kb.principles()
print(f'Parameters: {len(params)} entries')
print(f'Matrix: {len(matrix)} rows')
print(f'Principles: {len(principles)} entries')
print(f'Sample param: {list(params.keys())[:3]}')
"
```

| 項目 | 預期 |
|:-----|:-----|
| Parameters | 39 entries |
| Matrix | 39 rows |
| Principles | 40 entries |

**PASS / FAIL**：______

---

## B. HTTP API 基礎設施

### B1. 啟動 Server

```bash
# 開一個新 terminal，或在背景執行
cd /home/os-sunnie.gd.weng/python_workstation/sunny_01/RD_copilot_system/backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
sleep 2
```

### B2. Health Check

```bash
curl -s http://localhost:8000/api/v1/health | python3 -m json.tool
```

| 項目 | 預期 |
|:-----|:-----|
| HTTP status | 200 |
| body | `{"status": "ok"}` |

**PASS / FAIL**：______

### B3. 建立 Session（dev bypass auth）

```bash
# DEV_BYPASS_AUTH=true 時，任意 Bearer token 都通過
curl -s -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev-test-token" \
  -d '{"title": "UAT e-Bike test"}' | python3 -m json.tool
```

| 項目 | 預期 |
|:-----|:-----|
| HTTP status | 200 |
| body | 包含 `session_id`（格式 `sess_xxxx`）和 `created_at` |

記下 `session_id`：**__________________________**

**PASS / FAIL**：______

### B4. 取回 Session

```bash
# 替換 <SESSION_ID>
curl -s http://localhost:8000/api/v1/sessions/<SESSION_ID> \
  -H "Authorization: Bearer dev-test-token" | python3 -m json.tool
```

| 項目 | 預期 |
|:-----|:-----|
| title | `UAT e-Bike test` |
| runs | `[]`（空陣列） |

**PASS / FAIL**：______

---

## C. Domain Config 解耦驗證（無 LLM）

### C1. domain.yaml 被正確載入

```bash
python3 -c "
from pathlib import Path
from app.harness.domain_config import load_domain_config
cfg = load_domain_config(Path('..'))
print(f'domain_id: {cfg.domain_id}')
print(f'prefixes: {cfg.command_prefixes}')
print(f'kb_root: {cfg.paths.kb_root}')
print(f'categories: {len(cfg.artifact_categories)} items')
"
```

| 項目 | 預期 |
|:-----|:-----|
| domain_id | `triz-mechanical` |
| prefixes | `['triz-', 'triz', 'tr-', 'tr']` |
| kb_root | `knowledge/triz` |
| categories | 13 items |

**PASS / FAIL**：______

### C2. Domain 指令判定

```bash
python3 -c "
from pathlib import Path
from app.harness.domain_config import load_domain_config
cfg = load_domain_config(Path('..'))
tests = ['triz-solve', 'tr-gate', 'triz', 'help', 'deploy', 'tr-dfm']
for cmd in tests:
    print(f'  {cmd:15s} → domain={cfg.is_domain_command(cmd)}')
"
```

| 指令 | 預期 |
|:-----|:-----|
| triz-solve | `True` |
| tr-gate | `True` |
| triz | `True` |
| help | `False` |
| deploy | `False` |
| tr-dfm | `True` |

**PASS / FAIL**：______

### C3. Fallback — 無 domain.yaml 時使用預設值

```bash
python3 -c "
from pathlib import Path
from app.harness.domain_config import load_domain_config, DomainConfig
# 用一個不存在 domain.yaml 的路徑
load_domain_config.cache_clear()
cfg = load_domain_config(Path('/tmp'))
print(f'domain_id: {cfg.domain_id}')
print(f'prefixes: {cfg.command_prefixes}')
print('OK: fallback to defaults')
load_domain_config.cache_clear()  # 清除，不影響後續
"
```

| 項目 | 預期 |
|:-----|:-----|
| 輸出 | `OK: fallback to defaults` |
| domain_id | `triz-mechanical`（預設值） |

**PASS / FAIL**：______

---

## D. TRIZ 完整流程（CLI — 真實 LLM 呼叫）

> **重要**：以下每步都會呼叫 LLM，每步約 $0.02-0.05。
> 所有指令在 `backend/` 目錄下執行。
> 使用 `--max-iterations 5 --max-tokens 4000` 節省成本。

### D0. 清理舊 session（開始全新流程）

```bash
# 先備份（P2 已做過，這裡再確認）
cd /home/os-sunnie.gd.weng/python_workstation/sunny_01/RD_copilot_system

# 移除舊 state，讓 /triz 建立全新 session
mv .claude/context/triz/.triz-state.json \
   .claude/context/triz/.triz-state.json.bak-uat-d0 2>/dev/null
echo "清理完成，準備全新 session"
```

### D1. `/triz` — 主入口路由

```bash
cd backend
python3 -m app.harness triz \
  "e-Bike mid-drive unit: coaxial structure, gearbox+motor+drive board+pedaling shaft. \
   目標: OD111mm, axial 92mm, 2500g, peak 125Nm, continuous 100Nm, 低噪對標 TQ HPR50" \
  --max-iterations 5 --max-tokens 4000 2>&1 | tee /tmp/uat_d1_triz.log
```

**驗證清單**：

| # | 驗證項目 | 預期 | 實際 |
|:-:|:---------|:-----|:-----|
| 1 | stderr 顯示路由資訊 | `==> /triz → Skill: triz-router \| provider=azure \| model=claude-sonnet-4-6` | |
| 2 | 輸出包含路由判斷 | 識別為「有多個技術矛盾」或「問題症狀需定向」 | |
| 3 | 建議下一步 | 提示執行 `/triz-scope` 或 `/triz-solve` | |
| 4 | .triz-state.json 被建立 | `cat ../.claude/context/triz/.triz-state.json` 有內容 | |
| 5 | session 報告檔被建立 | `ls ../.claude/context/triz/session-*.md` 有新檔案 | |

**PASS / FAIL**：______

### D2. `/triz-scope` — Step 0 問題定向

```bash
python3 -m app.harness triz-scope \
  "馬達在爬坡持續高扭力輸出時，殼體溫度過高(>85°C)導致磁鐵退磁風險，但散熱空間被 OD111mm 限制" \
  --max-iterations 5 --max-tokens 4000 2>&1 | tee /tmp/uat_d2_scope.log
```

**驗證清單**：

| # | 驗證項目 | 預期 |
|:-:|:---------|:-----|
| 1 | 輸出包含 5Why 分析 | 至少 3 層 Why |
| 2 | 識別子系統 | 提到 motor/shell/thermal 相關組件 |
| 3 | TC 假設 | 提出至少一個技術矛盾假設 |
| 4 | OZ/OT 候選 | 識別操作區域和操作時間 |
| 5 | state 更新 | `.triz-state.json` 中 step0 區段有 `completed: true` |

```bash
# 驗證 state
python3 -c "
import json
from pathlib import Path
state = json.loads(Path('../.claude/context/triz/.triz-state.json').read_text())
print(f'current_step: {state.get(\"current_step\")}')
s0 = state.get('step0', {})
print(f'step0.completed: {s0.get(\"completed\")}')
"
```

**PASS / FAIL**：______

### D3. `/triz-model` — Step 1 功能建模

```bash
python3 -m app.harness triz-model \
  "子系統: motor stator + rotor + shell + 空氣間隙。痛點: 散熱不足導致磁鐵退磁" \
  --max-iterations 8 --max-tokens 4000 2>&1 | tee /tmp/uat_d3_model.log
```

**驗證清單**：

| # | 驗證項目 | 預期 |
|:-:|:---------|:-----|
| 1 | 組件交互圖 | 表格列出 source → function → target，至少 5 行 |
| 2 | 交互類型標記 | 包含 有效/有害/不足 至少兩種類型 |
| 3 | SF 診斷 | S1-F-S2 模型，至少 2 個紅線診斷 |
| 4 | 改善/惡化造句 | 「在 [系統] 中，為了 [A]，會導致 [B]」格式 |
| 5 | 路由建議 | TC 路徑 或 SF-only |
| 6 | state 更新 | step1.completed = true |

```bash
# 驗證 state
python3 -c "
import json
from pathlib import Path
state = json.loads(Path('../.claude/context/triz/.triz-state.json').read_text())
print(f'current_step: {state.get(\"current_step\")}')
s1 = state.get('step1', {})
print(f'step1.completed: {s1.get(\"completed\")}')
print(f'routing: {s1.get(\"routing\")}')
"
```

**PASS / FAIL**：______

### D4. `/triz-solve` — Step 2+3 解題管線（核心功能）

```bash
python3 -m app.harness triz-solve \
  "改善散熱效率（溫度）會惡化體積/重量（外殼尺寸受限OD111mm）" \
  --max-iterations 15 --max-tokens 8000 2>&1 | tee /tmp/uat_d4_solve.log
```

**驗證清單**：

| # | 驗證項目 | 預期 |
|:-:|:---------|:-----|
| 1 | **參數映射** | 改善/惡化各映射到 39 參數中的具體參數（如 #17 溫度、#8 體積） |
| 2 | **矩陣查表** | 輸出候選發明原理編號（如 #35 參數變化、#2 抽取） |
| 3 | **原理具體化** | 每個原理有針對 e-Bike 散熱的具體化方案 |
| 4 | **OZ-OT 定義** | 識別操作區域（motor-shell 界面）和操作時間（爬坡高扭力段） |
| 5 | **PC 物理矛盾** | 格式：「散熱面積應該大（導熱）又應該小（體積限制）」 |
| 6 | **分離策略** | 選擇了 4 大分離原則之一並說明理由 |
| 7 | **SF 標準解** | 匹配到 76 標準解中的具體編號 |
| 8 | **Tool 使用記錄** | stderr 顯示 MatrixLookup / ParamMap 等 tool_use 事件 |
| 9 | **state 更新** | step2.completed = true, step3.completed = true |

```bash
# 驗證 tool 使用（從 log 中找）
grep -c "tool_calls=" /tmp/uat_d4_solve.log
# 預期：至少 1（stderr 最後一行有 tool_calls=N，N > 0）

# 驗證 state
python3 -c "
import json
from pathlib import Path
state = json.loads(Path('../.claude/context/triz/.triz-state.json').read_text())
print(f'current_step: {state.get(\"current_step\")}')
for key in ['step2', 'step3']:
    s = state.get(key, {})
    print(f'{key}.completed: {s.get(\"completed\")}')
"
```

**PASS / FAIL**：______

### D5. `/triz-verify` — Step 4 驗證

```bash
python3 -m app.harness triz-verify \
  --max-iterations 10 --max-tokens 4000 2>&1 | tee /tmp/uat_d5_verify.log
```

**驗證清單**：

| # | 驗證項目 | 預期 |
|:-:|:---------|:-----|
| 1 | 讀取 Step 3 產出 | 從 state 載入解法方案 |
| 2 | Px 分離驗證 | 驗證分離策略的物理可行性 |
| 3 | 複雜度判定（CCI） | 四問 + 量化分數 |
| 4 | 新 TC 偵測 | 檢查解法是否引入新矛盾 |
| 5 | 進化/補丁判定 | 明確輸出「進化」或「補丁」 |
| 6 | state 更新 | step4.completed = true |

**PASS / FAIL**：______

### D6. `/triz-wi` — Step 5 WI 產出

```bash
python3 -m app.harness triz-wi \
  --max-iterations 10 --max-tokens 4000 2>&1 | tee /tmp/uat_d6_wi.log
```

**驗證清單**：

| # | 驗證項目 | 預期 |
|:-:|:---------|:-----|
| 1 | 讀取 verify 產出 | 從 state 載入概念凍結方案 |
| 2 | WI 文件產出 | 在 `docs/engineering/work_instructions/` 產出新 WI |
| 3 | 內容完整性 | WI 包含：目的、適用範圍、材料/工具、步驟、驗收標準 |
| 4 | state 更新 | step5.completed = true |

```bash
# 檢查是否有新 WI 產出
ls -lt ../docs/engineering/work_instructions/ | head -5
```

**PASS / FAIL**：______

### D7. `/triz-status` — 狀態總覽

```bash
python3 -m app.harness triz-status \
  --max-iterations 3 --max-tokens 2000 2>&1 | tee /tmp/uat_d7_status.log
```

**驗證清單**：

| # | 驗證項目 | 預期 |
|:-:|:---------|:-----|
| 1 | 顯示 session ID | 與 .triz-state.json 一致 |
| 2 | 顯示各步驟狀態 | Step 0-5 各顯示 completed/pending |
| 3 | 顯示問題描述 | 包含 e-Bike 相關關鍵字 |

**PASS / FAIL**：______

---

## E. TR 工程執行（CLI）

### E1. `/tr` — TR 儀表板

```bash
python3 -m app.harness tr \
  --max-iterations 3 --max-tokens 2000 2>&1 | tee /tmp/uat_e1_tr.log
```

| # | 驗證項目 | 預期 |
|:-:|:---------|:-----|
| 1 | 顯示 TR 狀態 | 列出 TR0-TR10 進度 |
| 2 | 路由建議 | 提示下一步該做的 gate |

**PASS / FAIL**：______

### E2. `/tr-gate TR1` — Gate Review

```bash
python3 -m app.harness tr-gate TR1 \
  --max-iterations 8 --max-tokens 4000 2>&1 | tee /tmp/uat_e2_gate.log
```

| # | 驗證項目 | 預期 |
|:-:|:---------|:-----|
| 1 | Gate review 報告 | 結構化的可行性評估 |
| 2 | 讀取 WI/MC/ICD | 參照 docs/engineering/ 下的文件 |
| 3 | Gate 判定 | GO / CONDITIONAL GO / NO-GO |
| 4 | 報告落地 | `docs/engineering/gate_reviews/` 下有新檔案 |

```bash
ls -lt ../docs/engineering/gate_reviews/ | head -5
```

**PASS / FAIL**：______

### E3. `/tr-dfm` — DFM 審查

```bash
python3 -m app.harness tr-dfm shell \
  --max-iterations 8 --max-tokens 4000 2>&1 | tee /tmp/uat_e3_dfm.log
```

| # | 驗證項目 | 預期 |
|:-:|:---------|:-----|
| 1 | DFM 報告 | 針對 shell（AZ91D 鎂合金壓鑄）的製造性審查 |
| 2 | 讀取 MC | 參照 MC-05_az91d.md 材料卡 |
| 3 | 報告落地 | `docs/engineering/dfm_reviews/` 下有新檔案 |

**PASS / FAIL**：______

### E4. `/tr-test` — 測試報告

```bash
python3 -m app.harness tr-test V1 \
  --max-iterations 8 --max-tokens 4000 2>&1 | tee /tmp/uat_e4_test.log
```

| # | 驗證項目 | 預期 |
|:-:|:---------|:-----|
| 1 | 測試報告 | V1 驗證報告結構（目的、方法、標準、結果） |
| 2 | 報告落地 | `docs/engineering/test_reports/` 下有新檔案 |

**PASS / FAIL**：______

---

## F. HTTP SSE 串流驗證

> 需要 server 在 B1 已啟動。

### F1. SSE `/triz-status`（低成本快速測試）

```bash
# 替換 <SESSION_ID> 為 B3 取得的 session_id
curl -s -N -X POST \
  http://localhost:8000/api/v1/sessions/<SESSION_ID>/run/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev-test-token" \
  -d '{
    "command": "/triz-status",
    "user_message": "顯示目前進度",
    "max_iterations": 3,
    "max_tokens": 2000
  }' 2>&1 | head -50
```

| # | 驗證項目 | 預期 |
|:-:|:---------|:-----|
| 1 | SSE 格式 | 每個事件 `event: xxx\ndata: {...}\n\n` |
| 2 | worker_status | 出現 `spawning` → `running` → `finished` |
| 3 | text_delta 事件 | 出現多個 text_delta（漸進輸出） |
| 4 | done 事件 | 最後一個事件為 `event: done` |
| 5 | JSON 可解析 | 每行 data 都是有效 JSON |

**PASS / FAIL**：______

### F2. SSE `/triz-solve`（驗證 tool_use 事件可見）

```bash
curl -s -N -X POST \
  http://localhost:8000/api/v1/sessions/<SESSION_ID>/run/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev-test-token" \
  -d '{
    "command": "/triz-solve",
    "user_message": "改善散熱效率會惡化體積重量",
    "max_iterations": 5,
    "max_tokens": 4000
  }' 2>&1 | tee /tmp/uat_f2_sse.log | head -80
```

| # | 驗證項目 | 預期 |
|:-:|:---------|:-----|
| 1 | tool_use 事件 | 出現 `event: tool_use`，name 為 MatrixLookup/ParamMap 等 |
| 2 | tool_result 事件 | 對應的 `event: tool_result` 回傳 |
| 3 | iteration_end | 每輪迭代結束有 `event: iteration_end` |

```bash
# 統計事件類型
grep "^event:" /tmp/uat_f2_sse.log | sort | uniq -c | sort -rn
```

**PASS / FAIL**：______

---

## G. 狀態持久化與恢復

### G1. State JSON 格式驗證

```bash
python3 -c "
import json
from pathlib import Path
state_path = Path('../.claude/context/triz/.triz-state.json')
state = json.loads(state_path.read_text())
required = ['session_id', 'created_at', 'current_step', 'problem_description']
for key in required:
    val = state.get(key)
    print(f'  {key}: {\"OK\" if val else \"MISSING\"} → {str(val)[:60] if val else \"\"}'  )
"
```

| 項目 | 預期 |
|:-----|:-----|
| 所有 required keys | `OK` |

**PASS / FAIL**：______

### G2. 報告檔逐步追加

```bash
# 檢查 session 報告檔
REPORT=$(python3 -c "
import json; from pathlib import Path
s = json.loads(Path('../.claude/context/triz/.triz-state.json').read_text())
print(s.get('report_file', 'NOT SET'))
")
echo "Report file: $REPORT"

# 檢查有多少 Step 區段
grep -c "^## Step" "../$REPORT" 2>/dev/null || echo "報告檔不存在或無 Step 標題"
```

| 項目 | 預期 |
|:-----|:-----|
| 報告檔存在 | `.claude/context/triz/session-*.md` |
| Step 區段數 | 與完成的步驟數一致 |

**PASS / FAIL**：______

### G3. 中斷恢復 — `/triz resume`

```bash
python3 -m app.harness triz resume \
  --max-iterations 3 --max-tokens 2000 2>&1 | tee /tmp/uat_g3_resume.log
```

| # | 驗證項目 | 預期 |
|:-:|:---------|:-----|
| 1 | 讀取既有 state | 識別到 session ID 和已完成步驟 |
| 2 | 提示下一步 | 建議執行尚未完成的步驟 |

**PASS / FAIL**：______

---

## H. 邊界條件與錯誤處理（無 LLM）

### H1. 不存在的指令

```bash
python3 -m app.harness nonexistent-cmd "test" 2>&1
echo "exit code: $?"
```

| 項目 | 預期 |
|:-----|:-----|
| stderr | `error: ...not found...` |
| exit code | `2` |

**PASS / FAIL**：______

### H2. 不存在的 Session（HTTP）

```bash
curl -s -w "\nHTTP_STATUS: %{http_code}\n" \
  http://localhost:8000/api/v1/sessions/sess_nonexistent \
  -H "Authorization: Bearer dev-test-token"
```

| 項目 | 預期 |
|:-----|:-----|
| HTTP status | 404 |
| body | `session sess_nonexistent not found` |

**PASS / FAIL**：______

### H3. 無 Auth Header

```bash
curl -s -w "\nHTTP_STATUS: %{http_code}\n" \
  http://localhost:8000/api/v1/sessions
```

| 項目 | 預期 |
|:-----|:-----|
| HTTP status | 401 或 403（取決於 bypass mode） |

> 注意：若 `VITE_DEV_BYPASS_AUTH=true`，此測試可能返回 422（缺少 header）而非 401。記錄實際行為。

**PASS / FAIL**：______

### H4. 非法 max_iterations

```bash
curl -s -w "\nHTTP_STATUS: %{http_code}\n" -X POST \
  http://localhost:8000/api/v1/sessions/<SESSION_ID>/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev-test-token" \
  -d '{"command": "/triz-status", "max_iterations": 999}'
```

| 項目 | 預期 |
|:-----|:-----|
| HTTP status | 422（Validation Error，max_iterations le 100） |

**PASS / FAIL**：______

### H5. 空 user_message（使用預設）

```bash
python3 -m app.harness triz-status \
  --max-iterations 2 --max-tokens 1000 2>&1 | tail -3
```

| 項目 | 預期 |
|:-----|:-----|
| 不報錯 | 正常執行，使用預設中文提示 |
| exit code | `0` |

**PASS / FAIL**：______

---

## 收尾

### 1. 還原備份（可選）

```bash
cd /home/os-sunnie.gd.weng/python_workstation/sunny_01/RD_copilot_system

# 如果要恢復 UAT 前的 session state
cp .claude/context/triz/.triz-state.json.bak-uat \
   .claude/context/triz/.triz-state.json
```

### 2. 停止 Server

```bash
kill %1  # 或找到 uvicorn PID
# pkill -f "uvicorn app.main:app"
```

### 3. 清理 log

```bash
rm -f /tmp/uat_d*.log /tmp/uat_e*.log /tmp/uat_f*.log /tmp/uat_g*.log
```

---

## 結果總表

| 區段 | 項目數 | PASS | FAIL | 備註 |
|:-----|:------:|:----:|:----:|:-----|
| A. CLI 基礎 | 5 | | | |
| B. HTTP API | 4 | | | |
| C. Domain Config | 3 | | | |
| D. TRIZ 流程 | 7 | | | |
| E. TR 執行 | 4 | | | |
| F. SSE 串流 | 2 | | | |
| G. 狀態持久化 | 3 | | | |
| H. 邊界條件 | 5 | | | |
| **合計** | **33** | | | |

**UAT 判定**：
- 33/33 PASS → **Release Ready**
- A+B+C+D 全 PASS, E/F/G/H 有 minor → **Conditional Pass**（記錄 known issues）
- D 區段有 FAIL → **Block**（核心 TRIZ 流程不完整）

---

## 缺陷記錄

| # | 區段 | 測試項 | 現象 | 嚴重度 | 備註 |
|:-:|:----:|:------:|:-----|:------:|:-----|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
