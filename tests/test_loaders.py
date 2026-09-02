from __future__ import annotations

from pathlib import Path

import duckdb
import polars as pl
import pyarrow as pa
import pyarrow.ipc as ipc
import pytest

from schemasnap.errors import UnsafeQueryError
from schemasnap.loaders import LoadRequest, load_frame


def test_loads_csv_parquet_and_arrow_ipc(tmp_path: Path) -> None:
    expected = pl.DataFrame({"id": [1, 2], "value": ["a", "b"]})
    csv_path = tmp_path / "data.csv"
    parquet_path = tmp_path / "data.parquet"
    arrow_path = tmp_path / "data.arrow"
    expected.write_csv(csv_path)
    expected.write_parquet(parquet_path)
    table = expected.to_arrow()
    with pa.OSFile(str(arrow_path), "wb") as sink, ipc.new_file(sink, table.schema) as writer:
        writer.write_table(table)

    for path, kind in ((csv_path, "csv"), (parquet_path, "parquet"), (arrow_path, "arrow")):
        loaded = load_frame(LoadRequest(source=path))
        assert loaded.kind == kind
        assert loaded.frame.to_dict(as_series=False) == expected.to_dict(as_series=False)


def test_loads_arrow_stream(tmp_path: Path) -> None:
    path = tmp_path / "stream.arrow"
    table = pa.table({"id": [1, 2]})
    with pa.OSFile(str(path), "wb") as sink, ipc.new_stream(sink, table.schema) as writer:
        writer.write_table(table)

    loaded = load_frame(LoadRequest(source=path))

    assert loaded.frame["id"].to_list() == [1, 2]


def test_duckdb_sql_is_read_only_single_query(tmp_path: Path) -> None:
    database = tmp_path / "warehouse.duckdb"
    connection = duckdb.connect(str(database))
    connection.execute("CREATE TABLE metrics AS SELECT 1 id, 10 score UNION ALL SELECT 2, 20")
    connection.close()

    loaded = load_frame(
        LoadRequest(source=database, sql="SELECT id, score FROM metrics ORDER BY id")
    )

    assert loaded.kind == "duckdb"
    assert loaded.frame["score"].to_list() == [10, 20]
    assert loaded.query_sha256 is not None
    assert len(loaded.query_sha256) == 64


@pytest.mark.parametrize(
    "query",
    [
        "DROP TABLE metrics",
        "SELECT * FROM metrics; DROP TABLE metrics",
        "COPY metrics TO 'leak.csv'",
        "INSTALL httpfs",
        "LOAD httpfs",
        "ATTACH 'other.duckdb'",
        "SELECT * FROM read_csv_auto('private.csv')",
    ],
)
def test_duckdb_rejects_mutating_or_external_sql(tmp_path: Path, query: str) -> None:
    database = tmp_path / "warehouse.duckdb"
    duckdb.connect(str(database)).close()

    with pytest.raises(UnsafeQueryError):
        load_frame(LoadRequest(source=database, sql=query))


def test_unknown_extension_and_missing_sql_fail_cleanly(tmp_path: Path) -> None:
    unknown = tmp_path / "data.json"
    unknown.write_text("[]", encoding="utf-8")
    database = tmp_path / "warehouse.duckdb"
    duckdb.connect(str(database)).close()

    with pytest.raises(ValueError, match="supported"):
        load_frame(LoadRequest(source=unknown))
    with pytest.raises(ValueError, match="SQL"):
        load_frame(LoadRequest(source=database))
