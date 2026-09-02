from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from schemasnap.models import Snapshot, SourceDescriptor
from schemasnap.storage import read_snapshot, write_snapshot, write_text_atomic

pytestmark = pytest.mark.integration


def _empty_snapshot() -> Snapshot:
    return Snapshot(
        source=SourceDescriptor(kind="csv", label="empty.csv"),
        row_count=0,
        columns=[],
    )


def test_snapshot_round_trip_and_parent_creation(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "baseline.snap.json"

    write_snapshot(path, _empty_snapshot())

    assert read_snapshot(path) == _empty_snapshot()


def test_atomic_writer_refuses_overwrite_and_leaves_original_intact(tmp_path: Path) -> None:
    path = tmp_path / "result.md"
    path.write_text("original\n", encoding="utf-8")

    with pytest.raises(FileExistsError, match="already exists"):
        write_text_atomic(path, "replacement\n")

    assert path.read_text(encoding="utf-8") == "original\n"
    assert list(tmp_path.glob("*.tmp")) == []


def test_atomic_writer_can_replace_when_explicit(tmp_path: Path) -> None:
    path = tmp_path / "result.md"
    path.write_text("old\n", encoding="utf-8")

    write_text_atomic(path, "new\n", overwrite=True)

    assert path.read_text(encoding="utf-8") == "new\n"


def test_malformed_and_future_snapshot_are_rejected(tmp_path: Path) -> None:
    malformed = tmp_path / "malformed.snap.json"
    malformed.write_text("{not-json", encoding="utf-8")
    with pytest.raises(ValidationError):
        read_snapshot(malformed)

    future = tmp_path / "future.snap.json"
    future.write_text(
        '{"schema_version":"2.0","source":{"kind":"csv","label":"x.csv"},'
        '"row_count":0,"columns":[]}',
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        read_snapshot(future)
