from __future__ import annotations

import polars as pl

from schemasnap.diff import diff_snapshots
from schemasnap.models import Severity, SourceDescriptor
from schemasnap.profile import profile_dataframe


def _snap(frame: pl.DataFrame):  # type: ignore[no-untyped-def]
    return profile_dataframe(frame, SourceDescriptor(kind="csv", label="data.csv"))


def test_diff_has_deterministic_info_warning_and_breaking_changes() -> None:
    baseline = _snap(
        pl.DataFrame(
            {
                "removed": [1, 2, 3, 4],
                "typed": [1, 2, 3, 4],
                "nullable": [1, 2, 3, 4],
                "metric": [10.0, 11.0, 12.0, 13.0],
                "category": ["a", "a", "b", "b"],
            }
        )
    )
    current = _snap(
        pl.DataFrame(
            {
                "typed": ["1", "2", "3", "4"],
                "nullable": [1, None, 3, 4],
                "metric": [1000.0, 1100.0, 1200.0, 1300.0],
                "category": ["a", "b", "c", "d"],
                "added": [True, True, False, False],
            }
        )
    )

    report = diff_snapshots(baseline, current)
    codes = [change.code for change in report.changes]

    assert codes == sorted(codes, key=report.sort_key_for_code)
    assert report.highest_severity is Severity.BREAKING
    assert "COLUMN_REMOVED" in codes
    assert "TYPE_CHANGED" in codes
    assert "NULLABILITY_RELAXED" in codes
    assert "RANGE_SHIFT" in codes
    assert "DISTRIBUTION_SHIFT" in codes
    assert "CATEGORY_DRIFT" in codes
    assert "COLUMN_ADDED" in codes
    assert report.counts == {"INFO": 1, "WARNING": 3, "BREAKING": 3}


def test_timezone_change_is_breaking_and_tightened_nullability_is_info() -> None:
    baseline = _snap(
        pl.DataFrame(
            {
                "when": pl.Series(["2026-01-01T00:00:00Z"]).str.to_datetime(time_zone="UTC"),
                "note": [None],
            }
        )
    )
    current = _snap(
        pl.DataFrame(
            {
                "when": pl.Series(["2026-01-01T00:00:00"]).str.to_datetime(),
                "note": ["present"],
            }
        )
    )

    report = diff_snapshots(baseline, current)
    by_code = {change.code: change for change in report.changes}

    assert by_code["TIMEZONE_CHANGED"].severity is Severity.BREAKING
    assert by_code["NULLABILITY_TIGHTENED"].severity is Severity.INFO


def test_equal_frequency_category_replacement_is_privacy_preserving_noop() -> None:
    baseline = _snap(pl.DataFrame({"category": ["alpha", "alpha", "beta", "beta"]}))
    current = _snap(pl.DataFrame({"category": ["secret-x", "secret-x", "secret-y", "secret-y"]}))

    report = diff_snapshots(baseline, current)

    assert report.changes == []
    assert "alpha" not in baseline.to_json()
    assert "secret-x" not in current.to_json()
