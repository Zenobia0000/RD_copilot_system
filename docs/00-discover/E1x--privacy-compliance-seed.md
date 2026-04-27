# E1x — Privacy & Compliance Seed (隱私與合規種子文件)

| 項目 | 內容 |
|------|------|
| **版本** | v0.1 (Seed — 需法務審查) |
| **日期** | 2026-04-13 |
| **狀態** | 種子文件 — 所有條款待法務正式審查 |
| **擁有者** | [Legal / DPO] |

---

## §1 資料分類 (Data Classification)

| 分類 | 說明 | 敏感等級 | 範例 |
|------|------|---------|------|
| **客戶 IP (Customer Intellectual Property)** | 客戶上傳的設計文件、CAD 參數、專有技術資料 | **機密 (Confidential)** | 馬達規格書、減速機設計參數、專利相關描述 |
| **設計決策紀錄 (Design Decision Records)** | 系統內產生的矛盾分析、KT 決策表、Evidence Matrix | **內部 (Internal)** | TRIZ 矛盾解法、方案比較表、假設台帳 |
| **AI 生成內容 (AI-Generated Content)** | LLM 產出的建議、摘要、知識回寫內容 | **內部 (Internal)** | AI 建議的發明原理、TRIZ 候選方案 |
| **使用遙測 (Usage Telemetry)** | 產品使用行為數據 (匿名化) | **一般 (General)** | 功能使用頻率、Session 時長、錯誤率 |

---

## §2 資料駐留 (Data Residency)

| 法規 | 適用場景 | 要求 | 狀態 |
|------|---------|------|------|
| **台灣 PDPA (個人資料保護法)** | 台灣企業客戶 | 個資蒐集/處理/利用需符合 PDPA 規定；跨境傳輸需評估目的國保護水準 | [TBD — 需法務評估] |
| **EU GDPR** | 若未來服務歐盟客戶 | 資料處理需有合法基礎 (Lawful Basis)；跨境傳輸需 SCC 或 Adequacy Decision | [TBD — 非 Year 1 優先] |
| **資料主機位置** | 所有客戶 | [TBD — 評估選項: AWS ap-northeast-1 (Tokyo) / ap-southeast-1 (Singapore)] | [TBD — 需架構決策] |

> **原則**: 客戶 IP 資料不離開客戶指定的資料區域 (Data Region)。

---

## §3 租戶隔離 (Tenant Isolation)

| 層級 | 隔離要求 | 實作方式 |
|------|---------|---------|
| **資料儲存** | 每家企業的設計資料完全隔離，不得跨租戶存取 | Database-level isolation (每租戶獨立 schema 或獨立 DB) |
| **知識庫 (RAG)** | 每家企業的 RAG 向量資料庫完全隔離 | 獨立 Vector Store namespace / 獨立 Collection |
| **AI Agent 上下文** | Agent 對話不得洩漏其他租戶資訊 | Tenant ID 綁定於每次 LLM 呼叫，System Prompt 隔離 |
| **使用遙測** | 匿名化後可跨租戶聚合分析 | 移除 PII 後聚合 |
| **備份與還原** | 租戶可獨立備份/還原/刪除 | 租戶級 Backup & Restore API |

---

## §4 AI 資料使用政策

| 問題 | 政策 |
|------|------|
| 客戶資料是否用於模型訓練？ | **否 (NO)** — 客戶資料絕不用於任何 LLM fine-tuning 或 pre-training。 |
| 客戶資料是否傳送至第三方 LLM？ | 是 — 經由 API 傳送至 LLM 供應商 (Anthropic Claude)，但僅用於即時推論 (inference)，不被供應商保留或訓練。需確認供應商 DPA (Data Processing Agreement)。 |
| AI 生成內容的資料保留期間？ | 依客戶合約設定，客戶可隨時要求刪除。 |
| 匿名化使用數據可否用於產品改善？ | 是 — 僅限匿名化、去識別化的使用行為數據 (Telemetry)，用於功能優化。需於隱私政策中揭露。 |

---

## §5 智慧財產權 (Intellectual Property)

