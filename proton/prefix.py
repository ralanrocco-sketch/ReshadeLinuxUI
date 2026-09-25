"""Locate and describe a Steam game's Proton prefix."""

from pathlib import Path


def is_valid_prefix(path: Path | None) -> bool:
    return bool(path and path.is_dir() and (path / "drive_c").is_dir())
