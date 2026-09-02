# DuckDB SQL boundary

DuckDB input is intentionally narrow:

```bash
schemasnap snapshot warehouse.duckdb \
  --sql-file queries/orders.sql \
  --output orders.snap.json
```

The query must be one non-empty statement beginning with `SELECT` or `WITH`. Semicolons,
mutation/DDL/administration keywords, extension operations, and known external file-reader functions
are rejected. The database opens with `read_only=True`, `enable_external_access=false`, and unsigned
extensions disabled. Results cross the boundary as an Arrow table.

This is defense in depth, not a general SQL sandbox. Only run queries against databases you are
authorized to read. The SQL file may contain sensitive business logic and should be protected like
source code. The snapshot retains only its SHA-256 fingerprint.

Inline `--sql` is useful for local experiments. `sql_file` in `schemasnap.toml` is easier to review and
avoids shell-history leakage.

