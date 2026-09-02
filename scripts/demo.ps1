$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $RepoRoot

uv sync --locked
uv run python scripts/build_gallery.py
New-Item -ItemType Directory -Force -Path demo-output, assets | Out-Null
uv run schemasnap snapshot examples/gallery/baseline.csv --output demo-output/baseline.snap.json --force
uv run schemasnap diff demo-output/baseline.snap.json examples/gallery/broken-all.csv --format markdown --output demo-output/diff.md
uv run schemasnap diff demo-output/baseline.snap.json examples/gallery/broken-all.csv --format terminal |
    Tee-Object -FilePath assets/demo-transcript.txt
uv run python scripts/render_demo_svg.py
