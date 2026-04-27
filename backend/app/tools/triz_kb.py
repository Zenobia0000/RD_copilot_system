"""TRIZ Knowledge Base tools — rule engine for contradiction matrix lookup.

Loads the static Markdown knowledge base files and provides:
- Parameter mapping (natural language → 39 TRIZ parameters)
- Contradiction matrix lookup (improving × worsening → candidate principles)
- Separation principle matching (for physical contradictions)
- 76 Standard solutions matching

Ref: AI_Agent_Architecture.md §6.2 triz_solver_agent tools
Ref: triz_knowledge_base/README.md — injection strategy
"""

import re
from pathlib import Path
from functools import lru_cache

from app.core.config import settings


# ---------------------------------------------------------------------------
# File loaders (cached)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _kb_path() -> Path:
    return Path(settings.triz_kb_path).resolve()


@lru_cache(maxsize=1)
def load_39_parameters() -> str:
    """Full text of 39 parameters — inject into prompt context (~1,500 tokens)."""
    return (_kb_path() / "01_39_parameters.md").read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def load_40_principles() -> str:
    """Full text of 40 principles — inject into prompt context (~4,000 tokens)."""
    return (_kb_path() / "03_40_principles.md").read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def load_separation_principles() -> str:
    """Full text of separation principles (~1,000 tokens)."""
    return (_kb_path() / "04_separation_principles.md").read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def _load_matrix_raw() -> str:
    return (_kb_path() / "02_contradiction_matrix.md").read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def load_76_standard_solutions() -> str:
    return (_kb_path() / "05_76_standard_solutions.md").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Contradiction Matrix Lookup (RAG-style row extraction)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=128)
def lookup_matrix(improving: int, worsening: int) -> list[int]:
    """Look up the contradiction matrix and return candidate principle numbers.

    The matrix markdown is organized as one section per improving parameter,
    each containing a two-column table where rows represent worsening parameters
    and cells hold comma-separated principle numbers.

    Args:
        improving: The improving parameter number (1-39).
        worsening: The worsening parameter number (1-39).

    Returns:
        A list of candidate inventive principle numbers, or [] if no entry found.
    """
    raw = _load_matrix_raw()

    # Locate the section for the given improving parameter.
    pattern = rf"## 參數\s+{improving}\s*[:：]"
    match = re.search(pattern, raw)
    if not match:
        return []

    # Extract text until the next section (or end of file).
    next_section = re.search(r"## 參數\s+\d+\s*[:：]", raw[match.end():])
    if next_section:
        section = raw[match.start():match.end() + next_section.start()]
    else:
        section = raw[match.start():]

    # Scan table rows within the section to find the worsening parameter.
    for line in section.split("\n"):
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 2:
            continue

        # The first cell starts with the worsening parameter number,
        # e.g. "27 可靠性 (Reliability)".
        num_match = re.match(r"(\d+)\s", cells[0])
        if not num_match:
            continue

        if int(num_match.group(1)) == worsening:
            # The second cell contains comma-separated principle numbers.
            return [int(n) for n in re.findall(r"\d+", cells[1])]

    return []


def get_matrix_context(improving: int, worsening: int) -> str:
    """Get a human-readable context string for the matrix lookup result."""
    principles = lookup_matrix(improving, worsening)
    if not principles:
        return f"No TRIZ principles found for improving={improving}, worsening={worsening}. Consider physical contradiction approach."
    return (
        f"TRIZ Contradiction Matrix lookup:\n"
        f"  Improving parameter: #{improving}\n"
        f"  Worsening parameter: #{worsening}\n"
        f"  Candidate principles: {principles}\n"
        f"  → Inject 40_principles.md for principle details"
    )


# ---------------------------------------------------------------------------
# Prompt context builders (for LLM injection)
# ---------------------------------------------------------------------------

