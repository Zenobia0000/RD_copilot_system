"""Declarative gate definitions — replaces hardcoded if-elif chain.

Each gate is registered with composable checker functions and an optional
AI evaluator identifier. Thresholds are specified here (single source of truth).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.gate_checks import (
    CheckFn,
    check_field_exists,
    check_table_count,
    check_all_have_field,
    check_severity_count,
    check_cross_table,
    check_any_status,
    check_manual,
)


@dataclass
class GateDefinition:
    gate_id: str
    name: str
    phase: str
    checks: list[CheckFn] = field(default_factory=list)
    ai_evaluator: str | None = None   # "must" | "pre_cad" | "convergence" | None
    manual: bool = False


GATE_REGISTRY: dict[str, GateDefinition] = {}


def _register(defn: GateDefinition) -> None:
    GATE_REGISTRY[defn.gate_id] = defn


# ---------------------------------------------------------------------------
# Phase D (Define)
# ---------------------------------------------------------------------------

_register(GateDefinition(
    gate_id="D1",
    name="Mission + KPI 完整性",
    phase="D",
    ai_evaluator="brief_quality",
    checks=[
        check_field_exists(
            "briefs", "mission",
            label="Mission 已定義",
            fail_reason="Mission 尚未定義",
        ),
        check_table_count(
            "kpis",
            min_count=3,
            label_template="KPI 數量 >= {min}（現有 {actual}）",
            fail_template="KPI 不足：需要 >= {min}，目前 {actual}",
        ),
        check_all_have_field(
            "kpis", "measurement_method",
            min_total=3,
            label_template="KPI 皆有量測方法（{with_field}/{total}）",
        ),
    ],
))

_register(GateDefinition(
    gate_id="D2",
    name="假設 + 矛盾充分性",
    phase="D",
    ai_evaluator="depth_quality",
    checks=[
        check_table_count(
            "assumptions",
            min_count=10,
            label_template="假設 >= {min}（現有 {actual}）",
            fail_template="假設不足：需要 >= {min}，目前 {actual}",
        ),
        check_severity_count(
            "assumptions", "worst_severity",
            severity_values=["critical", "high"],
            min_count=3,
            label_template="高風險假設 >= {min}（現有 {actual}）",
            fail_template="高風險假設不足：需要 >= {min}，目前 {actual}",
        ),
        check_table_count(
            "contradictions",
            min_count=3,
            use_count_exact=True,
            label_template="矛盾 >= {min}（現有 {actual}）",
            fail_template="矛盾不足：需要 >= {min}，目前 {actual}",
        ),
    ],
))

_register(GateDefinition(
    gate_id="PG-D",
    name="Phase Gate D — CLD + 矛盾形式化",
    phase="PG-D",
    ai_evaluator="convergence",
    checks=[
        check_table_count(
            "cld_nodes",
            min_count=1,
            use_count_exact=True,
            label_template="CLD 已建立",
            fail_template="尚未建立因果迴路圖",
        ),
        check_table_count(
            "cld_nodes",
            min_count=3,
            use_count_exact=True,
            filters={"is_leverage": True},
            label_template="Breakpoints >= {min}（現有 {actual}）",
            fail_template="Breakpoints 不足：需要 >= {min}，目前 {actual}",
        ),
    ],
))

# ---------------------------------------------------------------------------
# Phase X (Diverge)
# ---------------------------------------------------------------------------

_register(GateDefinition(
    gate_id="X1",
    name="高風險假設實驗覆蓋",
    phase="X",
    ai_evaluator="experiment_coverage",
    checks=[
        check_cross_table(
            "assumptions", "code",
            "experiments", "assumption_code",
            primary_severity_field="worst_severity",
            primary_severity_values=["critical", "high"],
            min_count=3,
            label_template="高風險假設有實驗 >= {min}（現有 {actual}）",
            fail_template="高風險假設缺少實驗：需要 >= {min}，目前 {actual}",
        ),
    ],
))

_register(GateDefinition(
    gate_id="X2",
    name="方案篩選 (MUST)",
    phase="X",
    ai_evaluator="must",
    checks=[
        check_table_count(
            "alternatives",
            min_count=3,
            label_template="方案 >= {min}（現有 {actual}）",
            fail_template="方案不足：需要 >= {min}，目前 {actual}",
        ),
    ],
))

_register(GateDefinition(
    gate_id="PG-X",
    name="Phase Gate X — Pre-CAD 通過",
    phase="PG-X",
    ai_evaluator="pre_cad",
    checks=[
        check_table_count(
            "alternatives",
            min_count=1,
            filters={"overall_pass": True},
            use_count_exact=True,
            label_template="Pre-CAD 通過 >= {min}（現有 {actual}）",
            fail_template="尚無方案通過 Pre-CAD 審查",
        ),
    ],
))

# ---------------------------------------------------------------------------
# Phase V (Converge)
# ---------------------------------------------------------------------------

_register(GateDefinition(
    gate_id="V2",
    name="決策簽核",
    phase="V",
    checks=[
        check_any_status(
            "decisions", "status",
            valid_statuses=["confirmed", "signed"],
            label="決策記錄已簽核",
            fail_reason="決策記錄尚未簽核",
        ),
    ],
))

_register(GateDefinition(
    gate_id="PG-V",
    name="Phase Gate V — 人工確認",
    phase="PG-V",
    manual=True,
    checks=[
        check_manual(
            label="所有核心 artifacts 已發佈",
            detail="需人工確認",
            fail_reason="Phase Gate V 需人工確認所有 artifacts 狀態",
        ),
    ],
))
