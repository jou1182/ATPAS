#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""BKL-016: Proposal Archive — searchable archive dialog.

ProposalArchiveDialog  — filterable, scrollable archive of all past builds
                          (up to 50 entries).  Replaces BuildHistoryDialog
                          as the primary history UI entry point.

Layout (RTL, navy/gold theme):
  ┌─ Header: title + entry count ───────────────────────────────────────────┐
  ├─ Filter bar: search QLineEdit | owner QComboBox | project QComboBox | مسح│
  ├─ Scrollable list of _ArchiveCard ────────────────────────────────────────┤
  ├─ Status bar: "عرض X من Y" ───────────────────────────────────────────────┤
  └─ Close button ───────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ui import theme
from ui.build_history import BuildHistoryManager, _OWNER_NAMES, _PROJECT_NAMES


# ─────────────────────────────────────────────────────────────────────────────
# Archive card widget
# ─────────────────────────────────────────────────────────────────────────────

class _ArchiveCard(QFrame):
    """A single archive entry card — larger and richer than _HistoryCard."""

    restore_requested = pyqtSignal(str, str, list)   # project_id, owner_id, codes

    def __init__(self, entry: dict[str, Any], idx: int, parent=None) -> None:
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 1px solid #DDD8CC;
                border-right: 4px solid {theme.ACCENT};
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
        output_file = entry.get("output_file", "")
        out_name    = Path(output_file).name if output_file else ""
        template_vars: dict | None = entry.get("template_vars")
        boq_count   = entry.get("boq_item_count", 0)

        proj_ar  = _PROJECT_NAMES.get(project_id, project_id)
        owner_ar = _OWNER_NAMES.get(owner_id, owner_id)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(5)

        # ── Row 1: counter · project/owner · timestamp ──────────────────
        row1 = QHBoxLayout()

        num_lbl = QLabel(f"#{idx + 1}")
        num_lbl.setFixedWidth(32)
        num_lbl.setAlignment(Qt.AlignCenter)
        num_lbl.setStyleSheet(
            "font-size: 10px; color: #8090A0; font-weight: bold; "
            "background: #F0EDE6; border-radius: 4px; padding: 2px; "
            "border: none;"
        )

        proj_lbl = QLabel(f"\U0001f3d7️  {proj_ar}  —  {owner_ar}")
        proj_lbl.setStyleSheet(
            f"font-size: 13px; font-weight: bold; color: {theme.HEADER};"
            " background: transparent; border: none;"
        )
        proj_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        ts_lbl = QLabel(ts)
        ts_lbl.setLayoutDirection(Qt.LeftToRight)
        ts_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        ts_lbl.setStyleSheet(
            "font-size: 10px; color: #8090A0; background: transparent; border: none;"
        )

        row1.addWidget(num_lbl)
        row1.addWidget(proj_lbl, 1)
        row1.addWidget(ts_lbl)
        layout.addLayout(row1)

        # ── Row 2: stats ────────────────────────────────────────────────
        stats_parts = [
            f"\U0001f4cb {code_count} كود",
            f"\U0001f4c4 {page_count} صفحة",
            f"⏱ {elapsed:.1f}ث",
        ]
        if boq_count:
            stats_parts.append(f"BOQ: {boq_count} بند")

        stats_lbl = QLabel("   |   ".join(stats_parts))
        stats_lbl.setStyleSheet(
            "font-size: 11px; color: #4A5A6A; background: transparent; border: none;"
        )
        stats_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(stats_lbl)

        # ── Row 3: template_vars summary (if present) ───────────────────
        if template_vars:
            proj_name   = template_vars.get("project_name", "")
            tender_num  = template_vars.get("tender_number", "")
            parts = []
            if proj_name:
                parts.append(f"مشروع: {proj_name}")
            if tender_num:
                parts.append(f"رقم المناقصة: {tender_num}")
            if parts:
                tv_lbl = QLabel("  •  ".join(parts))
                tv_lbl.setStyleSheet(
                    "font-size: 10px; color: #5A7A9A; background: #F0F4F8; "
                    "border-radius: 4px; padding: 2px 6px; border: none;"
                )
                tv_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                layout.addWidget(tv_lbl)

        # ── Row 4: output filename + action buttons ─────────────────────
        row4 = QHBoxLayout()
        row4.setSpacing(6)

        if out_name:
            file_lbl = QLabel(f"\U0001f4c2 {out_name}")
            file_lbl.setLayoutDirection(Qt.LeftToRight)
            file_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            file_lbl.setStyleSheet(
                "font-size: 10px; color: #9BA8B5; background: transparent; border: none;"
            )
            row4.addWidget(file_lbl, 1)
        else:
            row4.addStretch(1)

        # "فتح الملف" button — only active if file exists
        file_exists = bool(output_file) and Path(output_file).exists()
        open_btn = QPushButton("\U0001f4c2 فتح الملف")
        open_btn.setFixedWidth(100)
        open_btn.setEnabled(file_exists)
        open_btn.setCursor(Qt.PointingHandCursor if file_exists else Qt.ArrowCursor)
        open_btn.setToolTip(
            output_file if file_exists
            else "الملف غير موجود"
        )
        open_btn.setStyleSheet("""
            QPushButton {
                background: #EAF2FB; color: #1A5276;
                border: 1px solid #A9CCE3; border-radius: 5px;
                font-size: 10px; font-weight: 600;
                padding: 3px 8px;
            }
            QPushButton:hover:enabled  { background: #D6EAF8; }
            QPushButton:pressed:enabled{ background: #AED6F1; }
            QPushButton:disabled       { background: #F4F6F7; color: #AEB6BF; border-color: #D5D8DC; }
        """)
        _file = output_file  # capture for lambda
        open_btn.clicked.connect(lambda: self._open_file(_file))

        restore_btn = QPushButton("↩ إعادة التطبيق")
        restore_btn.setFixedWidth(120)
        restore_btn.setCursor(Qt.PointingHandCursor)
        restore_btn.setToolTip(
            f"إعادة تحديد نفس الأكواد — {proj_ar} / {owner_ar}"
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

        row4.addWidget(open_btn)
        row4.addWidget(restore_btn)
        layout.addLayout(row4)

    @staticmethod
    def _open_file(path: str) -> None:
        """Open a file with the OS default handler."""
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.run(["open", path], check=False)
            else:
                subprocess.run(["xdg-open", path], check=False)
        except Exception:  # noqa: BLE001
            pass


# ─────────────────────────────────────────────────────────────────────────────
# Archive dialog
# ─────────────────────────────────────────────────────────────────────────────

class ProposalArchiveDialog(QDialog):
    """Searchable, filterable archive dialog for all past builds.

    Emits restore_requested(project_id, owner_id, codes) when the user clicks
    "إعادة التطبيق" on any card.  The dialog auto-closes after emit.
    """

    restore_requested = pyqtSignal(str, str, list)   # project_id, owner_id, codes

    def __init__(self, manager: BuildHistoryManager, parent=None) -> None:
        super().__init__(parent)
        self._manager = manager
        self._all_entries: list[dict] = manager.load()

        self.setWindowTitle("أرشيف العروض")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumWidth(640)
        self.setMinimumHeight(560)
        self.setStyleSheet(f"background: {theme.SURFACE_ALT};")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 14)
        outer.setSpacing(10)

        # ── Header ──────────────────────────────────────────────────────
        header_row = QHBoxLayout()
        title_lbl = QLabel(
            "\U0001f5c2️  أرشيف العروض الفنية"
        )
        title_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        title_lbl.setStyleSheet(
            f"font-size: 16px; font-weight: 800; color: {theme.HEADER}; "
            f"padding-bottom: 4px; border-bottom: 2px solid {theme.ACCENT}; "
            "background: transparent;"
        )

        total = len(self._all_entries)
        count_lbl_text = f"{total} عرض" if total else "لا يوجد"
        self._count_badge = QLabel(count_lbl_text)
        self._count_badge.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._count_badge.setStyleSheet(
            "font-size: 11px; color: #8090A0; background: transparent; border: none;"
        )

        header_row.addWidget(title_lbl, 1)
        header_row.addWidget(self._count_badge)
        outer.addLayout(header_row)

        # ── Filter bar ──────────────────────────────────────────────────
        filter_frame = QFrame()
        filter_frame.setStyleSheet(
            "QFrame { background: white; border: 1px solid #DDD8CC; border-radius: 8px; }"
        )
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(10, 8, 10, 8)
        filter_layout.setSpacing(8)

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText(
            "\U0001f50d بحث..."
        )
        self._search_edit.setLayoutDirection(Qt.RightToLeft)
        self._search_edit.setMinimumWidth(180)
        self._search_edit.setStyleSheet(
            f"QLineEdit {{ border: 1px solid #CCC; border-radius: 5px; "
            f"padding: 4px 8px; font-size: 12px; background: #FAFAF8; }}"
            f"QLineEdit:focus {{ border-color: {theme.ACCENT}; }}"
        )

        self._owner_combo = QComboBox()
        self._owner_combo.setLayoutDirection(Qt.RightToLeft)
        self._owner_combo.setMinimumWidth(130)
        self._owner_combo.addItem(
            "كل الجهات", ""
        )
        for key, label in sorted(_OWNER_NAMES.items(), key=lambda x: x[1]):
            self._owner_combo.addItem(label, key)
        self._owner_combo.setStyleSheet(
            "QComboBox { border: 1px solid #CCC; border-radius: 5px; "
            "padding: 4px 8px; font-size: 12px; background: #FAFAF8; }"
        )

        self._project_combo = QComboBox()
        self._project_combo.setLayoutDirection(Qt.RightToLeft)
        self._project_combo.setMinimumWidth(130)
        self._project_combo.addItem(
            "كل المشاريع", ""
        )
        for key, label in sorted(_PROJECT_NAMES.items(), key=lambda x: x[1]):
            self._project_combo.addItem(label, key)
        self._project_combo.setStyleSheet(
            "QComboBox { border: 1px solid #CCC; border-radius: 5px; "
            "padding: 4px 8px; font-size: 12px; background: #FAFAF8; }"
        )

        clear_btn = QPushButton("مسح")
        clear_btn.setFixedWidth(60)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet(
            f"QPushButton {{ background: {theme.BG}; color: #4A5A6A; "
            f"border: none; border-radius: 5px; font-size: 12px; padding: 4px 8px; }}"
            f"QPushButton:hover {{ background: {theme.BORDER}; }}"
        )
        clear_btn.clicked.connect(self._clear_filters)

        filter_layout.addWidget(self._search_edit, 1)
        filter_layout.addWidget(self._owner_combo)
        filter_layout.addWidget(self._project_combo)
        filter_layout.addWidget(clear_btn)
        outer.addWidget(filter_frame)

        # ── Results area ─────────────────────────────────────────────────
        self._scroll_widget = QWidget()
        self._scroll_widget.setLayoutDirection(Qt.RightToLeft)
        self._scroll_layout = QVBoxLayout(self._scroll_widget)
        self._scroll_layout.setContentsMargins(4, 4, 4, 4)
        self._scroll_layout.setSpacing(6)
        self._scroll_layout.setAlignment(Qt.AlignTop)

        self._scroll = QScrollArea()
        self._scroll.setWidget(self._scroll_widget)
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setStyleSheet(f"background: {theme.SURFACE_ALT};")
        outer.addWidget(self._scroll, 1)

        # ── Status bar ───────────────────────────────────────────────────
        self._status_lbl = QLabel()
        self._status_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._status_lbl.setStyleSheet(
            "font-size: 11px; color: #8090A0; background: transparent; "
            "padding: 2px 4px;"
        )
        outer.addWidget(self._status_lbl)

        # ── Close button ─────────────────────────────────────────────────
        bottom_row = QHBoxLayout()
        bottom_row.addStretch()
        close_btn = QPushButton("إغلاق")
        close_btn.setFixedWidth(90)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(
            f"QPushButton {{ background: {theme.HEADER}; color: {theme.ACCENT}; "
            f"border: none; border-radius: 6px; font-size: 12px; font-weight: 700; "
            f"padding: 6px 16px; }}"
            f"QPushButton:hover {{ background: {theme.NAVY_MID}; }}"
        )
        close_btn.clicked.connect(self.accept)
        bottom_row.addWidget(close_btn)
        outer.addLayout(bottom_row)

        # ── Wire filters ─────────────────────────────────────────────────
        self._search_edit.textChanged.connect(self._refresh)
        self._owner_combo.currentIndexChanged.connect(self._refresh)
        self._project_combo.currentIndexChanged.connect(self._refresh)

        # Initial render
        self._refresh()

    # ------------------------------------------------------------------
    # Filter helpers
    # ------------------------------------------------------------------

    def _clear_filters(self) -> None:
        """Reset all filter controls to their defaults."""
        self._search_edit.blockSignals(True)
        self._owner_combo.blockSignals(True)
        self._project_combo.blockSignals(True)

        self._search_edit.clear()
        self._owner_combo.setCurrentIndex(0)
        self._project_combo.setCurrentIndex(0)

        self._search_edit.blockSignals(False)
        self._owner_combo.blockSignals(False)
        self._project_combo.blockSignals(False)

        self._refresh()

    def _refresh(self) -> None:
        """Re-query and re-render cards according to current filter state."""
        query      = self._search_edit.text().strip()
        owner_id   = self._owner_combo.currentData() or ""
        project_id = self._project_combo.currentData() or ""

        results = self._manager.search(
            query=query,
            owner_id=owner_id,
            project_id=project_id,
        )

        # Clear current cards
        while self._scroll_layout.count():
            item = self._scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not results:
            empty_lbl = QLabel(
                "لا توجد نتائج تطابق معايير البحث"
            )
            empty_lbl.setAlignment(Qt.AlignCenter)
            empty_lbl.setStyleSheet(
                "color: #8090A0; font-size: 13px; padding: 40px; background: transparent;"
            )
            self._scroll_layout.addWidget(empty_lbl)
        else:
            for i, entry in enumerate(results):
                card = _ArchiveCard(entry, i, parent=self._scroll_widget)
                card.restore_requested.connect(self._on_restore)
                self._scroll_layout.addWidget(card)

        # Update status
        total = len(self._all_entries)
        shown = len(results)
        self._status_lbl.setText(
            f"عرض {shown} من {total}"
        )

    def _on_restore(self, project_id: str, owner_id: str, codes: list) -> None:
        self.restore_requested.emit(project_id, owner_id, codes)
        self.accept()
