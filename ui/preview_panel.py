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

import csv
from pathlib import Path
from typing import Any

from PyQt5.QtCore import QEasingCurve, QPropertyAnimation, Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QDialog,
    QFileDialog,
    QGraphicsOpacityEffect,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from utils.content_library import ContentLibrary
from ui import theme
from ui.motion import motion_ms, prefers_reduced_motion

_CONTENT_LIB = ContentLibrary()   # shared singleton — reads templates/source_documents/

_COLOR_ERROR = theme.ERROR
_COLOR_WARNING = theme.WARNING
_COLOR_OK = theme.SUCCESS
_COLOR_INFO = theme.INFO

_BG_CONTENT_REAL = theme.SUCCESS_PALE
_BG_CONTENT_PLACEHOLDER = theme.NEUTRAL_PALE
_BG_ERROR = theme.ERROR_PALE
_BG_WARNING = theme.WARNING_PALE
_BG_OK = theme.SUCCESS_PALE
_BG_INFO = theme.INFO_PALE


def _section_title(text: str) -> QLabel:
    """Create an internal section title to avoid clipped QGroupBox titles."""
    label = QLabel(text)
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet(
        f"font-size: 12px; font-weight: 800; color: {theme.HEADER}; "
        f"background: {theme.ACCENT_PALE}; border: 1px solid {theme.BORDER}; "
        "border-radius: 6px; padding: 4px 10px;"
    )
    return label


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

    def __init__(
        self,
        registry_data: dict[str, Any],
        config_data: dict[str, Any] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)

        self._codes: dict[str, dict] = registry_data.get("codes", {})
        self._code_ranges: dict[str, dict] = (config_data or {}).get("code_ranges", {})

        # أُزيل العنوان المكرر — شريط الجاهزية أدناه يؤدي الدور (توفير ارتفاع)
        self._summary_label = None
        self._readiness_label = QLabel("جاهزية التسليم: لم يتم اختيار أكواد بعد")
        self._readiness_label.setAlignment(Qt.AlignCenter)
        self._readiness_label.setWordWrap(True)
        self._readiness_label.setStyleSheet(
            "font-weight: 800; padding: 6px 10px; color: #30465E; "
            "background: #EEF3FA; border: 1px solid #D5E1F0; border-radius: 8px;"
        )

        # Code list
        codes_box = QGroupBox("")
        codes_box.setLayoutDirection(Qt.RightToLeft)
        codes_layout = QVBoxLayout(codes_box)
        codes_layout.setContentsMargins(10, 10, 10, 10)
        codes_layout.setSpacing(8)
        codes_layout.addWidget(_section_title("الأكواد المختارة (مرتبة حسب التسلسل)"))
        self._codes_list = QListWidget()
        self._codes_list.setLayoutDirection(Qt.RightToLeft)
        self._codes_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._codes_list.setMinimumHeight(44)   # أرضية مرنة — لا انهار كشرائحة
        codes_layout.addWidget(self._codes_list)

        # Validation messages
        val_box = QGroupBox("")
        val_box.setLayoutDirection(Qt.RightToLeft)
        val_layout = QVBoxLayout(val_box)
        val_layout.setContentsMargins(10, 10, 10, 10)
        val_layout.setSpacing(8)
        val_layout.addWidget(_section_title("التحقق والتحذيرات"))
        self._validation_list = QListWidget()
        self._validation_list.setLayoutDirection(Qt.RightToLeft)
        self._validation_list.setMinimumHeight(40)   # نفس الحماية من الانهيار
        self._validation_list.setMaximumHeight(140)
        val_layout.addWidget(self._validation_list)

        # Buttons — top row: auto-fix + build
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

        # Secondary row: CSV export
        export_row = QHBoxLayout()
        self._outline_btn = QPushButton("🧭  معاينة هيكل العرض")
        self._outline_btn.setEnabled(False)
        self._outline_btn.setToolTip("عرض ترتيب الأكواد المتوقع قبل بناء ملف Word")
        self._outline_btn.clicked.connect(self._on_show_outline)
        self._export_btn = QPushButton("📊  تصدير CSV")
        self._export_btn.setEnabled(False)
        self._export_btn.setToolTip(
            "تصدير قائمة الأكواد المختارة إلى ملف CSV\n"
            "(يمكن فتحه في Excel للمراجعة أو المقارنة)"
        )
        self._export_btn.setCursor(Qt.PointingHandCursor)
        self._export_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {theme.INFO};
                border: 1px solid {theme.INFO}60;
                border-radius: 5px;
                font-size: 11px;
                padding: 4px 14px;
            }}
            QPushButton:hover  {{ background: {theme.INFO_PALE}; border-color: {theme.INFO}; }}
            QPushButton:pressed {{ background: #C8E5F5; }}
            QPushButton:disabled {{ color: #AAB8C4; border-color: #DDEAF4; }}
        """)
        self._export_btn.clicked.connect(self._on_export_csv)
        export_row.addStretch()
        export_row.addWidget(self._outline_btn)
        export_row.addWidget(self._export_btn)

        # Keep a reference to current selected codes for the export action
        self._current_selected: list[str] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)
        root.addWidget(self._readiness_label)
        root.addWidget(codes_box, stretch=3)
        root.addWidget(val_box, stretch=2)
        # صف أزرار واحد: إصلاح | بناء | (مساحة) | هيكل | CSV — توفير صف كامل
        btn_layout.addStretch()
        btn_layout.addWidget(self._outline_btn)
        btn_layout.addWidget(self._export_btn)
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
        self._current_selected = list(selected_codes)
        self._refresh_codes_list(selected_codes)
        self._refresh_validation(errors, warnings)
        self._refresh_readiness(selected_codes, errors, warnings)

        now_enabled = len(errors) == 0 and len(selected_codes) > 0
        now_autofix = len(warnings) > 0
        self._build_btn.setEnabled(now_enabled)
        self._autofix_btn.setEnabled(now_autofix)
        self._export_btn.setEnabled(len(selected_codes) > 0)
        self._outline_btn.setEnabled(len(selected_codes) > 0)

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
        self._current_selected = []
        self._codes_list.clear()
        self._validation_list.clear()
        self._readiness_label.setText("جاهزية التسليم: لم يتم اختيار أكواد بعد")
        self._readiness_label.setStyleSheet(
            "font-weight: 800; padding: 6px 10px; color: #30465E; "
            "background: #EEF3FA; border: 1px solid #D5E1F0; border-radius: 8px;"
        )
        self._build_btn.setEnabled(False)
        self._autofix_btn.setEnabled(False)
        self._export_btn.setEnabled(False)
        self._outline_btn.setEnabled(False)
        self._build_btn_was_enabled = False
        self._autofix_btn_was_enabled = False

    def _on_export_csv(self) -> None:
        """Export selected codes to a UTF-8 CSV file."""
        if not self._current_selected:
            return

        default_name = f"ATPAS_codes_{len(self._current_selected)}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "تصدير قائمة الأكواد",
            str(Path.home() / "Desktop" / default_name),
            "CSV Files (*.csv);;All Files (*)",
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "رقم",
                    "كود",
                    "الاسم العربي",
                    "الاسم الإنجليزي",
                    "الفئة",
                    "الشبكة",
                    "الصفحات",
                    "الترتيب",
                    "محتوى حقيقي",
                ])
                for i, cid in enumerate(self._sorted_codes(self._current_selected), 1):
                    c = self._codes.get(cid, {})
                    has_content = _CONTENT_LIB.exists(cid)
                    writer.writerow([
                        i,
                        cid,
                        c.get("activity_name_ar", ""),
                        c.get("activity_name_en", ""),
                        c.get("category", ""),
                        c.get("network", ""),
                        _safe_int(c.get("page_count"), 0),
                        _safe_int(c.get("sequence_order"), 0),
                        "نعم" if has_content else "لا",
                    ])

            QMessageBox.information(
                self,
                "تم التصدير",
                f"تم تصدير {len(self._current_selected)} كود إلى:\n{path}",
            )
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "خطأ", f"تعذّر التصدير:\n{exc}")

    def _on_show_outline(self) -> None:
        """Show the expected proposal outline before building.

        A tree grouped by category (001–005) with per-code columns
        (code, name, pages, content) — collapsible, colour-coded,
        matching the actual built document structure.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("معاينة هيكل العرض الفني")
        dialog.setLayoutDirection(Qt.RightToLeft)
        dialog.resize(760, 560)

        layout = QVBoxLayout(dialog)
        title = QLabel("هيكل العرض المتوقع قبل البناء — حسب مراحل التنفيذ")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"font-size: 16px; font-weight: 900; color: {theme.HEADER}; "
            f"border-bottom: 2px solid {theme.ACCENT}; padding-bottom: 8px;"
        )

        tree = QTreeWidget(dialog)
        tree.setLayoutDirection(Qt.RightToLeft)
        tree.setColumnCount(4)
        tree.setHeaderLabels(["المرحلة / الكود", "الكود", "الصفحات", "المحتوى"])
        tree.setAlternatingRowColors(True)
        header = tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, header.ResizeMode.Stretch)

        self._populate_outline_tree(tree)
        tree.expandAll()

        # Summary header
        total_codes = len(self._current_selected)
        total_pages = sum(
            _safe_int(self._codes.get(cid, {}).get("page_count"), 0)
            for cid in self._current_selected
        )
        total_cats = len(self._outline_categories())
        summary = QLabel(
            f"📦 {total_codes} كوداً  ·  📄 {total_pages} صفحة  ·  🗂 {total_cats} مراحل"
        )
        summary.setAlignment(Qt.AlignCenter)
        summary.setStyleSheet(
            f"font-weight: 800; padding: 5px; color: {theme.HEADER}; "
            f"background: {theme.ACCENT_PALE}; border-radius: 6px;"
        )

        btn_row = QHBoxLayout()
        expand_btn = QPushButton("توسيع الكل")
        expand_btn.clicked.connect(tree.expandAll)
        collapse_btn = QPushButton("طي الكل")
        collapse_btn.clicked.connect(tree.collapseAll)
        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(dialog.accept)
        btn_row.addWidget(expand_btn)
        btn_row.addWidget(collapse_btn)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)

        layout.addWidget(title)
        layout.addWidget(summary)
        layout.addWidget(tree, stretch=1)
        layout.addLayout(btn_row)
        dialog.exec_()

    def _outline_categories(self) -> list[str]:
        """Ordered list of category ids present in the current selection."""
        cats: list[str] = []
        for cid in self._sorted_codes(self._current_selected):
            c = self._codes.get(cid, {})
            cat = str(c.get("category", ""))
            if cat and cat not in cats:
                cats.append(cat)
        return cats

    def _populate_outline_tree(self, tree: QTreeWidget) -> None:
        """Fill the tree: category top-level rows → code child rows."""
        tree.clear()
        if tree.columnCount() < 4:
            tree.setColumnCount(4)
            tree.setHeaderLabels(["المرحلة / الكود", "الكود", "الصفحات", "المحتوى"])
        cat_color = {
            "001": theme.CTX_INFRA,
            "002": theme.CTX_WATER,
            "003": theme.CTX_ROAD,
            "004": theme.CTX_BUILD,
            "005": theme.CTX_MIXED,
        }

        # Group selected codes by category, preserving sequence order
        grouped: dict[str, list[str]] = {}
        for cid in self._sorted_codes(self._current_selected):
            c = self._codes.get(cid, {})
            cat = str(c.get("category", "") or "أخرى")
            grouped.setdefault(cat, []).append(cid)

        for cat in self._outline_categories() or grouped.keys():
            codes = grouped.get(cat, [])
            info = self._code_ranges.get(cat, {})
            cat_name = info.get("category_name_ar") or cat
            cat_pages = sum(
                _safe_int(self._codes.get(cid, {}).get("page_count"), 0)
                for cid in codes
            )
            color = cat_color.get(cat, theme.NEUTRAL)

            cat_item = QTreeWidgetItem(tree)
            cat_item.setText(0, f"📂 {cat_name}")
            cat_item.setText(1, "")
            cat_item.setText(2, str(cat_pages))
            cat_item.setText(3, f"{len(codes)} نشاط")
            cat_item.setForeground(0, QColor(color))
            font = cat_item.font(0)
            font.setBold(True)
            cat_item.setFont(0, font)

            for cid in codes:
                c = self._codes.get(cid, {})
                name_ar = c.get("activity_name_ar", cid)
                pages = _safe_int(c.get("page_count"), 0)
                has_content = _CONTENT_LIB.exists(cid)

                child = QTreeWidgetItem(cat_item)
                child.setText(0, name_ar)
                child.setText(1, cid)
                child.setText(2, str(pages))
                child.setText(3, "🟢 Word" if has_content else "🔘 بديل")
                child.setToolTip(
                    3,
                    "محتوى Word حقيقي" if has_content
                    else "لا يوجد ملف Word بعد — سيُعرض نص بديل",
                )
                if has_content:
                    child.setForeground(3, QColor(_COLOR_OK))
                else:
                    child.setForeground(3, QColor(theme.NEUTRAL))
                child.setTextAlignment(2, Qt.AlignCenter)

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
                item.setForeground(QColor(theme.NEUTRAL))
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

    def _refresh_readiness(
        self,
        selected_codes: list[str],
        errors: list[str],
        warnings: list[str],
    ) -> None:
        if not selected_codes:
            self._readiness_label.setText("جاهزية التسليم: لم يتم اختيار أكواد بعد")
            return
        missing_content = [cid for cid in selected_codes if not _CONTENT_LIB.exists(cid)]
        if errors:
            text = f"جاهزية التسليم: غير جاهز - {len(errors)} خطأ يمنع البناء"
            color, bg, border = _COLOR_ERROR, _BG_ERROR, theme.ERROR
        elif missing_content:
            text = (
                f"جاهزية التسليم: يحتاج مراجعة محتوى - "
                f"{len(missing_content)} كود بلا ملف Word"
            )
            color, bg, border = _COLOR_WARNING, _BG_WARNING, theme.WARNING
        elif warnings:
            text = f"جاهزية التسليم: صالح مع {len(warnings)} تحذير"
            color, bg, border = _COLOR_WARNING, _BG_WARNING, theme.WARNING
        else:
            text = "جاهزية التسليم: جاهز للتسليم"
            color, bg, border = _COLOR_OK, _BG_OK, theme.SUCCESS
        self._readiness_label.setText(text)
        self._readiness_label.setStyleSheet(
            f"font-weight: 900; padding: 6px 10px; color: {color}; "
            f"background: {bg}; border: 1px solid {border}; border-radius: 8px;"
        )
