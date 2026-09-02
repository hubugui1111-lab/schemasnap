from __future__ import annotations

from pathlib import Path

import duckdb
import pytest
from typer.testing import CliRunner

from schemasnap.cli import app

runner = CliRunner()
pytestmark = pytest.mark.integration


def test_snapshot_refuses_overwrite_without_force(tmp_path: Path) -> None:
    source = tmp_path / "data.csv"
    output = tmp_path / "baseline.snap.json"
    source.write_text("value\n1\n", encoding="utf-8")
    output.write_text("keep-me\n", encoding="utf-8")

    result = runner.invoke(app, ["snapshot", str(source), "-o", str(output)])

    assert result.exit_code == 2
    assert output.read_text(encoding="utf-8") == "keep-me\n"


def test_snapshot_force_overwrites_and_output_file_rendering(tmp_path: Path) -> None:
    baseline_source = tmp_path / "before.csv"
    current_source = tmp_path / "after.csv"
    snapshot = tmp_path / "baseline.snap.json"
    report = tmp_path / "report.md"
    baseline_source.write_text("value\n1\n2\n", encoding="utf-8")
    current_source.write_text("value,added\n100,x\n200,y\n", encoding="utf-8")
    snapshot.write_text("replace-me\n", encoding="utf-8")

    first = runner.invoke(
        app,
        ["snapshot", str(baseline_source), "-o", str(snapshot), "--force"],
    )
    second = runner.invoke(
        app,
        ["diff", str(snapshot), str(current_source), "--format", "markdown", "-o", str(report)],
    )

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert "## SchemaSnap diff" in report.read_text(encoding="utf-8")


def test_invalid_format_and_mutually_exclusive_sql_are_exit_two(tmp_path: Path) -> None:
    source = tmp_path / "data.csv"
    baseline = tmp_path / "baseline.snap.json"
    sql_file = tmp_path / "query.sql"
    source.write_text("value\n1\n", encoding="utf-8")
    sql_file.write_text("SELECT 1", encoding="utf-8")
    assert runner.invoke(app, ["snapshot", str(source), "-o", str(baseline)]).exit_code == 0

    invalid_format = runner.invoke(
        app,
        ["diff", str(baseline), str(source), "--format", "xml"],
    )
    both_sql = runner.invoke(
        app,
        [
            "snapshot",
            str(source),
            "--sql",
            "SELECT 1",
            "--sql-file",
            str(sql_file),
            "--force",
        ],
    )

    assert invalid_format.exit_code == 2
    assert "terminal, markdown, or json" in invalid_format.output
    assert both_sql.exit_code == 2
    assert "only one" in both_sql.output


def test_check_passes_when_only_info_is_below_threshold(tmp_path: Path) -> None:
    baseline_source = tmp_path / "before.csv"
    current_source = tmp_path / "after.csv"
    snapshot = tmp_path / "baseline.snap.json"
    config = tmp_path / "schemasnap.toml"
    baseline_source.write_text("value\n1\n2\n", encoding="utf-8")
    current_source.write_text("value,added\n1,x\n2,y\n", encoding="utf-8")
    assert (
        runner.invoke(app, ["snapshot", str(baseline_source), "-o", str(snapshot)]).exit_code == 0
    )
    config.write_text(
        'source = "after.csv"\nbaseline = "baseline.snap.json"\nfail_on = "WARNING"\n',
        encoding="utf-8",
    )

    result = runner.invoke(app, ["check", "--config", str(config)])

    assert result.exit_code == 0
    assert "COLUMN_ADDED" in result.output


def test_duckdb_sql_file_cli_never_persists_query_text(tmp_path: Path) -> None:
    database = tmp_path / "warehouse.duckdb"
    query_file = tmp_path / "query.sql"
    output = tmp_path / "warehouse.snap.json"
    connection = duckdb.connect(str(database))
    connection.execute("CREATE TABLE metrics AS SELECT 1 AS id, 42 AS value")
    connection.close()
    query = "SELECT id, value FROM metrics"
    query_file.write_text(query, encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "snapshot",
            str(database),
            "--sql-file",
            str(query_file),
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    content = output.read_text(encoding="utf-8")
    assert query not in content
    assert "query_sha256" in content


def test_python_module_entrypoint_reports_version() -> None:
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "schemasnap", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "schemasnap 0.1.0"
