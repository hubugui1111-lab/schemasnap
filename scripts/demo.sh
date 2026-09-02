#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

uv sync --locked
uv run python scripts/build_gallery.py
mkdir -p demo-output assets
uv run schemasnap snapshot examples/gallery/baseline.csv --output demo-output/baseline.snap.json --force
uv run schemasnap diff demo-output/baseline.snap.json examples/gallery/broken-all.csv --format markdown --output demo-output/diff.md
uv run schemasnap diff demo-output/baseline.snap.json examples/gallery/broken-all.csv --format terminal | tee assets/demo-transcript.txt
uv run python scripts/render_demo_svg.py

