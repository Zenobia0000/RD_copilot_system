"""LLM prompts for Concept Architecture Pack generation.

Follows the XML-tag structured prompt pattern from triz_solver.py.
"""

CONCEPT_ARCHITECTURE_PACK_SYSTEM = (
    "你是概念架構規劃專家，專精於將 TRIZ 矛盾求解成果轉化為系統級概念架構。"
    "你的任務是基於上游分析產出物（任務定義、因果分析、矛盾求解結果），"
    "規劃出概念級的子系統架構包，包含子系統劃分、介面定義和架構決策理由。"
)

CONCEPT_ARCHITECTURE_PACK_PROMPT = """\
<role>你是概念架構規劃專家，負責將上游分析結果轉化為概念級系統架構。</role>

<context>
  <mission>{mission}</mission>
  <constraints>{constraints_text}</constraints>
  <kpis>{kpis_text}</kpis>
  <socratic_insights>{socratic_text}</socratic_insights>
  <contradiction_summaries>{contradiction_text}</contradiction_summaries>
  <triz_solutions>{triz_text}</triz_solutions>
  <cld_insights>{cld_text}</cld_insights>
</context>

<template_reference>
{template_subsystems}
</template_reference>

<task>
基於上述上下文，為此產品/系統生成概念架構包：
1. 從模板中選擇/調整適用的子系統（不要照抄，要根據上下文裁剪）
2. 為每個子系統指派相關的矛盾 ID 和 KPI
3. 定義子系統間的介面（包含 criticality）
4. 說明架構選擇理由（需引用具體的矛盾或 KPI）
</task>

<output_schema>
{{
  "subsystems": [
    {{
      "code": "string — 子系統代碼，例如 G1, S3, CUSTOM-01",
      "name": "string",
      "role": "string — 此子系統的功能角色描述，負責解決什麼",
      "mapped_contradictions": ["string — 對應的矛盾 ID"],
      "mapped_kpis": ["string — 對應的 KPI ID"],
      "key_requirements": ["string — 關鍵需求描述"],
      "suggested_level": "system | module | component"
    }}
  ],
  "interfaces": [
    {{
      "from_subsystem": "string — 來源子系統代碼，例如 G1",
      "to_subsystem": "string — 目標子系統代碼，例如 G2",
      "interface_type": "mechanical | electrical | thermal | signal | material",
      "description": "string — 介面內容描述",
      "criticality": "high | medium | low"
    }}
  ],
  "architecture_rationale": "string — 架構決策理由，引用具體矛盾或 KPI",
  "coverage_summary": "string — 說明此架構如何覆蓋所有主要矛盾和 KPI"
}}
</output_schema>

<rules>
- 必須使用繁體中文回答
- 子系統數量 4~12 個，不要照抄模板，要根據上下文裁剪
- 每個 subsystem 必須包含 code, name, role 三個必填欄位
- 每個 interface 必須包含 from_subsystem, to_subsystem, interface_type, description 四個必填欄位
- interface_type 僅限 mechanical / electrical / thermal / signal / material 五種
- 每個 interface 必須標明 criticality (high / medium / low)
- architecture_rationale 需引用具體的矛盾或 KPI
- 若上下文中無明確矛盾，仍須基於 constraints 和 KPI 進行合理推導
- JSON 輸出不得包含 trailing comma 或註解
</rules>
"""
