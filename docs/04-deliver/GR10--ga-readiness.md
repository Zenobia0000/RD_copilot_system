# GR10 — GA Readiness Gate Review

| Field     | Value                                                                 |
|-----------|-----------------------------------------------------------------------|
| Version   | v1.0                                                                  |
| Date      | 2026-04-15                                                            |
| Status    | Draft                                                                 |
| Gate      | TR10 (GA Readiness / Launch)                                          |
| Chair     | CTO / Launch Owner TBD — by launch date TBD                            |

> **Template** — 於 TR10 gate 會議逐條確認；任一 P0 未 close 不得 GA。

---

## §1 進入條件 / Entry Criteria

- [ ] **GR7 Pass** 且所有 condition 已 close（見 [GR7](../03-develop/GR7--integration.md) §7）
- [ ] TR8（安全）+ TR9（部署）gate 已通過（對應 [E8](E8--security-and-readiness-checklists.md) + [E9](E9--deployment-and-operations-guide.md)）
- [ ] 產品負責人最終驗收 PRD scope（[E1](../00-discover/E1--project-brief-and-prd.md)）簽核
- [ ] 使用者文檔 v1.0 就緒（[E9x user manual](E9x--user-manual-v0.1.md)）

---

## §2 Security Signoff（對應 E8 §F AI-01..AI-15）

依 [E8 §F 行動項表](E8--security-and-readiness-checklists.md)；每條確認 Done / 有 Waiver（標 Risk 級別）。

- [ ] **AI-01** Privacy Policy / ToS 撰寫 完成（P0）
- [ ] **AI-02** Anthropic DPA 審查 完成（P0）
- [ ] **AI-03** Dependabot / pip-audit / ruff-audit CI 整合 完成（P1）
- [ ] **AI-04** API rate limit（slowapi）上線（P1）
- [ ] **AI-05** 日誌 PII / prompt 遮罩 完成（P0）
- [ ] **AI-06** nginx CSP / 安全 header 完成（P1）
- [ ] **AI-07** 容器非 root 硬化 完成（P1）
- [ ] **AI-08** 鏡像漏洞掃描（Trivy on CI）完成（P1）
- [ ] **AI-09** MFA 強制 + Supabase 暴力破解強化 完成（P1）
- [ ] **AI-10** API Key Rotation 流程 + 文件化 完成（P1）
- [ ] **AI-11** 滲透測試（黑箱 + 授權）完成（P2）
- [ ] **AI-12** Incident Response Plan 完成（P1）
- [ ] **AI-13** 使用者刪除權 UI + 流程 完成（P1）
- [ ] **AI-14** Supabase RLS 跨租戶測試覆蓋 完成（P0）
- [ ] **AI-15** Secrets Manager（Vault / AWS SM）遷移 完成（P2）

> P0 未全 close = 強制 Fail。P1/P2 可帶 Waiver 上線但需記錄至 [E8 §G](E8--security-and-readiness-checklists.md)。

---

## §3 Deployment Readiness

參考 [E9 部署與運維指南](E9--deployment-and-operations-guide.md)。

- [ ] **E9 §CI/CD** build/test/deploy 三階段 YAML 生產環境 pass
- [ ] **部署策略**（Blue-Green / Rolling / Canary 擇一）演練完成且文件化
- [ ] **Rollback 決策樹**（E9）已演練 ≥ 1 次，RTO < target TBD
- [ ] Runbooks 最新版本且經 on-call 工程師驗證：
  - [ ] [runbook_pc_decomposition](operations/runbook_pc_decomposition.md)
  - [ ] [TRIZ_Layered_Rollout_Runbook](operations/TRIZ_Layered_Rollout_Runbook.md)
- [ ] Database migration 正式環境乾跑（backup → apply → verify → rollback drill）通過
- [ ] DNS / TLS / 負載均衡器設定 review 通過
- [ ] 灰度發佈策略（feature flag 或 canary %）定案

---

## §4 Observability

- [ ] **監控儀表板**：APM（latency / error rate / throughput）儀表板 live（連結 TBD）
- [ ] **日誌聚合**：所有 service 統一送入 log stack；query 可用
- [ ] **Trace**：關鍵 request（Solver / 跨域去錨定 / Pre-CAD）端到端 trace 可觀察
- [ ] **告警規則**：
  - [ ] API 5xx error rate > threshold → PagerDuty（threshold TBD）
  - [ ] LLM service timeout rate > threshold → 告警
  - [ ] Supabase connection pool saturation 告警
  - [ ] Disk / CPU / memory 基礎設施告警
- [ ] **SLO 定義**：可用性、延遲、錯誤預算 目標值記錄於 E9（目標值 TBD — SRE TBD by TBD）

---

## §5 Support Plan

- [ ] **On-call 輪值**：至少 2 人覆蓋 24/7 或定義的支援時段（名單 TBD）
- [ ] **Incident Response Plan**（AI-12）就緒，包含 severity 分級、溝通模板
- [ ] **支援文檔完整**：troubleshooting guide、常見 issue FAQ 就緒
- [ ] **Escalation Path** 定義（L1 → L2 → L3）
- [ ] **Feedback 通道**（issue tracker / support email）設定完成

---

## §6 User Documentation

- [ ] [E9x--user-manual-v0.1](E9x--user-manual-v0.1.md) 升級為 v1.0
- [ ] Quick start（getting started）章節完整
- [ ] 主要功能（TRIZ drill-down / 跨域去錨定 / Pre-CAD）使用手冊含截圖
- [ ] 常見錯誤 / FAQ 章節就緒
- [ ] 使用者可存取位置公布（docs site URL TBD）
- [ ] Release note / CHANGELOG v1.0 發佈

---

## §7 Legal / Compliance Signoff

- [ ] **Privacy Policy** 發佈且使用者同意流程上線（AI-01）
- [ ] **Terms of Service** 發佈且使用者同意流程上線（AI-01）
- [ ] **Anthropic DPA** 已簽署（AI-02）
- [ ] **GDPR 適用性評估** 完成（見 [E8 §E](E8--security-and-readiness-checklists.md)）
  - [ ] 使用者刪除權（AI-13）
  - [ ] 資料保留策略 文件化
  - [ ] DSAR（資料主體存取請求）流程就緒
- [ ] **Data Processing Map** 完成（哪些資料送到 Anthropic / Supabase / 自有服務）
- [ ] 契約 / 授權（open source 合規、第三方服務 T&C）review 通過

---

## §8 GA Launch Decision

| Field                | Value                                          |
|----------------------|------------------------------------------------|
| 會議日期             | TBD — Launch Owner TBD by TBD                  |
| 主席 / Chair         | CTO / Launch Owner TBD                          |
| Reviewers            | PM / ARCH / QA / Security / SRE / Legal TBD     |
| Decision             | [ ] Go (GA)  [ ] Conditional Go  [ ] No-Go      |
| Launch Window        | TBD                                            |
| Conditions / Caveats | TBD                                            |
| Rollback Trigger     | TBD（error rate / P1 incident count threshold） |
| Communication Plan   | TBD（customer email / blog post / changelog）  |
| Signed-off           | CTO TBD / Legal TBD / Security TBD              |

> Go → 正式上線、啟動 post-GA monitoring 14 天加強期；Conditional Go → 灰度 X% 流量；No-Go → 回到對應 gate（E8 / E9 / GR7）補救。
