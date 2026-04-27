"""
Build the BD -> RD pitch deck for RD Design Copilot.
Output: RD_Copilot_BD_Pitch_v1.pptx (25 slides, 16:9)
Source plan: ~/.claude/plans/fancy-wobbling-kernighan.md
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

# ---------- Theme ----------
NAVY = RGBColor(0x0B, 0x25, 0x45)       # primary
ORANGE = RGBColor(0xF9, 0x73, 0x16)     # accent (Delta)
GREY = RGBColor(0xEE, 0xF2, 0xF5)       # neutral bg
DARK = RGBColor(0x1F, 0x2D, 0x3D)       # body text
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GREY = RGBColor(0xD5, 0xDB, 0xE1)
MUTED = RGBColor(0x64, 0x74, 0x8B)

SLIDE_W, SLIDE_H = Inches(13.333), Inches(7.5)

prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H
blank = prs.slide_layouts[6]


# ---------- helpers ----------
def add_rect(slide, x, y, w, h, fill, line=None):
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(0.75)
    shp.shadow.inherit = False
    return shp


def add_text(slide, x, y, w, h, text, size=14, bold=False, color=DARK,
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, font="Microsoft JhengHei"):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Emu(0)
    tf.margin_top = tf.margin_bottom = Emu(0)
    tf.vertical_anchor = anchor
    lines = text.split("\n") if isinstance(text, str) else text
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        run = p.add_run()
        run.text = line
        run.font.name = font
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = color
    return tb


def header_band(slide, title, subtitle=None, page_num=None):
    """Top navy band + title"""
    add_rect(slide, 0, 0, SLIDE_W, Inches(1.1), NAVY)
    add_rect(slide, 0, Inches(1.1), SLIDE_W, Inches(0.08), ORANGE)
    add_text(slide, Inches(0.5), Inches(0.2), Inches(11), Inches(0.6),
             title, size=26, bold=True, color=WHITE)
    if subtitle:
        add_text(slide, Inches(0.5), Inches(0.68), Inches(11), Inches(0.4),
                 subtitle, size=13, color=LIGHT_GREY)
    if page_num is not None:
        add_text(slide, Inches(12.4), Inches(0.35), Inches(0.8), Inches(0.4),
                 f"{page_num:02d}", size=16, bold=True, color=ORANGE, align=PP_ALIGN.RIGHT)


def footer(slide, text="RD Design Copilot  ·  BD × RD 合作提案  ·  2026 Q2"):
    add_rect(slide, 0, Inches(7.1), SLIDE_W, Inches(0.4), GREY)
    add_text(slide, Inches(0.5), Inches(7.15), Inches(12.3), Inches(0.3),
             text, size=10, color=MUTED)


def new_slide(title=None, subtitle=None, page=None):
    s = prs.slides.add_slide(blank)
    # white bg by default
    if title is not None:
        header_band(s, title, subtitle, page)
        footer(s)
    return s


# =====================================================
# P1. Cover
# =====================================================
s = prs.slides.add_slide(blank)
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, NAVY)
# accent bar
add_rect(s, 0, Inches(5.2), SLIDE_W, Inches(0.1), ORANGE)
# title
add_text(s, Inches(0.8), Inches(1.8), Inches(12), Inches(1.2),
         "RD Design Copilot", size=60, bold=True, color=WHITE)
add_text(s, Inches(0.85), Inches(3.0), Inches(12), Inches(0.8),
         "讓每一次設計決策，都比上次更接近真相", size=28, color=ORANGE)
add_text(s, Inches(0.85), Inches(3.9), Inches(12), Inches(0.6),
         "Externalize  ·  Trace  ·  Audit", size=18, color=LIGHT_GREY)
add_text(s, Inches(0.85), Inches(5.6), Inches(12), Inches(0.5),
         "BD × RD 合作提案", size=20, bold=True, color=WHITE)
add_text(s, Inches(0.85), Inches(6.1), Inches(12), Inches(0.4),
         "2026 Q2  ·  e-Bike 產品線", size=14, color=LIGHT_GREY)
# decorative block right
add_rect(s, Inches(11.5), Inches(1.8), Inches(1.2), Inches(1.2), ORANGE)
add_rect(s, Inches(11.5), Inches(3.1), Inches(1.2), Inches(0.4), WHITE)


# =====================================================
# P2. Seven Pain Points
# =====================================================
s = new_slide("「你一定遇過」— RD 的七個真實痛點", "資料來源：PRD_RD_Design_Copilot.md §3.3", 2)

pains = [
    ("🔒", "經驗鎖定", "方案探索只有 1-2 條\n跳不出熟悉架構"),
    ("📚", "腦內庫存有限", "跨域知識缺失\nTRIZ 答不出"),
    ("👻", "假設隱藏", "前提沒被翻出來\n後期才發現，返工最貴"),
    ("💥", "風險後置", "拖到原型才爆炸\n架構級返工 3-5 次/專案"),
    ("🗃", "決策不可追溯", "「為什麼選這個？」\n無人記得"),
    ("🗣", "溝通斷層", "RD/PM/老闆各說各話\n評審 3-4 hr/次"),
    ("🕳", "證據缺口不可見", "Gate Review 流於形式\n沒人知道缺什麼"),
    ("⚙️", "共同根因", "隱性 · 無追溯 · 無驗證\n流程缺基礎設施"),
]
# 4x2 grid
card_w = Inches(3.0)
card_h = Inches(2.45)
gap_x = Inches(0.18)
gap_y = Inches(0.18)
x0 = Inches(0.5)
y0 = Inches(1.5)
for i, (icon, title, body) in enumerate(pains):
    r, c = divmod(i, 4)
    x = x0 + c * (card_w + gap_x)
    y = y0 + r * (card_h + gap_y)
    is_accent = (i == 7)
    fill = ORANGE if is_accent else GREY
    add_rect(s, x, y, card_w, card_h, fill)
    add_rect(s, x, y, Inches(0.1), card_h, NAVY if not is_accent else WHITE)
    add_text(s, x + Inches(0.25), y + Inches(0.2), Inches(0.6), Inches(0.6),
             icon, size=28)
    add_text(s, x + Inches(0.9), y + Inches(0.25), card_w - Inches(1.0), Inches(0.5),
             title, size=18, bold=True, color=WHITE if is_accent else NAVY)
    add_text(s, x + Inches(0.25), y + Inches(1.05), card_w - Inches(0.5), Inches(1.3),
             body, size=12, color=WHITE if is_accent else DARK)


# =====================================================
# P3. Common Root Cause
# =====================================================
s = new_slide("這些痛點的共同根因", "不是 RD 不努力，是流程缺一層基礎設施", 3)

# big statement
add_text(s, Inches(0.8), Inches(1.8), Inches(11.5), Inches(0.8),
         "隱性  ×  無追溯  ×  無驗證", size=36, bold=True, color=NAVY, align=PP_ALIGN.CENTER)

items = [
    ("隱性 (Implicit)", "假設 / 決策依據都在腦袋裡\n沒有被寫下，無法被審查"),
    ("無追溯 (Untraceable)", "沒有 artifact、沒有版本\n經驗無法累積、無法複用"),
    ("無驗證 (Unverified)", "LLM 的數字「在它的想像裡」\n沒被算術或資料庫校驗"),
]
x0 = Inches(0.8)
y0 = Inches(3.2)
w = Inches(3.95)
h = Inches(2.3)
gap = Inches(0.1)
for i, (t, b) in enumerate(items):
    x = x0 + i * (w + gap)
    add_rect(s, x, y0, w, h, GREY)
    add_rect(s, x, y0, w, Inches(0.5), NAVY)
    add_text(s, x + Inches(0.2), y0 + Inches(0.08), w - Inches(0.4), Inches(0.4),
             t, size=15, bold=True, color=WHITE)
    add_text(s, x + Inches(0.25), y0 + Inches(0.7), w - Inches(0.5), Inches(1.6),
             b, size=13, color=DARK)

add_text(s, Inches(0.8), Inches(6.0), Inches(11.5), Inches(0.6),
         "➜ 我們要建的不是另一個 LLM，而是把隱性變顯性的基礎設施",
         size=16, bold=True, color=ORANGE, align=PP_ALIGN.CENTER)


# =====================================================
# P4. Mission
# =====================================================
s = new_slide("系統使命", "引用 PRD_RD_Design_Copilot.md §1.1", 4)

add_text(s, Inches(1.0), Inches(1.8), Inches(11.3), Inches(0.6),
         "把 —", size=20, color=MUTED)

mission_lines = [
    ("「未知」", "可追蹤的假設"),
    ("「靈感」", "可審查的方案"),
    ("「試錯」", "最小實驗"),
]
y = Inches(2.4)
for left, right in mission_lines:
    add_text(s, Inches(1.0), y, Inches(3.5), Inches(0.7),
             left, size=30, bold=True, color=NAVY)
    add_text(s, Inches(4.5), y + Inches(0.1), Inches(1.5), Inches(0.6),
             "變成", size=18, color=MUTED)
    add_text(s, Inches(5.9), y, Inches(7), Inches(0.7),
             right, size=30, bold=True, color=ORANGE)
    y += Inches(0.85)

add_text(s, Inches(1.0), Inches(5.3), Inches(11.3), Inches(0.5),
         "並用數位線索連結所有設計工件與證據。", size=18, color=DARK)

# three verbs
add_rect(s, Inches(1.0), Inches(6.15), Inches(11.3), Inches(0.7), GREY)
add_text(s, Inches(1.0), Inches(6.25), Inches(11.3), Inches(0.5),
         "Externalize  ·  Trace  ·  Audit     —    顯式化 · 追蹤化 · 審查化",
         size=16, bold=True, color=NAVY, align=PP_ALIGN.CENTER)


# =====================================================
# P5. 5 Goals x KPI Table
# =====================================================
s = new_slide("5 大產品目標 × 對應 KPI", "PRD §2", 5)

headers = ["#", "目標", "對應痛點", "KPI 指標"]
rows = [
    ("O1", "擴大可能性空間、破除路徑依賴", "經驗鎖定", "方案探索 ≥3 條（含跨域去錨定非對標）"),
    ("O2", "讓未知可見、可追蹤", "假設隱藏", "假設驗證覆蓋率 ≥80%"),
    ("O3", "前置風險驗證、證據驅動決策", "風險後置", "返工 ≤2 次；證據缺口識別 ≥90%"),
    ("O4", "決策可審查、可複用", "決策不可追溯", "100% 追溯率（KT 記錄）"),
    ("O5", "跨層級溝通效率", "溝通斷層", "單次評審時間 ≤2 hr"),
]
col_w = [Inches(0.7), Inches(4.3), Inches(2.5), Inches(5.0)]
x0 = Inches(0.4)
y = Inches(1.5)
row_h = Inches(0.55)
# header
x = x0
for i, hname in enumerate(headers):
    add_rect(s, x, y, col_w[i], row_h, NAVY)
    add_text(s, x + Inches(0.15), y + Inches(0.1), col_w[i] - Inches(0.2), Inches(0.4),
             hname, size=13, bold=True, color=WHITE)
    x += col_w[i]
y += row_h
for ri, row in enumerate(rows):
    x = x0
    bg = WHITE if ri % 2 == 0 else GREY
    for i, cell in enumerate(row):
        add_rect(s, x, y, col_w[i], Inches(0.85), bg)
        is_num = (i == 0)
        add_text(s, x + Inches(0.15), y + Inches(0.2),
                 col_w[i] - Inches(0.2), Inches(0.5),
                 cell, size=13, bold=is_num,
                 color=ORANGE if is_num else DARK)
        x += col_w[i]
    y += Inches(0.85)


# =====================================================
# P6. 5-layer Architecture
# =====================================================
s = new_slide("架構全貌 — 5 層堆疊（C4 Model）",
              "「LLM 負責創造、純算術負責驗證、資料庫負責累積」", 6)

layers = [
    ("L1", "UI 層", "React SPA + 工作區視覺化", NAVY),
    ("L2", "編排層 Orchestrator", "Step 流轉 / Gate 判定 / Artifact 生命週期", NAVY),
    ("L3", "AI Agent 層", "Analyst · TRIZ Solver · Evaluator · Knowledge", ORANGE),
    ("L4", "Tool / Service 層", "TRIZ KB · Spatial Validator · MUST Engine", NAVY),
    ("L5", "Data 層", "Supabase Postgres · Vector DB · Seed JSON", NAVY),
]
x = Inches(1.3)
w = Inches(10.7)
y = Inches(1.6)
h = Inches(0.9)
gap = Inches(0.12)
for tag, name, desc, color in layers:
    add_rect(s, x, y, Inches(1.0), h, color)
    add_text(s, x, y + Inches(0.22), Inches(1.0), Inches(0.5),
             tag, size=22, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_rect(s, x + Inches(1.0), y, w - Inches(1.0), h, GREY)
    add_text(s, x + Inches(1.2), y + Inches(0.12), Inches(4.0), Inches(0.4),
             name, size=16, bold=True, color=NAVY)
    add_text(s, x + Inches(1.2), y + Inches(0.45), w - Inches(1.4), Inches(0.4),
             desc, size=12, color=DARK)
    y += h + gap

add_text(s, Inches(0.5), Inches(6.55), Inches(12.3), Inches(0.4),
         "✦  關鍵原則：LLM 創造 → 純算術驗證 → 資料庫覆寫 → 下游消費",
         size=13, bold=True, color=ORANGE, align=PP_ALIGN.CENTER)


# =====================================================
# P7. 4 AI Agents
# =====================================================
s = new_slide("4 個 AI Agent 的角色", "誰做什麼 · 輸入輸出一目瞭然", 7)

agents = [
    ("Analyst", "需求解構 · 蘇格拉底問答\n矛盾掃描 · 假設質疑",
     "Brief", "Constraint / Contradiction\nAssumption"),
    ("TRIZ Solver", "三層求解 L1/L2/L3\n子系統拆解",
     "Contradiction", "LayeredTrizSolution\nConcept Route"),
    ("Evaluator", "MUST 規則驗證\nKT 決策 · Gate 判定",
     "Concept Route", "Validation Passport\nDecision Record"),
    ("Knowledge", "企業 RAG · Web 搜尋\n跨域類比",
     "Query", "Reference / Evidence"),
]
card_w = Inches(3.05)
card_h = Inches(4.9)
x0 = Inches(0.45)
y0 = Inches(1.5)
gap = Inches(0.12)
for i, (name, job, inp, outp) in enumerate(agents):
    x = x0 + i * (card_w + gap)
    add_rect(s, x, y0, card_w, card_h, GREY)
    add_rect(s, x, y0, card_w, Inches(0.7), NAVY)
    add_text(s, x, y0 + Inches(0.15), card_w, Inches(0.5),
             name, size=18, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    # job
    add_text(s, x + Inches(0.2), y0 + Inches(0.9), card_w - Inches(0.4), Inches(1.4),
             "▸ 職責", size=11, bold=True, color=ORANGE)
    add_text(s, x + Inches(0.2), y0 + Inches(1.15), card_w - Inches(0.4), Inches(1.3),
             job, size=12, color=DARK)
    # input
    add_text(s, x + Inches(0.2), y0 + Inches(2.55), card_w - Inches(0.4), Inches(0.4),
             "▸ Input", size=11, bold=True, color=ORANGE)
    add_text(s, x + Inches(0.2), y0 + Inches(2.8), card_w - Inches(0.4), Inches(0.5),
             inp, size=12, color=DARK)
    # output
    add_text(s, x + Inches(0.2), y0 + Inches(3.4), card_w - Inches(0.4), Inches(0.4),
             "▸ Output", size=11, bold=True, color=ORANGE)
    add_text(s, x + Inches(0.2), y0 + Inches(3.65), card_w - Inches(0.4), Inches(1.1),
             outp, size=12, color=DARK)


# =====================================================
# P8. Tool Layer — 3 kits
# =====================================================
s = new_slide("工具層 — 關鍵三件套", "LLM 產出的數字，一定會被真值覆寫", 8)

kits = [
    ("TRIZ 知識庫", "5 份 Markdown",
     ["39 工程參數", "矛盾矩陣", "40 發明原理",
      "4 分離原則", "76 標準解"]),
    ("MUST 規則引擎", "6 條硬規則 M1–M6",
     ["M1 空間 · M2 成本",
      "M3 安全 · M4 解耦",
      "M5 供應 · M6 製造",
      "E0–E4 證據分級",
      "Gate 快篩輸出"]),
    ("純算術驗證器", "不呼叫 LLM",
     ["Spatial Discovery Validator",
      "Layered Spatial Resolver",
      "跨 5 層真值查找",
      "Package Map 生成",
      "anchor / bbox 保護"]),
]
x0 = Inches(0.6)
y0 = Inches(1.5)
w = Inches(4.0)
h = Inches(5.0)
gap = Inches(0.15)
for i, (name, sub, items) in enumerate(kits):
    x = x0 + i * (w + gap)
    add_rect(s, x, y0, w, h, GREY)
    add_rect(s, x, y0, w, Inches(1.0), ORANGE)
    add_text(s, x + Inches(0.25), y0 + Inches(0.15), w - Inches(0.5), Inches(0.5),
             name, size=18, bold=True, color=WHITE)
    add_text(s, x + Inches(0.25), y0 + Inches(0.58), w - Inches(0.5), Inches(0.4),
             sub, size=12, color=WHITE)
    yy = y0 + Inches(1.3)
    for it in items:
        add_text(s, x + Inches(0.35), yy, w - Inches(0.5), Inches(0.4),
                 "• " + it, size=13, color=DARK)
        yy += Inches(0.55)


# =====================================================
# P9. 10 Artifacts lifecycle
# =====================================================
s = new_slide("10 種核心工件 Artifact", "從 Brief 到 Asset 的完整生命週期", 9)

arts = [
    ("1", "Constraint", "D1"),
    ("2", "Contradiction", "D2-D4"),
    ("3", "Assumption", "D2-X1"),
    ("4", "Breakpoint", "D4"),
    ("5", "Concept Route", "X2-V3"),
    ("6", "Interface\nContract", "X2-V1"),
    ("7", "Evidence\nMatrix", "V1"),
    ("8", "Risk\nRegister", "V1"),
    ("9", "Validation\nPassport", "X2-V1"),
    ("10", "Decision\nRecord", "V3"),
]
# 5x2 grid
card_w = Inches(2.4)
card_h = Inches(2.3)
x0 = Inches(0.4)
y0 = Inches(1.6)
gx = Inches(0.15)
gy = Inches(0.2)
for i, (n, name, stage) in enumerate(arts):
    r, c = divmod(i, 5)
    x = x0 + c * (card_w + gx)
    y = y0 + r * (card_h + gy)
    add_rect(s, x, y, card_w, card_h, GREY)
    add_rect(s, x, y, Inches(0.6), card_h, NAVY)
    add_text(s, x, y + Inches(0.7), Inches(0.6), Inches(0.8),
             n, size=24, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(s, x + Inches(0.75), y + Inches(0.35), card_w - Inches(0.9), Inches(1.0),
             name, size=14, bold=True, color=NAVY)
    add_text(s, x + Inches(0.75), y + Inches(1.55), card_w - Inches(0.9), Inches(0.5),
             stage, size=11, color=ORANGE)


# =====================================================
# P10. Closed loop (data flow)
# =====================================================
s = new_slide("資料流與驗證封閉迴圈", "RD 最在意的「數字可不可信」正面回應", 10)

steps = [
    ("LLM 產出", "結構化候選"),
    ("純算術驗證", "真值覆寫幻覺"),
    ("資料庫持久化", "Artifact 累積"),
    ("下游消費", "決策中心 / Pre-CAD"),
]
w = Inches(2.7)
h = Inches(1.6)
x0 = Inches(0.5)
y = Inches(2.8)
gap = Inches(0.35)
colors = [ORANGE, NAVY, NAVY, NAVY]
for i, (t, sub) in enumerate(steps):
    x = x0 + i * (w + gap)
    add_rect(s, x, y, w, h, colors[i])
    add_text(s, x, y + Inches(0.3), w, Inches(0.5),
             t, size=18, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(s, x, y + Inches(0.85), w, Inches(0.5),
             sub, size=12, color=WHITE, align=PP_ALIGN.CENTER)
    if i < 3:
        ax = x + w + Inches(0.05)
        ay = y + h / 2 - Inches(0.15)
        arrow = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, ax, ay, Inches(0.25), Inches(0.3))
        arrow.fill.solid()
        arrow.fill.fore_color.rgb = ORANGE
        arrow.line.fill.background()

# feedback arrow
add_text(s, Inches(0.5), Inches(5.0), Inches(12), Inches(0.5),
         "↻  回饋：下游發現問題 → 更新 Assumption / Evidence → 重啟相應步驟",
         size=14, color=MUTED, align=PP_ALIGN.CENTER)

add_rect(s, Inches(1.5), Inches(5.9), Inches(10.3), Inches(0.9), NAVY)
add_text(s, Inches(1.5), Inches(6.0), Inches(10.3), Inches(0.7),
         "✦  LLM 的數字一定會被真值覆寫，不再「拍腦袋」",
         size=18, bold=True, color=WHITE, align=PP_ALIGN.CENTER)


# =====================================================
# P11. Module relationship (simplified graph)
# =====================================================
s = new_slide("模組關係圖", "單張總圖：Forward 軌（正向）+ Reverse 軌（反向）", 11)

# central orchestrator
add_rect(s, Inches(5.3), Inches(3.4), Inches(2.7), Inches(0.9), ORANGE)
add_text(s, Inches(5.3), Inches(3.55), Inches(2.7), Inches(0.6),
         "Orchestrator", size=16, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

# UI top
add_rect(s, Inches(5.3), Inches(1.6), Inches(2.7), Inches(0.7), NAVY)
add_text(s, Inches(5.3), Inches(1.7), Inches(2.7), Inches(0.5),
         "UI (React SPA)", size=13, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

# Data bottom
add_rect(s, Inches(5.3), Inches(6.0), Inches(2.7), Inches(0.7), NAVY)
add_text(s, Inches(5.3), Inches(6.1), Inches(2.7), Inches(0.5),
         "Postgres + Vector DB", size=13, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

# Forward track (left)
add_rect(s, Inches(0.4), Inches(2.6), Inches(4.2), Inches(0.55), NAVY)
add_text(s, Inches(0.4), Inches(2.65), Inches(4.2), Inches(0.45),
         "Forward 軌", size=13, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
fwd = ["Analyst Agent", "TRIZ Solver (L1/L2/L3)",
       "Subsystem Discovery"]
for i, it in enumerate(fwd):
    add_rect(s, Inches(0.4), Inches(3.25) + i * Inches(0.55),
             Inches(4.2), Inches(0.45), GREY)
    add_text(s, Inches(0.5), Inches(3.3) + i * Inches(0.55),
             Inches(4.0), Inches(0.4), "▸ " + it, size=12, color=DARK)

# Reverse track (right)
add_rect(s, Inches(8.7), Inches(2.6), Inches(4.2), Inches(0.55), ORANGE)
add_text(s, Inches(8.7), Inches(2.65), Inches(4.2), Inches(0.45),
         "Reverse 軌（TRIZ L1 跨域去錨定）", size=13, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
rev = ["First Principles", "Cross-domain Analogy",
       "Validation Passport", "≥3 非對標路線"]
for i, it in enumerate(rev):
    add_rect(s, Inches(8.7), Inches(3.25) + i * Inches(0.55),
             Inches(4.2), Inches(0.45), GREY)
    add_text(s, Inches(8.8), Inches(3.3) + i * Inches(0.55),
             Inches(4.0), Inches(0.4), "▸ " + it, size=12, color=DARK)

# Decision hub
add_rect(s, Inches(5.3), Inches(5.0), Inches(2.7), Inches(0.7), ORANGE)
add_text(s, Inches(5.3), Inches(5.1), Inches(2.7), Inches(0.5),
         "Decision Hub (5d)", size=13, bold=True, color=WHITE, align=PP_ALIGN.CENTER)


# =====================================================
# P12. E2E Overview (3 phase x 8 step)
# =====================================================
s = new_slide("E2E 流程總覽 — 3 Phase × D1-V4", "每個 Gate 都是可否決的檢查點，不是 rubber stamp", 12)

phases = [
    ("Define", "定義問題空間", NAVY,
     [("D1", "問題界定"), ("D2", "蘇格拉底問答"),
      ("D4", "系統建模")]),
    ("eXplore", "假設與發散", ORANGE,
     [("X1", "假設 & 驗證規劃"),
      ("X2", "創造與調整"),
      ("X5", "Pre-CAD Review")]),
    ("Verify", "收斂與驗證", NAVY,
     [("V1", "設計審查"), ("V3", "決策與行動"),
      ("V4", "內化與傳達")]),
]
x0 = Inches(0.4)
y0 = Inches(1.6)
pw = Inches(4.15)
ph = Inches(4.5)
gap = Inches(0.2)
for i, (tag, name, color, steps_) in enumerate(phases):
    x = x0 + i * (pw + gap)
    add_rect(s, x, y0, pw, ph, GREY)
    add_rect(s, x, y0, pw, Inches(0.9), color)
    add_text(s, x, y0 + Inches(0.1), pw, Inches(0.4),
             tag, size=16, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(s, x, y0 + Inches(0.45), pw, Inches(0.4),
             name, size=13, color=WHITE, align=PP_ALIGN.CENTER)
    yy = y0 + Inches(1.1)
    for st, sn in steps_:
        add_rect(s, x + Inches(0.3), yy, pw - Inches(0.6), Inches(0.9), WHITE)
        add_text(s, x + Inches(0.45), yy + Inches(0.12),
                 pw - Inches(0.8), Inches(0.4),
                 st, size=13, bold=True, color=ORANGE)
        add_text(s, x + Inches(0.45), yy + Inches(0.4),
                 pw - Inches(0.8), Inches(0.5),
                 sn, size=13, color=DARK)
        yy += Inches(1.1)

add_text(s, Inches(0.4), Inches(6.25), Inches(12.5), Inches(0.5),
         "Gate D1 → D3 → D4 → X1 → X5 → C → V3 → V4     共 8 個檢查點",
         size=14, bold=True, color=NAVY, align=PP_ALIGN.CENTER)


# =====================================================
# P13. Phase I — Brief → Problem → Contradiction
# =====================================================
s = new_slide("Define｜Brief → 問題界定 → 矛盾識別",
              "把『隱藏假設』逼出來，Gate D4 出口有量化門檻", 13)

steps = [
    ("D1", "問題界定",
     "Constraint（硬/軟/非目標/KPI）\n輸入：Brief + 客戶需求\n輸出：Constraint 工件"),
    ("D2", "蘇格拉底問答",
     "Analyst Agent 連環提問\n把「隱藏假設」翻出來\n輸出：Contradiction + Assumption"),
    ("D4", "系統建模",
     "因果迴路圖 + TRIZ 正式化\n找到可介入斷路點\n輸出：Breakpoint"),
]
for i, (st, name, body) in enumerate(steps):
    y = Inches(1.6) + i * Inches(1.65)
    add_rect(s, Inches(0.5), y, Inches(1.6), Inches(1.4), NAVY)
    add_text(s, Inches(0.5), y + Inches(0.2), Inches(1.6), Inches(0.5),
             st, size=16, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(s, Inches(0.5), y + Inches(0.75), Inches(1.6), Inches(0.5),
             name, size=12, color=LIGHT_GREY, align=PP_ALIGN.CENTER)
    add_rect(s, Inches(2.2), y, Inches(10.6), Inches(1.4), GREY)
    add_text(s, Inches(2.35), y + Inches(0.2), Inches(10.4), Inches(1.1),
             body, size=13, color=DARK)

add_rect(s, Inches(0.5), Inches(6.6), Inches(12.3), Inches(0.6), ORANGE)
add_text(s, Inches(0.5), Inches(6.7), Inches(12.3), Inches(0.5),
         "Gate D4 出口條件：≥1 因果迴路  ·  ≥3 斷路點  ·  ≥3 核心矛盾",
         size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER)


# =====================================================
# P14. Phase II — Subsystem Discovery
# =====================================================
s = new_slide("eXplore｜探索 · Subsystem Discovery",
              "X3：System → Module → Component 三層拆解", 14)

# three layers vertical
layers = [
    ("System", "整車層級", ["Mission", "KPI", "Package"]),
    ("Module", "模組層級", ["動力", "傳動", "控制", "結構"]),
    ("Component", "零件層級", ["Motor", "Battery", "BMS", "Frame ..."]),
]
for i, (tag, desc, items) in enumerate(layers):
    y = Inches(1.5) + i * Inches(1.35)
    add_rect(s, Inches(0.5), y, Inches(1.8), Inches(1.15), NAVY)
    add_text(s, Inches(0.5), y + Inches(0.2), Inches(1.8), Inches(0.5),
             tag, size=17, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(s, Inches(0.5), y + Inches(0.65), Inches(1.8), Inches(0.4),
             desc, size=11, color=LIGHT_GREY, align=PP_ALIGN.CENTER)
    add_rect(s, Inches(2.4), y, Inches(5.1), Inches(1.15), GREY)
    add_text(s, Inches(2.55), y + Inches(0.3), Inches(4.9), Inches(0.6),
             "  ·  ".join(items), size=13, color=DARK)

# Right: 6D interface contract
add_rect(s, Inches(8.0), Inches(1.5), Inches(4.9), Inches(4.2), GREY)
add_rect(s, Inches(8.0), Inches(1.5), Inches(4.9), Inches(0.6), ORANGE)
add_text(s, Inches(8.0), Inches(1.55), Inches(4.9), Inches(0.5),
         "6 維介面合約", size=16, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
dims = [("📐", "尺寸 (Geometry)"),
        ("⚙️", "功能 (Function)"),
        ("🔥", "熱 (Thermal)"),
        ("📳", "振動 (Vibration)"),
        ("🎛", "控制 (Control)"),
        ("💰", "成本 (Cost)")]
for i, (icon, name) in enumerate(dims):
    yy = Inches(2.3) + i * Inches(0.52)
    add_text(s, Inches(8.3), yy, Inches(0.5), Inches(0.4),
             icon, size=14)
    add_text(s, Inches(8.85), yy + Inches(0.03), Inches(4.0), Inches(0.4),
             name, size=13, color=DARK)

add_rect(s, Inches(0.5), Inches(6.0), Inches(7.0), Inches(0.9), NAVY)
add_text(s, Inches(0.6), Inches(6.1), Inches(6.8), Inches(0.7),
         "✦ Spatial Validator 純算術驗證\n    防 LLM 幻覺 · 真值覆寫",
         size=12, bold=True, color=WHITE)


# =====================================================
# P15. Forward TRIZ Solver — 3 layer drill-down
# =====================================================
s = new_slide("eXplore｜正向分析 · Forward TRIZ Solver",
              "TRIZ 三層 drill-down — L1 必跑 / L2 有條件 / L3 平行必跑", 15)

triz = [
    ("L1", "TC 現象層", "✅ 必跑",
     "39 參數 + 矛盾矩陣 + 40 原理", "快掃表象衝突"),
    ("L2", "PC 本質層", "⛔ 有條件",
     "4 分離原則（時/空/條件/整體）", "深挖物理兩難"),
    ("L3", "SF 結構層", "✅ 平行必跑",
     "76 標準解 + Su-Field 模型", "結構旁路檢查"),
]
# header
heads = ["層", "名稱", "是否必跑", "工具", "意義"]
col_w = [Inches(1.0), Inches(2.3), Inches(2.0), Inches(4.3), Inches(2.9)]
x0 = Inches(0.4)
y = Inches(1.5)
x = x0
for i, h in enumerate(heads):
    add_rect(s, x, y, col_w[i], Inches(0.5), NAVY)
    add_text(s, x + Inches(0.1), y + Inches(0.08), col_w[i] - Inches(0.2), Inches(0.4),
             h, size=13, bold=True, color=WHITE)
    x += col_w[i]
y += Inches(0.5)
for row in triz:
    x = x0
    for i, cell in enumerate(row):
        add_rect(s, x, y, col_w[i], Inches(0.85), GREY)
        is_tag = (i == 0)
        add_text(s, x + Inches(0.1), y + Inches(0.22), col_w[i] - Inches(0.2), Inches(0.5),
                 cell, size=15 if is_tag else 12,
                 bold=is_tag, color=ORANGE if is_tag else DARK)
        x += col_w[i]
    y += Inches(0.85)

# callout
add_rect(s, Inches(0.4), Inches(4.8), Inches(12.5), Inches(0.9), ORANGE)
add_text(s, Inches(0.5), Inches(4.9), Inches(12.3), Inches(0.7),
         "關鍵澄清：TC / PC / SF 不是互斥分類，而是同一矛盾的三層視角",
         size=16, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

add_text(s, Inches(0.4), Inches(5.9), Inches(12.5), Inches(0.5),
         "L2 觸發條件：L1 全是折衷  ·  L1 hits ≤ 2  ·  矛盾 severity ≥ major  ·  RD 手動深挖",
         size=13, color=MUTED, align=PP_ALIGN.CENTER)
add_text(s, Inches(0.4), Inches(6.35), Inches(12.5), Inches(0.4),
         "輸出工件：LayeredTrizSolution（可選採納深度）",
         size=12, color=MUTED, align=PP_ALIGN.CENTER)


# =====================================================
# P16. Reverse Anti-Anchor Sprint
# =====================================================
s = new_slide("eXplore｜反向分析 · TRIZ L1 跨域去錨定",
              "TRIZ L1 內建步驟（原 Anti-Anchor Sprint，已併入）", 16)

# definition big
add_rect(s, Inches(0.4), Inches(1.5), Inches(12.5), Inches(1.4), NAVY)
add_text(s, Inches(0.6), Inches(1.65), Inches(12.1), Inches(1.2),
         "What is 跨域去錨定?\n「從第一性原理出發、強制跨領域類比、自我標記假設強度」的非典型架構產生器（TRIZ L1 內建步驟）",
         size=15, bold=True, color=WHITE)

# why needed
add_text(s, Inches(0.4), Inches(3.1), Inches(12), Inches(0.4),
         "為什麼需要？", size=15, bold=True, color=ORANGE)
reasons = [
    "• RD 路徑依賴：無意識從主流架構微調",
    "• LLM 路徑依賴：把訓練資料常見品重新包裝",
    "• 傳統 TRIZ 只產出「更好的舊架構」，不是「新架構」",
]
for i, r in enumerate(reasons):
    add_text(s, Inches(0.6), Inches(3.5) + i * Inches(0.35),
             Inches(12), Inches(0.4), r, size=13, color=DARK)

# three constraints
add_text(s, Inches(0.4), Inches(4.75), Inches(12), Inches(0.4),
         "三個核心約束", size=15, bold=True, color=ORANGE)
cons = [
    ("1", "物理不相容",
     "≥1 條路線必須\n與竞品物理路徑不相容"),
    ("2", "自我誠實",
     "每條路線附\nValidation Passport"),
    ("3", "Schema 共用",
     "輸出可直接晉升\n正向候選池"),
]
for i, (n, t, b) in enumerate(cons):
    x = Inches(0.4) + i * Inches(4.2)
    add_rect(s, x, Inches(5.2), Inches(4.0), Inches(1.7), GREY)
    add_text(s, x + Inches(0.2), Inches(5.3), Inches(0.5), Inches(0.6),
             n, size=22, bold=True, color=ORANGE)
    add_text(s, x + Inches(0.85), Inches(5.35), Inches(3.1), Inches(0.5),
             t, size=14, bold=True, color=NAVY)
    add_text(s, x + Inches(0.85), Inches(5.8), Inches(3.1), Inches(1.0),
             b, size=11, color=DARK)


# =====================================================
# P17. Decision Hub (converge)
# =====================================================
s = new_slide("正反向匯流 — X4 Decision Hub",
              "Phase B 矛盾掃描 → MUST 快篩 → Pre-CAD Review", 17)

# Forward
add_rect(s, Inches(0.5), Inches(1.6), Inches(4.0), Inches(2.3), NAVY)
add_text(s, Inches(0.5), Inches(1.75), Inches(4.0), Inches(0.5),
         "Forward 軌", size=16, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
add_text(s, Inches(0.7), Inches(2.3), Inches(3.8), Inches(1.5),
         "• TRIZ L1/L2/L3\n• Subsystem Discovery",
         size=13, color=WHITE)

# Reverse
add_rect(s, Inches(8.8), Inches(1.6), Inches(4.0), Inches(2.3), ORANGE)
add_text(s, Inches(8.8), Inches(1.75), Inches(4.0), Inches(0.5),
         "Reverse 軌", size=16, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
add_text(s, Inches(9.0), Inches(2.3), Inches(3.8), Inches(1.5),
         "• TRIZ L1 跨域去錨定\n• 第一性原理\n• 跨域類比",
         size=13, color=WHITE)

# Merge arrows → Decision Hub
a1 = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(4.6), Inches(2.5),
                         Inches(0.8), Inches(0.5))
a1.fill.solid()
a1.fill.fore_color.rgb = NAVY
a1.line.fill.background()
a2 = s.shapes.add_shape(MSO_SHAPE.LEFT_ARROW, Inches(7.95), Inches(2.5),
                         Inches(0.8), Inches(0.5))
a2.fill.solid()
a2.fill.fore_color.rgb = ORANGE
a2.line.fill.background()

# Hub
add_rect(s, Inches(5.5), Inches(1.6), Inches(2.3), Inches(2.3), GREY)
add_text(s, Inches(5.5), Inches(2.0), Inches(2.3), Inches(0.6),
         "Decision Hub", size=15, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
add_text(s, Inches(5.5), Inches(2.5), Inches(2.3), Inches(0.5),
         "X4", size=13, color=ORANGE, align=PP_ALIGN.CENTER)
add_text(s, Inches(5.5), Inches(3.0), Inches(2.3), Inches(0.5),
         "候選池", size=12, color=MUTED, align=PP_ALIGN.CENTER)

# downstream
flow = ["Phase B 矛盾掃描", "MUST 快篩 (E0-E1)", "Pre-CAD Review",
        "保留 3-5 條最優路線"]
y = Inches(4.5)
w = Inches(2.85)
for i, t in enumerate(flow):
    x = Inches(0.5) + i * (w + Inches(0.2))
    add_rect(s, x, y, w, Inches(1.4), NAVY if i < 3 else ORANGE)
    add_text(s, x, y + Inches(0.45), w, Inches(0.5),
             t, size=13, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    if i < 3:
        ar = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW,
                                 x + w + Inches(0.02),
                                 y + Inches(0.55),
                                 Inches(0.16), Inches(0.3))
        ar.fill.solid()
        ar.fill.fore_color.rgb = ORANGE
        ar.line.fill.background()


# =====================================================
# P18. Phase III
# =====================================================
s = new_slide("Verify｜收斂與證據",
              "Evidence Matrix · Risk Register · KT Decision", 18)

ph3 = [
    ("V1", "設計審查 (CAD Gate)",
     "Evidence Matrix + Risk Register + MVP CAD → Gate C"),
    ("V2", "證據補齊（迴圈）",
     "最小實驗設計 · 證據等級升級 (E0→E4)"),
    ("V3", "決策與行動",
     "KT Decision Analysis → Decision Record (100% 可追溯)"),
    ("V4", "內化與傳達",
     "Asset 知識回寫 → 下一個專案冷啟動 Seed"),
]
for i, (st, name, body) in enumerate(ph3):
    y = Inches(1.5) + i * Inches(1.3)
    add_rect(s, Inches(0.5), y, Inches(1.8), Inches(1.1), NAVY)
    add_text(s, Inches(0.5), y + Inches(0.15), Inches(1.8), Inches(0.4),
             st, size=16, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(s, Inches(0.5), y + Inches(0.55), Inches(1.8), Inches(0.4),
             name.split(" ")[0] if " " in name else "",
             size=11, color=LIGHT_GREY, align=PP_ALIGN.CENTER)
    add_rect(s, Inches(2.4), y, Inches(10.5), Inches(1.1), GREY)
    add_text(s, Inches(2.55), y + Inches(0.15), Inches(10.3), Inches(0.4),
             name, size=15, bold=True, color=NAVY)
    add_text(s, Inches(2.55), y + Inches(0.55), Inches(10.3), Inches(0.5),
             body, size=12, color=DARK)


# =====================================================
# P19. Final deliverables
# =====================================================
s = new_slide("最終產出物 — RD 會拿到什麼？", "三大報告 + 配套工件", 19)

reports = [
    ("MUST Rulebook",
     "6 條硬規則 M1-M6",
     ["M1 空間 / M2 成本",
      "M3 安全 / M4 解耦",
      "M5 供應 / M6 製造",
      "E0-E4 證據分級"]),
    ("Evidence Matrix\n× Risk Register",
     "假設 × 證據 × 風險",
     ["關鍵假設清單",
      "證據等級 E0-E4",
      "Top-10 風險",
      "緩解措施 + Owner"]),
    ("Pre-CAD Review",
     "5 維評分 + 3-5 條路線",
     ["Spatial / Thermal",
      "Cost / Manufacturability",
      "Risk Score",
      "下一步 MVP CAD 範圍"]),
]
x0 = Inches(0.6)
y0 = Inches(1.5)
w = Inches(4.0)
h = Inches(4.3)
gap = Inches(0.15)
for i, (name, sub, items) in enumerate(reports):
    x = x0 + i * (w + gap)
    add_rect(s, x, y0, w, h, GREY)
    add_rect(s, x, y0, w, Inches(1.1), NAVY)
    add_text(s, x + Inches(0.2), y0 + Inches(0.15), w - Inches(0.4), Inches(0.7),
             name, size=16, bold=True, color=WHITE)
    add_text(s, x + Inches(0.2), y0 + Inches(0.75), w - Inches(0.4), Inches(0.4),
             sub, size=11, color=LIGHT_GREY)
    yy = y0 + Inches(1.4)
    for it in items:
        add_text(s, x + Inches(0.3), yy, w - Inches(0.5), Inches(0.4),
                 "✓  " + it, size=13, color=DARK)
        yy += Inches(0.55)

add_text(s, Inches(0.5), Inches(6.1), Inches(12.3), Inches(0.7),
         "＋ Validation Passport × N  ·  Decision Record (KT)  ·  Interface Contract (6 維)",
         size=13, bold=True, color=ORANGE, align=PP_ALIGN.CENTER)


# =====================================================
# P20. Not another ChatGPT
# =====================================================
s = new_slide("這不是另一個 ChatGPT", "對照差異一目瞭然", 20)

cmp_headers = ["維度", "ChatGPT / Gemini", "RD Design Copilot"]
cmp_rows = [
    ("知識來源", "網路雜訊", "企業 RAG + TRIZ KB + 種子資料"),
    ("數字可信度", "LLM 幻覺", "純算術驗證 + 資料庫覆寫"),
    ("流程結構", "無狀態對話", "D1-V4 × 8 Gate 狀態機"),
    ("假設管理", "隱性", "Validation Passport + Evidence Matrix"),
    ("決策追溯", "無", "KT Decision Record"),
    ("反偏誤", "無", "TRIZ L1 跨域去錨定 + 矛盾收斂掃描"),
    ("產出可審查", "段落文字", "結構化工件 + Gate 判定"),
]
col_w = [Inches(2.5), Inches(4.5), Inches(5.7)]
x0 = Inches(0.4)
y = Inches(1.5)
# header
x = x0
for i, h in enumerate(cmp_headers):
    color = NAVY if i < 2 else ORANGE
    add_rect(s, x, y, col_w[i], Inches(0.5), color)
    add_text(s, x + Inches(0.15), y + Inches(0.08), col_w[i] - Inches(0.2), Inches(0.4),
             h, size=13, bold=True, color=WHITE)
    x += col_w[i]
y += Inches(0.5)
for ri, row in enumerate(cmp_rows):
    x = x0
    bg = WHITE if ri % 2 == 0 else GREY
    for i, cell in enumerate(row):
        add_rect(s, x, y, col_w[i], Inches(0.65), bg)
        is_ours = (i == 2)
        add_text(s, x + Inches(0.15), y + Inches(0.17),
                 col_w[i] - Inches(0.2), Inches(0.4),
                 cell, size=12, bold=(i == 0 or is_ours),
                 color=ORANGE if is_ours else DARK)
        x += col_w[i]
    y += Inches(0.65)


# =====================================================
# P21. Automation grading — RD not replaced
# =====================================================
s = new_slide("自動化分級 — RD 永遠是最終決策者",
              "AI 消除重複腦力與盲點，不取代判斷", 21)

grades = [
    ("Human-Led", "RD 決策，AI 記錄", "V3", NAVY),
    ("AI-Assisted", "RD 主導，AI 協助", "D1 · X1 · V1 · V2", NAVY),
    ("AI-Driven", "AI 主導，RD 審核", "D2 · D4 · X3 · X4 · X2e · X5 · V1", ORANGE),
    ("Fully Auto", "AI 獨立產出，RD 選擇", "X2-0 · X2a · X2c · V4", NAVY),
]
for i, (tag, desc, steps_, color) in enumerate(grades):
    y = Inches(1.5) + i * Inches(1.05)
    add_rect(s, Inches(0.5), y, Inches(2.7), Inches(0.9), color)
    add_text(s, Inches(0.5), y + Inches(0.2), Inches(2.7), Inches(0.5),
             tag, size=17, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_rect(s, Inches(3.25), y, Inches(4.0), Inches(0.9), GREY)
    add_text(s, Inches(3.4), y + Inches(0.25), Inches(3.8), Inches(0.5),
             desc, size=13, color=DARK)
    add_rect(s, Inches(7.3), y, Inches(5.5), Inches(0.9), WHITE, line=LIGHT_GREY)
    add_text(s, Inches(7.45), y + Inches(0.25), Inches(5.3), Inches(0.5),
             steps_, size=12, color=MUTED)

add_rect(s, Inches(0.5), Inches(6.2), Inches(12.3), Inches(0.8), ORANGE)
add_text(s, Inches(0.5), Inches(6.35), Inches(12.3), Inches(0.5),
         "RD 永遠是最終決策者，AI 負責消除重複腦力勞動與盲點",
         size=16, bold=True, color=WHITE, align=PP_ALIGN.CENTER)


# =====================================================
# P22. Quantified benefits
# =====================================================
s = new_slide("對 RD 的具體收益（量化）", "從「感覺有用」到「數字會說話」", 22)

kpis = [
    ("⏱", "方案探索時間", "2 天", "0.5 天"),
    ("🔁", "架構級返工", "3-5 次", "≤2 次"),
    ("✅", "假設驗證覆蓋", "<30%", "≥80%"),
    ("🗃", "決策追溯率", "~0%", "100%"),
    ("💬", "單次設計評審", "3-4 hr", "≤2 hr"),
    ("🧠", "經驗資產化", "個人腦袋", "團隊 artifact"),
]
# 3 col x 2 row
card_w = Inches(4.1)
card_h = Inches(2.4)
x0 = Inches(0.4)
y0 = Inches(1.5)
gx = Inches(0.15)
gy = Inches(0.2)
for i, (icon, name, before, after) in enumerate(kpis):
    r, c = divmod(i, 3)
    x = x0 + c * (card_w + gx)
    y = y0 + r * (card_h + gy)
    add_rect(s, x, y, card_w, card_h, GREY)
    add_rect(s, x, y, card_w, Inches(0.6), NAVY)
    add_text(s, x + Inches(0.2), y + Inches(0.1), Inches(0.6), Inches(0.5),
             icon, size=18)
    add_text(s, x + Inches(0.8), y + Inches(0.1), card_w - Inches(1.0), Inches(0.5),
             name, size=14, bold=True, color=WHITE)
    # before
    add_text(s, x + Inches(0.3), y + Inches(0.85), Inches(1.7), Inches(0.4),
             "Before", size=11, color=MUTED)
    add_text(s, x + Inches(0.3), y + Inches(1.15), Inches(1.7), Inches(0.6),
             before, size=16, bold=True, color=DARK)
    # arrow
    ar = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW,
                             x + Inches(2.05), y + Inches(1.25),
                             Inches(0.35), Inches(0.4))
    ar.fill.solid()
    ar.fill.fore_color.rgb = ORANGE
    ar.line.fill.background()
    # after
    add_text(s, x + Inches(2.5), y + Inches(0.85), Inches(1.5), Inches(0.4),
             "After", size=11, color=ORANGE, bold=True)
    add_text(s, x + Inches(2.5), y + Inches(1.15), Inches(1.5), Inches(0.6),
             after, size=16, bold=True, color=ORANGE)


# =====================================================
# P23. What we need from RD
# =====================================================
s = new_slide("我們需要 RD 提供什麼", "引用 docs/raw/簡報內容.md 第 5 點", 23)

needs = [
    ("1", "Brief 與約束",
     "硬目標 / 軟目標 / 非目標 / KPI 門檻"),
    ("2", "歷史設計 Artifact",
     "舊專案的矛盾、假設、決策 → 冷啟動 Seed"),
    ("3", "關鍵零件真值",
     "datasheet、尺寸、熱/電參數 → 覆寫 LLM 幻覺"),
    ("4", "2-3 位 RD 工程師",
     "擔任 Design Partner，參與 Gate 審核迭代"),
    ("5", "1-2 個 Pilot 專案",
     "建議選「中風險」專案作為試點"),
]
for i, (n, t, b) in enumerate(needs):
    y = Inches(1.5) + i * Inches(1.0)
    add_rect(s, Inches(0.5), y, Inches(0.9), Inches(0.85), ORANGE)
    add_text(s, Inches(0.5), y + Inches(0.15), Inches(0.9), Inches(0.6),
             n, size=24, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_rect(s, Inches(1.5), y, Inches(11.3), Inches(0.85), GREY)
    add_text(s, Inches(1.7), y + Inches(0.1), Inches(11), Inches(0.4),
             t, size=15, bold=True, color=NAVY)
    add_text(s, Inches(1.7), y + Inches(0.45), Inches(11), Inches(0.4),
             b, size=12, color=DARK)


# =====================================================
# P24. What we deliver + timeline
# =====================================================
s = new_slide("我們提供什麼 & 時程", "6 個月分 3 階段，每階段可獨立驗收", 24)

phases = [
    ("Phase A", "Month 1-2",
     "TRIZ KB + Forward 軌 MVP\n跑通 D1-D4\n第一次 Gate Review"),
    ("Phase B", "Month 3-4",
     "TRIZ L1 跨域去錨定\nDecision Hub (5d)\nPre-CAD Review"),
    ("Phase C", "Month 5-6",
     "Evidence Matrix + Pre-CAD\n知識回寫\nPilot 專案結案"),
]
x0 = Inches(0.5)
y0 = Inches(1.5)
w = Inches(4.1)
h = Inches(3.8)
gap = Inches(0.15)
for i, (tag, month, body) in enumerate(phases):
    x = x0 + i * (w + gap)
    add_rect(s, x, y0, w, h, GREY)
    add_rect(s, x, y0, w, Inches(1.1), NAVY)
    add_text(s, x + Inches(0.2), y0 + Inches(0.12), w - Inches(0.4), Inches(0.5),
             tag, size=18, bold=True, color=WHITE)
    add_text(s, x + Inches(0.2), y0 + Inches(0.62), w - Inches(0.4), Inches(0.4),
             month, size=13, color=ORANGE)
    add_text(s, x + Inches(0.3), y0 + Inches(1.4), w - Inches(0.6), Inches(2.3),
             body, size=13, color=DARK)

add_rect(s, Inches(0.5), Inches(5.6), Inches(12.3), Inches(1.2), ORANGE)
add_text(s, Inches(0.6), Inches(5.75), Inches(12.1), Inches(0.5),
         "Future Extension", size=14, bold=True, color=WHITE)
add_text(s, Inches(0.6), Inches(6.1), Inches(12.1), Inches(0.7),
         "設計審查自動化  ·  製造可行性評估  ·  Simulation 介接  ·  企業知識資產沉澱",
         size=13, color=WHITE)


# =====================================================
# P25. Closing
# =====================================================
s = prs.slides.add_slide(blank)
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, NAVY)
add_rect(s, 0, Inches(5.2), SLIDE_W, Inches(0.08), ORANGE)

add_text(s, Inches(0.8), Inches(1.0), Inches(12), Inches(0.6),
         "三個動詞，一個承諾", size=22, color=LIGHT_GREY)

add_text(s, Inches(0.8), Inches(1.8), Inches(12), Inches(1.5),
         "Externalize", size=64, bold=True, color=WHITE)
add_text(s, Inches(0.8), Inches(2.8), Inches(12), Inches(1.5),
         "Trace", size=64, bold=True, color=ORANGE)
add_text(s, Inches(0.8), Inches(3.8), Inches(12), Inches(1.5),
         "Audit", size=64, bold=True, color=WHITE)

add_text(s, Inches(0.8), Inches(5.5), Inches(12), Inches(0.6),
         "讓你的每一個設計決策，都成為下一次設計的加速器。",
         size=20, color=LIGHT_GREY)

# CTA box
add_rect(s, Inches(0.8), Inches(6.2), Inches(11.7), Inches(0.9), ORANGE)
add_text(s, Inches(0.8), Inches(6.35), Inches(11.7), Inches(0.6),
         "➜ 下週啟動 Kick-off  ·  挑 1 個 pilot 專案  ·  6 週內看到可驗證成果",
         size=18, bold=True, color=WHITE, align=PP_ALIGN.CENTER)


# ---------- save ----------
import os
out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "RD_Copilot_BD_Pitch_v1.pptx")
prs.save(out)
print(f"Saved: {out}")
print(f"Total slides: {len(prs.slides)}")
