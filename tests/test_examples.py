from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from schemasnap.diff import diff_snapshots
from schemasnap.loaders import LoadRequest, load_frame
from schemasnap.models import SourceDescriptor
from schemasnap.profile import profile_dataframe

pytestmark = pytest.mark.integration
ROOT = Path(__file__).resolve().parents[1]
GALLERY = ROOT / "examples" / "gallery"


def _snapshot(path: Path):  # type: ignore[no-untyped-def]
    loaded = load_frame(LoadRequest(source=path))
    return profile_dataframe(
        loaded.frame,
        SourceDescriptor(kind=loaded.kind, label=path.name),
    )


@pytest.fixture(scope="module")
def generated_gallery() -> Path:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_gallery.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return GALLERY / "generated"


@pytest.mark.parametrize(
    ("fixture", "code"),
    [
        ("removed-column.csv", "COLUMN_REMOVED"),
        ("type-change.csv", "TYPE_CHANGED"),
        ("nullable.csv", "NULLABILITY_RELAXED"),
        ("category-drift.csv", "CATEGORY_DRIFT"),
        ("distribution-shift.csv", "DISTRIBUTION_SHIFT"),
    ],
)
def test_broken_data_gallery_signal(fixture: str, code: str) -> None:
    report = diff_snapshots(_snapshot(GALLERY / "baseline.csv"), _snapshot(GALLERY / fixture))

    assert code in {change.code for change in report.changes}


def test_binary_gallery_builder_and_all_loaders(generated_gallery: Path) -> None:
    assert load_frame(LoadRequest(generated_gallery / "orders.parquet")).frame.height == 4
    assert load_frame(LoadRequest(generated_gallery / "orders.arrow")).frame.height == 4
    sql = (GALLERY / "query.sql").read_text(encoding="utf-8")
    assert load_frame(LoadRequest(generated_gallery / "gallery.duckdb", sql=sql)).frame.height == 2


def test_timezone_gallery_detects_timezone_loss(generated_gallery: Path) -> None:
    report = diff_snapshots(
        _snapshot(generated_gallery / "timestamp-utc.parquet"),
        _snapshot(generated_gallery / "timestamp-naive.parquet"),
    )

    assert "TIMEZONE_CHANGED" in {change.code for change in report.changes}


def test_committed_snapshot_and_markdown_are_privacy_safe() -> None:
    snapshot = (GALLERY / "baseline.snap.json").read_text(encoding="utf-8")
    markdown = (GALLERY / "expected-broken-all.md").read_text(encoding="utf-8")

    for raw_label in ("new", "packed", "shipped", "north", "south", "west"):
        assert raw_label not in snapshot
    assert '"privacy": "sensitive"' in snapshot
    assert "3 breaking · 3 warning · 1 info" in markdown
