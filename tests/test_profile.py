from __future__ import annotations

import json

import polars as pl

from schemasnap.models import SourceDescriptor
from schemasnap.profile import profile_dataframe


def test_profile_records_safe_structural_and_statistical_contract(
    baseline_frame: pl.DataFrame,
) -> None:
    snapshot = profile_dataframe(
        baseline_frame,
        SourceDescriptor(kind="parquet", label="orders.parquet"),
    )
    columns = {column.name: column for column in snapshot.columns}

    assert snapshot.row_count == 4
    assert snapshot.column_count == 5
    assert columns["amount"].data_type == "float64"
    assert columns["amount"].numeric is not None
    assert columns["amount"].numeric.minimum == 10.0
    assert columns["amount"].numeric.maximum == 13.0
    assert columns["amount"].numeric.q50 == 12.0
    assert columns["optional_note"].nullable is True
    assert columns["optional_note"].null_ratio == 0.75
    assert columns["region"].category is not None
    assert columns["region"].category.cardinality == 3
    assert columns["region"].category.frequency_ratios == [0.5, 0.25, 0.25]
    assert columns["created_at"].temporal is not None
    assert columns["created_at"].temporal.timezone == "UTC"


def test_profile_is_deterministic_and_normalizes_non_finite_numbers() -> None:
    frame = pl.DataFrame({"metric": [1.0, float("nan"), float("inf"), None]})
    source = SourceDescriptor(kind="arrow", label="metrics.arrow")

    first = profile_dataframe(frame, source).to_json()
    second = profile_dataframe(frame, source).to_json()

    assert first == second
    assert "NaN" not in first
    assert "Infinity" not in first
    numeric = json.loads(first)["columns"][0]["numeric"]
    assert numeric["non_finite_count"] == 2
    assert numeric["minimum"] == 1.0
