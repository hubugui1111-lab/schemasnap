# Deterministic drift rules

SchemaSnap v0.1.0 uses fixed local rules. There is no learned baseline, LLM, remote policy, or random
sampling.

## BREAKING

- `COLUMN_REMOVED`: a baseline column is absent.
- `TYPE_CHANGED`: the canonical Polars data type changed.
- `NULLABILITY_RELAXED`: a column with no baseline nulls now contains at least one null.
- `TIMEZONE_CHANGED`: a temporal column's timezone changed, appeared, or disappeared.

## WARNING

- `RANGE_SHIFT`: either numeric boundary moved by more than 50% of the baseline span. A 1% absolute
  baseline-value floor prevents zero-width ranges from becoming unstable.
- `DISTRIBUTION_SHIFT`: the median moved by more than both two baseline q05–q95 spans and 50% of the
  baseline median magnitude.
- `CATEGORY_DRIFT`: label-free cardinality changed, frequency-profile L1 distance exceeded 0.25, or
  entropy moved by more than 0.5 bits.
- `ROW_COUNT_SHIFT`: row count fell below 0.5× or rose above 2×; empty-to-non-empty also warns.

## INFO

- `NULLABILITY_TIGHTENED`: baseline nulls are no longer observed.
- `COLUMN_ADDED`: a current column did not exist in the baseline.

The default `check` threshold is `BREAKING`. Set `fail_on = "WARNING"` or `"INFO"` in
`schemasnap.toml` for stricter projects. A rule can emit more than one change for one column—for
example, a large numeric shift can produce both range and distribution warnings.

Observed nullability is an empirical property, not a database `NOT NULL` declaration. Small datasets
can therefore move between nullable states as values appear or disappear.
