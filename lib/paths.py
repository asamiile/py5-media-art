from __future__ import annotations

from pathlib import Path


def project_root(file: str) -> Path:
    """Return the repository root for a sketch file."""
    return Path(file).resolve().parents[2]


def sketch_dir(file: str) -> Path:
    """Return the directory containing a sketch file."""
    return Path(file).resolve().parent
