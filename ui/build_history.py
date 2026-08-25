#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""BKL-011: Build History — persistence manager.

BuildHistoryManager — reads/writes build_history.json (last MAX_HISTORY entries).

(The former BuildHistoryDialog UI was superseded by
 ui.proposal_archive_dialog.ProposalArchiveDialog and has been removed.)

Each history entry:
    timestamp_display, project_id, owner_id, codes[],
    output_file, elapsed_seconds, code_count, page_count
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

_HISTORY_FILE = Path("build_history.json")
_MAX_HISTORY  = 50

_PROJECT_NAMES: dict[str, str] = {
    "wastewater":          "صرف صحي",
    "water_supply":        "مياه شرب",
    "asphalt":             "أسفلت",
    "road_maintenance":    "صيانة طرق",
    "general_construction":"إنشاءات عامة",
    "water_transmission":  "ناقل مياه",
}
_OWNER_NAMES: dict[str, str] = {
    "nwc":           "NWC",
    "makkah":        "أمانة مكة",
    "moh":           "وزارة الصحة",
    "mot":           "وزارة النقل",
    "nhi":           "NHI",
    "amana_riyadh":  "أمانة الرياض",
    "amana_qassim":  "أمانة القصيم",
    "swa":           "SWA",
    "ksia":          "KSIA",
}


# ─────────────────────────────────────────────────────────────────────────────
# Manager
# ─────────────────────────────────────────────────────────────────────────────

class BuildHistoryManager:
    """Reader/writer for build_history.json.

    Call save_entry() right after a successful build.
    Call load() to get the sorted list (newest first).
    Errors are silently swallowed — history is non-critical.

    Args:
        history_path: Override the default file path. Useful in tests so
                      each test can use an isolated tmp_path location.
    """

    def __init__(self, history_path: str | Path | None = None) -> None:
        self._history_file = Path(history_path) if history_path else _HISTORY_FILE

    def save_entry(
        self,
        project_id: str,
        owner_id: str,
        codes: list[str],
        output_file: str,
        elapsed_seconds: float,
        page_count: int,
        template_vars: dict | None = None,
        boq_item_count: int = 0,
    ) -> None:
        """Prepend new entry and prune to MAX_HISTORY."""
        history = self._load_raw()
        now = datetime.now()
        entry: dict[str, Any] = {
            "timestamp":         now.isoformat(),
            "timestamp_display": now.strftime("%Y-%m-%d  %H:%M"),
            "project_id":        project_id,
            "owner_id":          owner_id,
            "codes":             codes,
            "output_file":       output_file,
            "elapsed_seconds":   round(elapsed_seconds, 1),
            "code_count":        len(codes),
            "page_count":        page_count,
            "template_vars":     template_vars,
            "boq_item_count":    boq_item_count,
        }
        history.insert(0, entry)
        history = history[:_MAX_HISTORY]
        try:
            with open(self._history_file, "w", encoding="utf-8") as f:
                json.dump({"history": history}, f, ensure_ascii=False, indent=2)
        except OSError:
            pass   # non-fatal

    def search(
        self,
        query: str = "",
        owner_id: str = "",
        project_id: str = "",
    ) -> list[dict]:
        """Filter history and return matching entries (newest first).

        Args:
            query:      Case-insensitive substring matched against project_id,
                        owner_id, and output_file.
            owner_id:   Exact match on owner_id (empty = all).
            project_id: Exact match on project_id (empty = all).

        Returns:
            Filtered list of entry dicts, newest first.
        """
        history = self._load_raw()
        q = query.lower()
        results = []
        for entry in history:
            # Exact filters
            if owner_id and entry.get("owner_id", "") != owner_id:
                continue
            if project_id and entry.get("project_id", "") != project_id:
                continue
            # Substring query
            if q:
                haystack = " ".join([
                    entry.get("project_id", ""),
                    entry.get("owner_id", ""),
                    entry.get("output_file", ""),
                ]).lower()
                if q not in haystack:
                    continue
            results.append(entry)
        return results

    def load(self) -> list[dict]:
        """Return history list (newest first); empty on any error."""
        return self._load_raw()

    def _load_raw(self) -> list[dict]:
        try:
            with open(self._history_file, encoding="utf-8") as f:
                data = json.load(f)
            return data.get("history", [])
        except (OSError, json.JSONDecodeError):
            return []


# ─────────────────────────────────────────────────────────────────────────────
# History card widget
# ─────────────────────────────────────────────────────────────────────────────

