# Limitations

- Nullability is observed from the current data, not imported from an external schema declaration.
- Exact distinct counts can be expensive on very wide/high-cardinality datasets.
- CSV inference can select different types when early values change; use Parquet/Arrow for explicit
  types.
- Category labels are never retained, so equal-frequency label replacement is invisible by design.
- Fixed thresholds are useful defaults, not domain-specific anomaly detection.
- Numeric distribution checks use q05/q50/q95 rather than a full statistical test.
- Nested Polars types are represented by canonicalized type text but receive no deep field-level diff.
- DuckDB queries are intentionally conservative and some safe-looking queries may be rejected.
- SchemaSnap does not perform row validation, referential integrity checks, scheduling, alert routing,
  cataloging, lineage, RBAC, or hosted history.
