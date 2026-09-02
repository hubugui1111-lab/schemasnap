from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from schemasnap.cli import app

runner = CliRunner()


def test_init_creates_snapshot_and_config_without_overwriting(csv_pair: tuple[Path, Path]) -> None:
    baseline, _ = csv_pair
    with runner.isolated_filesystem():
        result = runner.invoke(app, ["init", str(baseline)])
        assert result.exit_code == 0, result.output
        assert Path("schemasnap.toml").is_file()
        assert Path(".schemasnap/baseline.snap.json").is_file()

        second = runner.invoke(app, ["init", str(baseline)])
        assert second.exit_code == 2
        assert "already exists" in second.output


def test_diff_renders_markdown_without_failing_build(
    csv_pair: tuple[Path, Path], tmp_path: Path
) -> None:
    baseline, current = csv_pair
    snapshot = tmp_path / "baseline.snap.json"
    init_result = runner.invoke(app, ["snapshot", str(baseline), "--output", str(snapshot)])
    assert init_result.exit_code == 0, init_result.output

    result = runner.invoke(
        app,
        ["diff", str(snapshot), str(current), "--format", "markdown"],
    )

    assert result.exit_code == 0, result.output
    assert "## SchemaSnap diff" in result.output
    assert "BREAKING" in result.output


def test_check_uses_config_and_threshold_exit_codes(
    csv_pair: tuple[Path, Path], tmp_path: Path
) -> None:
    baseline, current = csv_pair
    snapshot = tmp_path / "baseline.snap.json"
    config = tmp_path / "schemasnap.toml"
    assert runner.invoke(app, ["snapshot", str(baseline), "-o", str(snapshot)]).exit_code == 0
    config.write_text(
        f'source = "{current.name}"\nbaseline = "{snapshot.name}"\nfail_on = "BREAKING"\n',
        encoding="utf-8",
    )

    result = runner.invoke(app, ["check", "--config", str(config)])

    assert result.exit_code == 1
    assert "contract check failed" in result.output


def test_operational_error_is_exit_two(tmp_path: Path) -> None:
    result = runner.invoke(app, ["snapshot", str(tmp_path / "missing.csv")])

    assert result.exit_code == 2
    assert "Error:" in result.output


def test_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.output.strip() == "schemasnap 0.1.0"
