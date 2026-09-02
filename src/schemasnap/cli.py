"""SchemaSnap command-line interface."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated

import typer

from schemasnap import __version__
from schemasnap.config import SnapConfig, load_config, write_config
from schemasnap.diff import diff_snapshots
from schemasnap.loaders import LoadRequest, load_frame
from schemasnap.models import DiffReport, Severity, Snapshot, SourceDescriptor
from schemasnap.profile import profile_dataframe
from schemasnap.render import render_json, render_markdown, render_terminal
from schemasnap.storage import read_snapshot, write_snapshot, write_text_atomic

app = typer.Typer(
    name="schemasnap",
    help="Privacy-first, Git-native data contract snapshots.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"schemasnap {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option("--version", callback=_version_callback, is_eager=True, help="Show version."),
    ] = None,
) -> None:
    """Inspect local data contracts without storing raw rows."""

    del version


def _read_sql(sql: str | None, sql_file: Path | None) -> str | None:
    if sql is not None and sql_file is not None:
        raise ValueError("provide only one of --sql and --sql-file")
    if sql_file is not None:
        return sql_file.read_text(encoding="utf-8")
    return sql


def _snapshot(source: Path, sql: str | None, sql_file: Path | None) -> Snapshot:
    loaded = load_frame(LoadRequest(source=source, sql=_read_sql(sql, sql_file)))
    descriptor = SourceDescriptor(
        kind=loaded.kind,
        label=source.name,
        query_sha256=loaded.query_sha256,
    )
    return profile_dataframe(loaded.frame, descriptor)


def _render(report: DiffReport, output_format: str) -> str:
    normalized = output_format.casefold()
    if normalized == "terminal":
        return render_terminal(report)
    if normalized == "markdown":
        return render_markdown(report)
    if normalized == "json":
        return render_json(report)
    raise ValueError("format must be terminal, markdown, or json")


def _emit(content: str, output: Path | None) -> None:
    if output is None:
        typer.echo(content, nl=False)
    else:
        write_text_atomic(output, content, overwrite=True)
        typer.echo(f"Wrote {output}")


def _abort(error: Exception) -> None:
    typer.echo(f"Error: {error}", err=True)
    raise typer.Exit(2) from error


@app.command("snapshot")
def snapshot_command(
    source: Annotated[Path, typer.Argument(help="CSV, Parquet, Arrow, or DuckDB file.")],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Snapshot JSON path."),
    ] = Path(".schemasnap/current.snap.json"),
    sql: Annotated[str | None, typer.Option(help="Read-only DuckDB SELECT/WITH query.")] = None,
    sql_file: Annotated[Path | None, typer.Option(help="UTF-8 file containing DuckDB SQL.")] = None,
    force: Annotated[bool, typer.Option(help="Replace an existing output file.")] = False,
) -> None:
    """Create one privacy-safe snapshot."""

    try:
        snapshot = _snapshot(source, sql, sql_file)
        write_snapshot(output, snapshot, overwrite=force)
        typer.echo(f"Wrote {output} ({snapshot.row_count} rows, {snapshot.column_count} columns)")
    except Exception as error:  # expected errors are normalized at the CLI boundary
        _abort(error)


@app.command("init")
def init_command(
    source: Annotated[Path, typer.Argument(help="Initial data source.")],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Baseline snapshot path."),
    ] = Path(".schemasnap/baseline.snap.json"),
    config: Annotated[
        Path,
        typer.Option("--config", help="Project configuration path."),
    ] = Path("schemasnap.toml"),
    sql: Annotated[str | None, typer.Option(help="Read-only DuckDB SELECT/WITH query.")] = None,
    sql_file: Annotated[Path | None, typer.Option(help="UTF-8 file containing DuckDB SQL.")] = None,
    fail_on: Annotated[Severity, typer.Option(case_sensitive=False)] = Severity.BREAKING,
    force: Annotated[bool, typer.Option(help="Replace existing baseline and config.")] = False,
) -> None:
    """Create a baseline snapshot and schemasnap.toml."""

    try:
        if not force:
            for path in (output, config):
                if path.exists():
                    raise FileExistsError(f"already exists: {path}")
        snapshot = _snapshot(source, sql, sql_file)
        config_parent = config.resolve().parent
        relative_source = Path(os.path.relpath(source.resolve(), config_parent))
        relative_baseline = Path(os.path.relpath(output.resolve(), config_parent))
        relative_sql_file = (
            Path(os.path.relpath(sql_file.resolve(), config_parent))
            if sql_file is not None
            else None
        )
        project_config = SnapConfig(
            source=relative_source,
            baseline=relative_baseline,
            fail_on=fail_on,
            sql=sql,
            sql_file=relative_sql_file,
        )
        write_snapshot(output, snapshot, overwrite=force)
        try:
            write_config(config, project_config, overwrite=force)
        except Exception:
            if not force:
                output.unlink(missing_ok=True)
            raise
        typer.echo(f"Initialized {config} with baseline {output}")
    except Exception as error:
        _abort(error)


@app.command("diff")
def diff_command(
    baseline: Annotated[Path, typer.Argument(help="Baseline snapshot JSON.")],
    source: Annotated[Path, typer.Argument(help="Current data source.")],
    output_format: Annotated[
        str,
        typer.Option("--format", help="terminal, markdown, or json."),
    ] = "terminal",
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
    sql: Annotated[str | None, typer.Option()] = None,
    sql_file: Annotated[Path | None, typer.Option()] = None,
) -> None:
    """Compare a saved baseline with current data; never fails on drift."""

    try:
        report = diff_snapshots(read_snapshot(baseline), _snapshot(source, sql, sql_file))
        _emit(_render(report, output_format), output)
    except Exception as error:
        _abort(error)


@app.command("check")
def check_command(
    config: Annotated[Path, typer.Option("--config", help="Project configuration.")] = Path(
        "schemasnap.toml"
    ),
    output_format: Annotated[
        str,
        typer.Option("--format", help="terminal, markdown, or json."),
    ] = "terminal",
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
) -> None:
    """Check configured current data and fail at the configured severity threshold."""

    try:
        project = load_config(config)
        sql = _read_sql(project.sql, project.sql_file)
        report = diff_snapshots(
            read_snapshot(project.baseline),
            _snapshot(project.source, sql, None),
        )
        _emit(_render(report, output_format), output)
        highest = report.highest_severity
        if highest is not None and highest.rank >= project.fail_on.rank:
            typer.echo(
                f"SchemaSnap contract check failed at {highest.value} "
                f"(threshold {project.fail_on.value}).",
                err=True,
            )
            raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as error:
        _abort(error)


if __name__ == "__main__":
    app()
