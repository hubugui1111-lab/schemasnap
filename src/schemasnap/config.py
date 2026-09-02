"""Minimal strict TOML project configuration."""

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass
from pathlib import Path

from schemasnap.models import Severity
from schemasnap.storage import write_text_atomic


@dataclass(frozen=True, slots=True)
class SnapConfig:
    source: Path
    baseline: Path
    fail_on: Severity = Severity.BREAKING
    sql: str | None = None
    sql_file: Path | None = None


_KEYS = {"source", "baseline", "fail_on", "sql", "sql_file"}


def _relative_path(value: object, key: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty relative path")
    path = Path(value)
    if path.is_absolute():
        raise ValueError(f"{key} must be relative to schemasnap.toml")
    return path


def load_config(path: Path) -> SnapConfig:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    unknown = set(raw) - _KEYS
    if unknown:
        raise ValueError(f"unknown config keys: {', '.join(sorted(unknown))}")
    missing = {"source", "baseline"} - set(raw)
    if missing:
        raise ValueError(f"missing config keys: {', '.join(sorted(missing))}")
    base = path.resolve().parent
    source = (base / _relative_path(raw["source"], "source")).resolve()
    baseline = (base / _relative_path(raw["baseline"], "baseline")).resolve()
    try:
        fail_on = Severity(str(raw.get("fail_on", Severity.BREAKING.value)).upper())
    except ValueError as error:
        raise ValueError("fail_on must be INFO, WARNING, or BREAKING") from error
    sql = raw.get("sql")
    if sql is not None and not isinstance(sql, str):
        raise ValueError("sql must be a string")
    sql_file_value = raw.get("sql_file")
    sql_file = (
        (base / _relative_path(sql_file_value, "sql_file")).resolve()
        if sql_file_value is not None
        else None
    )
    if sql is not None and sql_file is not None:
        raise ValueError("configure only one of sql and sql_file")
    return SnapConfig(
        source=source,
        baseline=baseline,
        fail_on=fail_on,
        sql=sql,
        sql_file=sql_file,
    )


def write_config(path: Path, config: SnapConfig, *, overwrite: bool = False) -> None:
    for key, candidate in (("source", config.source), ("baseline", config.baseline)):
        if candidate.is_absolute():
            raise ValueError(f"{key} must be relative to schemasnap.toml")
    if config.sql_file is not None and config.sql_file.is_absolute():
        raise ValueError("sql_file must be relative to schemasnap.toml")
    lines = [
        f"source = {json.dumps(config.source.as_posix())}",
        f"baseline = {json.dumps(config.baseline.as_posix())}",
        f"fail_on = {json.dumps(config.fail_on.value)}",
    ]
    if config.sql is not None:
        lines.append(f"sql = {json.dumps(config.sql)}")
    if config.sql_file is not None:
        lines.append(f"sql_file = {json.dumps(config.sql_file.as_posix())}")
    write_text_atomic(path, "\n".join(lines) + "\n", overwrite=overwrite)
