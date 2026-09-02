"""Render a verified plain-text CLI transcript as a lightweight SVG."""

from __future__ import annotations

import html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRANSCRIPT = ROOT / "assets" / "demo-transcript.txt"
OUTPUT = ROOT / "assets" / "demo.svg"


def render() -> None:
    lines = TRANSCRIPT.read_text(encoding="utf-8").splitlines()
    line_height = 23
    width = 1120
    height = 86 + line_height * len(lines)
    spans = "\n".join(
        f'<text x="28" y="{72 + index * line_height}" class="line">{html.escape(line)}</text>'
        for index, line in enumerate(lines)
    )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
  viewBox="0 0 {width} {height}">
  <rect width="{width}" height="{height}" rx="16" fill="#0b1220"/>
  <rect width="{width}" height="44" rx="16" fill="#172033"/>
  <rect y="28" width="{width}" height="16" fill="#172033"/>
  <circle cx="24" cy="22" r="6" fill="#ff5f57"/>
  <circle cx="44" cy="22" r="6" fill="#febc2e"/>
  <circle cx="64" cy="22" r="6" fill="#28c840"/>
  <text x="{width // 2}" y="27" text-anchor="middle" fill="#94a3b8"
    font-family="Segoe UI, sans-serif" font-size="14">SchemaSnap · verified demo</text>
  <style>
    .line {{ fill: #dbeafe; font-family: Consolas, Menlo, monospace;
      font-size: 14px; white-space: pre; }}
  </style>
  {spans}
</svg>
"""
    OUTPUT.write_text(svg, encoding="utf-8", newline="\n")
    print(f"Rendered {OUTPUT.relative_to(ROOT)} from {TRANSCRIPT.relative_to(ROOT)}")


if __name__ == "__main__":
    render()
