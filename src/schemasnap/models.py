"""Strict, versioned wire models for snapshots and diffs."""

from __future__ import annotations

import json
from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    """Immutable model that rejects unknown wire fields."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class GeneratorInfo(StrictModel):
    name: Literal["schemasnap"] = "schemasnap"
    version: str = "0.1.0"


class SourceDescriptor(StrictModel):
    kind: Literal["csv", "parquet", "arrow", "duckdb"]
    label: str = Field(min_length=1, max_length=255)
    query_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")


class NumericProfile(StrictModel):
    minimum: float | int | None = None
    maximum: float | int | None = None
    q05: float | int | None = None
    q50: float | int | None = None
    q95: float | int | None = None
    mean: float | None = None
    non_finite_count: int = Field(default=0, ge=0)


class TemporalProfile(StrictModel):
    minimum: str | None = None
    maximum: str | None = None
    timezone: str | None = None


class CategoryProfile(StrictModel):
    cardinality: int = Field(ge=0)
    frequency_ratios: list[float] = Field(default_factory=list)
    entropy_bits: float = Field(ge=0.0)


class ColumnProfile(StrictModel):
    name: str = Field(min_length=1)
    data_type: str = Field(min_length=1)
    nullable: bool
    null_count: int = Field(ge=0)
    null_ratio: float = Field(ge=0.0, le=1.0)
    non_null_count: int = Field(ge=0)
    distinct_count: int = Field(ge=0)
    uniqueness_ratio: float | None = Field(default=None, ge=0.0, le=1.0)
    privacy: Literal["standard", "sensitive"]
    numeric: NumericProfile | None = None
    temporal: TemporalProfile | None = None
    category: CategoryProfile | None = None


class Snapshot(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    generator: GeneratorInfo = Field(default_factory=GeneratorInfo)
    source: SourceDescriptor
    row_count: int = Field(ge=0)
    column_count: int | None = Field(default=None, ge=0)
    columns: list[ColumnProfile]

    @model_validator(mode="after")
    def fill_and_validate_column_count(self) -> Self:
        expected = len(self.columns)
        if self.column_count is None:
            object.__setattr__(self, "column_count", expected)
        elif self.column_count != expected:
            raise ValueError("column_count does not match columns")
        names = [column.name for column in self.columns]
        if len(names) != len(set(names)):
            raise ValueError("column names must be unique")
        return self

    def to_json(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        return (
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            + "\n"
        )


class Severity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    BREAKING = "BREAKING"

    @property
    def rank(self) -> int:
        return {Severity.INFO: 1, Severity.WARNING: 2, Severity.BREAKING: 3}[self]


Scalar = str | int | float | bool | None


class Change(StrictModel):
    code: str = Field(pattern=r"^[A-Z][A-Z0-9_]+$")
    severity: Severity
    column: str | None = None
    message: str
    before: Scalar = None
    after: Scalar = None


CHANGE_ORDER = (
    "COLUMN_REMOVED",
    "TYPE_CHANGED",
    "NULLABILITY_RELAXED",
    "TIMEZONE_CHANGED",
    "RANGE_SHIFT",
    "DISTRIBUTION_SHIFT",
    "CATEGORY_DRIFT",
    "ROW_COUNT_SHIFT",
    "NULLABILITY_TIGHTENED",
    "COLUMN_ADDED",
)


class DiffReport(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    baseline_label: str
    current_label: str
    changes: list[Change]

    @property
    def highest_severity(self) -> Severity | None:
        if not self.changes:
            return None
        return max((change.severity for change in self.changes), key=lambda severity: severity.rank)

    @property
    def counts(self) -> dict[str, int]:
        return {
            severity.value: sum(change.severity is severity for change in self.changes)
            for severity in Severity
        }

    @staticmethod
    def sort_key_for_code(code: str) -> int:
        try:
            return CHANGE_ORDER.index(code)
        except ValueError:
            return len(CHANGE_ORDER)

    def to_json(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload["counts"] = self.counts
        payload["highest_severity"] = (
            self.highest_severity.value if self.highest_severity is not None else None
        )
        return (
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            + "\n"
        )
