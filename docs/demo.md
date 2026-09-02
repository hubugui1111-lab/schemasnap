# Reproducing the demo

PowerShell 7:

```powershell
./scripts/demo.ps1
```

Bash:

```bash
./scripts/demo.sh
```

The script installs the locked environment, generates synthetic Parquet/Arrow/DuckDB fixtures, takes
a CSV baseline, diffs the all-failures fixture, writes Markdown, captures the real terminal output, and
renders `assets/demo.svg` from that transcript.

Expected summary:

```text
BREAKING 3  WARNING 3  INFO 1
```

Generated binary data and `demo-output/` remain ignored. The transcript and SVG are committed so a
README visitor sees actual product output, not a mockup.
