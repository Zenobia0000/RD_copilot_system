"""Reusable gate checker factories.

Each factory returns a callable with signature:
    (sb: SupabaseClient, project_id: str) -> tuple[GateCheckItem, str | None]

The returned tuple contains:
- GateCheckItem: label + met status for the checklist
- str | None: failure reason (None if check passed)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from app.models.schemas import GateCheckItem

if TYPE_CHECKING:
    pass

# Type alias
CheckFn = Callable[..., tuple[GateCheckItem, str | None]]


# ---------------------------------------------------------------------------
# check_field_exists — single record field is truthy
# ---------------------------------------------------------------------------

def check_field_exists(
    table: str,
    field: str,
    label: str,
    fail_reason: str,
) -> CheckFn:
    """Check that a single record exists and has a truthy field value."""

    def _check(sb, project_id: str) -> tuple[GateCheckItem, str | None]:
        row = sb.table(table).select(field).eq("project_id", project_id).maybe_single().execute()
        met = bool(row.data and row.data.get(field))
        return GateCheckItem(label=label, met=met), (None if met else fail_reason)

    return _check


# ---------------------------------------------------------------------------
# check_table_count — row count >= min_count
# ---------------------------------------------------------------------------

def check_table_count(
    table: str,
    *,
    min_count: int = 1,
    label_template: str = "{table} >= {min}（現有 {actual}）",
    fail_template: str = "{table}不足：需要 >= {min}，目前 {actual}",
    filters: dict[str, object] | None = None,
    use_count_exact: bool = False,
) -> CheckFn:
    """Check that a table has at least min_count matching rows."""

    def _check(sb, project_id: str) -> tuple[GateCheckItem, str | None]:
        if use_count_exact:
            query = sb.table(table).select("id", count="exact").eq("project_id", project_id)
        else:
            query = sb.table(table).select("id").eq("project_id", project_id)
        for k, v in (filters or {}).items():
            query = query.eq(k, v)
        result = query.execute()
        actual = result.count if use_count_exact else len(result.data or [])
        met = actual >= min_count
        label = label_template.format(table=table, min=min_count, actual=actual)
        reason = None if met else fail_template.format(table=table, min=min_count, actual=actual)
        return GateCheckItem(label=label, met=met), reason

    return _check


# ---------------------------------------------------------------------------
# check_all_have_field — all rows have a truthy field + total >= min_total
# ---------------------------------------------------------------------------

def check_all_have_field(
    table: str,
    field: str,
    *,
    min_total: int = 1,
    label_template: str = "{table} 皆有 {field}（{with_field}/{total}）",
) -> CheckFn:
    """Check that all rows in a table have a truthy value for a field."""

    def _check(sb, project_id: str) -> tuple[GateCheckItem, str | None]:
        rows = sb.table(table).select(f"id, {field}").eq("project_id", project_id).execute()
        data = rows.data or []
        total = len(data)
        with_field = sum(1 for r in data if r.get(field))
        met = with_field >= total and total >= min_total
        label = label_template.format(table=table, field=field, with_field=with_field, total=total)
        reason = None if met else label
        return GateCheckItem(label=label, met=met), reason

    return _check


# ---------------------------------------------------------------------------
# check_severity_count — count rows matching severity filter
# ---------------------------------------------------------------------------

def check_severity_count(
    table: str,
    severity_field: str,
    severity_values: list[str],
    *,
    min_count: int = 1,
    label_template: str = "高風險 {table} >= {min}（現有 {actual}）",
    fail_template: str = "高風險 {table} 不足：需要 >= {min}，目前 {actual}",
) -> CheckFn:
    """Count rows where severity_field is in severity_values."""

    def _check(sb, project_id: str) -> tuple[GateCheckItem, str | None]:
        rows = sb.table(table).select(f"id, {severity_field}").eq("project_id", project_id).execute()
        actual = sum(1 for r in (rows.data or []) if r.get(severity_field) in severity_values)
        met = actual >= min_count
        label = label_template.format(table=table, min=min_count, actual=actual)
        reason = None if met else fail_template.format(table=table, min=min_count, actual=actual)
        return GateCheckItem(label=label, met=met), reason

    return _check


# ---------------------------------------------------------------------------
# check_cross_table — rows in table A that also appear in table B
# ---------------------------------------------------------------------------

def check_cross_table(
    primary_table: str,
    primary_field: str,
    secondary_table: str,
    secondary_field: str,
    *,
    primary_severity_field: str | None = None,
    primary_severity_values: list[str] | None = None,
    min_count: int = 1,
    label_template: str = "關聯數量 >= {min}（現有 {actual}）",
    fail_template: str = "關聯不足：需要 >= {min}，目前 {actual}",
) -> CheckFn:
    """Count primary rows (optionally filtered by severity) that have a match in secondary table."""

    def _check(sb, project_id: str) -> tuple[GateCheckItem, str | None]:
        secondary = sb.table(secondary_table).select(secondary_field).eq("project_id", project_id).execute()
        secondary_set = {r.get(secondary_field) for r in (secondary.data or [])}

        primary_select = f"{primary_field}"
        if primary_severity_field:
            primary_select += f", {primary_severity_field}"
        primary = sb.table(primary_table).select(primary_select).eq("project_id", project_id).execute()

        actual = 0
        for r in (primary.data or []):
            if primary_severity_field and primary_severity_values:
                if r.get(primary_severity_field) not in primary_severity_values:
                    continue
            if r.get(primary_field) in secondary_set:
                actual += 1

        met = actual >= min_count
        label = label_template.format(min=min_count, actual=actual)
        reason = None if met else fail_template.format(min=min_count, actual=actual)
        return GateCheckItem(label=label, met=met), reason

    return _check


# ---------------------------------------------------------------------------
# check_any_status — at least one row has matching status
# ---------------------------------------------------------------------------

def check_any_status(
    table: str,
    field: str,
    valid_statuses: list[str],
    *,
    label: str,
    fail_reason: str,
) -> CheckFn:
    """Check that at least one row has a status in the valid set."""

    def _check(sb, project_id: str) -> tuple[GateCheckItem, str | None]:
        rows = sb.table(table).select(field).eq("project_id", project_id).execute()
        met = any(r.get(field) in valid_statuses for r in (rows.data or []))
        return GateCheckItem(label=label, met=met), (None if met else fail_reason)

    return _check


# ---------------------------------------------------------------------------
# check_manual — always fails (requires human confirmation)
# ---------------------------------------------------------------------------

def check_manual(
    label: str,
    detail: str,
    fail_reason: str,
) -> CheckFn:
    """Always returns met=False. For gates requiring manual confirmation."""

    def _check(sb, project_id: str) -> tuple[GateCheckItem, str | None]:
        return GateCheckItem(label=label, met=False, detail=detail), fail_reason

    return _check


# ---------------------------------------------------------------------------
# check_evidence_coverage — evidence claims coverage ratio (WBS 8.4.4)
# ---------------------------------------------------------------------------

def check_evidence_coverage(
    *,
    min_ratio: float = 0.4,
    label_template: str = "Evidence 覆蓋率 >= {min_pct}%（現有 {actual_pct}%）",
    fail_template: str = "Evidence 覆蓋率不足：需要 >= {min_pct}%，目前 {actual_pct}%",
) -> CheckFn:
    """Check that project evidence coverage ratio meets threshold.

    Queries evidence_claims table and computes verified / total.
    Returns a warning (not a hard fail) when below min_ratio.
    """

    def _check(sb, project_id: str) -> tuple[GateCheckItem, str | None]:
        result = (
            sb.table("evidence_claims")
            .select("status")
            .eq("project_id", project_id)
            .execute()
        )
        rows = result.data or []
        total = len(rows)
        if total == 0:
            label = label_template.format(min_pct=int(min_ratio * 100), actual_pct=0)
            return GateCheckItem(label=label, met=False, detail="尚無 evidence claims"), (
                fail_template.format(min_pct=int(min_ratio * 100), actual_pct=0)
            )

        verified = sum(1 for r in rows if r["status"] == "verified")
        ratio = verified / total
        actual_pct = round(ratio * 100, 1)
        min_pct = int(min_ratio * 100)
        met = ratio >= min_ratio
        label = label_template.format(min_pct=min_pct, actual_pct=actual_pct)
        reason = None if met else fail_template.format(min_pct=min_pct, actual_pct=actual_pct)
        return GateCheckItem(label=label, met=met), reason

    return _check
