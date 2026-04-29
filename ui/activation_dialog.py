#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ATPAS Activation Dialog
========================
تظهر عند أول تشغيل أو عند انتهاء صلاحية الترخيص.
تعرض Machine ID للمستخدم ليُرسله للمطور، ثم يُدخل الـ License Key.
"""

from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from utils.license_manager import activate, get_machine_id


class ActivationDialog(QDialog):
    """نافذة تفعيل ATPAS — تُعرض عند أول تشغيل."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("تفعيل ATPAS")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setFixedSize(560, 400)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self._machine_id = get_machine_id()
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(18)

        # Title
        title = QLabel("تفعيل نظام ATPAS")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet("color: #152433;")
        root.addWidget(title)

        # Subtitle
        sub = QLabel(
            "هذه النسخة مرتبطة بجهازك فقط.\n"
            "أرسل رقم الجهاز أدناه للحصول على مفتاح التفعيل."
        )
        sub.setAlignment(Qt.AlignCenter)
        sub.setWordWrap(True)
        sub.setStyleSheet("color: #5A6B7C; font-size: 13px;")
        root.addWidget(sub)

        # Machine ID display
        mid_label = QLabel("رقم جهازك  (Machine ID):")
        mid_label.setStyleSheet("font-weight: bold; color: #152433;")
        root.addWidget(mid_label)

        mid_row = QHBoxLayout()
        self._mid_display = QLineEdit(self._machine_id)
        self._mid_display.setReadOnly(True)
        self._mid_display.setAlignment(Qt.AlignCenter)
        self._mid_display.setLayoutDirection(Qt.LeftToRight)
        self._mid_display.setFont(QFont("Courier New", 14, QFont.Bold))
        self._mid_display.setStyleSheet(
            "background: #EEF4FF; border: 2px solid #003D7A; "
            "border-radius: 8px; padding: 8px; color: #003D7A; "
            "letter-spacing: 2px;"
        )
        mid_row.addWidget(self._mid_display)

        copy_btn = QPushButton("نسخ")
        copy_btn.setFixedWidth(70)
        copy_btn.clicked.connect(self._copy_machine_id)
        copy_btn.setStyleSheet(
            "QPushButton { background: #003D7A; color: white; "
            "border-radius: 7px; font-weight: bold; padding: 8px; }"
            "QPushButton:hover { background: #002A5C; }"
        )
        mid_row.addWidget(copy_btn)
        root.addLayout(mid_row)

        # License key input
        key_label = QLabel("مفتاح التفعيل  (License Key):")
        key_label.setStyleSheet("font-weight: bold; color: #152433;")
        root.addWidget(key_label)

        self._key_input = QLineEdit()
        self._key_input.setPlaceholderText("ATPAS-XXXXX-XXXXX-XXXXX-XXXXX")
        self._key_input.setLayoutDirection(Qt.LeftToRight)
        self._key_input.setAlignment(Qt.AlignCenter)
        self._key_input.setFont(QFont("Courier New", 12))
        self._key_input.setStyleSheet(
            "background: white; border: 1px solid #C3BBAA; "
            "border-radius: 8px; padding: 8px; color: #121B28;"
        )
        self._key_input.returnPressed.connect(self._activate)
        root.addWidget(self._key_input)

        # Buttons
        btn_row = QHBoxLayout()
        exit_btn = QPushButton("خروج")
        exit_btn.setFixedWidth(110)
        exit_btn.clicked.connect(self.reject)
        exit_btn.setStyleSheet(
            "QPushButton { background: #FEFCF7; border: 1px solid #C3BBAA; "
            "border-radius: 7px; font-weight: bold; padding: 8px; color: #121B28; }"
            "QPushButton:hover { background: #FAF0DC; }"
        )
        activate_btn = QPushButton("تفعيل البرنامج")
        activate_btn.setFixedWidth(160)
        activate_btn.clicked.connect(self._activate)
        activate_btn.setStyleSheet(
            "QPushButton { background: #2B7549; color: white; "
            "border-radius: 7px; font-weight: 900; padding: 10px; border: none; }"
            "QPushButton:hover { background: #236040; }"
        )
        btn_row.addWidget(exit_btn)
        btn_row.addStretch()
        btn_row.addWidget(activate_btn)
        root.addLayout(btn_row)

        # Help hint
        hint = QLabel(
            "للحصول على مفتاح التفعيل، تواصل مع فريق الرواف بعد إتمام الشراء."
        )
        hint.setAlignment(Qt.AlignCenter)
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #8A9BAC; font-size: 11px;")
        root.addWidget(hint)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _copy_machine_id(self) -> None:
        QApplication.clipboard().setText(self._machine_id)
        QMessageBox.information(
            self,
            "تم النسخ",
            f"تم نسخ رقم الجهاز:\n{self._machine_id}\n\nأرسله لفريق الرواف للحصول على مفتاحك.",
        )

    def _activate(self) -> None:
        key = self._key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "مطلوب", "أدخل مفتاح التفعيل أولاً.")
            return

        success, message = activate(key)
        if success:
            QMessageBox.information(self, "تم التفعيل", message)
            self.accept()
        else:
            QMessageBox.critical(self, "فشل التفعيل", message)
