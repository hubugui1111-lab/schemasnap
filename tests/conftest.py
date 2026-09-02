from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest


@pytest.fixture
def baseline_frame() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "order_id": [1001, 1002, 1003, 1004],
            "amount": [10.0, 12.0, 11.0, 13.0],
            "region": ["north", "south", "north", "west"],
            "optional_note": [None, "fragile", None, None],
            "created_at": pl.Series(
                [
                    "2026-01-01T00:00:00Z",
                    "2026-01-02T00:00:00Z",
                    "2026-01-03T00:00:00Z",
                    "2026-01-04T00:00:00Z",
                ]
            ).str.to_datetime(time_zone="UTC"),
        }
    )


@pytest.fixture
def csv_pair(tmp_path: Path) -> tuple[Path, Path]:
    baseline = tmp_path / "baseline.csv"
    current = tmp_path / "current.csv"
    baseline.write_text(
        "id,score,status\n1,10,new\n2,11,done\n3,12,new\n",
        encoding="utf-8",
    )
    current.write_text(
        "id,score,status,owner_email\n1,100,new,a@example.test\n2,,blocked,b@example.test\n",
        encoding="utf-8",
    )
    return baseline, current