class _HistoryCard(QFrame):
    """Single history-entry card with a Re-apply button."""

    restore_requested = pyqtSignal(str, str, list)   # project_id, owner_id, codes

    def __init__(self, entry: dict[str, Any], idx: int, parent=None) -> None:
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 1px solid #DDD8CC;
                border-left: 4px solid {theme.ACCENT};
                border-radius: 8px;
            }}
        """)

        project_id  = entry.get("project_id", "")
        owner_id    = entry.get("owner_id", "")
        codes: list = entry.get("codes", [])
        ts          = entry.get("timestamp_display", entry.get("timestamp", "")[:16])
        code_count  = entry.get("code_count", len(codes))
        page_count  = entry.get("page_count", 0)
        elapsed     = entry.get("elapsed_seconds", 0.0)
        out_file    = Path(entry.get("output_file", "")).name

        proj_ar  = _PROJECT_NAMES.get(project_id, project_id)
        owner_ar = _OWNER_NAMES.get(owner_id, owner_id)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        # ── Row 1: counter · project/owner · timestamp ──────────────────
        row1 = QHBoxLayout()

        num_lbl = QLabel(f"#{idx + 1}")
        num_lbl.setFixedWidth(28)
        num_lbl.setAlignment(Qt.AlignCenter)
        num_lbl.setStyleSheet(
            "font-size: 10px; color: #8090A0; font-weight: bold; "
            "background: #F0EDE6; border-radius: 4px; padding: 2px;"
        )

        proj_lbl = QLabel(f"\U0001f3d7\ufe0f  {proj_ar}  \u2014  {owner_ar}")
        proj_lbl.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {theme.HEADER};"
                               " background: transparent; border: none;")
        proj_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        ts_lbl = QLabel(ts)
        ts_lbl.setLayoutDirection(Qt.LeftToRight)
        ts_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        ts_lbl.setStyleSheet("font-size: 10px; color: #8090A0;"
                             " background: transparent; border: none;")

        row1.addWidget(num_lbl)
        row1.addWidget(proj_lbl, 1)
        row1.addWidget(ts_lbl)
        layout.addLayout(row1)

        # ── Row 2: stats · re-apply button ─────────────────────────────
        row2 = QHBoxLayout()

        stats_lbl = QLabel(
            f"\U0001f4cb {code_count} \u0643\u0648\u062f"
            f"   |   \U0001f4c4 {page_count} \u0635\u0641\u062d\u0629"
            f"   |   \u23f1 {elapsed:.1f}\u062b"
        )
        stats_lbl.setStyleSheet("font-size: 11px; color: #4A5A6A;"
                                " background: transparent; border: none;")
        stats_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        restore_btn = QPushButton("\u21a9 \u0625\u0639\u0627\u062f\u0629 \u0627\u0644\u062a\u0637\u0628\u064a\u0642")
        restore_btn.setFixedWidth(120)
        restore_btn.setCursor(Qt.PointingHandCursor)
        restore_btn.setToolTip(
            f"\u0625\u0639\u0627\u062f\u0629 \u062a\u062d\u062f\u064a\u062f \u0646\u0641\u0633 \u0627\u0644\u0623\u0643\u0648\u0627\u062f \u2014 {proj_ar} / {owner_ar}"
        )
        restore_btn.setStyleSheet(f"""
            QPushButton {{
                background: {theme.HEADER}; color: {theme.ACCENT};
                border: none; border-radius: 5px;
                font-size: 11px; font-weight: 700;
                padding: 4px 10px;
            }}
            QPushButton:hover  {{ background: {theme.NAVY_MID}; }}
            QPushButton:pressed{{ background: {theme.HEADER2}; }}
        """)
        restore_btn.clicked.connect(
            lambda: self.restore_requested.emit(project_id, owner_id, list(codes))
        )

        row2.addWidget(stats_lbl, 1)
        row2.addWidget(restore_btn)
        layout.addLayout(row2)

        # ── Row 3: output filename (small, LTR) ─────────────────────────
        if out_file:
            file_lbl = QLabel(f"\U0001f4c2 {out_file}")
            file_lbl.setLayoutDirection(Qt.LeftToRight)
            file_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            file_lbl.setStyleSheet("font-size: 10px; color: #9BA8B5;"
                                   " background: transparent; border: none;")
            layout.addWidget(file_lbl)


# ─────────────────────────────────────────────────────────────────────────────
