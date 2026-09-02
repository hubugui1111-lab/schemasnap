## SchemaSnap diff

`baseline.csv` → `broken-all.csv`

**3 breaking · 3 warning · 1 info**

| Severity | Code | Column | Before | After | Detail |
|---|---|---|---|---|---|
| BREAKING | COLUMN_REMOVED | region | string | — | column was removed |
| BREAKING | TYPE_CHANGED | order_id | int64 | string | column data type changed |
| BREAKING | NULLABILITY_RELAXED | amount | false | true | null values are now observed |
| WARNING | RANGE_SHIFT | amount | 10.0..13.0 | 1000.0..1300.0 | numeric range moved beyond the 50% baseline-span threshold |
| WARNING | DISTRIBUTION_SHIFT | amount | 12.0 | 1200.0 | median moved beyond the deterministic baseline threshold |
| WARNING | CATEGORY_DRIFT | status | 3 | 4 | label-free category cardinality or frequency profile changed |
| INFO | COLUMN_ADDED | new_flag | — | bool | column was added |
