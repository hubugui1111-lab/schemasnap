"""Human and machine-readable diff renderers."""

from __future__ import annotations

from schemasnap.models import DiffReport


def _display(value: object) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def _escape_markdown(value: object) -> str:
    return _display(value).replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def render_markdown(report: DiffReport) -> str:
    counts = report.counts
    lines = [
        "## SchemaSnap diff",
        "",
        f"`{_escape_markdown(report.baseline_label)}` → `{_escape_markdown(report.current_label)}`",
        "",
        (
            f"**{counts['BREAKING']} breaking · {counts['WARNING']} warning · "
            f"{counts['INFO']} info**"
        ),
        "",
    ]
    if not report.changes:
        lines.extend(["No contract changes detected.", ""])
        return "\n".join(lines)
    lines.extend(
        [
            "| Severity | Code | Column | Before | After | Detail |",
            "|---|---|---|---|---|---|",
        ]
    )
    for change in report.changes:
        lines.append(
            "| "
            + " | ".join(
                _escape_markdown(value)
                for value in (
                    change.severity.value,
                    change.code,
                    change.column,
                    change.before,
                    change.after,
                    change.message,
                )
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def render_terminal(report: DiffReport, *, color: bool = True) -> str:
    del color  # Reserved for a future ANSI renderer; plain output is deterministic everywhere.
    counts = report.counts
    lines = [
        f"SchemaSnap diff: {report.baseline_label} -> {report.current_label}",
        f"BREAKING {counts['BREAKING']}  WARNING {counts['WARNING']}  INFO {counts['INFO']}",
    ]
    for change in report.changes:
        column = f" [{change.column}]" if change.column is not None else ""
        lines.append(
            f"{change.severity.value:<8} {change.code}{column}: {change.message} "
            f"({_display(change.before)} -> {_display(change.after)})"
        )
    if not report.changes:
        lines.append("No contract changes detected.")
    return "\n".join(lines) + "\n"


def render_json(report: DiffReport) -> str:
    return report.to_json()
