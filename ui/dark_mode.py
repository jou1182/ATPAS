#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Dark Mode Manager — يبدّل بين الوضع الفاتح والداكن في كامل التطبيق.

الآلية:
- يحقن CSS داكن إضافي يغلب على الثيم الأساسي
- يبدّل QPalette إلى ألوان داكنة
- يحفظ التفضيل في QSettings
- يُطلق إشارة عند التبديل لتحديث الـ widgets المخصصة
"""

from __future__ import annotations

from PyQt5.QtCore import QObject, QSettings, pyqtSignal
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QApplication

# Dark palette lives in theme.py now (single SSOT). Re-exported here so
# existing imports keep working.
from ui.theme import (  # noqa: F401
    DARK_ACCENT,
    DARK_BG,
    DARK_BORDER,
    DARK_BORDER2,
    DARK_ERROR,
    DARK_HEADER,
    DARK_HOVER,
    DARK_INPUT,
    DARK_SUCCESS,
    DARK_SURFACE,
    DARK_TEXT,
    DARK_TEXT2,
    DARK_WARNING,
)


class DarkModeManager(QObject):
    """يدير حالة Dark Mode ويطبق التغييرات على كامل التطبيق."""

    # يُطلق عند التبديل — الـ widgets المخصصة تستمع لتحديث CSS
    dark_mode_changed = pyqtSignal(bool)

    def __init__(self, settings: QSettings, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self._active: bool = self._settings.value("darkMode", False, type=bool)

    # ── Properties ────────────────────────────────────────────────────

    @property
    def is_active(self) -> bool:
        return self._active

    # ── Public API ────────────────────────────────────────────────────

    def toggle(self) -> bool:
        """تبديل الوضع. تعيد الحالة الجديدة (True = داكن)."""
        self._active = not self._active
        self._settings.setValue("darkMode", self._active)
        self._apply()
        self.dark_mode_changed.emit(self._active)
        return self._active

    def set_active(self, active: bool) -> None:
        """تعيين الوضع مباشرة."""
        if active == self._active:
            return
        self._active = active
        self._settings.setValue("darkMode", self._active)
        self._apply()
        self.dark_mode_changed.emit(self._active)

    def apply_if_active(self) -> None:
        """تطبيق Dark Mode إذا كان مفعّلاً (يُستدعى عند بدء التشغيل)."""
        if self._active:
            self._apply()

    # ── Internal ──────────────────────────────────────────────────────

    def _apply(self) -> None:
        """تطبيق Dark Mode على QApplication."""
        app = QApplication.instance()
        if app is None:
            return

        if self._active:
            self._apply_dark_palette(app)
            self._inject_dark_css(app)
        else:
            # استعادة الثيم الأصلي
            from ui.theme import apply_palette, get_stylesheet
            apply_palette(app)
            app.setStyleSheet(get_stylesheet())

    def _apply_dark_palette(self, app) -> None:
        """تطبيق QPalette داكن."""
        pal = QPalette()
        pal.setColor(QPalette.Window,          QColor(DARK_BG))
        pal.setColor(QPalette.WindowText,      QColor(DARK_TEXT))
        pal.setColor(QPalette.Base,            QColor(DARK_SURFACE))
        pal.setColor(QPalette.AlternateBase,   QColor(DARK_HOVER))
        pal.setColor(QPalette.Text,            QColor(DARK_TEXT))
        pal.setColor(QPalette.BrightText,      QColor(DARK_TEXT))
        pal.setColor(QPalette.Button,          QColor(DARK_SURFACE))
        pal.setColor(QPalette.ButtonText,      QColor(DARK_TEXT))
        pal.setColor(QPalette.Highlight,       QColor(DARK_ACCENT))
        pal.setColor(QPalette.HighlightedText, QColor("#000000"))
        pal.setColor(QPalette.ToolTipBase,     QColor(DARK_HEADER))
        pal.setColor(QPalette.ToolTipText,     QColor(DARK_TEXT))
        pal.setColor(QPalette.Midlight,        QColor(DARK_BORDER))
        pal.setColor(QPalette.Mid,             QColor(DARK_BORDER2))
        pal.setColor(QPalette.Dark,            QColor("#0A0A1A"))
        pal.setColor(QPalette.Shadow,          QColor("#00000044"))
        app.setPalette(pal)

    def _inject_dark_css(self, app) -> None:
        """حقن CSS داكن يغلب على الثيم الأساسي."""
        dark_css = f"""
        /* ════════════════════════════════════════════
           DARK MODE OVERRIDES
           ════════════════════════════════════════════ */
        QMainWindow, QDialog {{
            background: {DARK_BG};
            color: {DARK_TEXT};
        }}

        QWidget {{
            color: {DARK_TEXT};
        }}

        QWidget#mainCentral,
        QWidget#mainContent {{
            background: {DARK_BG};
            color: {DARK_TEXT};
        }}

        QDialog QWidget {{
            background: {DARK_SURFACE};
            color: {DARK_TEXT};
        }}

        QDialog QLabel {{
            color: {DARK_TEXT};
        }}

        QMessageBox {{
            background: {DARK_SURFACE};
        }}

        QMessageBox QLabel {{
            color: {DARK_TEXT};
        }}

        QGroupBox {{
            background: {DARK_SURFACE};
            border: 1px solid {DARK_BORDER2};
        }}

        QGroupBox::title {{
            background: {DARK_HOVER};
            color: {DARK_ACCENT};
            border: 1px solid {DARK_BORDER2};
        }}

        QCheckBox {{
            color: {DARK_TEXT};
        }}

        QCheckBox::indicator {{
            border: 2px solid {DARK_BORDER2};
            background: {DARK_INPUT};
        }}

        QCheckBox::indicator:hover {{
            border-color: {DARK_ACCENT};
        }}

        QCheckBox::indicator:checked {{
            background: {DARK_ACCENT};
            border-color: {DARK_ACCENT};
        }}

        QPushButton {{
            background: {DARK_SURFACE};
            border: 1px solid {DARK_BORDER2};
            color: {DARK_TEXT};
        }}

        QPushButton:hover {{
            background: {DARK_HOVER};
            border-color: {DARK_ACCENT};
            color: {DARK_ACCENT};
        }}

        QPushButton:focus {{
            border: 2px solid {DARK_ACCENT};
            color: {DARK_ACCENT};
        }}

        QPushButton:pressed {{
            background: #2A3555;
            border-color: {DARK_ACCENT};
        }}

        QPushButton:disabled {{
            background: #1A1A2E;
            color: #555;
            border-color: #2A2A4A;
        }}

        QPushButton#buildBtn {{
            background: {DARK_SUCCESS};
            color: white;
        }}

        QPushButton#buildBtn:hover {{
            background: #388E3C;
        }}

        QLineEdit {{
            background: {DARK_INPUT};
            border: 1.5px solid {DARK_BORDER2};
            color: {DARK_TEXT};
        }}

        QLineEdit:focus {{
            border: 2px solid {DARK_ACCENT};
        }}

        QLineEdit:hover {{
            border-color: {DARK_ACCENT};
        }}

        QLineEdit#codeSearchBox {{
            background: #1E2A45;
        }}

        QComboBox {{
            background: {DARK_INPUT};
            border: 1px solid {DARK_BORDER2};
            color: {DARK_TEXT};
        }}

        QComboBox:hover {{
            border-color: {DARK_ACCENT};
        }}

        QComboBox:focus {{
            border: 2px solid {DARK_ACCENT};
        }}

        QComboBox QAbstractItemView {{
            background: {DARK_SURFACE};
            border: 1px solid {DARK_BORDER};
            selection-background-color: {DARK_HOVER};
            selection-color: {DARK_ACCENT};
        }}

        QListWidget {{
            background: {DARK_SURFACE};
            border: 1px solid {DARK_BORDER};
        }}

        QListWidget::item {{
            color: {DARK_TEXT};
        }}

        QListWidget::item:selected {{
            background: {DARK_HOVER};
            color: {DARK_ACCENT};
            border-left: 4px solid {DARK_ACCENT};
        }}

        QListWidget::item:hover:!selected {{
            background: #1E2A45;
        }}

        QTableWidget, QTableView {{
            background: {DARK_SURFACE};
            alternate-background-color: {DARK_HOVER};
            gridline-color: {DARK_BORDER};
            selection-background-color: {DARK_HOVER};
            selection-color: {DARK_ACCENT};
        }}

        QHeaderView::section {{
            background: {DARK_HEADER};
            color: {DARK_ACCENT};
        }}

        QScrollBar::handle:vertical {{
            background: {DARK_BORDER2};
        }}

        QScrollBar::handle:vertical:hover {{
            background: {DARK_ACCENT};
        }}

        QScrollBar::handle:horizontal {{
            background: {DARK_BORDER2};
        }}

        QScrollBar::handle:horizontal:hover {{
            background: {DARK_ACCENT};
        }}

        QSpinBox {{
            background: {DARK_INPUT};
            border: 1px solid {DARK_BORDER2};
            color: {DARK_TEXT};
        }}

        QSpinBox:focus {{
            border: 2px solid {DARK_ACCENT};
        }}

        QSpinBox::up-button, QSpinBox::down-button {{
            background: {DARK_HOVER};
        }}

        QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
            background: {DARK_ACCENT};
        }}

        QStatusBar {{
            background: {DARK_HEADER};
            color: {DARK_ACCENT};
        }}

        QProgressBar {{
            background: {DARK_BORDER2};
            color: {DARK_TEXT};
        }}

        QProgressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #A07020,
                stop:0.6 {DARK_ACCENT},
                stop:1.0 #F0C860);
        }}

        QTabWidget::pane {{
            background: {DARK_SURFACE};
            border: 1px solid {DARK_BORDER2};
        }}

        QTabBar::tab {{
            background: #1A1A2E;
            color: {DARK_TEXT2};
            border: 1px solid {DARK_BORDER2};
        }}

        QTabBar::tab:selected {{
            background: {DARK_SURFACE};
            color: {DARK_ACCENT};
            border-top: 3px solid {DARK_ACCENT};
        }}

        QTabBar::tab:hover:!selected {{
            background: {DARK_HOVER};
            color: {DARK_ACCENT};
        }}

        QToolTip {{
            background: {DARK_HEADER};
            color: {DARK_TEXT};
            border: 1px solid {DARK_ACCENT};
        }}

        QFrame[frameShape="4"],
        QFrame[frameShape="5"] {{
            border-top: 1px solid {DARK_BORDER};
        }}
        """
        app.setStyleSheet(dark_css)
