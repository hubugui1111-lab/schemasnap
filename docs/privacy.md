# Privacy model

SchemaSnap is designed so that the normal snapshot artifact is safer to commit than sampled rows. It
does not claim to anonymize arbitrary datasets or provide formal differential privacy.

## Never persisted

- Raw rows or cell samples
- Raw strings or category labels
- E-mail addresses, personal names, phone/address/SSN values, user/account IDs, passwords, API keys,
  tokens, or secrets
- DuckDB SQL text
- Absolute source paths
- Wall-clock creation timestamps

## Persisted

- Column names and canonical data types
- Row, null, non-null, distinct, and column counts
- Null and uniqueness ratios
- Numeric min/max, mean, q05, q50, q95, and non-finite count for non-sensitive fields
- Temporal min/max and timezone for non-sensitive fields
- Category cardinality, entropy, and sorted frequency ratios for non-sensitive fields
- A SHA-256 fingerprint for DuckDB SQL

Column-name heuristics conservatively suppress detailed profiles for fields resembling names, e-mail,
IDs, phones, addresses, credentials, tokens, and secrets. Detection is schema-name based and cannot
understand every domain. Rename or exclude data before profiling if aggregate statistics or column
names themselves are sensitive under your threat model.

## Deliberate blind spot

Category labels never enter the artifact. Two categories replaced by two different categories with
the same frequencies produce the same profile. This is intentional: detecting that case would require
retaining a stable representation of each raw label, which can still enable guessing attacks for small
domains.

## Local execution

All profiling occurs in the current process. SchemaSnap has no telemetry, account, server, network
client, or upload path. DuckDB opens the selected database read-only with external access disabled.
Project configuration cannot use absolute paths or `..` traversal to read outside its directory.

## Safe publication checklist

1. Review column names for confidential business vocabulary.
2. Inspect the JSON before its first commit.
3. Keep source data, `.env` files, credentials, and generated database files out of Git.
4. Treat aggregate min/max/count statistics as potentially sensitive in very small populations.
5. Report bypasses privately through the repository security advisory flow.
