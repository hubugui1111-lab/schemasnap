# Contributing

Thanks for helping make data-contract reviews safer and clearer.

1. Open an issue before a large behavior or wire-format change.
2. Fork the repository and create a focused branch.
3. Add a failing regression test before changing behavior.
4. Run the complete local gate below.
5. Update the relevant privacy/rule/format documentation.
6. Submit a pull request describing behavior, risk, and test evidence.

```bash
uv sync --locked
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest --cov=schemasnap --cov-branch
uv run pip-audit --skip-editable
uv build
```

New profile fields require explicit review for privacy leakage and deterministic serialization. Never
add raw row samples, category labels, SQL text, absolute paths, or fixture credentials. Use synthetic
data in tests and examples.

By participating, you agree to follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Security reports belong
in a private advisory, not a public issue.
