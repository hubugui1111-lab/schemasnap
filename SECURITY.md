# Security policy

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x | Yes |
| < 0.1 | No |

## Reporting a vulnerability

Use **Security → Report a vulnerability** in this GitHub repository to open a private advisory. Include
the affected version, platform, proof of concept using synthetic data, impact, and suggested mitigation.
Do not attach real datasets, credentials, SQL, or personal information.

You should receive an acknowledgement within seven days. Validation, remediation, credit, and public
disclosure will be coordinated through the private advisory.

## Security boundary

SchemaSnap reads local files selected by the caller. It never sends them over a network. DuckDB opens
in read-only mode with external access disabled and a conservative query allowlist. Output redaction is
structural, but aggregate statistics and column names can still be sensitive in some domains. Review
[docs/privacy.md](docs/privacy.md) before committing a snapshot.
