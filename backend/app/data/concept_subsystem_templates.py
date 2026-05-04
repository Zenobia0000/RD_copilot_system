"""Concept-level subsystem templates for architecture pack generation.

Two template sets:
- GENERIC_PRODUCT_TEMPLATE (G1–G12): product-agnostic subsystems
- EBIKE_MID_DRIVE_TEMPLATE (S1–S10): e-bike mid-drive specialisation
"""

from __future__ import annotations

# ── Generic Product Template (G1–G12) ──────────────────────────────

GENERIC_PRODUCT_TEMPLATE: list[dict] = [
    {
        "code": "G1",
        "name_zh": "動力子系統",
        "name_en": "Power / Actuation",
        "description": "提供系統主要動力或致動能量的模組",
        "typical_functions": ["能量轉換", "扭矩/力輸出", "轉速控制"],
        "typical_interfaces": ["G2", "G5", "G9"],
    },
    {
        "code": "G2",
        "name_zh": "傳動子系統",
        "name_en": "Transmission / Power Transfer",
        "description": "將動力從來源傳遞至末端執行元件",
        "typical_functions": ["減速增扭", "運動方向轉換", "離合/解耦"],
        "typical_interfaces": ["G1", "G3", "G8"],
    },
    {
        "code": "G3",
        "name_zh": "結構子系統",
        "name_en": "Structural / Housing",
        "description": "承載並保護內部元件的殼體或骨架結構",
        "typical_functions": ["承載負荷", "定位元件", "保護內部"],
        "typical_interfaces": ["G2", "G7", "G8", "G11"],
    },
    {
        "code": "G4",
        "name_zh": "散熱子系統",
        "name_en": "Thermal Management",
        "description": "管理系統運作時的熱能散逸與溫度控制",
        "typical_functions": ["散熱", "隔熱", "溫度監控"],
        "typical_interfaces": ["G1", "G3", "G5"],
    },
    {
        "code": "G5",
        "name_zh": "控制子系統",
        "name_en": "Control / Logic",
        "description": "系統的運算邏輯與控制演算法執行單元",
        "typical_functions": ["訊號處理", "演算法執行", "通訊協定管理"],
        "typical_interfaces": ["G1", "G6", "G10"],
    },
    {
        "code": "G6",
        "name_zh": "感知子系統",
        "name_en": "Sensing / Feedback",
        "description": "偵測系統內外部狀態並回傳訊號",
        "typical_functions": ["物理量量測", "狀態偵測", "訊號調理"],
        "typical_interfaces": ["G5", "G7"],
    },
    {
        "code": "G7",
        "name_zh": "人機介面子系統",
        "name_en": "Human-Machine Interface",
        "description": "使用者與系統互動的介面（顯示、操作、回饋）",
        "typical_functions": ["資訊顯示", "使用者輸入", "觸覺/聲學回饋"],
        "typical_interfaces": ["G5", "G6", "G3"],
    },
    {
        "code": "G8",
        "name_zh": "防護子系統",
        "name_en": "Protection / Sealing",
        "description": "防水、防塵、防衝擊等環境防護措施",
        "typical_functions": ["密封", "緩衝", "EMC 屏蔽"],
        "typical_interfaces": ["G3", "G2", "G10"],
    },
    {
        "code": "G9",
        "name_zh": "能源子系統",
        "name_en": "Energy Supply / Storage",
        "description": "能量的儲存、供應與轉換管理",
        "typical_functions": ["儲能", "電壓轉換", "充放電管理"],
        "typical_interfaces": ["G1", "G5", "G10"],
    },
    {
        "code": "G10",
        "name_zh": "通訊子系統",
        "name_en": "Communication / Connectivity",
        "description": "有線或無線通訊連接外部裝置或雲端",
        "typical_functions": ["資料傳輸", "協定轉換", "無線通訊"],
        "typical_interfaces": ["G5", "G9", "G8"],
    },
    {
        "code": "G11",
        "name_zh": "裝配子系統",
        "name_en": "Assembly / Mounting",
        "description": "將產品整合至使用環境的安裝與緊固機構",
        "typical_functions": ["快拆/快裝", "對位", "鎖固"],
        "typical_interfaces": ["G3"],
    },
    {
        "code": "G12",
        "name_zh": "驗證子系統",
        "name_en": "Verification / Diagnostics",
        "description": "產品自檢、故障診斷與量測點設計",
        "typical_functions": ["自檢", "故障碼記錄", "測試點規劃"],
        "typical_interfaces": ["G5", "G6"],
    },
]


