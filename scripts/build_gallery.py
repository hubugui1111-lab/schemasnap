"""Build deterministic local binary fixtures for the Broken Data Gallery."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import duckdb
import polars as pl
import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.ipc as ipc  # type: ignore[import-untyped]

ROOT = Path(__file__).resolve().parents[1]
GALLERY = ROOT / "examples" / "gallery"
GENERATED = GALLERY / "generated"


def build() -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    baseline = pl.read_csv(GALLERY / "baseline.csv")
    baseline.write_parquet(GENERATED / "orders.parquet")

    table = baseline.to_arrow()
    arrow_path = GENERATED / "orders.arrow"
    with pa.OSFile(str(arrow_path), "wb") as sink, ipc.new_file(sink, table.schema) as writer:
        writer.write_table(table)

    utc = pl.DataFrame(
        {
            "event": ["created", "shipped"],
            "processed_at": [
                datetime(2026, 1, 1, tzinfo=UTC),
                datetime(2026, 1, 2, tzinfo=UTC),
            ],
        }
    )
    naive = utc.with_columns(pl.col("processed_at").dt.replace_time_zone(None))
    utc.write_parquet(GENERATED / "timestamp-utc.parquet")
    naive.write_parquet(GENERATED / "timestamp-naive.parquet")

    database = GENERATED / "gallery.duckdb"
    connection = duckdb.connect(str(database))
    try:
        connection.execute("DROP TABLE IF EXISTS orders")
        connection.execute(
            """
            CREATE TABLE orders AS
            SELECT * FROM (VALUES
              (1001, 10.0, 'new', TIMESTAMPTZ '2026-01-01 00:00:00+00'),
              (1002, 12.0, 'shipped', TIMESTAMPTZ '2026-01-02 00:00:00+00')
            ) AS data(order_id, amount, status, processed_at)
            """
        )
        connection.execute("CHECKPOINT")
    finally:
        connection.close()

    print(f"Built gallery fixtures in {GENERATED.relative_to(ROOT)}")


if __name__ == "__main__":
    build()
