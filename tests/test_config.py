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
