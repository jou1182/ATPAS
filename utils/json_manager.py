#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def load_json(file_path: str | Path, default: Optional[Dict] = None) -> Dict:
    """Load JSON file with UTF-8 encoding. Returns default on missing file."""
    path = Path(file_path)
    if not path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(f"JSON file not found: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}") from e
    except OSError as e:
        raise OSError(f"Cannot read {path}: {e}") from e


def save_json(data: Any, file_path: str | Path, indent: int = 2) -> None:
    """Save data to JSON file with UTF-8 encoding, creating parent dirs if needed."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
    except OSError as e:
        raise OSError(f"Cannot write {path}: {e}") from e


def merge_json(base: Dict, override: Dict) -> Dict:
    """Deep merge override into base, returning new dict."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_json(result[key], value)
        else:
            result[key] = value
    return result
