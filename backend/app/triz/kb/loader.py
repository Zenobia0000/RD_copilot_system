"""TRIZ Knowledge Base loader — parses markdown KB files into structured objects.

Parses:
- 01_39_parameters.md → dict[int, Parameter]
- 02_contradiction_matrix.md → dict[(improve, worsen), list[int]]
- 03_40_principles.md → dict[int, Principle]
- 04_separation_principles.md → list[SeparationPrinciple]

All parsing is done once and cached.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path


@dataclass(frozen=True)
class Parameter:
    """One of the 39 engineering parameters."""
    id: int
    name_zh: str
    name_en: str
    description: str
    engineering_mapping: str


@dataclass(frozen=True)
class Principle:
    """One of the 40 inventive principles."""
    id: int
    name_zh: str
    name_en: str
    description: str
    physics: str
    examples: str


@dataclass(frozen=True)
class SeparationPrinciple:
    """One of the 4 separation principles for physical contradictions."""
    name_zh: str
    name_en: str
    core_question: str
    physics: str
    strategies: list[str] = field(default_factory=list)


class KBLoader:
    """Loads and caches TRIZ knowledge base from markdown files."""

    def __init__(self, kb_root: Path) -> None:
        self._root = kb_root
        if not kb_root.exists():
            raise FileNotFoundError(f"KB root not found: {kb_root}")

    @cached_property
    def parameters(self) -> dict[int, Parameter]:
        """39 engineering parameters keyed by ID."""
        return self._parse_parameters()

    @cached_property
    def matrix(self) -> dict[tuple[int, int], list[int]]:
        """Contradiction matrix: (improve_id, worsen_id) → principle IDs."""
        return self._parse_matrix()

    @cached_property
    def principles(self) -> dict[int, Principle]:
        """40 inventive principles keyed by ID."""
        return self._parse_principles()

    @cached_property
    def separation_principles(self) -> list[SeparationPrinciple]:
        """4 separation principles for physical contradictions."""
        return self._parse_separation()

    def lookup_principles(self, improve_id: int, worsen_id: int) -> list[int]:
        """Look up candidate principles from the contradiction matrix.

        Returns empty list if the combination has no recommendation.
        """
        return self.matrix.get((improve_id, worsen_id), [])

    def get_matrix_row(self, improve_id: int) -> dict[int, list[int]]:
        """Get all worsen→principles mappings for a given improve parameter."""
        return {
            worsen: principles
            for (imp, worsen), principles in self.matrix.items()
            if imp == improve_id
        }

    def get_parameter(self, param_id: int) -> Parameter | None:
        return self.parameters.get(param_id)

    def get_principle(self, principle_id: int) -> Principle | None:
        return self.principles.get(principle_id)

    def inject_principles_for_prompt(self, principle_ids: list[int]) -> str:
        """Format selected principles as context for LLM prompt."""
        lines = []
        for pid in principle_ids:
            p = self.principles.get(pid)
            if p:
                lines.append(
                    f"### #{pid} {p.name_zh} ({p.name_en})\n"
                    f"- {p.description}\n"
                    f"- **物理本質**: {p.physics}\n"
                    f"- **跨域範例**: {p.examples}\n"
                )
        return "\n".join(lines)

    def inject_parameters_for_prompt(self) -> str:
        """Format all 39 parameters as context for LLM prompt."""
        lines = ["| # | 參數名稱 | 英文 | 說明 | 工程對應 |",
                 "|---|---------|------|------|---------|"]
        for pid in sorted(self.parameters):
            p = self.parameters[pid]
            lines.append(f"| {pid} | {p.name_zh} | {p.name_en} | {p.description} | {p.engineering_mapping} |")
        return "\n".join(lines)

    # ── Parsers ──────────────────────────────────────────────────────

    def _parse_parameters(self) -> dict[int, Parameter]:
        """Parse 01_39_parameters.md."""
        path = self._root / "01_39_parameters.md"
        text = path.read_text(encoding="utf-8")
        params: dict[int, Parameter] = {}

        # Match table rows: | # | name_zh | name_en | desc | mapping |
        row_re = re.compile(
            r"^\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|",
            re.MULTILINE,
        )
        for m in row_re.finditer(text):
            pid = int(m.group(1))
            params[pid] = Parameter(
                id=pid,
                name_zh=m.group(2).strip(),
                name_en=m.group(3).strip(),
                description=m.group(4).strip(),
                engineering_mapping=m.group(5).strip(),
            )
        return params

    def _parse_matrix(self) -> dict[tuple[int, int], list[int]]:
        """Parse 02_contradiction_matrix.md.

        Format: Each parameter has a section headed by
        '## 參數 N: name'. Under it, a table of worsen→principles.
        """
        path = self._root / "02_contradiction_matrix.md"
        text = path.read_text(encoding="utf-8")
        matrix: dict[tuple[int, int], list[int]] = {}

        # Split by parameter sections
        section_re = re.compile(r"^## 參數 (\d+):", re.MULTILINE)
        sections = list(section_re.finditer(text))

        for i, sec in enumerate(sections):
            improve_id = int(sec.group(1))
            start = sec.end()
            end = sections[i + 1].start() if i + 1 < len(sections) else len(text)
            block = text[start:end]

            # Parse table rows: | N description | principles |
            row_re = re.compile(
                r"^\|\s*(\d+)\s+.+?\|\s*([\d,\s]+?)\s*\|",
                re.MULTILINE,
            )
            for rm in row_re.finditer(block):
                worsen_id = int(rm.group(1))
                principles_str = rm.group(2).strip()
                principles = [
                    int(x.strip())
                    for x in principles_str.split(",")
                    if x.strip().isdigit()
                ]
                if principles:
                    matrix[(improve_id, worsen_id)] = principles

        return matrix

    def _parse_principles(self) -> dict[int, Principle]:
        """Parse 03_40_principles.md."""
        path = self._root / "03_40_principles.md"
        text = path.read_text(encoding="utf-8")
        principles: dict[int, Principle] = {}

        # Split by principle headers: ### #N name_zh (name_en)
        header_re = re.compile(
            r"^### #(\d+)\s+(.+?)\s*\((.+?)\)",
            re.MULTILINE,
        )
        headers = list(header_re.finditer(text))

        for i, h in enumerate(headers):
            pid = int(h.group(1))
            start = h.end()
            end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
            body = text[start:end].strip()

            # Extract description (first line starting with -)
            desc = ""
            physics = ""
            examples = ""
            for line in body.split("\n"):
                line = line.strip()
                if line.startswith("- **物理本質**"):
                    physics = line.replace("- **物理本質**：", "").replace("- **物理本質**:", "").strip()
                elif line.startswith("- **跨域**"):
                    examples = line.replace("- **跨域**：", "").replace("- **跨域**:", "").strip()
                elif line.startswith("- ") and not desc:
                    desc = line[2:].strip()

            principles[pid] = Principle(
                id=pid,
                name_zh=h.group(2).strip(),
                name_en=h.group(3).strip(),
                description=desc,
                physics=physics,
                examples=examples,
            )
        return principles

    def _parse_separation(self) -> list[SeparationPrinciple]:
        """Parse 04_separation_principles.md."""
        path = self._root / "04_separation_principles.md"
        text = path.read_text(encoding="utf-8")
        principles: list[SeparationPrinciple] = []

        # Match: ### N. name_zh (name_en)
        header_re = re.compile(
            r"^### \d+\.\s+(.+?)\s*\((.+?)\)",
            re.MULTILINE,
        )
        headers = list(header_re.finditer(text))

        for i, h in enumerate(headers):
            start = h.end()
            end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
            body = text[start:end]

            # Extract core question
            q_match = re.search(r"\*\*核心問題\*\*：(.+)", body)
            core_q = q_match.group(1).strip() if q_match else ""

            # Extract physics
            p_match = re.search(r"\*\*物理本質\*\*：(.+?)(?:\n\n|\n\|)", body, re.DOTALL)
            physics = p_match.group(1).strip() if p_match else ""

            # Extract strategy names from table
            strat_re = re.compile(r"^\|\s*(.+?)\s*\|", re.MULTILINE)
            strategies = []
            for sm in strat_re.finditer(body):
                val = sm.group(1).strip()
                if val and val != "策略" and not val.startswith("-"):
                    strategies.append(val)

            principles.append(SeparationPrinciple(
                name_zh=h.group(1).strip(),
                name_en=h.group(2).strip(),
                core_question=core_q,
                physics=physics,
                strategies=strategies,
            ))

        return principles
