#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Atomic JSON I/O with deep-merge utility.

Design guarantees
─────────────────
• save_json writes atomically (temp-file → os.replace) so a crash or power
  loss between bytes can never produce a half-written file.
• load_json always validates UTF-8 and JSON structure before returning.
• merge_json is non-mutating and handles arbitrary nesting depth.
• All public functions accept str | Path for file_path convenience.
"""

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def load_json(file_path: str | Path, default: Optional[Dict] = None) -> Dict:
    """Load and parse a UTF-8 JSON file.

    Args:
        file_path: Path to the JSON file (str or Path).
        default:   Value returned when the file does not exist.
                   Pass ``None`` (the default) to raise on missing file.

    Returns:
        Parsed dict.

    Raises:
        FileNotFoundError: File missing and no default provided.
        ValueError:        File contains invalid JSON.
        OSError:           File cannot be opened (permissions, etc.).
    """
    path = Path(file_path)
    if not path.exists():
        if default is not None:
            logger.debug("JSON file not found, returning default: %s", path)
            return default
        raise FileNotFoundError(f"JSON file not found: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.debug("Loaded JSON (%d keys): %s", len(data) if isinstance(data, dict) else -1, path)
        return data
    except json.JSONDecodeError as exc:
        logger.error("Invalid JSON in %s: %s", path, exc)
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    except OSError as exc:
        logger.error("Cannot read %s: %s", path, exc)
        raise OSError(f"Cannot read {path}: {exc}") from exc


def save_json(data: Any, file_path: str | Path, indent: int = 2) -> None:
    """Atomically write *data* to *file_path* as pretty-printed UTF-8 JSON.

    The write is performed via a sibling temporary file that is renamed into
    place only after the flush+sync sequence succeeds.  This ensures the target
    file is never left in a partial state even if the process is killed or the
    power fails mid-write.

    Args:
        data:      JSON-serialisable object.
        file_path: Destination path (str or Path).  Parent directories are
                   created automatically.
        indent:    JSON indentation width (default 2).

    Raises:
        OSError: Directory cannot be created or file cannot be written.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write to a temp file in the same directory so the rename is always
    # on the same filesystem (avoids EXDEV on cross-device rename).
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
            f.flush()
            os.fsync(f.fileno())
        # Atomic replacement — POSIX rename(2) / Windows MoveFileEx
        os.replace(tmp_name, path)
        logger.debug("Saved JSON atomically: %s", path)
    except Exception:
        # Best-effort cleanup of the temp file on any failure
        logger.exception("Failed to save JSON to %s — temp file cleaned up", path)
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def merge_json(base: Dict, override: Dict) -> Dict:
    """Deep-merge *override* into *base*, returning a new dict.

    Rules:
    • Both *base* and *override* are left untouched.
    • If the same key exists in both and both values are dicts, they are
      merged recursively.
    • For any other type mismatch (list, str, int, …) the override value wins.

    Args:
        base:     The starting dict.
        override: Values to layer on top.

    Returns:
        New merged dict.
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_json(result[key], value)
        else:
            result[key] = value
    return result
