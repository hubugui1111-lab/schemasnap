from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_readme_has_real_demo_core_commands_and_distribution_warning() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "assets/demo.svg" in readme
    assert "schemasnap init data.parquet" in readme
    assert "schemasnap diff .schemasnap/baseline.snap.json data.parquet" in readme
    assert "schemasnap check" in readme
    assert "schemasnap-data" in readme
    assert "do not run `pip install schemasnap`" in readme


def test_required_community_and_design_documents_exist() -> None:
    paths = [
        "LICENSE",
        "NOTICE",
        "SECURITY.md",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "CHANGELOG.md",
        "README.zh-CN.md",
        "docs/privacy.md",
        "docs/drift-rules.md",
        "docs/snapshot-format.md",
        "docs/duckdb-sql.md",
        "examples/github-actions/schemasnap.yml",
        "schemasnap.example.toml",
    ]

    assert all((ROOT / path).is_file() for path in paths)


def test_workflows_pin_setup_uv_to_published_exact_tag() -> None:
    workflows = list((ROOT / ".github" / "workflows").glob("*.yml"))

    assert workflows
    for workflow in workflows:
        content = workflow.read_text(encoding="utf-8")
        assert "astral-sh/setup-uv@v10\n" not in content
        if "setup-uv" in content:
            assert "astral-sh/setup-uv@v10.0.1" in content


def test_demo_asset_is_derived_from_verified_transcript() -> None:
    transcript = (ROOT / "assets" / "demo-transcript.txt").read_text(encoding="utf-8")
    svg = (ROOT / "assets" / "demo.svg").read_text(encoding="utf-8")

    assert "BREAKING 3  WARNING 3  INFO 1" in transcript
    assert "COLUMN_REMOVED" in transcript
    assert "CATEGORY_DRIFT" in transcript
    assert "verified demo" in svg
