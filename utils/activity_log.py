#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tiny append-only activity log for visible operational milestones."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from utils.json_manager import load_json, save_json


_DEFAULT_LOG_PATH = Path("output/reports/activity_log.json")
_MAX_ENTRIES = 200


class ActivityLog:
    """Record recent user-visible actions without making them mission-critical."""

    def __init__(self, path: str | Path = _DEFAULT_LOG_PATH) -> None:
        self._path = Path(path)

    def append(self, action_ar: str, details: dict[str, Any] | None = None) -> None:
        """Append one activity entry; failures are intentionally swallowed."""
        try:
            data = load_json(self._path, default={"activities": []})
            entries = data.get("activities", [])
            if not isinstance(entries, list):
                entries = []
            entries.insert(0, {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "timestamp_display": datetime.now().strftime("%Y-%m-%d  %H:%M"),
                "action_ar": action_ar,
                "details": details or {},
            })
            save_json({"activities": entries[:_MAX_ENTRIES]}, self._path)
        except Exception:
            return

    def latest(self, limit: int = 20) -> list[dict[str, Any]]:
        data = load_json(self._path, default={"activities": []})
        entries = data.get("activities", [])
        return entries[:limit] if isinstance(entries, list) else []
