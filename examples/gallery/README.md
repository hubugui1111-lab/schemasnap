# Broken Data Gallery

Each file changes one data-contract dimension relative to `baseline.csv`. The gallery is safe to
publish: it contains synthetic order data and no real identities or credentials.

Start with the committed [privacy-safe baseline snapshot](baseline.snap.json) and
[expected all-failures Markdown diff](expected-broken-all.md).

| Fixture | Expected signal |
|---|---|
| `removed-column.csv` | `COLUMN_REMOVED` (BREAKING) |
| `type-change.csv` | `TYPE_CHANGED` (BREAKING) |
| `nullable.csv` | `NULLABILITY_RELAXED` (BREAKING) |
| `category-drift.csv` | `CATEGORY_DRIFT` (WARNING) |
| `distribution-shift.csv` | `RANGE_SHIFT` + `DISTRIBUTION_SHIFT` (WARNING) |
| `broken-all.csv` | A reviewable mix of all CSV failure modes |
| `generated/timestamp-utc.parquet` → `timestamp-naive.parquet` | `TIMEZONE_CHANGED` (BREAKING) |
| `generated/orders.arrow` | Arrow IPC loader smoke fixture |
| `generated/gallery.duckdb` + `query.sql` | Read-only DuckDB SQL loader fixture |

Generate binary fixtures and the verified demo output with `scripts/demo.ps1` or
`scripts/demo.sh`. Generated data files stay untracked so DuckDB/Arrow/Parquet implementation
details do not create noisy Git diffs.

