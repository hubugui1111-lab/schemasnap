# Design

SchemaSnap has four small layers:

1. Loaders convert CSV, Parquet, Arrow IPC, or restricted DuckDB query output into a Polars DataFrame.
2. The profiler emits strict Pydantic format-1.0 models without raw samples.
3. The diff engine compares two models with fixed thresholds and stable ordering.
4. The CLI renders terminal, Markdown, or JSON and maps results to CI-safe exit codes.

Snapshot and report writes use a temporary file in the destination directory plus `fsync`. New files
are published with a no-clobber hard link; explicit `--force` uses atomic replace. Configuration paths
must be relative and resolve inside the directory containing `schemasnap.toml`.

The implementation favors an inspectable rule set over configuration breadth. v0.1.0 does not infer
primary keys, run remote queries, cache source data, or execute user plugins.
