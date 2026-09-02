"""Deterministic, rule-based snapshot comparison."""

from __future__ import annotations

from schemasnap.models import Change, ColumnProfile, DiffReport, Severity, Snapshot


def _number(value: float | int | None) -> float:
    if not isinstance(value, (int, float)):
        raise TypeError("expected a numeric profile value")
    return float(value)


def _change(
    code: str,
    severity: Severity,
    column: str | None,
    message: str,
    before: str | int | float | bool | None = None,
    after: str | int | float | bool | None = None,
) -> Change:
    return Change(
        code=code,
        severity=severity,
        column=column,
        message=message,
        before=before,
        after=after,
    )


def _numeric_changes(before: ColumnProfile, after: ColumnProfile) -> list[Change]:
    if before.numeric is None or after.numeric is None:
        return []
    old = before.numeric
    new = after.numeric
    changes: list[Change] = []
    range_values = (old.minimum, old.maximum, new.minimum, new.maximum)
    if all(isinstance(value, (int, float)) for value in range_values):
        old_min, old_max, new_min, new_max = (_number(value) for value in range_values)
        span = max(abs(old_max - old_min), abs(old_min) * 0.01, 1e-9)
        boundary_delta = max(abs(new_min - old_min), abs(new_max - old_max))
        if boundary_delta > span * 0.5:
            changes.append(
                _change(
                    "RANGE_SHIFT",
                    Severity.WARNING,
                    before.name,
                    "numeric range moved beyond the 50% baseline-span threshold",
                    f"{old.minimum}..{old.maximum}",
                    f"{new.minimum}..{new.maximum}",
                )
            )
    distribution_values = (old.q05, old.q50, old.q95, new.q50)
    if all(isinstance(value, (int, float)) for value in distribution_values):
        old_q05, old_q50, old_q95, new_q50 = (_number(value) for value in distribution_values)
        old_iqr_like = max(abs(old_q95 - old_q05), 1e-9)
        median_delta = abs(new_q50 - old_q50)
        relative_floor = max(abs(old_q50) * 0.5, 1e-9)
        if median_delta > max(2 * old_iqr_like, relative_floor):
            changes.append(
                _change(
                    "DISTRIBUTION_SHIFT",
                    Severity.WARNING,
                    before.name,
                    "median moved beyond the deterministic baseline threshold",
                    old.q50,
                    new.q50,
                )
            )
    return changes


def _category_changes(before: ColumnProfile, after: ColumnProfile) -> list[Change]:
    if before.category is None or after.category is None:
        return []
    old = before.category
    new = after.category
    width = max(len(old.frequency_ratios), len(new.frequency_ratios))
    old_ratios = old.frequency_ratios + [0.0] * (width - len(old.frequency_ratios))
    new_ratios = new.frequency_ratios + [0.0] * (width - len(new.frequency_ratios))
    distance = sum(abs(left - right) for left, right in zip(old_ratios, new_ratios, strict=True))
    if (
        old.cardinality != new.cardinality
        or distance > 0.25
        or abs(old.entropy_bits - new.entropy_bits) > 0.5
    ):
        return [
            _change(
                "CATEGORY_DRIFT",
                Severity.WARNING,
                before.name,
                "label-free category cardinality or frequency profile changed",
                old.cardinality,
                new.cardinality,
            )
        ]
    return []


def _common_column_changes(before: ColumnProfile, after: ColumnProfile) -> list[Change]:
    changes: list[Change] = []
    if before.data_type != after.data_type:
        changes.append(
            _change(
                "TYPE_CHANGED",
                Severity.BREAKING,
                before.name,
                "column data type changed",
                before.data_type,
                after.data_type,
            )
        )
    if not before.nullable and after.nullable:
        changes.append(
            _change(
                "NULLABILITY_RELAXED",
                Severity.BREAKING,
                before.name,
                "null values are now observed",
                False,
                True,
            )
        )
    elif before.nullable and not after.nullable:
        changes.append(
            _change(
                "NULLABILITY_TIGHTENED",
                Severity.INFO,
                before.name,
                "null values are no longer observed",
                True,
                False,
            )
        )
    if (
        before.temporal is not None
        and after.temporal is not None
        and before.temporal.timezone != after.temporal.timezone
    ):
        changes.append(
            _change(
                "TIMEZONE_CHANGED",
                Severity.BREAKING,
                before.name,
                "timestamp timezone changed",
                before.temporal.timezone,
                after.temporal.timezone,
            )
        )
    changes.extend(_numeric_changes(before, after))
    changes.extend(_category_changes(before, after))
    return changes


def diff_snapshots(baseline: Snapshot, current: Snapshot) -> DiffReport:
    """Compare snapshots with fixed thresholds and stable change ordering."""

    baseline_columns = {column.name: column for column in baseline.columns}
    current_columns = {column.name: column for column in current.columns}
    changes: list[Change] = []

    for name in baseline_columns.keys() - current_columns.keys():
        changes.append(
            _change(
                "COLUMN_REMOVED",
                Severity.BREAKING,
                name,
                "column was removed",
                baseline_columns[name].data_type,
                None,
            )
        )
    for name in baseline_columns.keys() & current_columns.keys():
        changes.extend(_common_column_changes(baseline_columns[name], current_columns[name]))
    if baseline.row_count > 0:
        ratio = current.row_count / baseline.row_count
        if ratio < 0.5 or ratio > 2.0:
            changes.append(
                _change(
                    "ROW_COUNT_SHIFT",
                    Severity.WARNING,
                    None,
                    "row count changed by more than 2x",
                    baseline.row_count,
                    current.row_count,
                )
            )
    elif current.row_count > 0:
        changes.append(
            _change(
                "ROW_COUNT_SHIFT",
                Severity.WARNING,
                None,
                "row count changed from empty to non-empty",
                0,
                current.row_count,
            )
        )
    for name in current_columns.keys() - baseline_columns.keys():
        changes.append(
            _change(
                "COLUMN_ADDED",
                Severity.INFO,
                name,
                "column was added",
                None,
                current_columns[name].data_type,
            )
        )

    changes.sort(key=lambda item: (DiffReport.sort_key_for_code(item.code), item.column or ""))
    return DiffReport(
        baseline_label=baseline.source.label,
        current_label=current.source.label,
        changes=changes,
    )
