#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.json_manager import save_json


_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_LOGS_DIR = _PROJECT_ROOT / "output" / "logs"
_AUDIT_DIR = _PROJECT_ROOT / "output" / "audit_trail"

_configured = False


def setup_logging(logs_dir: str | Path = _LOGS_DIR, level: int = logging.DEBUG) -> None:
    """Configure root logger with rotating file + console handlers."""
    global _configured
    if _configured:
        return
    logs_path = Path(logs_dir)
    logs_path.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level)

    # Rotating file handler — 5 MB × 3 backups
    file_handler = logging.handlers.RotatingFileHandler(
        logs_path / "atpas.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s — %(message)s")
    )
    root.addHandler(file_handler)

    # Console handler (INFO and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    root.addHandler(console_handler)

    _configured = True


def generate_audit_trail(build_context: Dict[str, Any], audit_dir: str | Path = _AUDIT_DIR) -> Path:
    """
    Write an audit trail JSON file for a completed build.

    Expected build_context keys:
        selected_codes, project_id, owner_id, output_path,
        status ("success" | "failure"), error (optional),
        processing_time_seconds (optional), file_size_bytes (optional)

    Returns the path of the written audit file.
    """
    audit_path = Path(audit_dir)
    audit_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"audit_{timestamp}.json"

    record: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "project_id": build_context.get("project_id", "unknown"),
        "owner_id": build_context.get("owner_id", "unknown"),
        "selected_codes": build_context.get("selected_codes", []),
        "codes_count": len(build_context.get("selected_codes", [])),
        "output_path": str(build_context.get("output_path", "")),
        "status": build_context.get("status", "unknown"),
        "processing_time_seconds": build_context.get("processing_time_seconds"),
        "file_size_bytes": build_context.get("file_size_bytes"),
        "error": build_context.get("error"),
    }

    file_path = audit_path / filename
    save_json(record, file_path)

    logging.getLogger(__name__).info("Audit trail written: %s", file_path)
    return file_path


def get_audit_history(
    audit_dir: str | Path = _AUDIT_DIR,
    limit: int = 500,
) -> List[Dict[str, Any]]:
    """Return audit records sorted by timestamp descending.

    Args:
        audit_dir: Directory containing audit_*.json files.
        limit:     Maximum number of records to return (newest first).
                   Older files remain on disk as the permanent archive —
                   they are never deleted by this function.
                   Default: 500 (prevents UI slowdown on large installations).
    """
    audit_path = Path(audit_dir)
    if not audit_path.exists():
        return []
    files = sorted(audit_path.glob("audit_*.json"), reverse=True)[:limit]
    records = []
    for f in files:
        try:
            with open(f, encoding="utf-8") as fp:
                records.append(json.load(fp))
        except (json.JSONDecodeError, OSError):
            pass
    return records
