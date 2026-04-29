"""Pydantic models for engineering deliverables exposed via the API.

These mirror the markdown-table rows in ``docs/engineering/kc_list.md``,
``risk_register.md``, etc. The schemas are *output* models — the source of
truth is still the markdown file. If a column is renamed in the source,
update the parser mapping in ``app.api.deliverables`` AND the field name
here.

Naming policy:
- Snake_case Python field names.
- The markdown column titles (often Chinese) are mapped at the API
  boundary, not on the Pydantic model — keeps the model importable from
  Python contexts that don't carry the docs.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class KCEntry(BaseModel):
    """One row of the Key Characteristics list (kc_list.md).

    Fields are filled best-effort: any column missing from a particular
    table just becomes the empty string.
    """

    id: str = Field(description="KC identifier, e.g. 'KC-001'.")
    feature: str = Field(default="", description="Characteristic name.")
    subsystem: str = Field(default="", description="Owning subsystem (motor/gear/...).")
    spec: str = Field(default="", description="Nominal spec value with unit.")
    tolerance: str = Field(default="", description="Allowable deviation.")
    source: str = Field(default="", description="WI/ICD references.")
    method: str = Field(default="", description="Measurement method.")
    level: str = Field(default="", description="Critical / Major / Minor.")


class RiskEntry(BaseModel):
    """One row of the risk register (risk_register.md)."""

    id: str = Field(description="Risk identifier, e.g. 'R-001'.")
    description: str = Field(default="", description="What could go wrong.")
    source: str = Field(default="", description="Origin of the risk (observation/evidence/CCI).")
    domain: str = Field(default="", description="Affected engineering domain.")
    probability: str = Field(default="", description="Likelihood: H/M/L.")
    impact: str = Field(default="", description="Severity: H/M/L.")
    mitigation: str = Field(default="", description="Planned response.")
    owner_wi: str = Field(default="", description="Responsible WI(s).")
