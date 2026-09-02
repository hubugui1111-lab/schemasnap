"""Privacy-preserving deterministic DataFrame profiler."""

from __future__ import annotations

import math
from collections import Counter
from datetime import date, datetime
from typing import Any

import polars as pl

from schemasnap.models import (
    CategoryProfile,
    ColumnProfile,
    NumericProfile,
    Snapshot,
    SourceDescriptor,
    TemporalProfile,
)
from schemasnap.privacy import PrivacyClass, classify_column


def _round(value: float) -> float:
    rounded = round(value, 8)
    return 0.0 if rounded == 0 else rounded


def _canonical_type(dtype: pl.DataType) -> str:
    integer_types = (
        pl.Int8,
        pl.Int16,
        pl.Int32,
        pl.Int64,
        pl.UInt8,
        pl.UInt16,
        pl.UInt32,
        pl.UInt64,
    )
    if dtype in integer_types:
        return str(dtype).casefold()
    if dtype in (pl.Float32, pl.Float64):
        return str(dtype).casefold()
    if dtype == pl.Boolean:
        return "bool"
    if dtype == pl.String:
        return "string"
    if dtype == pl.Binary:
        return "binary"
    if dtype == pl.Date:
        return "date"
    if isinstance(dtype, pl.Datetime):
        return "datetime"
    if isinstance(dtype, pl.Duration):
        return "duration"
    if isinstance(dtype, pl.Decimal):
        return f"decimal({dtype.precision},{dtype.scale})"
    if isinstance(dtype, pl.Categorical):
        return "category"
    return str(dtype).casefold().replace(" ", "")


def _numeric_profile(series: pl.Series) -> NumericProfile:
    finite_values: list[int | float] = []
    non_finite_count = 0
    for value in series.drop_nulls().to_list():
        if isinstance(value, float) and not math.isfinite(value):
            non_finite_count += 1
        else:
            finite_values.append(value)
    if not finite_values:
        return NumericProfile(non_finite_count=non_finite_count)
    clean = pl.Series("value", finite_values)

    def quantile(probability: float) -> int | float:
        value = clean.quantile(probability, interpolation="nearest")
        assert isinstance(value, (int, float))
        return _round(float(value)) if isinstance(value, float) else value

    minimum = min(finite_values)
    maximum = max(finite_values)
    mean = sum(float(value) for value in finite_values) / len(finite_values)
    return NumericProfile(
        minimum=_round(float(minimum)) if isinstance(minimum, float) else minimum,
        maximum=_round(float(maximum)) if isinstance(maximum, float) else maximum,
        q05=quantile(0.05),
        q50=quantile(0.50),
        q95=quantile(0.95),
        mean=_round(mean),
        non_finite_count=non_finite_count,
    )


def _temporal_profile(series: pl.Series) -> TemporalProfile:
    values = series.drop_nulls().to_list()
    if not values:
        minimum = maximum = None
    else:
        minimum_value = min(values)
        maximum_value = max(values)
        assert isinstance(minimum_value, (date, datetime))
        assert isinstance(maximum_value, (date, datetime))
        minimum = minimum_value.isoformat()
        maximum = maximum_value.isoformat()
    timezone: str | None = None
    if isinstance(series.dtype, pl.Datetime):
        timezone = series.dtype.time_zone
    return TemporalProfile(minimum=minimum, maximum=maximum, timezone=timezone)


def _category_profile(series: pl.Series) -> CategoryProfile:
    values: list[Any] = series.drop_nulls().to_list()
    if not values:
        return CategoryProfile(cardinality=0, frequency_ratios=[], entropy_bits=0.0)
    counts = Counter(values)
    ratios = sorted((_round(count / len(values)) for count in counts.values()), reverse=True)
    entropy = -sum(ratio * math.log2(ratio) for ratio in ratios if ratio > 0)
    return CategoryProfile(
        cardinality=len(counts),
        frequency_ratios=ratios,
        entropy_bits=_round(entropy),
    )


def _profile_column(series: pl.Series, row_count: int) -> ColumnProfile:
    privacy = classify_column(series.name)
    null_count = series.null_count()
    non_null_count = row_count - null_count
    distinct_count = series.drop_nulls().n_unique()
    uniqueness = _round(distinct_count / non_null_count) if non_null_count else None
    numeric: NumericProfile | None = None
    temporal: TemporalProfile | None = None
    category: CategoryProfile | None = None
    if privacy is PrivacyClass.STANDARD:
        if series.dtype.is_numeric():
            numeric = _numeric_profile(series)
        elif series.dtype.is_temporal():
            temporal = _temporal_profile(series)
        elif series.dtype in (pl.String, pl.Boolean) or isinstance(series.dtype, pl.Categorical):
            category = _category_profile(series)
    return ColumnProfile(
        name=series.name,
        data_type=_canonical_type(series.dtype),
        nullable=null_count > 0,
        null_count=null_count,
        null_ratio=_round(null_count / row_count) if row_count else 0.0,
        non_null_count=non_null_count,
        distinct_count=distinct_count,
        uniqueness_ratio=uniqueness,
        privacy=privacy.value,
        numeric=numeric,
        temporal=temporal,
        category=category,
    )


def profile_dataframe(frame: pl.DataFrame, source: SourceDescriptor) -> Snapshot:
    """Create a deterministic snapshot without row samples or category labels."""

    row_count = frame.height
    columns = [_profile_column(frame.get_column(name), row_count) for name in frame.columns]
    return Snapshot(source=source, row_count=row_count, columns=columns)
