# Snapshot format 1.0

Snapshots are UTF-8 JSON with sorted keys, two-space indentation, one trailing newline, and no
wall-clock metadata. Re-running against identical input produces byte-identical output.

```json
{
  "column_count": 1,
  "columns": [
    {
      "data_type": "float64",
      "distinct_count": 4,
      "name": "amount",
      "non_null_count": 4,
      "null_count": 0,
      "null_ratio": 0.0,
      "nullable": false,
      "numeric": {
        "maximum": 13.0,
        "mean": 11.5,
        "minimum": 10.0,
        "non_finite_count": 0,
        "q05": 10.0,
        "q50": 12.0,
        "q95": 13.0
      },
      "privacy": "standard",
      "uniqueness_ratio": 1.0
    }
  ],
  "generator": {"name": "schemasnap", "version": "0.1.0"},
  "row_count": 4,
  "schema_version": "1.0",
  "source": {"kind": "csv", "label": "orders.csv"}
}
```

Models reject unknown fields, duplicate column names, inconsistent column counts, non-finite JSON
numbers, and any schema version other than `1.0`. A future format will use a new version rather than
silently changing the meaning of existing fields.

Profiles are emitted in source column order. Diff changes use a fixed rule order and then column name,
so reviews remain stable across operating systems.