def build_triz_tc_context(improving: int, worsening: int) -> str:
    """Build full prompt context for Technical Contradiction resolution.

    Injection strategy (README.md §方式 3 混合注入):
    - 39 parameters: full inject
    - Matrix: only the relevant row
    - 40 principles: full inject (filtered to candidates)
    """
    principles = lookup_matrix(improving, worsening)
    params_text = load_39_parameters()
    principles_text = load_40_principles()

    # Filter principles text to only include candidate principles
    if principles:
        filtered_sections = []
        for p in principles:
            pattern = rf"### #{p}\s"
            match = re.search(pattern, principles_text)
            if match:
                start = match.start()
                next_match = re.search(r"### #\d+\s", principles_text[start + 1:])
                end = start + 1 + next_match.start() if next_match else len(principles_text)
                filtered_sections.append(principles_text[start:end].strip())
        principles_context = "\n\n".join(filtered_sections)
    else:
        principles_context = "（矩陣無推薦原理，請使用物理矛盾分離原則或 76 標準解）"

    return (
        f"## TRIZ 39 工程參數\n\n{params_text}\n\n"
        f"---\n\n"
        f"## 矛盾矩陣查表結果\n\n"
        f"改善參數: #{improving} / 惡化參數: #{worsening}\n"
        f"候選原理: {principles if principles else '無 → 請用分離原則'}\n\n"
        f"---\n\n"
        f"## 候選發明原理詳細說明\n\n{principles_context}"
    )


def _extract_class_sections(full_text: str, class_numbers: list[int]) -> str:
    """Extract specific Class sections from 76 standard solutions by class number.

    E.g., class_numbers=[1,2] extracts "## Class 1: ..." and "## Class 2: ..."
    """
    sections = []
    for cn in class_numbers:
        # Match "## Class N" header until next "## Class" or "## 三" (reference section)
        pattern = rf"(## Class {cn}[：:].+?)(?=## Class \d|## 三|$)"
        match = re.search(pattern, full_text, re.DOTALL)
        if match:
            sections.append(match.group(1).strip())
    return "\n\n---\n\n".join(sections) if sections else full_text


# Su-Field state → relevant Classes mapping
_SUFIELD_STATE_TO_CLASSES: dict[str, list[int]] = {
    "incomplete":   [1],      # Class 1.1: build Su-Field
    "harmful":      [1],      # Class 1.2: destroy harmful effect
    "insufficient": [1, 2],   # Class 1.3 enhance + Class 2 transform
    "effective":    [2, 3],   # already working → transform or scale
    "measurement":  [4],      # detection & measurement
    "simplify":     [5],      # simplification strategies
}


def build_sufield_context(system_state: str | None = None) -> str:
    """Build prompt context for Su-Field analysis (76 standard solutions).

    Level 1 optimization: if system_state is provided, only inject the
    relevant Class sections (~500-1500 tokens) instead of all 76 (~6000 tokens).
    """
    full_text = load_76_standard_solutions()
    if system_state and system_state in _SUFIELD_STATE_TO_CLASSES:
        classes = _SUFIELD_STATE_TO_CLASSES[system_state]
        filtered = _extract_class_sections(full_text, classes)
        # Always include the intro and matching flow
        intro_match = re.search(r"(# TRIZ 76.+?)(?=## Class)", full_text, re.DOTALL)
        intro = intro_match.group(1).strip() if intro_match else ""
        flow_match = re.search(r"(## 三、標準解匹配流程.+)", full_text, re.DOTALL)
        flow = flow_match.group(1).strip() if flow_match else ""
        return f"{intro}\n\n---\n\n{filtered}\n\n---\n\n{flow}"
    return f"## Su-Field 76 標準解\n\n{full_text}"

    
@lru_cache(maxsize=1)
def _load_39_param_name_map() -> dict[int, str]:
    """Parse 01_39_parameters.md into {id: name} for deepen_link prompts."""
    raw = load_39_parameters()
    out: dict[int, str] = {}
    for line in raw.split("\n"):
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 2:
            continue
        m = re.match(r"^(\d+)$", cells[0])
        if not m:
            continue
        num = int(m.group(1))
        name = cells[1] if len(cells) > 1 else ""
        if 1 <= num <= 39 and name:
            out[num] = name
    return out


def get_param_name(num: int | None) -> str:
    """Return the Chinese parameter name for a TRIZ 39 parameter id (or '' if unknown)."""
    if not num:
        return ""
    return _load_39_param_name_map().get(int(num), "")


def build_triz_pc_context() -> str:
    """Build prompt context for Physical Contradiction resolution.

    Only injects the separation principles knowledge base.
    PC resolution uses separation strategies directly,
    not the 40 inventive principles.
    """
    sep_text = load_separation_principles()

    return f"## 物理矛盾分離原則\n\n{sep_text}"