# ── E-Bike Mid-Drive Template (S1–S10) ─────────────────────────────

EBIKE_MID_DRIVE_TEMPLATE: list[dict] = [
    {
        "code": "S1",
        "name_zh": "馬達模組",
        "name_en": "Motor Module",
        "description": "中驅系統的永磁無刷直流馬達（BLDC/PMSM）",
        "typical_functions": ["電能→機械能轉換", "扭矩輸出", "轉速響應"],
        "typical_interfaces": ["S2", "S4", "S8"],
    },
    {
        "code": "S2",
        "name_zh": "減速箱模組",
        "name_en": "Gearbox / Reduction",
        "description": "行星齒輪或斜齒輪組減速增扭機構",
        "typical_functions": ["減速增扭", "傳動效率", "噪音控制"],
        "typical_interfaces": ["S1", "S3", "S6"],
    },
    {
        "code": "S3",
        "name_zh": "外殼模組",
        "name_en": "Housing / Shell",
        "description": "容納馬達與減速箱的鋁合金或鎂合金殼體",
        "typical_functions": ["結構承載", "散熱路徑", "IP 防護"],
        "typical_interfaces": ["S1", "S2", "S6", "S9"],
    },
    {
        "code": "S4",
        "name_zh": "PCB 控制板",
        "name_en": "PCB / Controller Board",
        "description": "FOC/正弦波驅動控制器、BMS 通訊",
        "typical_functions": ["馬達驅動", "電流控制", "通訊協定"],
        "typical_interfaces": ["S1", "S5", "S7"],
    },
    {
        "code": "S5",
        "name_zh": "感測器群",
        "name_en": "Sensor Cluster",
        "description": "扭矩感測器、踏頻感測器、溫度感測器、Hall sensor",
        "typical_functions": ["扭矩量測", "踏頻偵測", "溫度監控"],
        "typical_interfaces": ["S4", "S10"],
    },
    {
        "code": "S6",
        "name_zh": "BB 介面模組",
        "name_en": "Bottom Bracket Interface",
        "description": "與車架五通（BB）連接的機構介面",
        "typical_functions": ["車架安裝", "對位", "振動隔離"],
        "typical_interfaces": ["S2", "S3"],
    },
    {
        "code": "S7",
        "name_zh": "線束模組",
        "name_en": "Wiring Harness",
        "description": "連接器、纜線、訊號線與電力線",
        "typical_functions": ["電力傳導", "訊號傳輸", "快拆連接"],
        "typical_interfaces": ["S4", "S5"],
    },
    {
        "code": "S8",
        "name_zh": "散熱模組",
        "name_en": "Thermal Management",
        "description": "散熱片、導熱膏/墊、散熱鰭片設計",
        "typical_functions": ["馬達散熱", "PCB 散熱", "溫度均化"],
        "typical_interfaces": ["S1", "S3", "S4"],
    },
    {
        "code": "S9",
        "name_zh": "密封模組",
        "name_en": "Sealing Module",
        "description": "O-ring、密封膠、防水接頭設計",
        "typical_functions": ["IP65/67 防護", "防塵", "防水"],
        "typical_interfaces": ["S3", "S7"],
    },
    {
        "code": "S10",
        "name_zh": "踏板偵測模組",
        "name_en": "Pedal Detection",
        "description": "人力踩踏的力量與節奏偵測機構",
        "typical_functions": ["踩踏力偵測", "前進/後退判斷", "助力比例計算"],
        "typical_interfaces": ["S5", "S4"],
    },
]


# ── Helper: get template by ID ──────────────────────────────────────

TEMPLATE_REGISTRY: dict[str, list[dict]] = {
    "generic": GENERIC_PRODUCT_TEMPLATE,
    "ebike_mid_drive": EBIKE_MID_DRIVE_TEMPLATE,
}


def get_template(template_id: str) -> list[dict]:
    """Return template list by ID, defaulting to generic."""
    return TEMPLATE_REGISTRY.get(template_id, GENERIC_PRODUCT_TEMPLATE)


def format_template_for_prompt(template_id: str) -> str:
    """Format a template into a human-readable string for LLM prompt injection."""
    entries = get_template(template_id)
    lines: list[str] = []
    for t in entries:
        lines.append(
            f"[{t['code']}] {t['name_zh']} ({t['name_en']})\n"
            f"  描述: {t['description']}\n"
            f"  典型功能: {', '.join(t['typical_functions'])}\n"
            f"  典型介面: {', '.join(t['typical_interfaces'])}"
        )
    return "\n\n".join(lines)
