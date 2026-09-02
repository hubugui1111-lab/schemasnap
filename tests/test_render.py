from __future__ import annotations

import polars as pl

from schemasnap.diff import diff_snapshots
from schemasnap.models import SourceDescriptor
from schemasnap.profile import profile_dataframe
from schemasnap.render import render_json, render_markdown, render_terminal


def test_renderers_are_deterministic_and_markdown_safe() -> None:
    baseline = profile_dataframe(
        pl.DataFrame({"value": [1, 2], "removed|column": [1, 2]}),
        SourceDescriptor(kind="csv", label="before.csv"),
    )
    current = profile_dataframe(
        pl.DataFrame({"value": [100, 200], "added": [1, 2]}),
        SourceDescriptor(kind="csv", label="after.csv"),
    )
    report = diff_snapshots(baseline, current)

    markdown = render_markdown(report)
    terminal = render_terminal(report, color=False)
    encoded = render_json(report)

    assert "## SchemaSnap diff" in markdown
    assert "removed\\|column" in markdown
    assert "BREAKING" in markdown
    assert "SchemaSnap diff" in terminal
    assert encoded.endswith("\n")
    assert render_markdown(report) == markdown
