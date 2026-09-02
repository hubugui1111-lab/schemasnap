"""Minimal strict TOML project configuration."""

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath

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


def _is_absolute_on_any_platform(value: str) -> bool:
    return PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute()


def _relative_path(value: object, key: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty relative path")
    if _is_absolute_on_any_platform(value):
        raise ValueError(f"{key} must be relative to schemasnap.toml")
    return Path(value)


def _resolve_project_path(base: Path, value: object, key: str) -> Path:
    candidate = (base / _relative_path(value, key)).resolve()
    try:
        candidate.relative_to(base)
    except ValueError as error:
        raise ValueError(f"{key} must stay inside the SchemaSnap project") from error
    return candidate


def load_config(path: Path) -> SnapConfig:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    unknown = set(raw) - _KEYS
    if unknown:
        raise ValueError(f"unknown config keys: {', '.join(sorted(unknown))}")
    missing = {"source", "baseline"} - set(raw)
    if missing:
        raise ValueError(f"missing config keys: {', '.join(sorted(missing))}")
    base = path.resolve().parent
    source = _resolve_project_path(base, raw["source"], "source")
    baseline = _resolve_project_path(base, raw["baseline"], "baseline")
    try:
        fail_on = Severity(str(raw.get("fail_on", Severity.BREAKING.value)).upper())
    except ValueError as error:
        raise ValueError("fail_on must be INFO, WARNING, or BREAKING") from error
    sql = raw.get("sql")
    if sql is not None and not isinstance(sql, str):
        raise ValueError("sql must be a string")
    sql_file_value = raw.get("sql_file")
    sql_file = (
        _resolve_project_path(base, sql_file_value, "sql_file")
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
    base = path.resolve().parent
    for key, candidate in (("source", config.source), ("baseline", config.baseline)):
        if _is_absolute_on_any_platform(str(candidate)):
            raise ValueError(f"{key} must be relative to schemasnap.toml")
        _resolve_project_path(base, str(candidate), key)
    if config.sql_file is not None and _is_absolute_on_any_platform(str(config.sql_file)):
        raise ValueError("sql_file must be relative to schemasnap.toml")
    if config.sql_file is not None:
        _resolve_project_path(base, str(config.sql_file), "sql_file")
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
