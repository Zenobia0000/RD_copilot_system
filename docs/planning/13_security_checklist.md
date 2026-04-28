# 安全與發布就緒檢查清單 — RD Design Copilot

---

**文件版本**：`v1.0`
**最後更新**：`2026-04-28`
**狀態**：`Skeleton`（pre-launch 必須全綠才可進入 [`14_deployment_ops.md`](./14_deployment_ops.md)）
**模板來源**：`VibeCoding_Workflow_Templates/13_security_and_readiness_checklists.md`

---

## A. 核心安全原則

- [ ] 最小權限（Least Privilege）：每個元件只取必要權限
- [ ] 縱深防禦（Defense in Depth）：多層防護
- [ ] 預設安全（Secure by Default）：新功能預設關閉、需顯性 opt-in
- [ ] Fail Securely：失敗時不洩漏資訊
- [ ] 不要相信用戶輸入

---

## B. 資料生命週期安全

### B.1 分類與蒐集

- [ ] 資料分級：公開 / 內部 / 機密 / 機密-專利
- [ ] 用戶同意（GDPR / 個資法）
- [ ] 資料最小化（只蒐集必要欄位）

### B.2 傳輸中（In Transit）

- [ ] TLS 1.3 強制（含內網）
- [ ] 憑證輪換策略
- [ ] mTLS for service-to-service（v3+）

### B.3 靜態（At Rest）

- [ ] DB 欄位加密（敏感欄位 application-level）
- [ ] S3/MinIO bucket 加密
- [ ] Key Management（Vault / KMS）

### B.4 使用與處理

- [ ] Log 不含 PII / 密碼 / token
- [ ] LLM 呼叫前 redact 敏感資訊
- [ ] 第三方分享前先評估必要性

### B.5 保留與銷毀

- [ ] 用戶資料保留政策（依 GDPR Art.5）
- [ ] 安全銷毀（shred / crypto-erase）

---

## C. 應用程式安全

### C.1 認證

- [ ] 密碼 bcrypt cost 12+
- [ ] MFA 可選（admin 強制）
- [ ] Session 30 min idle timeout
- [ ] Refresh token rotation

### C.2 授權

- [ ] RBAC 對所有 endpoint
- [ ] Project-level ACL（owner / collaborator / viewer）
- [ ] Object-level 檢查（不可越權存取他人 Project）

### C.3 輸入驗證

- [ ] Pydantic（BE）/ Zod（FE）強制 schema
- [ ] SQL：SQLAlchemy parameterized only（不 raw SQL）
- [ ] XSS：React 預設 escape + CSP header
- [ ] CSRF：HttpOnly Cookie + SameSite=Strict

### C.4 API 安全

- [ ] Authorization header 強制
- [ ] Rate limiting 配置（[`06_api_spec.md §6.3`](./06_api_spec.md)）
- [ ] CORS 白名單嚴格
- [ ] Pagination 限制（max 100/page）

### C.5 依賴安全

- [ ] Snyk / npm audit / pip-audit 在 CI 跑
- [ ] Dependabot 啟用
- [ ] SBOM 產出

---

## D. 基礎設施與運維安全

- [ ] Network：VPC / 內網隔離
- [ ] Secrets：Vault / K8s Secret，不寫 code
- [ ] 容器：non-root user、minimal image
- [ ] Logging：結構化 + 異常告警

---

## E. 合規

- [ ] GDPR / 個資法：資料導出 / 刪除 API
- [ ] 內部專利：分級存取
- [ ] 用戶條款 / 隱私政策

---

## F. 審查結論

| 類別 | 通過 / 待處理 / 不通過 |
|:-----|:----------------------|
| A. 核心安全 | — |
| B. 資料生命週期 | — |
| C. 應用程式安全 | — |
| D. 基礎設施 | — |
| E. 合規 | — |

**Go/No-Go**：— （SEC + SRE 簽核）

---

## G. 生產就緒

- [ ] Observability：Prometheus + Grafana 上線
- [ ] Alerting：PagerDuty / Slack 接通
- [ ] Runbook：[`14_deployment_ops.md`](./14_deployment_ops.md) 含 incident response
- [ ] DR：備份 + 恢復演練通過

---

## 文件溯源

- 模板：`VibeCoding_Workflow_Templates/13_security_and_readiness_checklists.md`
- 對應：[`05_architecture.md §7`](./05_architecture.md), [`06_api_spec.md §6`](./06_api_spec.md)