| 項目 | 歸屬 |
|------|------|
| **客戶上傳的設計資料** | 客戶完全擁有 |
| **系統內產生的設計決策紀錄** | 客戶完全擁有 |
| **AI 生成的建議內容** | 客戶擁有使用權；不主張 AI 輸出的獨立著作權 |
| **知識庫回寫內容** | 客戶完全擁有 (屬於客戶企業知識資產) |
| **產品本身的軟體與方法論** | RD Design Copilot 團隊擁有 |

---

## §6 AI 責任歸屬 (AI Liability)

| 原則 | 說明 |
|------|------|
| **AI 僅為諮詢性質 (Advisory Only)** | 所有 AI 輸出均為建議，不構成設計承諾或擔保。 |
| **人工簽核必要 (Human Sign-off Required)** | 所有設計決策必須經由人工確認簽核 (Gate X5 / Gate C)，AI 不可自動通過 Gate。 |
| **產品不承擔設計責任 (No Design Liability)** | RD Design Copilot 不對基於 AI 建議所做的設計決策承擔工程責任。責任歸屬於簽核的工程師與企業。 |
| **免責條款** | [TBD — 需法務撰寫正式免責條款與服務條款 (Terms of Service)] |

---

## §7 合規待辦 (Compliance Checklist)

| # | 項目 | 優先序 | 狀態 | 負責人 |
|---|------|--------|------|--------|
| 1 | PDPA 合規評估 (台灣個資法) | P0 | [TBD] | [Legal] |
| 2 | GDPR 合規評估 (若進入歐盟市場) | P2 | [TBD] | [Legal] |
| 3 | SOC 2 Type I 準備 | P1 | [TBD] | [Security Lead] |
| 4 | SOC 2 Type II 認證 | P2 | [TBD] | [Security Lead] |
| 5 | 滲透測試 (Penetration Testing) | P1 | [TBD] | [Security Lead] |
| 6 | LLM 供應商 DPA 審查 (Anthropic) | P0 | [TBD] | [Legal] |
| 7 | 隱私政策 (Privacy Policy) 撰寫 | P0 | [TBD] | [Legal] |
| 8 | 服務條款 (Terms of Service) 撰寫 | P0 | [TBD] | [Legal] |
| 9 | 資料處理協議 (DPA) 範本 — 供企業客戶簽署 | P1 | [TBD] | [Legal] |
| 10 | 資安事件應變計畫 (Incident Response Plan) | P1 | [TBD] | [Security Lead] |

---

## §8 威脅模型種子 (STRIDE Threat Model — Top 5)

| # | STRIDE 類別 | 威脅描述 | 衝擊 | 緩解措施 (初步) |
|---|------------|---------|------|----------------|
| T1 | **Spoofing (偽冒身份)** | 攻擊者偽冒合法用戶存取其他企業的設計資料 | 客戶 IP 外洩 | MFA 強制啟用 + SSO 整合 (SAML/OIDC) + Session Token 管理 |
| T2 | **Tampering (竄改證據)** | 攻擊者或內部人員竄改 Evidence Matrix 或決策紀錄 | 設計審查失去可信度 | Audit Log (不可竄改) + 證據快照 Hash + 版本控制 |
| T3 | **Repudiation (否認決策)** | 用戶否認曾做出某項設計決策 | 責任歸屬爭議 | 完整 Audit Trail + 數位簽章 (Gate 簽核時) + Timestamp |
| T4 | **Information Disclosure (資訊洩漏)** | 租戶 A 的競品設計資料被租戶 B 或第三方取得 | 嚴重商業損失 + 法律訴訟 | 租戶隔離 (§3) + 傳輸加密 (TLS 1.3) + 靜態加密 (AES-256) |
| T5 | **Elevation of Privilege (權限提升)** | 普通用戶取得管理員權限，跨租戶存取資料 | 全平台資料外洩 | RBAC + 最小權限原則 + 租戶 ID 綁定於所有 API 請求 + 定期權限審查 |

> **注意**: 本節為種子文件，完整威脅模型需於架構設計階段 (DEFINE Phase) 由資安團隊執行正式 STRIDE 分析。

---

**下一步行動**:
- [ ] 法務審查本文件所有條款
- [ ] 確認 LLM 供應商 (Anthropic) 的 DPA 條款
- [ ] 資料駐留架構決策 (配合 infra 團隊)
- [ ] 排定 SOC 2 準備時程
- [ ] 更新本文件至 v1.0 (法務審查後)
