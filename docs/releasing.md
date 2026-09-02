# v0.1.0 release checklist

- [ ] `uv lock --check`
- [ ] Ruff format and lint are clean
- [ ] strict mypy passes
- [ ] unit and integration suites pass on Python 3.12 and 3.13
- [ ] branch coverage remains at least 80%
- [ ] `uv run pip-audit --skip-editable` reports no known dependency vulnerabilities
- [ ] `actionlint` and Gitleaks report no findings
- [ ] `scripts/demo.ps1` and `scripts/demo.sh` produce the documented seven-change output
- [ ] `uv build` creates sdist and wheel
- [ ] the wheel installs in a clean environment and `schemasnap --version` prints `0.1.0`
- [ ] README installation-name warning still distinguishes `schemasnap-data` from unrelated PyPI
- [ ] CI, CodeQL, and Security workflows are green on the release commit
- [ ] tag `v0.1.0` points to that exact commit
- [ ] GitHub Release contains both distributions and generated notes

PyPI publication is deliberately separate. Do not publish under the occupied `schemasnap` name; the
only intended distribution name is `schemasnap-data`.
