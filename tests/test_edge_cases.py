from __future__ import annotations

from datetime import date

import polars as pl
import pytest

from schemasnap.diff import diff_snapshots
from schemasnap.errors import UnsafeQueryError
from schemasnap.loaders import validate_read_only_query
from schemasnap.models import (
    CategoryProfile,
    ColumnProfile,
    DiffReport,
    Severity,
    Snapshot,
    SourceDescriptor,
)
from schemasnap.profile import profile_dataframe
from schemasnap.render import render_markdown, render_terminal


def _source() -> SourceDescriptor:
    return SourceDescriptor(kind="csv", label="data.csv")


def test_empty_dataframe_profiles_without_division_by_zero() -> None:
    snapshot = profile_dataframe(
        pl.DataFrame(schema={"metric": pl.Float64, "label": pl.String}),
        _source(),
    )

    assert snapshot.row_count == 0
    assert all(column.null_ratio == 0.0 for column in snapshot.columns)
    assert all(column.uniqueness_ratio is None for column in snapshot.columns)
    assert snapshot.columns[0].numeric is not None
    assert snapshot.columns[0].numeric.minimum is None
    assert snapshot.columns[1].category is not None
    assert snapshot.columns[1].category.frequency_ratios == []


def test_date_and_boolean_profiles_are_safe() -> None:
    snapshot = profile_dataframe(
        pl.DataFrame({"day": [date(2026, 1, 1), date(2026, 1, 2)], "enabled": [True, False]}),
        _source(),
    )
    by_name = {column.name: column for column in snapshot.columns}

    assert by_name["day"].data_type == "date"
    assert by_name["day"].temporal is not None
    assert by_name["day"].temporal.minimum == "2026-01-01"
    assert by_name["enabled"].category is not None
    assert by_name["enabled"].category.cardinality == 2


def test_binary_values_are_never_sampled() -> None:
    snapshot = profile_dataframe(pl.DataFrame({"payload": [b"private-bytes"]}), _source())

    assert "private-bytes" not in snapshot.to_json()
    assert snapshot.columns[0].data_type == "binary"
    assert snapshot.columns[0].category is None


def test_duration_type_does_not_enter_timestamp_profiler() -> None:
    snapshot = profile_dataframe(
        pl.DataFrame({"latency": pl.Series([1_000, 2_000]).cast(pl.Duration("ms"))}),
        _source(),
    )

    assert snapshot.columns[0].data_type == "duration"
    assert snapshot.columns[0].temporal is None


def test_no_change_renderers_are_explicit() -> None:
    snapshot = profile_dataframe(pl.DataFrame({"metric": [1, 2]}), _source())
    report = diff_snapshots(snapshot, snapshot)

    assert report.highest_severity is None
    assert "No contract changes detected." in render_markdown(report)
    assert "No contract changes detected." in render_terminal(report)


@pytest.mark.parametrize(
    ("baseline_rows", "current_rows"),
    [(2, 5), (5, 2), (0, 1)],
)
def test_major_row_count_shift_is_warning(baseline_rows: int, current_rows: int) -> None:
    baseline = profile_dataframe(pl.DataFrame({"value": range(baseline_rows)}), _source())
    current = profile_dataframe(pl.DataFrame({"value": range(current_rows)}), _source())

    report = diff_snapshots(baseline, current)

    assert any(change.code == "ROW_COUNT_SHIFT" for change in report.changes)
    assert report.highest_severity is Severity.WARNING


def test_category_frequency_drift_without_cardinality_change_is_warning() -> None:
    baseline = profile_dataframe(pl.DataFrame({"kind": ["a", "a", "a", "b"]}), _source())
    current = profile_dataframe(pl.DataFrame({"kind": ["x", "x", "y", "y"]}), _source())

    report = diff_snapshots(baseline, current)

    assert [change.code for change in report.changes] == ["CATEGORY_DRIFT"]


def test_inconsistent_column_count_and_duplicate_names_are_rejected() -> None:
    column = ColumnProfile(
        name="x",
        data_type="string",
        nullable=False,
        null_count=0,
        null_ratio=0,
        non_null_count=1,
        distinct_count=1,
        uniqueness_ratio=1,
        privacy="standard",
        category=CategoryProfile(cardinality=1, frequency_ratios=[1.0], entropy_bits=0),
    )
    with pytest.raises(ValueError, match="column_count"):
        Snapshot(source=_source(), row_count=1, column_count=2, columns=[column])
    with pytest.raises(ValueError, match="unique"):
        Snapshot(source=_source(), row_count=1, columns=[column, column])


def test_unknown_change_code_sorts_after_known_codes() -> None:
    report = DiffReport(baseline_label="a", current_label="b", changes=[])

    assert report.sort_key_for_code("FUTURE_RULE") > report.sort_key_for_code("COLUMN_ADDED")


@pytest.mark.parametrize(
    "query",
    [
        "",
        "-- comment\nSELECT 1",
        "VALUES (1)",
        "SELECT 1;",
        "WITH x AS (DELETE FROM t) SELECT 1",
        "SELECT * FROM read_text('private.txt')",
    ],
)
def test_query_guard_fails_closed(query: str) -> None:
    with pytest.raises(UnsafeQueryError):
        validate_read_only_query(query)


def test_query_guard_accepts_select_and_cte() -> None:
    assert validate_read_only_query(" SELECT 1 ") == "SELECT 1"
    assert validate_read_only_query("WITH x AS (SELECT 1 AS n) SELECT n FROM x").startswith("WITH")
