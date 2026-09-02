"""Bounded local data loaders."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import duckdb
import polars as pl
import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.ipc as ipc  # type: ignore[import-untyped]

from schemasnap.errors import UnsafeQueryError, UnsupportedSourceError
from schemasnap.privacy import query_fingerprint


@dataclass(frozen=True, slots=True)
class LoadRequest:
    source: Path
    sql: str | None = None


@dataclass(frozen=True, slots=True)
class LoadedFrame:
    frame: pl.DataFrame
    kind: Literal["csv", "parquet", "arrow", "duckdb"]
    query_sha256: str | None = None


_BLOCKED_SQL = re.compile(
    r"\b(?:attach|call|copy|create|delete|detach|drop|export|import|insert|install|load|"
    r"pragma|replace|set|truncate|update|use|vacuum)\b",
    flags=re.IGNORECASE,
)
_EXTERNAL_SQL = re.compile(
    r"\b(?:httpfs|read_blob|read_csv|read_csv_auto|read_json|read_json_auto|read_ndjson|"
    r"read_parquet|sqlite_scan|postgres_scan|mysql_scan)\b",
    flags=re.IGNORECASE,
)


def validate_read_only_query(query: str) -> str:
    normalized = query.strip()
    if not normalized:
        raise UnsafeQueryError("DuckDB SQL cannot be empty")
    if ";" in normalized:
        raise UnsafeQueryError("DuckDB SQL must contain exactly one statement")
    if re.match(r"^(select|with)\b", normalized, flags=re.IGNORECASE) is None:
        raise UnsafeQueryError("DuckDB SQL must start with SELECT or WITH")
    if _BLOCKED_SQL.search(normalized) is not None:
        raise UnsafeQueryError("DuckDB SQL contains a mutating or administrative keyword")
    if _EXTERNAL_SQL.search(normalized) is not None:
        raise UnsafeQueryError("DuckDB SQL cannot read external files or extensions")
    return normalized


def _arrow_table(path: Path) -> pa.Table:
    try:
        with pa.memory_map(str(path), "r") as source:
            return ipc.open_file(source).read_all()
    except pa.ArrowInvalid:
        with pa.memory_map(str(path), "r") as source:
            return ipc.open_stream(source).read_all()


def _from_arrow(table: pa.Table) -> pl.DataFrame:
    frame = pl.from_arrow(table)
    if not isinstance(frame, pl.DataFrame):
        raise TypeError("Arrow input did not produce a table")
    return frame


def _load_duckdb(path: Path, query: str) -> LoadedFrame:
    safe_query = validate_read_only_query(query)
    connection = duckdb.connect(
        database=str(path),
        read_only=True,
        config={"enable_external_access": "false", "allow_unsigned_extensions": "false"},
    )
    try:
        table = connection.execute(safe_query).to_arrow_table()
    finally:
        connection.close()
    return LoadedFrame(
        frame=_from_arrow(table),
        kind="duckdb",
        query_sha256=query_fingerprint(safe_query),
    )


def load_frame(request: LoadRequest) -> LoadedFrame:
    """Load one supported local source without retaining its raw contents."""

    path = request.source.expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"source does not exist: {request.source}")
    suffix = path.suffix.casefold()
    if suffix == ".csv":
        return LoadedFrame(frame=pl.read_csv(path), kind="csv")
    if suffix in {".parquet", ".pq"}:
        return LoadedFrame(frame=pl.read_parquet(path), kind="parquet")
    if suffix in {".arrow", ".ipc", ".feather"}:
        return LoadedFrame(frame=_from_arrow(_arrow_table(path)), kind="arrow")
    if suffix in {".duckdb", ".ddb"}:
        if request.sql is None:
            raise ValueError("DuckDB sources require SQL via --sql or --sql-file")
        return _load_duckdb(path, request.sql)
    raise UnsupportedSourceError(
        "supported sources are CSV, Parquet, Arrow IPC, and DuckDB databases"
    )
