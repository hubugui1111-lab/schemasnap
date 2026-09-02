# SchemaSnap

[![CI](https://github.com/hubugui1111-lab/schemasnap/actions/workflows/ci.yml/badge.svg)](https://github.com/hubugui1111-lab/schemasnap/actions/workflows/ci.yml)
[![CodeQL](https://github.com/hubugui1111-lab/schemasnap/actions/workflows/codeql.yml/badge.svg)](https://github.com/hubugui1111-lab/schemasnap/actions/workflows/codeql.yml)
[![Security](https://github.com/hubugui1111-lab/schemasnap/actions/workflows/security.yml/badge.svg)](https://github.com/hubugui1111-lab/schemasnap/actions/workflows/security.yml)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-3776AB)](https://www.python.org/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)

**Git diff for data.** Snapshot a local dataset, review deterministic contract drift, and fail a
pull request before a silent schema change reaches production.

[中文文档](README.zh-CN.md) · [Broken Data Gallery](examples/gallery/README.md) ·
[Privacy model](docs/privacy.md) · [Drift rules](docs/drift-rules.md)

![Verified SchemaSnap CLI demo](assets/demo.svg)

## Why SchemaSnap?

Data contracts often live in dashboards, prose, or a developer's memory. SchemaSnap emits a small,
stable JSON artifact that belongs in Git next to the pipeline it protects. Every verdict comes from
documented rules—no LLM, remote service, telemetry, or hidden state.

- Reads **CSV, Parquet, Arrow IPC, and read-only DuckDB SQL**.
- Tracks names, canonical types, observed nullability, row/null/distinct counts, uniqueness, numeric
  ranges and quantiles, temporal bounds/timezones, and label-free category shape.
- Reports **INFO**, **WARNING**, and **BREAKING** changes in terminal, Markdown, or JSON.
- Never writes raw rows, string samples, category labels, SQL text, absolute paths, e-mail addresses,
  names, user IDs, or credential-like values into a snapshot.
- Runs locally and in GitHub Actions with useful exit codes: `0` pass, `1` contract threshold reached,
  `2` operational/configuration error.

## 30-second local demo

Requirements: Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/hubugui1111-lab/schemasnap.git
cd schemasnap
uv sync --locked

uv run schemasnap snapshot examples/gallery/baseline.csv \
  --output demo-output/baseline.snap.json --force
uv run schemasnap diff demo-output/baseline.snap.json \
  examples/gallery/broken-all.csv --format markdown
```

Or reproduce every binary fixture and the README demo:

```powershell
./scripts/demo.ps1
```

```bash
./scripts/demo.sh
```

The full gallery independently demonstrates removed columns, type changes, newly observed nulls,
category drift, timestamp timezone loss, range shifts, and distribution shifts.

## The three-command workflow

```bash
# 1. Commit a baseline and schemasnap.toml
schemasnap init data.parquet

# 2. Review drift without failing the shell
schemasnap diff .schemasnap/baseline.snap.json data.parquet

# 3. Enforce the configured threshold (BREAKING by default)
schemasnap check
```

`schemasnap snapshot` is also available for scripts that want an explicit output path without
creating project configuration.

## Inputs

| Source | Example |
|---|---|
| CSV | `schemasnap snapshot orders.csv -o orders.snap.json` |
| Parquet | `schemasnap snapshot orders.parquet -o orders.snap.json` |
| Arrow IPC file or stream | `schemasnap snapshot orders.arrow -o orders.snap.json` |
| DuckDB SQL | `schemasnap snapshot warehouse.duckdb --sql-file query.sql -o orders.snap.json` |

DuckDB accepts exactly one `SELECT` or `WITH` query. The connection is read-only, external access is
disabled, and mutation/administration/file-reader keywords are rejected before execution. Snapshots
store only a SHA-256 query fingerprint—not the SQL itself.

## What gets committed

```text
.schemasnap/baseline.snap.json  # deterministic, privacy-safe contract
schemasnap.toml                 # relative source/baseline paths + failure threshold
```

```toml
source = "data/orders.parquet"
baseline = ".schemasnap/baseline.snap.json"
fail_on = "BREAKING"
```

For DuckDB, prefer a relative `sql_file = "queries/orders.sql"`. See the
[snapshot format](docs/snapshot-format.md) and [SQL boundary](docs/duckdb-sql.md).

## Severity at a glance

| Severity | Default behavior | Examples |
|---|---|---|
| `INFO` | Report only | Column added; observed nullability tightened |
| `WARNING` | Report only | Major row/range/category/distribution shift |
| `BREAKING` | `check` exits 1 | Column removed; type changed; new nulls; timezone changed |

Rules and thresholds are fixed and versioned. Read [drift-rules.md](docs/drift-rules.md) before
treating them as policy.

## GitHub Actions

Copy [`examples/github-actions/schemasnap.yml`](examples/github-actions/schemasnap.yml) into the
repository that owns your data pipeline. It writes the Markdown report to the job summary and keeps
the report as an artifact even when the contract gate fails.

## Privacy boundary

SchemaSnap deliberately sacrifices some observability to avoid turning Git history into a data leak.
Category profiles contain only cardinality, entropy, and sorted frequency ratios. Therefore, replacing
two labels with two different labels at the same frequencies is intentionally invisible. Column names
remain visible because they are the schema contract; rename sensitive schema fields before publishing a
snapshot if even their names are confidential.

Read the complete [privacy model](docs/privacy.md) before committing snapshots from sensitive systems.

## Installation name

The Python distribution is **`schemasnap-data`**; the import package and executable are `schemasnap`.
The existing `schemasnap` project on PyPI is unrelated. Until a signed PyPI release is announced here,
install from source or the wheel attached to a GitHub release—do not run `pip install schemasnap`.

## Project boundary

SchemaSnap is a small local CLI, not a dashboard, SaaS, data catalog, RBAC system, pipeline scheduler,
or replacement for Great Expectations. It detects contract drift; it does not validate every business
rule or prove that aggregate statistics are non-sensitive for every threat model.

## Development

```bash
uv sync --locked
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest --cov=schemasnap --cov-branch
uv run pip-audit --skip-editable
uv build
```

The suite contains unit, CLI, failure-path, loader integration, privacy regression, gallery, and
packaging contracts. See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and the
[release checklist](docs/releasing.md).

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
