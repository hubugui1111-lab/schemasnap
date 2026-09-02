"""Atomic snapshot persistence."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from schemasnap.models import Snapshot


def read_snapshot(path: Path) -> Snapshot:
    return Snapshot.model_validate_json(path.read_text(encoding="utf-8"))


def write_text_atomic(path: Path, content: str, *, overwrite: bool = False) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_name = temporary.name
        if overwrite:
            os.replace(temporary_name, path)
        else:
            try:
                os.link(temporary_name, path)
            except FileExistsError as error:
                raise FileExistsError(f"already exists: {path}") from error
    finally:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)


def write_snapshot(path: Path, snapshot: Snapshot, *, overwrite: bool = False) -> None:
    write_text_atomic(path, snapshot.to_json(), overwrite=overwrite)
