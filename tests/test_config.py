from __future__ import annotations

from pathlib import Path

import pytest

from schemasnap.config import SnapConfig, load_config, write_config
from schemasnap.models import Severity


def test_config_paths_resolve_relative_to_config_file(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    config_path = project / "schemasnap.toml"
    config = SnapConfig(
        source=Path("data/orders.parquet"),
        baseline=Path(".schemasnap/orders.snap.json"),
        fail_on=Severity.WARNING,
    )

    write_config(config_path, config)
    loaded = load_config(config_path)

    assert loaded.source == project / "data" / "orders.parquet"
    assert loaded.baseline == project / ".schemasnap" / "orders.snap.json"
    assert loaded.fail_on is Severity.WARNING


def test_config_rejects_unknown_keys_and_absolute_paths(tmp_path: Path) -> None:
    config_path = tmp_path / "schemasnap.toml"
    config_path.write_text(
        'source = "data.csv"\nbaseline = "x.snap"\nsurprise = true\n', encoding="utf-8"
    )
    with pytest.raises(ValueError, match="unknown"):
        load_config(config_path)

    with pytest.raises(ValueError, match="relative"):
        write_config(
            config_path,
            SnapConfig(source=tmp_path / "private.csv", baseline=Path("base.snap")),
        )


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ('source = "data.csv"\n', "missing"),
        ('source = "data.csv"\nbaseline = "base.snap"\nfail_on = "LOUD"\n', "fail_on"),
        ('source = 7\nbaseline = "base.snap"\n', "source"),
        ('source = "data.csv"\nbaseline = "/absolute.snap"\n', "relative"),
        ('source = "C:\\\\private\\\\data.csv"\nbaseline = "base.snap"\n', "relative"),
        ('source = "../private.csv"\nbaseline = "base.snap"\n', "inside"),
        ('source = "data.csv"\nbaseline = "base.snap"\nsql = 7\n', "sql"),
        (
            'source = "data.duckdb"\nbaseline = "base.snap"\nsql = "SELECT 1"\n'
            'sql_file = "query.sql"\n',
            "only one",
        ),
    ],
)
def test_config_validation_failure_paths(tmp_path: Path, content: str, message: str) -> None:
    config_path = tmp_path / "schemasnap.toml"
    config_path.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        load_config(config_path)


def test_config_round_trips_sql_file(tmp_path: Path) -> None:
    config_path = tmp_path / "schemasnap.toml"
    config = SnapConfig(
        source=Path("warehouse.duckdb"),
        baseline=Path("baseline.snap.json"),
        sql_file=Path("queries/orders.sql"),
    )

    write_config(config_path, config)
    loaded = load_config(config_path)

    assert loaded.sql_file == tmp_path / "queries" / "orders.sql"


def test_config_writer_rejects_absolute_sql_file(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="sql_file"):
        write_config(
            tmp_path / "schemasnap.toml",
            SnapConfig(
                source=Path("warehouse.duckdb"),
                baseline=Path("baseline.snap.json"),
                sql_file=tmp_path / "query.sql",
            ),
        )


def test_config_writer_rejects_parent_traversal(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="inside"):
        write_config(
            tmp_path / "project" / "schemasnap.toml",
            SnapConfig(source=Path("../private.csv"), baseline=Path("baseline.snap.json")),
        )
