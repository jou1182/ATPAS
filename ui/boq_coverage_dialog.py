#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BOQ Coverage Report dialog — shows post-build coverage analysis.

BOQCoverageDialog displays three sections:
  1. Summary bar with coverage percentage and colored progress bar.
  2. Uncovered BOQ items (in BOQ but not selected) — shown in red.
  3. Extra selected codes (selected but not in BOQ) — shown in blue.

RTL layout throughout, consistent with existing ATPAS dark-navy style.
"""

from __future__ import annotations

import logging

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from utils.boq_coverage import CoverageResult

logger = logging.getLogger(__name__)

# ── Colour palette (matches existing ATPAS style) ─────────────────────────────
_NAVY   = "#152433"
_GOLD   = "#C9921B"
_GREEN  = "#1B5E20"
_ORANGE = "#E65100"
_RED    = "#B71C1C"
_BLUE   = "#0D47A1"

_HEADER_STYLE = (
    f"background: {_NAVY}; color: #FFFFFF;"
    "font-size: 15px; font-weight: bold; padding: 10px 14px;"
    "border-radius: 6px 6px 0 0;"
)

_SECTION_LABEL_STYLE = (
    "font-size: 12px; font-weight: bold; padding: 4px 2px;"
)

_CLOSE_BTN_STYLE = (
    f"QPushButton {{"
    f"  background: {_NAVY}; color: {_GOLD};"
    f"  border: none; border-radius: 6px;"
    f"  padding: 7px 22px; font-size: 13px; font-weight: 700;"
    f"}}"
    f"QPushButton:hover {{ background: #1C3045; }}"
    f"QPushButton:pressed {{ background: #0D1C2B; }}"
)


def _code_display_name(code_id: str, codes: dict) -> str:
    """Return 'CODE-ID — Arabic name' or just the code_id if not in registry."""
    entry = codes.get(code_id, {})
    name_ar = entry.get("name_ar") or entry.get("name", "")
    if name_ar:
        return f"{code_id}  —  {name_ar}"
    return code_id


class BOQCoverageDialog(QDialog):
    """RTL dialog showing BOQ coverage analysis after a successful build."""

    def __init__(
        self,
        coverage: CoverageResult,
        codes: dict,          # full codes registry dict
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._coverage = coverage
        self._codes = codes

        self.setWindowTitle("تقرير تغطية BOQ")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumSize(580, 480)
        self.setModal(True)

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 12)
        layout.setSpacing(0)

        # ── Dark navy header ───────────────────────────────────────────
        header = QLabel("تقرير تغطية BOQ")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(_HEADER_STYLE)
        layout.addWidget(header)

        # Inner content area with margins
        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(12, 10, 12, 4)
        inner_layout.setSpacing(10)
        layout.addWidget(inner, stretch=1)

        # ── Summary bar ────────────────────────────────────────────────
        summary_text = (
            f"تغطية:  {len(self._coverage.covered)} من "
            f"{self._coverage.total_boq} بند  "
            f"({self._coverage.coverage_pct}%)"
        )
        summary_label = QLabel(summary_text)
        summary_label.setAlignment(Qt.AlignCenter)
        summary_label.setStyleSheet(
            "font-size: 13px; font-weight: bold; padding: 4px;"
        )
        inner_layout.addWidget(summary_label)

        pct_bar = QProgressBar()
        pct_bar.setRange(0, 100)
        pct_bar.setValue(int(self._coverage.coverage_pct))
        pct_bar.setTextVisible(False)
        pct_bar.setFixedHeight(16)
        bar_color = self._bar_color(self._coverage.coverage_pct)
        pct_bar.setStyleSheet(
            f"QProgressBar {{ border-radius: 7px; background: #E0E0E0; }}"
            f"QProgressBar::chunk {{ background: {bar_color}; border-radius: 7px; }}"
        )
        inner_layout.addWidget(pct_bar)

        # ── Uncovered items section ────────────────────────────────────
        uncovered_label = QLabel(
            f"بنود BOQ غير مغطاة  ({len(self._coverage.uncovered)})"
        )
        uncovered_label.setStyleSheet(_SECTION_LABEL_STYLE + f"color: {_RED};")
        inner_layout.addWidget(uncovered_label)

        uncovered_list = QListWidget()
        uncovered_list.setLayoutDirection(Qt.RightToLeft)
        uncovered_list.setAlternatingRowColors(True)
        if not self._coverage.uncovered:
            item = QListWidgetItem("✓ جميع بنود BOQ مغطاة")
            item.setForeground(QColor(_GREEN))
            uncovered_list.addItem(item)
        else:
            for code_id in self._coverage.uncovered:
                display = _code_display_name(code_id, self._codes)
                item = QListWidgetItem(display)
                item.setForeground(QColor(_RED))
                uncovered_list.addItem(item)
        inner_layout.addWidget(uncovered_list, stretch=2)

        # ── Extra codes section ────────────────────────────────────────
        extra_label = QLabel(
            f"أكواد إضافية خارج BOQ  ({len(self._coverage.extra)})"
        )
        extra_label.setStyleSheet(_SECTION_LABEL_STYLE + f"color: {_BLUE};")
        inner_layout.addWidget(extra_label)

        extra_list = QListWidget()
        extra_list.setLayoutDirection(Qt.RightToLeft)
        extra_list.setAlternatingRowColors(True)
        if not self._coverage.extra:
            item = QListWidgetItem("— لا توجد أكواد إضافية خارج BOQ —")
            item.setForeground(QColor("#757575"))
            extra_list.addItem(item)
        else:
            for code_id in self._coverage.extra:
                display = _code_display_name(code_id, self._codes)
                item = QListWidgetItem(display)
                item.setForeground(QColor(_BLUE))
                extra_list.addItem(item)
        inner_layout.addWidget(extra_list, stretch=1)

        # ── Close button ───────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("إغلاق")
        close_btn.setStyleSheet(_CLOSE_BTN_STYLE)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        inner_layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _bar_color(pct: float) -> str:
        """Return green/orange/red hex based on coverage percentage."""
        if pct >= 80:
            return "#388E3C"    # green
        if pct >= 50:
            return "#F57C00"    # orange
        return "#C62828"        # red
