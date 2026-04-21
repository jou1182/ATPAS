#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""BKL-004: Preview panel with dependency warnings and build controls.

- Receives (selected_codes, errors, warnings) from MainWindow.
- Shows selected codes sorted by sequence_order with Arabic names.
- Shows total pages estimate.
- Displays blocking errors (red) and non-blocking warnings (orange).
- "إصلاح تلقائي" button: emits auto_fix_requested when dependencies are missing.
- "بناء العرض" button: enabled only when errors list is empty.
"""

from __future__ import annotations

from typing import Any

from PyQt5.QtCore import QEasingCurve, QPropertyAnimation, Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QGraphicsOpacityEffect,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from utils.content_library import ContentLibrary
from ui.motion import motion_ms, prefers_reduced_motion

_CONTENT_LIB = ContentLibrary()   # shared singleton — reads templates/source_documents/

_COLOR_ERROR = "#C62828"
_COLOR_WARNING = "#E65100"
_COLOR_OK = "#1B5E20"
_COLOR_INFO = "#1E4F86"

_BG_CONTENT_REAL = "#ECF6EF"
_BG_CONTENT_PLACEHOLDER = "#F5F1E8"
_BG_ERROR = "#FDEEEE"
_BG_WARNING = "#FFF4E7"
_BG_OK = "#EAF5EF"
_BG_INFO = "#EEF3FA"


def _safe_int(value: Any, default: int = 0) -> int:
    """Parse int safely; fallback to default on malformed values."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class PreviewPanelWidget(QWidget):
    """Right-side panel: summary, code list, validation messages, build button."""

    auto_fix_requested = pyqtSignal()
    build_requested = pyqtSignal()

    def __init__(self, registry_data: dict[str, Any], parent=None) -> None:
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)

        self._codes: dict[str, dict] = registry_data.get("codes", {})

        self._summary_label = QLabel("لم يتم اختيار أكواد بعد")
        self._summary_label.setAlignment(Qt.AlignCenter)
        self._summary_label.setStyleSheet("font-weight: bold; padding: 4px;")

        # Code list
        codes_box = QGroupBox("الأكواد المختارة (مرتبة حسب التسلسل)")
        codes_box.setLayoutDirection(Qt.RightToLeft)
        codes_layout = QVBoxLayout(codes_box)
        self._codes_list = QListWidget()
        self._codes_list.setLayoutDirection(Qt.RightToLeft)
        self._codes_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        codes_layout.addWidget(self._codes_list)

        # Validation messages
        val_box = QGroupBox("التحقق والتحذيرات")
        val_box.setLayoutDirection(Qt.RightToLeft)
        val_layout = QVBoxLayout(val_box)
        self._validation_list = QListWidget()
        self._validation_list.setLayoutDirection(Qt.RightToLeft)
        self._validation_list.setMaximumHeight(140)
        val_layout.addWidget(self._validation_list)

        # Buttons
        btn_layout = QHBoxLayout()
        self._autofix_btn = QPushButton("إصلاح تلقائي")
        self._autofix_btn.setEnabled(False)
        self._autofix_btn.setToolTip("إضافة الأكواد الناقصة تلقائياً")
        self._autofix_btn.clicked.connect(self.auto_fix_requested.emit)
        self._autofix_btn.pressed.connect(
            lambda: self._press_feedback(self._autofix_btn)
        )

        self._build_btn = QPushButton("⚡  بناء العرض الفني")
        self._build_btn.setObjectName("buildBtn")
        self._build_btn.setEnabled(False)
        self._build_btn.setToolTip("بناء ملف Word للعرض الفني")
        self._build_btn.clicked.connect(self.build_requested.emit)
        self._build_btn.pressed.connect(lambda: self._press_feedback(self._build_btn))
        self._build_btn_was_enabled: bool = False   # track previous enabled state
        self._autofix_btn_was_enabled: bool = False

        btn_layout.addWidget(self._autofix_btn)
        btn_layout.addWidget(self._build_btn)

        root = QVBoxLayout(self)
        root.addWidget(self._summary_label)
        root.addWidget(codes_box, stretch=3)
        root.addWidget(val_box, stretch=2)
        root.addLayout(btn_layout)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_preview(
        self,
        selected_codes: list[str],
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Refresh all sections from current selection + validation results."""
        self._refresh_codes_list(selected_codes)
        self._refresh_validation(errors, warnings)
        self._refresh_summary(selected_codes, errors)

        now_enabled = len(errors) == 0 and len(selected_codes) > 0
        now_autofix = len(warnings) > 0
        self._build_btn.setEnabled(now_enabled)
        self._autofix_btn.setEnabled(now_autofix)

        # Pulse attention when build button transitions disabled → enabled
        if now_enabled and not self._build_btn_was_enabled:
            self._pulse_build_btn()
        if now_autofix and not self._autofix_btn_was_enabled:
            self._pulse_autofix_btn()
        self._build_btn_was_enabled = now_enabled
        self._autofix_btn_was_enabled = now_autofix

    def _pulse_build_btn(self) -> None:
        """One-shot opacity dip to draw attention when build becomes available.

        Uses a single QPropertyAnimation with key values for a dip-and-return
        effect — no bounce, no elastic, just a confident "I'm ready" signal.
        Duration: 420ms  |  Shape: 1.0 → 0.45 → 1.0  |  Easing: InOutCubic
        """
        if prefers_reduced_motion():
            return

        effect = QGraphicsOpacityEffect(self._build_btn)
        self._build_btn.setGraphicsEffect(effect)

        anim = QPropertyAnimation(effect, b"opacity", self._build_btn)
        anim.setDuration(motion_ms(420))
        anim.setKeyValueAt(0.0,  1.0)
        anim.setKeyValueAt(0.35, 0.45)   # quick fade to 45%
        anim.setKeyValueAt(1.0,  1.0)    # full recovery
        anim.setEasingCurve(QEasingCurve.InOutCubic)
        # Remove the effect after animation so the button stays fully opaque
        anim.finished.connect(lambda: self._build_btn.setGraphicsEffect(None))
        anim.start(QPropertyAnimation.DeleteWhenStopped)

    def _pulse_autofix_btn(self) -> None:
        """Highlight autofix availability when new warnings appear."""
        if prefers_reduced_motion():
            return

        effect = QGraphicsOpacityEffect(self._autofix_btn)
        self._autofix_btn.setGraphicsEffect(effect)

        anim = QPropertyAnimation(effect, b"opacity", self._autofix_btn)
        anim.setDuration(motion_ms(300))
        anim.setKeyValueAt(0.0, 1.0)
        anim.setKeyValueAt(0.4, 0.5)
        anim.setKeyValueAt(1.0, 1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.finished.connect(lambda: self._autofix_btn.setGraphicsEffect(None))
        anim.start(QPropertyAnimation.DeleteWhenStopped)

    def _press_feedback(self, btn: QPushButton) -> None:
        """Instant micro-feedback for button presses."""
        if prefers_reduced_motion() or not btn.isEnabled():
            return

        effect = QGraphicsOpacityEffect(btn)
        btn.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", btn)
        anim.setDuration(motion_ms(140))
        anim.setStartValue(0.72)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.finished.connect(lambda: btn.setGraphicsEffect(None))
        anim.start(QPropertyAnimation.DeleteWhenStopped)

    def clear(self) -> None:
        self._codes_list.clear()
        self._validation_list.clear()
        self._summary_label.setText("لم يتم اختيار أكواد بعد")
        self._build_btn.setEnabled(False)
        self._autofix_btn.setEnabled(False)
        self._build_btn_was_enabled = False
        self._autofix_btn_was_enabled = False

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _sorted_codes(self, selected: list[str]) -> list[str]:
        def key(cid: str) -> int:
            c = self._codes.get(cid, {})
            return _safe_int(c.get("sequence_order"), 9999)
        return sorted(selected, key=key)

    def _refresh_codes_list(self, selected_codes: list[str]) -> None:
        self._codes_list.clear()
        for cid in self._sorted_codes(selected_codes):
            cdata = self._codes.get(cid, {})
            name_ar = cdata.get("activity_name_ar", cid)
            pages = _safe_int(cdata.get("page_count"), 0)
            has_content = _CONTENT_LIB.exists(cid)
            icon = "🟢" if has_content else "🔘"
            tooltip = "محتوى Word حقيقي مرتبط" if has_content else "placeholder — لا يوجد ملف Word بعد"
            item = QListWidgetItem(f"{icon} {cid}  —  {name_ar}  ({pages} صفحة)")
            item.setToolTip(tooltip)
            if has_content:
                item.setForeground(QColor(_COLOR_OK))
                item.setBackground(QColor(_BG_CONTENT_REAL))
            else:
                item.setForeground(QColor("#5B6672"))
                item.setBackground(QColor(_BG_CONTENT_PLACEHOLDER))
            self._codes_list.addItem(item)

    def _refresh_validation(self, errors: list[str], warnings: list[str]) -> None:
        self._validation_list.clear()
        for msg in errors:
            item = QListWidgetItem(f"✗  {msg}")
            item.setForeground(QColor(_COLOR_ERROR))
            item.setBackground(QColor(_BG_ERROR))
            self._validation_list.addItem(item)
        for msg in warnings:
            item = QListWidgetItem(f"⚠  {msg}")
            item.setForeground(QColor(_COLOR_WARNING))
            item.setBackground(QColor(_BG_WARNING))
            self._validation_list.addItem(item)
        if not errors and not warnings and self._codes_list.count() > 0:
            ok_item = QListWidgetItem("✓  جميع الأكواد صحيحة")
            ok_item.setForeground(QColor(_COLOR_OK))
            ok_item.setBackground(QColor(_BG_OK))
            self._validation_list.addItem(ok_item)
        elif self._codes_list.count() == 0:
            info_item = QListWidgetItem("ℹ  اختر أكواداً لبدء التحقق")
            info_item.setForeground(QColor(_COLOR_INFO))
            info_item.setBackground(QColor(_BG_INFO))
            self._validation_list.addItem(info_item)

    def _refresh_summary(self, selected_codes: list[str], errors: list[str]) -> None:
        if not selected_codes:
            self._summary_label.setText("لم يتم اختيار أكواد بعد")
            self._summary_label.setStyleSheet(
                "font-weight: bold; padding: 5px 8px; color: #30465E; "
                "background: #EEF3FA; border: 1px solid #D5E1F0; border-radius: 7px;"
            )
            return

        total_pages = sum(
            _safe_int(self._codes.get(cid, {}).get("page_count"), 0)
            for cid in selected_codes
        )
        real_count = sum(1 for cid in selected_codes if _CONTENT_LIB.exists(cid))
        ph_count = len(selected_codes) - real_count
        content_note = (
            f"🟢 {real_count} حقيقي"
            + (f"  🔘 {ph_count} placeholder" if ph_count else "")
        )
        status_color = _COLOR_ERROR if errors else _COLOR_OK
        status_text = "يوجد أخطاء" if errors else "جاهز للبناء"
        self._summary_label.setText(
            f"{len(selected_codes)} كود  |  {total_pages} صفحة تقريباً  |  "
            f"{content_note}  |  {status_text}"
        )
        bg_color = _BG_ERROR if errors else _BG_OK
        border_color = "#E3B6B6" if errors else "#B9D9C2"
        self._summary_label.setStyleSheet(
            f"font-weight: bold; padding: 5px 8px; color: {status_color}; "
            f"background: {bg_color}; border: 1px solid {border_color}; border-radius: 7px;"
        )
