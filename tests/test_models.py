from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from schemasnap.models import ColumnProfile, Snapshot, SourceDescriptor


def test_snapshot_serialization_is_stable_and_contains_no_wall_clock_time() -> None:
    snapshot = Snapshot(
        source=SourceDescriptor(kind="csv", label="orders.csv"),
        row_count=2,
        columns=[
            ColumnProfile(
                name="amount",
                data_type="float64",
                nullable=False,
                null_count=0,
                null_ratio=0.0,
                non_null_count=2,
                distinct_count=2,
                uniqueness_ratio=1.0,
                privacy="standard",
            )
        ],
    )

    first = snapshot.to_json()
    second = snapshot.to_json()

    assert first == second
    assert first.endswith("\n")
    payload = json.loads(first)
    assert payload["schema_version"] == "1.0"
    assert payload["generator"]["name"] == "schemasnap"
    assert "created_at" not in payload
    assert "E:\\" not in first


def test_models_are_strict_and_schema_version_is_fixed() -> None:
    with pytest.raises(ValidationError):
        Snapshot.model_validate(
            {
                "schema_version": "9.9",
                "source": {"kind": "csv", "label": "x.csv"},
                "row_count": 0,
                "columns": [],
            }
        )

    with pytest.raises(ValidationError):
        SourceDescriptor.model_validate({"kind": "csv", "label": "x.csv", "extra": True})
